# -*- coding: utf-8 -*-
"""
은하 이미지 영역(ROI) 측광 · 형태 분석 엔진
============================================
사진/FITS 위에 그린 영역을 받아 다음을 계산합니다.

- 영역 통계: 픽셀 수, 합/평균/중앙값/표준편차, 배경(시그마 클리핑), 순 플럭스, S/N
- 위치/모양: 광도 가중 중심, 2차 모멘트 → 타원율 · 방위각 · 등가 반경
- 반경 밝기 프로파일, 누적 광량 → R20 · R50 · R80 · R90, Petrosian 반경(η=0.2)
- 비모수 형태 지수: 집중도 C (CAS, SDSS), 비대칭도 A, 매끄러움 S, Gini, M20
- Sérsic 프로파일 피팅 → n (n≈1 원반, n≈4 타원)
- RGB 색지수 프록시 (B−R, G−R)
- 규칙 기반 형태 분류 (조기형/만기형/불규칙/병합 후보) + ML 입력 특성 추정
- 선 단면(Cuts) 프로파일, 모의 은하 이미지 생성기 (테스트용)

참고문헌: Conselice 2003 (CAS), Lotz+2004/2008 (Gini–M20), Graham & Driver 2005 (Sérsic),
Blanton+2003 / Strateva+2001 (SDSS 집중도 C=R90/R50 ≈ 2.6 경계)
"""

import math
import warnings
import numpy as np
from scipy import ndimage, optimize
from PIL import Image, ImageDraw


# ═══════════════════════════════════════════════════════
#           캔버스 객체(fabric.js) → 마스크 변환
# ═══════════════════════════════════════════════════════
class RegionGeometry:
    """streamlit-drawable-canvas 의 JSON 객체를 원본 해상도 마스크로 변환"""

    @staticmethod
    def _rot(px, py, ox, oy, angle_deg):
        if not angle_deg:
            return px, py
        a = math.radians(angle_deg)
        dx, dy = px - ox, py - oy
        return ox + dx * math.cos(a) - dy * math.sin(a), oy + dx * math.sin(a) + dy * math.cos(a)

    @staticmethod
    def _path_points(path):
        pts = []
        for seg in path or []:
            if not seg:
                continue
            nums = [v for v in seg[1:] if isinstance(v, (int, float))]
            for i in range(0, len(nums) - 1, 2):
                pts.append((float(nums[i]), float(nums[i + 1])))
        return pts

    _ORIGIN = {'left': 0.5, 'top': 0.5, 'center': 0.0, 'right': -0.5, 'bottom': -0.5}

    @classmethod
    def _center(cls, obj):
        """fabric 객체의 캔버스상 중심점: origin 점(left, top) + R(angle)·(origin→center 오프셋)"""
        sx = float(obj.get('scaleX', 1.0) or 1.0)
        sy = float(obj.get('scaleY', 1.0) or 1.0)
        sw = float(obj.get('strokeWidth', 0) or 0)
        w = (float(obj.get('width', 0) or 0) + sw) * sx
        h = (float(obj.get('height', 0) or 0) + sw) * sy
        ox = cls._ORIGIN.get(str(obj.get('originX', 'left')), 0.5) * w
        oy = cls._ORIGIN.get(str(obj.get('originY', 'top')), 0.5) * h
        left = float(obj.get('left', 0.0) or 0.0)
        top = float(obj.get('top', 0.0) or 0.0)
        return cls._rot(left + ox, top + oy, left, top, float(obj.get('angle', 0.0) or 0.0))

    @classmethod
    def _local_to_canvas(cls, obj, pts):
        """객체 중심 기준 로컬 좌표 → 캔버스 좌표 (scale → rotate → translate)"""
        sx = float(obj.get('scaleX', 1.0) or 1.0)
        sy = float(obj.get('scaleY', 1.0) or 1.0)
        a = math.radians(float(obj.get('angle', 0.0) or 0.0))
        ca, sa = math.cos(a), math.sin(a)
        cx, cy = cls._center(obj)
        out = []
        for lx, ly in pts:
            x, y = lx * sx, ly * sy
            out.append((cx + x * ca - y * sa, cy + x * sa + y * ca))
        return out

    @classmethod
    def object_to_shape(cls, obj, scale):
        """캔버스 객체 → (kind, 원본 좌표 기하정보) ; kind ∈ rect/circle/line/polygon"""
        t = obj.get('type', '')
        sx = float(obj.get('scaleX', 1.0) or 1.0)
        sy = float(obj.get('scaleY', 1.0) or 1.0)
        angle = float(obj.get('angle', 0.0) or 0.0)
        inv = 1.0 / scale

        if t == 'rect':
            w2 = float(obj.get('width', 0)) / 2
            h2 = float(obj.get('height', 0)) / 2
            corners = cls._local_to_canvas(obj, [(-w2, -h2), (w2, -h2), (w2, h2), (-w2, h2)])
            return 'rect', {'points': [(x * inv, y * inv) for x, y in corners], 'angle': angle}

        if t in ('circle', 'ellipse'):
            rx = float(obj.get('radius', obj.get('rx', 0)) or 0) * sx
            ry = float(obj.get('radius', obj.get('ry', 0)) or 0) * sy
            cx, cy = cls._center(obj)
            return 'circle', {'cx': cx * inv, 'cy': cy * inv, 'rx': max(rx * inv, 1.0),
                              'ry': max(ry * inv, 1.0), 'angle': angle}

        if t == 'line':
            # fabric.Line.toObject() 의 x1..y2 는 객체 중심 기준 좌표(calcLinePoints)
            p = cls._local_to_canvas(obj, [(float(obj.get('x1', 0)), float(obj.get('y1', 0))),
                                           (float(obj.get('x2', 0)), float(obj.get('y2', 0)))])
            (x1, y1), (x2, y2) = p
            return 'line', {'x1': x1 * inv, 'y1': y1 * inv, 'x2': x2 * inv, 'y2': y2 * inv,
                            'width': float(obj.get('strokeWidth', 3)) * inv}

        if t in ('path', 'polygon', 'polyline'):
            po = obj.get('pathOffset') or {}
            if t == 'path':
                raw = cls._path_points(obj.get('path'))
            else:
                raw = [(float(q['x']), float(q['y'])) for q in obj.get('points', [])]
            if po:
                pox, poy = float(po.get('x', 0)), float(po.get('y', 0))
                pts = cls._local_to_canvas(obj, [(x - pox, y - poy) for x, y in raw])
            else:
                pts = raw  # pathOffset 이 없으면 절대 좌표로 간주
            closed = t == 'polygon' or any(isinstance(seg, list) and seg and str(seg[0]).lower() == 'z'
                                           for seg in (obj.get('path') or []))
            return 'polygon', {'points': [(x * inv, y * inv) for x, y in pts], 'closed': closed,
                               'stroke': float(obj.get('strokeWidth', 3)) * inv}

        return None, {}

    @classmethod
    def object_to_mask(cls, obj, shape, scale, freedraw_as='area'):
        """캔버스 객체 → bool 마스크 (원본 해상도). freedraw_as: 'area'(올가미) | 'stroke'(붓)"""
        h, w = shape[:2]
        kind, g = cls.object_to_shape(obj, scale)
        canvas = Image.new('L', (w, h), 0)
        draw = ImageDraw.Draw(canvas)
        if kind == 'rect':
            draw.polygon(g['points'], fill=1)
        elif kind == 'circle':
            if g['angle']:
                ts = np.linspace(0, 2 * np.pi, 120)
                a = math.radians(g['angle'])
                pts = [(g['cx'] + g['rx'] * np.cos(t) * math.cos(a) - g['ry'] * np.sin(t) * math.sin(a),
                        g['cy'] + g['rx'] * np.cos(t) * math.sin(a) + g['ry'] * np.sin(t) * math.cos(a))
                       for t in ts]
                draw.polygon(pts, fill=1)
            else:
                draw.ellipse([g['cx'] - g['rx'], g['cy'] - g['ry'], g['cx'] + g['rx'], g['cy'] + g['ry']], fill=1)
        elif kind == 'line':
            draw.line([(g['x1'], g['y1']), (g['x2'], g['y2'])], fill=1, width=max(1, int(round(g['width']))))
        elif kind == 'polygon':
            pts = g['points']
            if len(pts) >= 3 and freedraw_as == 'area':
                draw.polygon(pts, fill=1)
            elif len(pts) >= 2:
                draw.line(pts, fill=1, width=max(2, int(round(g['stroke'] * 3))))
            elif len(pts) == 1:
                x, y = pts[0]
                draw.ellipse([x - 3, y - 3, x + 3, y + 3], fill=1)
        else:
            return None, kind
        return np.array(canvas, dtype=bool), kind


# ═══════════════════════════════════════════════════════
#                     측광 · 형태 분석
# ═══════════════════════════════════════════════════════
def sigma_clipped_stats(x, sigma=3.0, iters=5):
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    if len(x) == 0:
        return 0.0, 0.0, 0.0
    for _ in range(iters):
        med = np.median(x)
        sd = np.std(x)
        keep = np.abs(x - med) < sigma * sd if sd > 0 else np.ones_like(x, bool)
        if keep.all():
            break
        x = x[keep]
        if len(x) < 5:
            break
    return float(np.mean(x)), float(np.median(x)), float(np.std(x))


class GalaxyImageAnalyzer:
    """선택 영역에 대한 측광 및 비모수/모수 형태 분석"""

    def __init__(self, pixel_scale_arcsec: float = 0.396):
        self.pixel_scale = pixel_scale_arcsec  # SDSS 기본 0.396"/px

    # ── 기본 ─────────────────────────────────────────────
    @staticmethod
    def to_gray(arr):
        arr = np.asarray(arr)
        if arr.ndim == 3:
            rgb = arr[..., :3].astype(float)
            return 0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]
        return arr.astype(float)

    def background(self, gray, mask, ring=None):
        """배경: 마스크 주변 고리 영역(없으면 마스크 밖 전체)의 시그마 클리핑 중앙값"""
        outside = ~mask
        if ring is None:
            ys, xs = np.nonzero(mask)
            if len(ys) == 0:
                return 0.0, robust_noise(gray)
            it = max(5, int(np.sqrt(len(ys)) * 0.3))
            pad = it + 2
            y0, y1 = max(0, ys.min() - pad), min(gray.shape[0], ys.max() + pad + 1)
            x0, x1 = max(0, xs.min() - pad), min(gray.shape[1], xs.max() + pad + 1)
            sub_m = mask[y0:y1, x0:x1]
            dil = ndimage.binary_dilation(sub_m, iterations=it)
            ring_sub = dil & ~sub_m
            vals = gray[y0:y1, x0:x1][ring_sub]
            if vals.size < 30:
                vals = gray[outside]
                if vals.size > 400000:
                    vals = vals[:: vals.size // 400000]
        else:
            vals = gray[ring & outside]
        if vals.size < 10:
            return 0.0, robust_noise(gray)
        _, med, sd = sigma_clipped_stats(vals)
        return med, max(sd, 1e-9)

    def region_stats(self, image_array, mask, subtract_bg=True):
        gray = self.to_gray(image_array)
        mask = mask.astype(bool)
        n = int(mask.sum())
        if n == 0:
            return {'n_pix': 0}
        vals = gray[mask]
        bg, bg_sd = self.background(gray, mask) if subtract_bg else (0.0, robust_noise(gray))
        net = vals - bg
        net_flux = float(net.sum())
        snr = net_flux / (bg_sd * math.sqrt(n)) if bg_sd > 0 else float('nan')

        ys, xs = np.nonzero(mask)
        wts = np.clip(net, 0, None)
        if wts.sum() <= 0:
            wts = np.ones_like(net)
        cx = float(np.sum(xs * wts) / wts.sum())
        cy = float(np.sum(ys * wts) / wts.sum())
        mxx = np.sum(wts * (xs - cx) ** 2) / wts.sum()
        myy = np.sum(wts * (ys - cy) ** 2) / wts.sum()
        mxy = np.sum(wts * (xs - cx) * (ys - cy)) / wts.sum()
        tmp = math.sqrt(max(((mxx - myy) / 2) ** 2 + mxy ** 2, 0))
        l1 = (mxx + myy) / 2 + tmp
        l2 = max((mxx + myy) / 2 - tmp, 1e-12)
        a, b = math.sqrt(max(l1, 1e-12)), math.sqrt(l2)
        ellipticity = 1 - b / a if a > 0 else 0.0
        pa = math.degrees(0.5 * math.atan2(2 * mxy, mxx - myy))
        ipk = int(np.argmax(vals))

        out = {
            'n_pix': n, 'sum': float(vals.sum()), 'mean': float(vals.mean()),
            'median': float(np.median(vals)), 'std': float(vals.std()),
            'min': float(vals.min()), 'max': float(vals.max()),
            'background': float(bg), 'background_std': float(bg_sd),
            'net_flux': net_flux, 'snr': float(snr),
            'inst_mag': float(-2.5 * math.log10(net_flux)) if net_flux > 0 else None,
            'centroid_x': cx, 'centroid_y': cy,
            'peak_x': int(xs[ipk]), 'peak_y': int(ys[ipk]),
            'ellipticity': float(ellipticity), 'axis_ratio': float(b / a) if a > 0 else 1.0,
            'position_angle': float(pa), 'equiv_radius_px': float(math.sqrt(n / math.pi)),
            'bbox': (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())),
        }

        arr = np.asarray(image_array)
        if arr.ndim == 3 and arr.shape[2] >= 3:
            rgb = arr[..., :3].astype(float)
            r_m = float(np.mean(rgb[..., 0][mask]))
            g_m = float(np.mean(rgb[..., 1][mask]))
            b_m = float(np.mean(rgb[..., 2][mask]))
            r_bg = float(np.median(rgb[..., 0][~mask])) if (~mask).any() else 0.0
            g_bg = float(np.median(rgb[..., 1][~mask])) if (~mask).any() else 0.0
            b_bg = float(np.median(rgb[..., 2][~mask])) if (~mask).any() else 0.0
            R, G, B = max(r_m - r_bg, 1e-3), max(g_m - g_bg, 1e-3), max(b_m - b_bg, 1e-3)
            out.update({
                'mean_R': r_m, 'mean_G': g_m, 'mean_B': b_m,
                'color_BR': float(-2.5 * math.log10(B / R)),
                'color_GR': float(-2.5 * math.log10(G / R)),
            })
        return out

    # ── 반경 프로파일 ────────────────────────────────────
    def radial_profile(self, gray, cx, cy, mask=None, bg=0.0, rmax=None, nbins=None):
        h, w = gray.shape
        yy, xx = np.indices((h, w))
        r = np.hypot(xx - cx, yy - cy)
        valid = np.ones_like(gray, bool) if mask is None else mask
        if rmax is None:
            rmax = r[valid].max() if valid.any() else min(h, w) / 2
        rmax = max(rmax, 3)
        if nbins is None:
            nbins = int(min(60, max(8, rmax)))
        edges = np.linspace(0, rmax, nbins + 1)
        img = gray - bg
        centers, prof, cum = [], [], []
        idx = np.digitize(r[valid], edges) - 1
        v = img[valid]
        total = 0.0
        for i in range(nbins):
            sel = idx == i
            if sel.sum() == 0:
                continue
            centers.append(0.5 * (edges[i] + edges[i + 1]))
            prof.append(float(np.mean(v[sel])))
            total += float(np.sum(v[sel]))
            cum.append(total)
        return np.array(centers), np.array(prof), np.array(cum)

    @staticmethod
    def radius_at_fraction(r, cum, frac):
        if len(cum) == 0 or cum[-1] <= 0:
            return None
        c = np.maximum.accumulate(cum) / cum[-1]
        if c[0] >= frac:
            return float(r[0])
        j = np.searchsorted(c, frac)
        if j >= len(c):
            return float(r[-1])
        r0, r1, c0, c1 = r[j - 1], r[j], c[j - 1], c[j]
        return float(r0 + (frac - c0) * (r1 - r0) / (c1 - c0 + 1e-12))

    @staticmethod
    def petrosian_radius(r, prof, eta=0.2):
        """η(r) = I(r) / <I>(<r) = 0.2 인 반경"""
        if len(r) < 4:
            return None
        area = np.pi * r ** 2
        ring_flux = prof * np.gradient(area)
        mean_inside = np.cumsum(ring_flux) / np.maximum(area, 1e-9)
        ratio = prof / np.maximum(mean_inside, 1e-12)
        for i in range(1, len(r)):
            if ratio[i] < eta <= ratio[i - 1]:
                return float(r[i - 1] + (eta - ratio[i - 1]) * (r[i] - r[i - 1]) / (ratio[i] - ratio[i - 1] + 1e-12))
        return None

    # ── 비모수 형태 지수 ─────────────────────────────────
    @staticmethod
    def _cutout(gray, mask, cx, cy, pad=2):
        ys, xs = np.nonzero(mask)
        half = int(max(cx - xs.min(), xs.max() - cx, cy - ys.min(), ys.max() - cy)) + pad
        x0, x1 = int(round(cx)) - half, int(round(cx)) + half + 1
        y0, y1 = int(round(cy)) - half, int(round(cy)) + half + 1
        H, W = gray.shape
        px0, py0 = max(0, -x0), max(0, -y0)
        px1, py1 = max(0, x1 - W), max(0, y1 - H)
        g = np.pad(gray, ((py0, py1), (px0, px1)), mode='constant', constant_values=np.nan)
        m = np.pad(mask, ((py0, py1), (px0, px1)), mode='constant', constant_values=False)
        g = g[y0 + py0:y1 + py0, x0 + px0:x1 + px0]
        m = m[y0 + py0:y1 + py0, x0 + px0:x1 + px0]
        # 서브픽셀 중심 보정
        dx, dy = (cx - round(cx)), (cy - round(cy))
        g = ndimage.shift(np.nan_to_num(g, nan=0.0), (-dy, -dx), order=1, mode='constant')
        return g, m

    def asymmetry(self, gray, mask, cx, cy, bg, bg_sd):
        g, m = self._cutout(gray - bg, mask, cx, cy)
        rot = np.rot90(g, 2)
        mr = m & np.rot90(m, 2)
        if mr.sum() < 10:
            return None
        denom = np.sum(np.abs(g[mr]))
        if denom <= 0:
            return None
        A = np.sum(np.abs(g[mr] - rot[mr])) / denom
        # 배경 잡음 보정: 가우시안 잡음 차이의 기대값 ≈ 2σ/√π · N
        A_bg = (2 * bg_sd / math.sqrt(math.pi)) * mr.sum() / denom
        return float(max(A - A_bg, 0.0))

    @staticmethod
    def smoothness(gray, mask, bg, r_petro):
        if not r_petro or r_petro < 2:
            return None
        k = max(3, int(0.25 * r_petro))
        img = gray - bg
        sm = ndimage.uniform_filter(img, size=k)
        resid = (img - sm)[mask]
        tot = np.sum(np.abs(img[mask]))
        if tot <= 0:
            return None
        return float(np.sum(np.clip(resid, 0, None)) / tot)

    @staticmethod
    def gini(values):
        v = np.sort(np.abs(np.asarray(values, dtype=float)))
        n = len(v)
        if n < 3 or v.sum() <= 0:
            return None
        i = np.arange(1, n + 1)
        return float(np.sum((2 * i - n - 1) * v) / (v.mean() * n * (n - 1)))

    @staticmethod
    def m20(gray, mask, bg):
        ys, xs = np.nonzero(mask)
        f = np.clip(gray[mask] - bg, 0, None)
        if f.sum() <= 0 or len(f) < 10:
            return None
        cx = np.sum(xs * f) / f.sum()
        cy = np.sum(ys * f) / f.sum()
        mi = f * ((xs - cx) ** 2 + (ys - cy) ** 2)
        mtot = mi.sum()
        if mtot <= 0:
            return None
        order = np.argsort(f)[::-1]
        cumf = np.cumsum(f[order])
        k = np.searchsorted(cumf, 0.2 * f.sum()) + 1
        m20 = np.log10(max(mi[order][:k].sum(), 1e-12) / mtot)
        return float(m20)

    # ── 분할 지도 · 핵 개수 ──────────────────────────────
    def segmentation_map(self, gray, mask, cx, cy, bg, bg_sd, r, prof, r_petro):
        """Lotz+2004 방식: 평활 영상에서 I ≥ I(r_p) 인 픽셀 (+ 2σ 이상) 로 은하 본체 분할"""
        sm = ndimage.uniform_filter(gray - bg, size=3)
        thr = 2.0 * bg_sd
        if r_petro and len(r) > 2:
            thr = max(thr, float(np.interp(r_petro, r, prof)))
        seg = mask & (sm >= thr)
        if seg.sum() < 9:
            return mask
        lab, nlab = ndimage.label(seg)
        if nlab > 1:
            # 중심을 포함하거나 가장 밝은 연결 성분 우선, 그 외 충분히 큰 성분은 포함(병합 대비)
            sizes = ndimage.sum(np.ones_like(seg), lab, range(1, nlab + 1))
            keep = np.zeros(nlab + 1, bool)
            ci = lab[int(np.clip(round(cy), 0, lab.shape[0] - 1)), int(np.clip(round(cx), 0, lab.shape[1] - 1))]
            if ci > 0:
                keep[ci] = True
            big = np.argmax(sizes) + 1
            keep[big] = True
            for i, s in enumerate(sizes, start=1):
                if s >= 0.15 * sizes.max():
                    keep[i] = True
            seg = keep[lab]
        return seg

    @staticmethod
    def count_nuclei(gray, seg, bg, rel=0.25, min_sep=6):
        """평활 영상에서 최대값의 rel 배 이상인 국소 최대점(핵/덩어리) 개수"""
        if seg.sum() < 20:
            return 1, []
        sm = ndimage.gaussian_filter(gray - bg, 2.0)
        sm = np.where(seg, sm, 0)
        mx = sm.max()
        if mx <= 0:
            return 1, []
        footprint = np.ones((2 * min_sep + 1, 2 * min_sep + 1), bool)
        peaks = (sm == ndimage.maximum_filter(sm, footprint=footprint)) & (sm >= rel * mx)
        ys, xs = np.nonzero(peaks)
        vals = sm[ys, xs]
        order = np.argsort(vals)[::-1]
        pts = [(int(xs[i]), int(ys[i]), float(vals[i] / mx)) for i in order]
        return max(1, len(pts)), pts

    # ── Sérsic ───────────────────────────────────────────
    @staticmethod
    def _bn(n):
        return 2 * n - 1.0 / 3 + 4.0 / (405 * n) + 46.0 / (25515 * n ** 2)

    def sersic_fit(self, r, prof):
        good = (prof > 0) & np.isfinite(prof) & (r > 0)
        if good.sum() < 5:
            return None
        rr, pp = r[good], prof[good]

        def model(x, ie, re, n):
            return ie * np.exp(-self._bn(n) * ((x / re) ** (1.0 / n) - 1))

        best = None
        for n0 in (1.0, 2.5, 4.0):
            try:
                p0 = [np.interp(np.median(rr), rr, pp), np.median(rr), n0]
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore')
                    popt, _ = optimize.curve_fit(lambda x, ie, re, n: np.log(np.maximum(model(x, ie, re, n), 1e-12)),
                                                 rr, np.log(pp), p0=p0,
                                                 bounds=([1e-9, 0.3, 0.3], [np.inf, rr.max() * 5, 8.0]),
                                                 maxfev=5000)
                res = np.sum((np.log(model(rr, *popt)) - np.log(pp)) ** 2)
                if best is None or res < best[1]:
                    best = (popt, res)
            except Exception:
                continue
        if best is None:
            return None
        ie, re, n = best[0]
        return {'I_e': float(ie), 'R_e': float(re), 'n': float(n),
                'rms_log': float(math.sqrt(best[1] / good.sum())),
                'model_r': rr, 'model_I': model(rr, ie, re, n)}

    # ── 분류 ─────────────────────────────────────────────
    @staticmethod
    def classify_morphology(m):
        """규칙 기반 형태 분류 (점수 0~1) + 근거 목록"""
        C = m.get('C_sdss')
        A = m.get('asymmetry')
        G = m.get('gini')
        M20 = m.get('m20')
        n = m.get('sersic_n')
        S = m.get('smoothness')
        nn = m.get('n_nuclei') or 1
        reasons = []
        early = late = irr = merger = 0.0
        w = 0.0
        if C is not None:
            w += 1
            if C >= 2.6:
                early += 1.2
                reasons.append('집중도 C=R90/R50=%.2f ≥ 2.6 → 중심 집중 (조기형 경향, Strateva+2001)' % C)
            elif C >= 2.0:
                late += 1.0
                reasons.append('집중도 C=%.2f < 2.6 → 완만한 원반 (만기형 경향)' % C)
            else:
                late += 0.4
                irr += 0.6
                reasons.append('집중도 C=%.2f < 2.0 → 매우 퍼진 구조 (불규칙/교란 경향)' % C)
        if n is not None:
            w += 1
            if n >= 2.5:
                early += 1
                reasons.append('Sérsic n=%.2f ≥ 2.5 → de Vaucouleurs형 (타원/팽대부)' % n)
            else:
                late += 1
                reasons.append('Sérsic n=%.2f < 2.5 → 지수 원반형' % n)
        if A is not None:
            w += 1
            if A > 0.35:
                if nn >= 2:
                    merger += 2.0
                    reasons.append('비대칭도 A=%.2f > 0.35 + 밝은 핵 %d개 → 병합/상호작용 강력 후보' % (A, nn))
                else:
                    irr += 1.8
                    merger += 0.6
                    reasons.append('비대칭도 A=%.2f > 0.35, 뚜렷한 핵 1개 → 강한 교란 (불규칙 경향)' % A)
            elif A > 0.15:
                irr += 0.5
                late += 0.7
                reasons.append('비대칭도 A=%.2f → 나선팔/별생성 덩어리 존재' % A)
            else:
                early += 0.6
                late += 0.4
                reasons.append('비대칭도 A=%.2f ≤ 0.15 → 대칭적 구조' % A)
        if G is not None and M20 is not None:
            w += 1
            if G > -0.14 * M20 + 0.33:
                merger += 1
                reasons.append('Gini=%.2f, M20=%.2f → Lotz(2008) 병합 영역' % (G, M20))
            elif G > 0.14 * M20 + 0.80:
                early += 1
                reasons.append('Gini=%.2f, M20=%.2f → 조기형(E/S0/Sa) 영역' % (G, M20))
            else:
                if A is not None and A > 0.25:
                    irr += 0.6
                    late += 0.4
                else:
                    late += 1
                reasons.append('Gini=%.2f, M20=%.2f → 만기형(Sb–Irr) 영역' % (G, M20))
        if nn >= 4:
            irr += 1.0
            reasons.append('밝은 덩어리 %d개 → 덩어리진(clumpy) 별생성 구조' % nn)
        if S is not None and S > 0.15:
            irr += 0.3
            late += 0.3
            reasons.append('매끄러움 S=%.2f → 덩어리진 구조' % S)
        if w == 0:
            return {'class': '판정 불가', 'class_en': 'Unknown', 'scores': {}, 'reasons': ['측정값 부족']}
        tot = early + late + irr + merger
        scores = {
            '조기형 (타원/렌즈형)': early / tot, '만기형 (나선/원반)': late / tot,
            '불규칙': irr / tot, '병합/상호작용 후보': merger / tot,
        }
        cls = max(scores, key=scores.get)
        en = {'조기형 (타원/렌즈형)': 'Early-type', '만기형 (나선/원반)': 'Late-type',
              '불규칙': 'Irregular', '병합/상호작용 후보': 'Merger candidate'}[cls]
        return {'class': cls, 'class_en': en, 'scores': scores, 'reasons': reasons}

    # ── 통합 ─────────────────────────────────────────────
    @staticmethod
    def linearize_image(image_array, mode='srgb'):
        """8비트 사진(sRGB 감마≈2.2) → 근사 선형 광량. mode: 'srgb' | 'auto' | 'none'"""
        arr = np.asarray(image_array)
        if mode in ('srgb', 'auto') and arr.dtype == np.uint8:
            return ((arr.astype(float) / 255.0) ** 2.2) * 255.0
        return arr.astype(float)

    def analyze(self, image_array, mask, linearize='auto'):
        """영역 하나에 대한 전체 분석 결과 dict.
        linearize: 'auto'(8비트면 sRGB 감마 해제) | 'srgb' | 'none'"""
        mask = np.asarray(mask, dtype=bool)
        if linearize == 'auto':
            linearize = 'srgb' if np.asarray(image_array).dtype == np.uint8 else 'none'
        image_array = self.linearize_image(image_array, linearize)
        stats = self.region_stats(image_array, mask)
        if stats.get('n_pix', 0) < 9:
            return {'stats': stats, 'error': '영역이 너무 작습니다 (최소 9픽셀).'}
        gray_full = self.to_gray(image_array)
        bg, bg_sd = stats['background'], stats['background_std']

        # ROI 주변으로 잘라서 계산 (대형 FITS 대비)
        x0b, y0b, x1b, y1b = stats['bbox']
        pad = 4
        ox, oy = max(0, x0b - pad), max(0, y0b - pad)
        ex, ey = min(gray_full.shape[1], x1b + pad + 1), min(gray_full.shape[0], y1b + pad + 1)
        gray = gray_full[oy:ey, ox:ex]
        mask = mask[oy:ey, ox:ex]
        cx, cy = stats['centroid_x'] - ox, stats['centroid_y'] - oy

        # 1차 프로파일 → Petrosian 반경
        r, prof, cum = self.radial_profile(gray, cx, cy, mask=mask, bg=bg)
        Rp = self.petrosian_radius(r, prof)

        # SDSS 방식: 2·Rp 구경 안에서 누적 광량 반경
        aperture = mask
        if Rp:
            yy, xx = np.indices(gray.shape)
            ap = np.hypot(xx - cx, yy - cy) <= 2.0 * Rp
            if (mask & ap).sum() >= 9:
                aperture = mask & ap
        ra, pa_, ca = self.radial_profile(gray, cx, cy, mask=aperture, bg=bg)
        R20 = self.radius_at_fraction(ra, ca, 0.2)
        R50 = self.radius_at_fraction(ra, ca, 0.5)
        R80 = self.radius_at_fraction(ra, ca, 0.8)
        R90 = self.radius_at_fraction(ra, ca, 0.9)
        C_cas = 5 * math.log10(R80 / R20) if R20 and R80 and R20 > 0 else None
        C_sdss = R90 / R50 if R50 and R90 and R50 > 0 else None

        seg = self.segmentation_map(gray, mask, cx, cy, bg, bg_sd, r, prof, Rp)
        n_nuc, nuclei = self.count_nuclei(gray, seg, bg)
        A = self.asymmetry(gray, seg, cx, cy, bg, bg_sd)
        S = self.smoothness(gray, seg, bg, Rp or (R90 or 0) * 0.7)
        G = self.gini(np.clip(gray[seg] - bg, 0, None))
        M20 = self.m20(gray, seg, bg)
        sersic = self.sersic_fit(ra, pa_)
        metrics = {
            'R20_px': R20, 'R50_px': R50, 'R80_px': R80, 'R90_px': R90, 'R_petro_px': Rp,
            'C_cas': C_cas, 'C_sdss': C_sdss, 'asymmetry': A, 'smoothness': S,
            'gini': G, 'm20': M20, 'sersic_n': sersic['n'] if sersic else None,
            'sersic_Re_px': sersic['R_e'] if sersic else None,
            'n_nuclei': n_nuc, 'seg_pixels': int(seg.sum()),
        }
        morph = self.classify_morphology(metrics)
        snr = stats.get('snr')
        peak_sig = (float(np.max(gray[mask])) - bg) / bg_sd if mask.any() and bg_sd > 0 else 0.0
        if (snr is not None and np.isfinite(snr) and snr < 5) or stats.get('net_flux', 0) <= 0 \
                or metrics['seg_pixels'] < 9 or peak_sig < 5:
            morph = {'class': '유의미한 천체 없음 (배경/잡음)', 'class_en': 'No significant source', 'scores': {},
                     'reasons': ['영역 S/N=%.1f, 최대 밝기 유의도 %.1fσ, 분할 영역 %d픽셀 → 형태 지수를 신뢰할 수 없음'
                                 % (snr if snr is not None else float('nan'), peak_sig, metrics['seg_pixels']),
                                 '은하가 영역 안에 들어오도록 다시 그려 보세요.']}
            metrics['significant'] = False
        else:
            metrics['significant'] = True
        return {
            'stats': stats, 'metrics': metrics, 'morphology': morph,
            'profile': {'r': ra, 'I': pa_, 'cum': ca}, 'sersic': sersic,
            'segmentation': seg, 'crop_offset': (ox, oy), 'cutout': gray - bg,
            'nuclei': [(x + ox, y + oy, v) for x, y, v in nuclei[:8]],
            'ml_features': self.to_ml_features(stats, metrics, morph),
        }

    def to_ml_features(self, stats, metrics, morph):
        """형태 분석 결과 → 학습 모델 특성(SDSS 컬럼명) 근사치"""
        f = {}
        if metrics.get('C_sdss') is not None:
            f['concentration_index_r'] = float(np.clip(metrics['C_sdss'], 1.5, 5.0))
        n = metrics.get('sersic_n')
        if n is not None:
            f['fracDeV_r'] = float(np.clip((n - 1.0) / 3.0, 0.0, 1.0))
        ps = self.pixel_scale
        if metrics.get('R50_px'):
            f['petroR50_r'] = float(metrics['R50_px'] * ps)
        if metrics.get('R90_px'):
            f['petroR90_r'] = float(metrics['R90_px'] * ps)
        sc = morph.get('scores') or {}
        if sc:
            f['gz_p_el'] = float(sc.get('조기형 (타원/렌즈형)', 0))
            f['gz_p_cs'] = float(sc.get('만기형 (나선/원반)', 0) + 0.5 * sc.get('불규칙', 0))
            f['gz_p_mg'] = float(sc.get('병합/상호작용 후보', 0))
        if stats.get('axis_ratio') is not None:
            f['expAB_r'] = float(stats['axis_ratio'])
            f['deVAB_r'] = float(stats['axis_ratio'])
        return f

    @staticmethod
    def estimate_ur_from_rgb(color_gr_proxy):
        """비교정 RGB (G−R) 프록시 → u−r 대략 추정 (청색구름 1.5 / 적색계열 2.4 을 기준으로 선형 사상)"""
        if color_gr_proxy is None:
            return None
        return float(np.clip(1.9 + 3.0 * color_gr_proxy, 0.8, 3.5))

    @staticmethod
    def line_cut(image_array, x1, y1, x2, y2, n=None):
        """Ginga 'Cuts' 플러그인: 선분을 따른 밝기 단면"""
        gray = GalaxyImageAnalyzer.to_gray(image_array)
        length = max(2, int(np.hypot(x2 - x1, y2 - y1)))
        n = n or length
        xs = np.linspace(x1, x2, n)
        ys = np.linspace(y1, y2, n)
        vals = ndimage.map_coordinates(gray, [ys, xs], order=1, mode='nearest')
        dist = np.hypot(xs - x1, ys - y1)
        return dist, vals


def robust_noise(gray):
    g = np.asarray(gray, dtype=float).ravel()
    if g.size > 200000:
        g = g[:: g.size // 200000]
    mad = np.median(np.abs(g - np.median(g)))
    return float(1.4826 * mad) if mad > 0 else float(np.std(g) or 1.0)


# ═══════════════════════════════════════════════════════
#                 모의 은하 이미지 (데모/테스트)
# ═══════════════════════════════════════════════════════
def synthetic_galaxy_image(kind='spiral', size=420, seed=7):
    """테스트용 모의 은하 RGB 이미지: 'elliptical' | 'spiral' | 'merger' | 'irregular'"""
    rng = np.random.default_rng(seed)
    yy, xx = np.indices((size, size)).astype(float)
    cx = cy = size / 2
    bn = GalaxyImageAnalyzer._bn

    def sersic(x0, y0, re, n, q=1.0, pa=0.0, amp=1.0):
        a = math.radians(pa)
        dx, dy = xx - x0, yy - y0
        xr = dx * math.cos(a) + dy * math.sin(a)
        yr = (-dx * math.sin(a) + dy * math.cos(a)) / q
        r = np.hypot(xr, yr) + 1e-3
        return amp * np.exp(-bn(n) * ((r / re) ** (1.0 / n) - 1))

    R = np.zeros((size, size)); G = np.zeros_like(R); B = np.zeros_like(R)
    if kind == 'elliptical':
        I = sersic(cx, cy, 30, 4.0, q=0.75, pa=30, amp=0.25)
        R += I * 1.0; G += I * 0.78; B += I * 0.55
    elif kind == 'merger':
        I1 = sersic(cx - 45, cy - 10, 20, 2.5, q=0.8, pa=10, amp=0.5)
        I2 = sersic(cx + 50, cy + 25, 16, 1.5, q=0.6, pa=70, amp=0.45)
        t = np.linspace(0, 1, 400)
        tail = np.zeros_like(R)
        for ti in t:
            px = cx + 50 + 120 * ti * math.cos(2.5 * ti)
            py = cy + 25 - 110 * ti
            tail += 0.02 * np.exp(-((xx - px) ** 2 + (yy - py) ** 2) / (2 * 6 ** 2))
        I = I1 + I2 + tail
        R += I * 0.95; G += I * 0.85; B += I * 0.8
    elif kind == 'irregular':
        I = np.zeros_like(R)
        for _ in range(14):
            I += sersic(cx + rng.normal(0, 45), cy + rng.normal(0, 30), rng.uniform(5, 14), 1.0,
                        q=rng.uniform(0.5, 1), pa=rng.uniform(0, 180), amp=rng.uniform(0.15, 0.5))
        R += I * 0.6; G += I * 0.75; B += I * 1.0
    else:  # spiral
        bulge = sersic(cx, cy, 10, 3.5, amp=0.9)
        disk = sersic(cx, cy, 55, 1.0, q=0.85, pa=20, amp=0.12)
        r = np.hypot(xx - cx, yy - cy) + 1e-3
        th = np.arctan2(yy - cy, xx - cx)
        arms = 0.5 * (1 + np.cos(2 * (th - np.log(r / 8) / 0.35))) ** 3
        disk = disk * (0.35 + 1.2 * arms)
        knots = np.zeros_like(R)
        for _ in range(25):
            rr = rng.uniform(25, 120); tt = rng.uniform(0, 2 * np.pi)
            knots += 0.15 * np.exp(-((xx - cx - rr * math.cos(tt)) ** 2 + (yy - cy - rr * math.sin(tt)) ** 2) / 8)
        R += bulge * 1.0 + disk * 0.55 + knots * 0.5
        G += bulge * 0.8 + disk * 0.7 + knots * 0.7
        B += bulge * 0.55 + disk * 1.0 + knots * 1.0
    img = np.stack([R, G, B], axis=-1)
    img = img / (np.percentile(img, 99.9) or 1.0)
    img += np.abs(rng.normal(0.004, 0.003, img.shape))
    # 배경 별 몇 개
    for _ in range(6):
        sx, sy = rng.integers(10, size - 10, 2)
        img += 0.8 * np.exp(-((xx - sx) ** 2 + (yy - sy) ** 2) / 3)[..., None]
    img = np.clip(img, 0, 1) ** (1 / 2.2)  # 카메라처럼 sRGB 감마 인코딩
    return Image.fromarray((img * 255).astype(np.uint8))
