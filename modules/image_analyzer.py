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
    def _normalize_channels(arr):
        """(C, H, W) FITS 큐브 또는 고차원 배열을 2D (H, W) 또는 채널-마지막 (H, W, C) 배열로 정규화"""
        arr = np.asarray(arr)
        while arr.ndim > 3:
            arr = arr[0]
        if arr.ndim == 3:
            if arr.shape[0] == 1 and arr.shape[2] > 4:
                arr = arr[0]
            elif arr.shape[2] == 1 and arr.shape[0] > 4:
                arr = arr[..., 0]
            elif arr.shape[0] in (3, 4) and arr.shape[2] not in (3, 4):
                arr = np.transpose(arr, (1, 2, 0))
            elif arr.shape[0] not in (3, 4) and arr.shape[2] not in (3, 4):
                arr = arr[0]
        return arr

    @classmethod
    def to_gray(cls, arr):
        arr = np.asarray(cls._normalize_channels(arr), dtype=float)
        if not np.all(np.isfinite(arr)):
            finite_vals = arr[np.isfinite(arr)]
            fill = float(np.median(finite_vals)) if finite_vals.size > 0 else 0.0
            arr = np.nan_to_num(arr, nan=fill, posinf=fill, neginf=fill)
        if arr.ndim == 3:
            rgb = arr[..., :3]
            return 0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]
        return arr

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
            # 전체 이미지가 마스크인 경우 가장자리(테두리) 픽셀에서 배경 추정
            H, W = gray.shape
            b_px = max(1, min(H, W) // 12)
            border = np.zeros_like(gray, dtype=bool)
            border[:b_px, :] = True; border[-b_px:, :] = True
            border[:, :b_px] = True; border[:, -b_px:] = True
            vals = gray[border]
        if vals.size < 5:
            return float(np.median(gray)), max(robust_noise(gray), 1e-6)
        _, med, sd = sigma_clipped_stats(vals)
        return med, max(sd, 1e-6)

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

        arr = self._normalize_channels(image_array)
        if arr.ndim == 3 and arr.shape[2] >= 3:
            rgb = arr[..., :3].astype(float)
            r_pix = rgb[..., 0][mask]
            g_pix = rgb[..., 1][mask]
            b_pix = rgb[..., 2][mask]
            r_m = float(np.mean(r_pix))
            g_m = float(np.mean(g_pix))
            b_m = float(np.mean(b_pix))
            # L 필터/단색 이미지가 3채널 RGB로 저장된 경우(R≈G≈B) 가짜 색지수(u-r≈1.9) 생성 방지
            scale_rgb = max(abs(r_m), abs(g_m), abs(b_m), float(np.std(r_pix)), 1e-9)
            diff_rg = float(np.median(np.abs(r_pix - g_pix))) / scale_rgb
            diff_rb = float(np.median(np.abs(r_pix - b_pix))) / scale_rgb
            is_mono = (diff_rg < 0.012 and diff_rb < 0.012)
            out['is_monochrome'] = bool(is_mono)
            if not is_mono:
                r_bg = float(np.median(rgb[..., 0][~mask])) if (~mask).any() else 0.0
                g_bg = float(np.median(rgb[..., 1][~mask])) if (~mask).any() else 0.0
                b_bg = float(np.median(rgb[..., 2][~mask])) if (~mask).any() else 0.0
                R, G, B = max(r_m - r_bg, 1e-3), max(g_m - g_bg, 1e-3), max(b_m - b_bg, 1e-3)
                out.update({
                    'mean_R': r_m, 'mean_G': g_m, 'mean_B': b_m,
                    'color_BR': float(-2.5 * math.log10(B / R)),
                    'color_GR': float(-2.5 * math.log10(G / R)),
                })
        else:
            out['is_monochrome'] = True
        return out

    # ── 반경 프로파일 ────────────────────────────────────
    @staticmethod
    def _elliptical_radius_grid(shape, cx, cy, axis_ratio=1.0, pa_deg=0.0):
        """면적 보존 원형화 타원 반경 r_circ = r_major * sqrt(b/a) (q=1 이면 원형 반경과 완전히 동일)"""
        h, w = shape
        yy, xx = np.indices((h, w), dtype=float)
        dx = xx - cx
        dy = yy - cy
        q = float(np.clip(axis_ratio if (axis_ratio and np.isfinite(axis_ratio)) else 1.0, 0.22, 1.0))
        if q >= 0.97:
            return np.hypot(dx, dy)
        ang = math.radians(pa_deg if (pa_deg and np.isfinite(pa_deg)) else 0.0)
        ca, sa = math.cos(ang), math.sin(ang)
        xr = dx * ca + dy * sa
        yr = (-dx * sa + dy * ca) / q
        return np.hypot(xr, yr) * math.sqrt(q)

    def radial_profile(self, gray, cx, cy, mask=None, bg=0.0, rmax=None, nbins=None,
                       axis_ratio=1.0, pa_deg=0.0):
        h, w = gray.shape
        r = self._elliptical_radius_grid((h, w), cx, cy, axis_ratio=axis_ratio, pa_deg=pa_deg)
        valid = np.ones_like(gray, bool) if mask is None else mask
        if rmax is None:
            rmax = r[valid].max() if valid.any() else min(h, w) / 2
        rmax = max(rmax, 3)
        if nbins is None:
            nbins = int(min(64, max(8, rmax)))
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
            vals_i = v[sel]
            # 외곽 고리(i >= 3)에서 미제거 점광원/우주선 극단 스파이크(> 4.5×P95)만 상위 1% 클리핑 (측면 원반 플럭스 보존)
            if i >= 3 and vals_i.size >= 60:
                p95 = float(np.percentile(vals_i, 95.0))
                if p95 > 0 and float(np.max(vals_i)) > 4.5 * p95:
                    hi_cut = np.percentile(vals_i, 99.0)
                    trimmed = vals_i[vals_i <= hi_cut]
                    mean_v = float(np.mean(trimmed)) if trimmed.size > 0 else float(np.mean(vals_i))
                    sum_v = mean_v * float(vals_i.size)
                else:
                    mean_v = float(np.mean(vals_i))
                    sum_v = float(np.sum(vals_i))
            else:
                mean_v = float(np.mean(vals_i))
                sum_v = float(np.sum(vals_i))
            centers.append(0.5 * (edges[i] + edges[i + 1]))
            prof.append(mean_v)
            total += sum_v
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
        H, W = gray.shape
        if not np.isfinite(cx) or not np.isfinite(cy):
            cx, cy = W / 2.0, H / 2.0
        ys, xs = np.nonzero(mask)
        if len(xs) == 0:
            return gray.copy(), mask.copy()
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
        """Conselice+2000 표준 회전 비대칭도: 중심 (cx, cy) 주변 ±1.5px 격자에서 180° 비대칭도를 최소화"""
        net_img = gray - bg

        def _eval_asym(xc, yc):
            g, m = self._cutout(net_img, mask, xc, yc)
            rot = np.rot90(g, 2)
            mr = m & np.rot90(m, 2)
            if mr.sum() < 10:
                return None
            denom = float(np.sum(np.abs(g[mr])))
            if denom <= 0:
                return None
            a_raw = float(np.sum(np.abs(g[mr] - rot[mr]))) / denom
            a_bg = (2.0 * bg_sd / math.sqrt(math.pi)) * float(mr.sum()) / denom
            return max(a_raw - a_bg, 0.0)

        best_a = _eval_asym(cx, cy)
        if best_a is None:
            # 중심(cx, cy)이 먼지띠 등으로 분할 지도(mask)에서 벗어난 경우 분할 영역의 광도 중심으로 폴백
            ys_s, xs_s = np.nonzero(mask)
            if ys_s.size < 10:
                return None
            w_s = np.clip(net_img[mask], 0.0, None)
            ws_sum = float(w_s.sum())
            cx = float(np.sum(xs_s * w_s) / ws_sum) if ws_sum > 0 else float(np.mean(xs_s))
            cy = float(np.sum(ys_s * w_s) / ws_sum) if ws_sum > 0 else float(np.mean(ys_s))
            best_a = _eval_asym(cx, cy)
            if best_a is None:
                return None
        best_x, best_y = cx, cy
        for dy in (-1.0, 0.0, 1.0):
            for dx in (-1.0, 0.0, 1.0):
                if dx == 0.0 and dy == 0.0:
                    continue
                val = _eval_asym(cx + dx, cy + dy)
                if val is not None and val < best_a:
                    best_a, best_x, best_y = val, cx + dx, cy + dy
        for dy in (-0.5, 0.0, 0.5):
            for dx in (-0.5, 0.0, 0.5):
                if dx == 0.0 and dy == 0.0:
                    continue
                val = _eval_asym(best_x + dx, best_y + dy)
                if val is not None and val < best_a:
                    best_a = val
        return float(best_a)

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

    @staticmethod
    def spiral_winding(gray, cx, cy, r50, bg, bg_sd=1.0, axis_ratio=1.0, pa_deg=0.0):
        """탈투영 타원 고리 위에서 방위각 푸리에 모드(m=2,3,4) 및 위상 회전량으로 나선팔 감김도 W_spiral 계산
        (편평한 E3~E7 타원은하의 고정 사중극자(ellipticity quadrupole)가 나선팔로 오인되는 현상 제거)"""
        if r50 is None or not np.isfinite(r50) or r50 < 2.0:
            return 0.0
        H, W = gray.shape
        q = float(np.clip(axis_ratio if (axis_ratio and np.isfinite(axis_ratio)) else 1.0, 0.25, 1.0))
        ang = math.radians(pa_deg if (pa_deg and np.isfinite(pa_deg)) else 0.0)
        ca, sa = math.cos(ang), math.sin(ang)
        sq = math.sqrt(q)
        r_min = max(2.2, 0.38 * r50)
        r_max = min(max(H, W) * 0.45, 3.0 * r50)
        if r_max <= r_min + 2.0:
            return 0.0
        n_rings = 10
        n_theta = 36
        z2_list, amp_hi_list, phases2 = [], [], []
        radii = np.linspace(r_min, r_max, n_rings)
        thetas = np.linspace(0, 2 * np.pi, n_theta, endpoint=False)
        ct, st = np.cos(thetas), np.sin(thetas)
        for rad in radii:
            # 원형화 반경 rad 에 대응하는 등광도 타원 고리 (장반경 rad/sqrt(q), 단반경 rad*sqrt(q))
            x_ell = (rad / sq) * ct
            y_ell = (rad * sq) * st
            xs = cx + x_ell * ca - y_ell * sa
            ys = cy + x_ell * sa + y_ell * ca
            valid = (xs >= 0) & (xs < W - 1) & (ys >= 0) & (ys < H - 1)
            if valid.sum() < n_theta * 0.75:
                continue
            vals = np.maximum(0.0, ndimage.map_coordinates(gray, [ys, xs], order=1, mode='nearest') - bg)
            # 미세 잔여 전경별/점광원 스파이크가 m=2,3,4 푸리에 진폭을 부풀리는 현상 방지 (나선팔은 6~15개 각도 샘플 이상에 걸침)
            vals = ndimage.median_filter(vals, size=3, mode='wrap')
            a0 = float(np.mean(vals))
            if a0 <= 0.6 * bg_sd:
                continue
            c2 = float(np.mean(vals * np.cos(2 * thetas))) / a0
            s2 = float(np.mean(vals * np.sin(2 * thetas))) / a0
            c3 = float(np.mean(vals * np.cos(3 * thetas))) / a0
            s3 = float(np.mean(vals * np.sin(3 * thetas))) / a0
            c4 = float(np.mean(vals * np.cos(4 * thetas))) / a0
            s4 = float(np.mean(vals * np.sin(4 * thetas))) / a0
            z2_list.append(complex(c2, s2))
            amp_hi_list.append(0.6 * math.hypot(c3, s3) + 0.4 * math.hypot(c4, s4))
            phases2.append(math.atan2(s2, c2))
        if len(z2_list) < 3:
            return 0.0
        z2_arr = np.asarray(z2_list, dtype=complex)
        # 반경 전체에 걸쳐 위상이 고정된 잔여 타원율/막대 성분(0-피치 사중극자) 차감
        z2_static = np.mean(z2_arr)
        amp2_winding = float(np.mean(np.abs(z2_arr - 0.85 * z2_static)))
        mean_amp = amp2_winding + float(np.mean(amp_hi_list))
        phase_diffs = []
        for i in range(1, len(phases2)):
            dp = phases2[i] - phases2[i - 1]
            while dp > np.pi:
                dp -= 2 * np.pi
            while dp < -np.pi:
                dp += 2 * np.pi
            phase_diffs.append(abs(dp))
        mean_wind = float(np.mean(phase_diffs)) if phase_diffs else 0.0
        return float(mean_amp * (1.0 + 0.6 * min(1.5, mean_wind)))

    def sersic_fit(self, r, prof):
        good = (prof > 0) & np.isfinite(prof) & (r > 0)
        if good.sum() >= 8:
            # 시상(seeing) PSF 에 의해 평탄화되는 최내곽 ~1.5px 빈 제외
            no_psf = good & (r >= 1.5)
            if no_psf.sum() >= 6:
                good = no_psf
        if good.sum() >= 7:
            pmax = np.nanmax(prof[good])
            non_sat = good & ~((r < 3.5) & (prof > 0.92 * pmax))
            if non_sat.sum() >= 5:
                good = non_sat
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
        C_cas = m.get('C_cas')
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
        if C_cas is not None and C_cas >= 3.45:
            early += 0.7
            reasons.append('CAS 집중도 C_cas=%.2f ≥ 3.45 → 강한 중심부 광도 집중 (Conselice 2003 조기형)' % C_cas)
        if n is not None:
            w += 1
            if n >= 2.5:
                early += 1
                reasons.append('Sérsic n=%.2f ≥ 2.5 → de Vaucouleurs형 (타원/팽대부)' % n)
            elif n >= 1.85:
                early += 0.4
                late += 0.4
                reasons.append('Sérsic n=%.2f (중간 집중 프로파일: 시상 완화된 조기형 또는 팽대부 나선)' % n)
            else:
                late += 1
                reasons.append('Sérsic n=%.2f < 1.85 → 지수 원반형' % n)
        if A is not None:
            w += 1
            if A > 0.35:
                if nn >= 5 and C is not None and C < 2.15 and (G is None or G < 0.50):
                    irr += 2.2
                    merger += 0.5
                    reasons.append('비대칭도 A=%.2f > 0.35 + 저집중 다중 별생성 덩어리 %d개 → 불규칙 은하 강력 후보' % (A, nn))
                elif nn >= 2:
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
        axis_q = m.get('axis_ratio')
        if axis_q is not None and axis_q < 0.34 and (nn >= 2 or (M20 is not None and M20 > -1.55) or (A is not None and A > 0.18)):
            late += 3.2
            merger = max(0.0, merger - 1.5)
            irr = max(0.0, irr - 1.0)
            reasons.append('초고경사 측면 원반·적도 먼지띠 구조 (축비 b/a=%.2f < 0.34) → 측면 나선은하(Edge-on Spiral)' % axis_q)
        elif axis_q is not None and axis_q < 0.44 and (nn >= 2 or (M20 is not None and M20 > -1.55) or (A is not None and A > 0.18)):
            late += 1.6
            irr = max(0.0, irr - 0.6)
            reasons.append('고경사 원반·먼지띠 구조 (축비 b/a=%.2f < 0.44) → 측면 나선은하 경향' % axis_q)
        W = m.get('W_spiral')
        if W is not None and W >= 0.08 and (A is None or A < 0.38):
            late += 0.8
            reasons.append('나선팔 감김도 W=%.2f ≥ 0.08 → 방위각 푸리에 나선팔 패턴 검출' % W)
        elif W is not None and W < 0.04 and (A is not None and A <= 0.12):
            early += 0.4
            reasons.append('나선팔 감김도 W=%.2f < 0.04 → 매끄러운 타원형 등광도선' % W)
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
        tot3 = max(early + late + (irr + 0.5 * merger), 1e-6)
        scores_3 = {
            '타원은하 (Elliptical)': early / tot3,
            '나선은하 (Spiral)': late / tot3,
            '불규칙은하 (Irregular)': (irr + 0.5 * merger) / tot3,
        }
        cls = max(scores, key=scores.get)
        cls_3 = max(scores_3, key=scores_3.get)
        en = {'조기형 (타원/렌즈형)': 'Early-type', '만기형 (나선/원반)': 'Late-type',
              '불규칙': 'Irregular', '병합/상호작용 후보': 'Merger candidate'}[cls]
        return {'class': cls, 'class_en': en, 'class_3': cls_3, 'scores': scores, 'scores_3': scores_3, 'reasons': reasons}

    # ── 전경 별 마스킹 · 광시야 타깃 자동 분리 ────────────
    @classmethod
    def _find_extended_core_and_mask_stars(cls, gray, mask, bg, bg_sd):
        """확장 은하 헤일로 중심(gx0, gy0)을 보호하면서 전경 점광원(PSF 별)만 국소 헤일로 밝기로 복원.
        은하 병합의 이중 핵(R_e ≥ 5 px) 및 나선팔 HII 매듭(σ ≥ 1.9 px)은 100% 보존합니다."""
        H, W = gray.shape
        mask_b = np.asarray(mask, dtype=bool)
        if min(H, W) < 18 or mask_b.sum() < 25:
            ys, xs = np.nonzero(mask_b)
            gx0 = float(np.mean(xs)) if xs.size else W / 2.0
            gy0 = float(np.mean(ys)) if ys.size else H / 2.0
            return gray.copy(), (gx0, gy0), 0

        net = np.clip(gray - bg, 0.0, None)
        # 11x11 중앙값 필터는 점광원(FWHM ~ 3px, 면적 < 35%)에 반응하지 않고 확장 은하 중심핵만 추출
        k_med = min(11, max(5, (min(H, W) // 6) | 1))
        halo_map = ndimage.median_filter(np.where(mask_b, net, 0.0), size=k_med)
        yy, xx = np.indices((H, W), dtype=float)
        ys_m, xs_m = np.nonzero(mask_b)
        mcx, mcy = float(np.mean(xs_m)), float(np.mean(ys_m))
        r_scale = max(18.0, 0.55 * min(H, W))
        center_w = np.exp(-0.5 * ((xx - mcx) ** 2 + (yy - mcy) ** 2) / (r_scale ** 2))
        score_map = np.where(mask_b & (halo_map > 1.6 * bg_sd), halo_map * center_w, -1.0)
        if np.max(score_map) > 0:
            iy, ix = np.unravel_index(int(np.argmax(score_map)), (H, W))
            # ±6 px 내 3x3 평균 첨점(cusp) 미세 보정
            y0c, y1c = max(1, iy - 6), min(H - 1, iy + 7)
            x0c, x1c = max(1, ix - 6), min(W - 1, ix + 7)
            cusp = ndimage.uniform_filter(net, size=3)[y0c:y1c, x0c:x1c]
            dyc, dxc = np.unravel_index(int(np.argmax(cusp)), cusp.shape)
            gx0, gy0 = float(x0c + dxc), float(y0c + dyc)
        else:
            ipk = int(np.argmax(np.where(mask_b, net, -1.0)))
            gy0, gx0 = [float(v) for v in np.unravel_index(ipk, (H, W))]

        core_protect_r = max(6.5, 0.065 * min(H, W))
        # 포화(saturated) 평탄 정점 별도 단일 중심 피크로 수렴하도록 σ=1.0 평활 맵에서 국소 최대점 탐색
        net_sm = ndimage.gaussian_filter(net, sigma=1.0)
        local_max = (net_sm == ndimage.maximum_filter(net_sm, size=5)) & mask_b & (net >= 6.0 * bg_sd)
        py_all, px_all = np.nonzero(local_max)
        if py_all.size == 0:
            return gray.copy(), (gx0, gy0), 0

        order = np.argsort(net_sm[py_all, px_all])[::-1][:60]
        dirs8 = [(1.0, 0.0), (-1.0, 0.0), (0.0, 1.0), (0.0, -1.0),
                 (0.7071, 0.7071), (-0.7071, 0.7071), (0.7071, -0.7071), (-0.7071, -0.7071)]
        stars = []
        for idx in order:
            py, px = int(py_all[idx]), int(px_all[idx])
            if px < 4 or px >= W - 4 or py < 4 or py >= H - 4:
                continue
            if math.hypot(px - gx0, py - gy0) <= core_protect_r:
                continue
            v0 = float(np.max(net[py - 1:py + 2, px - 1:px + 2]))
            m3 = float(np.mean(net[py - 1:py + 2, px - 1:px + 2]))
            mid4, mid6, ring = [], [], []
            for ux, uy in dirs8:
                x4, y4 = int(round(px + 4.0 * ux)), int(round(py + 4.0 * uy))
                if 0 <= x4 < W and 0 <= y4 < H:
                    mid4.append(float(net[y4, x4]))
                x6, y6 = int(round(px + 6.5 * ux)), int(round(py + 6.5 * uy))
                if 0 <= x6 < W and 0 <= y6 < H:
                    mid6.append(float(net[y6, x6]))
                for rr in (9.5, 12.5):
                    xr, yr = int(round(px + rr * ux)), int(round(py + rr * uy))
                    if 0 <= xr < W and 0 <= yr < H:
                        ring.append(float(net[yr, xr]))
            if len(mid4) < 6 or len(mid6) < 6 or len(ring) < 6:
                continue
            ring_med = float(np.percentile(ring, 45.0))
            m3_prom = m3 - ring_med
            peak_prom = v0 - ring_med
            if (m3_prom > max(5.0 * bg_sd, 0.35 * ring_med + 2.5 * bg_sd)
                    and peak_prom > max(6.5 * bg_sd, 0.45 * ring_med + 3.0 * bg_sd)
                    and (np.percentile(mid4, 50.0) - ring_med) < 0.35 * peak_prom
                    and (np.percentile(mid4, 75.0) - ring_med) < 0.50 * peak_prom
                    and (np.percentile(mid6, 50.0) - ring_med) < 0.16 * peak_prom):
                snr_star = max(2.0, peak_prom / max(bg_sd, 1e-6))
                rad = int(np.clip(math.ceil(2.2 * math.sqrt(2.0 * math.log(snr_star))), 5, 10))
                stars.append((px, py, rad, ring_med))

        if not stars:
            return gray.copy(), (gx0, gy0), 0

        clean = gray.copy()
        n_masked_pix = 0
        for px, py, rad, ring_med in stars:
            outer = []
            for ux, uy in dirs8:
                xo, yo = int(round(px + (rad + 1.5) * ux)), int(round(py + (rad + 1.5) * uy))
                if 0 <= xo < W and 0 <= yo < H:
                    outer.append(float(net[yo, xo]))
            fill_val = bg + (float(np.percentile(outer, 45.0)) if len(outer) >= 3 else ring_med)
            y0s, y1s = max(0, py - rad), min(H, py + rad + 1)
            x0s, x1s = max(0, px - rad), min(W, px + rad + 1)
            sub_yy, sub_xx = np.ogrid[y0s:y1s, x0s:x1s]
            disk = ((sub_xx - px) ** 2 + (sub_yy - py) ** 2 <= rad * rad) & (
                (sub_xx - gx0) ** 2 + (sub_yy - gy0) ** 2 > (0.85 * core_protect_r) ** 2
            )
            patch = clean[y0s:y1s, x0s:x1s]
            replace = disk & (patch > fill_val + 0.5 * bg_sd)
            n_masked_pix += int(replace.sum())
            patch[replace] = fill_val
        return clean, (gx0, gy0), len(stars)

    @classmethod
    def auto_isolate_primary_mask(cls, gray, mask=None):
        """광시야 다중 은하 FITS(예: Draco Trio NGC 5982 + NGC 5985 + NGC 5981) 또는 mask=None 호출 시
        주 은하 타깃을 자동 탐지하고 분리된 동반은하 영역을 배제한 최적 마스크를 반환합니다."""
        H, W = gray.shape
        if mask is not None:
            mask_b = np.asarray(mask, dtype=bool)
            if min(H, W) < 600 or float(mask_b.mean()) <= 0.55:
                return mask_b
        else:
            mask_b = np.ones((H, W), dtype=bool)

        step = max(1, int(math.ceil(max(H, W) / 520.0)))
        sub = gray[::step, ::step]
        sub_m = mask_b[::step, ::step]
        SH, SW = sub.shape
        vals = sub[sub_m] if sub_m.any() else sub.ravel()
        if vals.size < 50:
            return mask_b
        bg = float(np.percentile(vals, 25.0))
        low = vals[vals <= np.percentile(vals, 65.0)]
        sd = max(1e-7, float(1.4826 * np.median(np.abs(low - np.median(low))))) if low.size >= 10 else robust_noise(sub)
        halo = ndimage.median_filter(np.clip(sub - bg, 0.0, None), size=7)
        seg = (halo >= 3.2 * sd) & sub_m
        lab, nlab = ndimage.label(seg)
        if nlab == 0:
            return mask_b

        ys_m, xs_m = np.nonzero(sub_m)
        mcx, mcy = (float(np.mean(xs_m)), float(np.mean(ys_m))) if xs_m.size else (SW / 2.0, SH / 2.0)
        targets = []
        for cid in range(1, nlab + 1):
            cy_i, cx_i = np.nonzero(lab == cid)
            if cy_i.size < 24:
                continue
            w_i = halo[cy_i, cx_i]
            f_sum = float(np.sum(w_i))
            if f_sum <= 0:
                continue
            tcx = float(np.sum(cx_i * w_i) / f_sum)
            tcy = float(np.sum(cy_i * w_i) / f_sum)
            span = max(float(math.sqrt(cy_i.size / math.pi)),
                       0.5 * float(max(np.ptp(cx_i), np.ptp(cy_i))))
            dist_c = math.hypot(tcx - mcx, tcy - mcy)
            cw = math.exp(-0.5 * (dist_c / max(20.0, 0.36 * min(SW, SH))) ** 2)
            targets.append({'cx': tcx * step, 'cy': tcy * step, 'r_span': span * step,
                            'score': f_sum * cw, 'flux': f_sum})

        if not targets:
            return mask_b
        targets.sort(key=lambda t: t['score'], reverse=True)
        prim = targets[0]
        # 분리된 원거리 동반은하 필터링
        min_sep = 0.12 * min(H, W)
        comps = [t for t in targets[1:6]
                 if math.hypot(t['cx'] - prim['cx'], t['cy'] - prim['cy']) >= max(min_sep, 1.8 * prim['r_span'])
                 and t['flux'] >= 0.04 * prim['flux']]
        area_frac = (math.pi * (prim['r_span'] ** 2)) / float(H * W)
        if mask is not None and not comps and area_frac >= 0.035:
            return mask_b

        yy, xx = np.indices((H, W), dtype=float)
        r_cut = float(np.clip(3.6 * prim['r_span'], 56.0, 0.44 * max(H, W)))
        d0 = np.hypot(xx - prim['cx'], yy - prim['cy'])
        out_mask = mask_b & (d0 <= r_cut)
        for comp in comps:
            dc = np.hypot(xx - comp['cx'], yy - comp['cy'])
            r_comp = max(24.0, 2.2 * comp['r_span'])
            out_mask &= ~((dc < 0.85 * d0) | (dc < r_comp))
        return out_mask if int(out_mask.sum()) >= 25 else mask_b

    # ── 통합 ─────────────────────────────────────────────
    @classmethod
    def linearize_image(cls, image_array, mode='srgb'):
        """8비트 사진 및 사전 스트레칭된 [0,1] 천체 FITS → 근사 선형 광량 복원.
        mode: 'srgb'(2.2) | 'astro'(역-Asinh) | 'auto' | 'none'"""
        arr = cls._normalize_channels(image_array)
        if mode == 'none':
            return arr.astype(float)
        if arr.dtype == np.uint8:
            if mode == 'astro':
                u = np.clip(arr.astype(float) / 255.0, 0.0, 1.0)
                return (np.sinh(4.0 * u) / math.sinh(4.0)) * 255.0
            if mode in ('srgb', 'auto'):
                return ((arr.astype(float) / 255.0) ** 2.2) * 255.0
            return arr.astype(float)

        arr_f = arr.astype(float)
        if mode == 'astro':
            finite = arr_f[np.isfinite(arr_f)]
            if finite.size == 0:
                return arr_f
            lo, hi = float(np.percentile(finite, 1.0)), float(np.percentile(finite, 99.9))
            u = np.clip((arr_f - lo) / max(hi - lo, 1e-9), 0.0, 1.15)
            return (np.sinh(4.0 * u) / math.sinh(4.0)) * 1000.0

        if mode == 'auto':
            # PixInsight / Siril / GraXpert 등에서 [0, 1] 로 사전 Asinh 스트레칭된 실수형 FITS 자동 감지 및 선형화
            finite = arr_f[np.isfinite(arr_f)]
            if finite.size >= 100:
                sub = finite[::max(1, finite.size // 120000)]
                vmin, vmax = float(np.min(sub)), float(np.max(sub))
                p999 = float(np.percentile(sub, 99.9))
                if vmin >= -0.25 and vmax <= 2.05 and p999 >= 0.55:
                    bg = float(np.percentile(sub, 25.0))
                    low = sub[sub <= np.percentile(sub, 65.0)]
                    sd = max(1e-7, float(1.4826 * np.median(np.abs(low - np.median(low))))) if low.size >= 10 else 1e-4
                    net = np.clip(sub - bg, 0.0, None)
                    p998 = float(np.percentile(net, 99.8))
                    sig = net[net > 3.5 * sd]
                    p85_sig = float(np.percentile(sig, 85.0)) if sig.size >= 20 else 0.35 * p998
                    comp_ratio = p998 / max(p85_sig, 1e-9)
                    if comp_ratio < 3.8:
                        k_asinh = 4.2 if comp_ratio < 2.8 else 3.6
                        u = np.clip((arr_f - bg) / max(p998, 1e-6), 0.0, 1.18)
                        return (np.sinh(k_asinh * u) / math.sinh(k_asinh)) * 1000.0
        return arr_f

    def analyze(self, image_array, mask=None, linearize='auto'):
        """영역 하나에 대한 전체 분석 결과 dict.
        mask=None 또는 대형 광시야 FITS 전체 마스크일 때 주 은하 타깃을 자동 분리합니다.
        linearize: 'auto'(8비트 sRGB 해제 + 스트레칭된 [0,1] FITS 역-Asinh 복원) | 'srgb' | 'astro' | 'none'"""
        image_norm = self._normalize_channels(image_array)
        image_lin = self.linearize_image(image_norm, linearize)
        gray_full = self.to_gray(image_lin)
        mask = self.auto_isolate_primary_mask(gray_full, mask)

        stats = self.region_stats(image_lin, mask)
        if stats.get('n_pix', 0) < 9:
            return {'stats': stats, 'error': '영역이 너무 작습니다 (최소 9픽셀).'}
        bg, bg_sd = stats['background'], stats['background_std']

        # ROI 주변으로 잘라서 계산 (대형 FITS 대비)
        x0b, y0b, x1b, y1b = stats['bbox']
        pad = 4
        ox, oy = max(0, x0b - pad), max(0, y0b - pad)
        ex, ey = min(gray_full.shape[1], x1b + pad + 1), min(gray_full.shape[0], y1b + pad + 1)
        gray_raw = gray_full[oy:ey, ox:ex]
        mask = mask[oy:ey, ox:ex]

        # 광시야 [0,1] 스트레칭 FITS(예: NGC 5982_denoised.fit)에서 전역 배경 비율이 높아 ROI 내부가 미선형화된 경우
        # 전경별 마스킹 및 중심 정밀화 이전에 ROI 단위 역-Asinh 복원 수행
        if linearize == 'auto' and image_norm.dtype != np.uint8 and float(np.nanmax(gray_raw)) <= 2.05:
            net_roi0 = np.clip(gray_raw[mask] - bg, 0.0, None)
            sig_roi0 = net_roi0[net_roi0 > 3.5 * bg_sd]
            if sig_roi0.size >= 30:
                p998_s = float(np.percentile(sig_roi0, 99.8))
                p80_s = float(np.percentile(sig_roi0, 80.0))
                if p80_s > 0 and (p998_s / p80_s) < 4.5:
                    k_roi = 4.3 if (p998_s / p80_s) < 3.0 else 3.6
                    u_r = np.clip((gray_raw - bg) / max(p998_s, 1e-6), 0.0, 1.18)
                    gray_raw = bg + (np.sinh(k_roi * u_r) / math.sinh(k_roi)) * 1000.0
                    bg_sd = max(bg_sd * (1000.0 / max(p998_s, 1e-6)) * (k_roi / math.sinh(k_roi)), 1e-4)

        # 전경 점광원(PSF 별) 마스킹 + 확장 헤일로 중심 보호
        gray, (gx0, gy0), n_stars_masked = self._find_extended_core_and_mask_stars(gray_raw, mask, bg, bg_sd)

        # 전경 별이 마스킹된 경우에만 광도 중심(cx, cy)·축비(b/a)·방위각(PA)을 재계산하여 별 편향 제거
        if n_stars_masked > 0:
            sig_m = mask & ((gray - bg) >= 2.0 * bg_sd)
            use_m = sig_m if int(sig_m.sum()) >= 20 else mask
            ys_m, xs_m = np.nonzero(use_m)
            net_m = np.clip(gray[use_m] - bg, 0.0, None)
            w_m = net_m if net_m.sum() > 0 else np.ones_like(net_m)
            w_sum = float(w_m.sum()) or 1.0
            cx = float(np.sum(xs_m * w_m) / w_sum)
            cy = float(np.sum(ys_m * w_m) / w_sum)
            if math.hypot(cx - gx0, cy - gy0) > 0.25 * min(gray.shape):
                cx, cy = 0.40 * cx + 0.60 * gx0, 0.40 * cy + 0.60 * gy0
            mxx = float(np.sum(w_m * (xs_m - cx) ** 2) / w_sum)
            myy = float(np.sum(w_m * (ys_m - cy) ** 2) / w_sum)
            mxy = float(np.sum(w_m * (xs_m - cx) * (ys_m - cy)) / w_sum)
            tmp = math.sqrt(max(((mxx - myy) / 2.0) ** 2 + mxy ** 2, 0.0))
            l1 = (mxx + myy) / 2.0 + tmp
            l2 = max((mxx + myy) / 2.0 - tmp, 1e-12)
            a_ax, b_ax = math.sqrt(max(l1, 1e-12)), math.sqrt(l2)
            axis_q = float(np.clip(b_ax / a_ax if a_ax > 0 else 1.0, 0.15, 1.0))
            pa_deg = float(math.degrees(0.5 * math.atan2(2.0 * mxy, mxx - myy)))
            stats['centroid_x'] = float(cx + ox)
            stats['centroid_y'] = float(cy + oy)
            stats['axis_ratio'] = axis_q
            stats['ellipticity'] = float(1.0 - axis_q)
            stats['position_angle'] = pa_deg
        else:
            cx, cy = stats['centroid_x'] - ox, stats['centroid_y'] - oy
            axis_q = float(np.clip(stats.get('axis_ratio', 1.0), 0.15, 1.0))
            pa_deg = float(stats.get('position_angle', 0.0))
        stats['stars_masked'] = int(n_stars_masked)

        # Lotz+2004 표준 원형 프로파일 기반 분할 지도(seg) 및 핵/덩어리 수 먼저 추출
        r_circ, prof_circ, _ = self.radial_profile(gray, cx, cy, mask=mask, bg=bg, axis_ratio=1.0, pa_deg=0.0)
        Rp_circ = self.petrosian_radius(r_circ, prof_circ)
        seg = self.segmentation_map(gray, mask, cx, cy, bg, bg_sd, r_circ, prof_circ, Rp_circ)
        n_nuc, nuclei = self.count_nuclei(gray, seg, bg)

        # 단일 중심핵 은하(타원/정규나선, n_nuc == 1)는 외곽 배경 경사에 의해 중심(cx, cy)이 끌려가지 않도록
        # 확장 헤일로 중심(gx0, gy0) 주변 내부 고신호 영역(≥3σ)에서 2단계 수축 구경으로 중심·타원율을 정밀 고정
        if n_nuc == 1:
            yy_g, xx_g = np.indices(gray.shape, dtype=float)
            cx_r, cy_r = gx0, gy0
            net_all = np.clip(gray - bg, 0.0, None)
            peak_c = float(np.max(np.where(mask, net_all, 0.0))) if mask.any() else 0.0
            for r_fac in (0.38, 0.18):
                r_loc = max(9.0, r_fac * min(gray.shape))
                in_ap = mask & (((xx_g - cx_r) ** 2 + (yy_g - cy_r) ** 2) <= r_loc ** 2) & (
                    net_all >= max(2.5 * bg_sd, 0.025 * peak_c)
                )
                if int(in_ap.sum()) >= 12:
                    w_ap = net_all[in_ap]
                    ws = float(w_ap.sum())
                    if ws > 0:
                        cx_r = float(np.sum(xx_g[in_ap] * w_ap) / ws)
                        cy_r = float(np.sum(yy_g[in_ap] * w_ap) / ws)
            cx, cy = cx_r, cy_r
            # 내부 등광도 영역(≥ max(3σ, 3.5% peak))에서 2차 모멘트 타원율·방위각 산출
            iso_ap = mask & (((xx_g - cx) ** 2 + (yy_g - cy) ** 2) <= (0.45 * max(gray.shape)) ** 2) & (
                net_all >= max(3.0 * bg_sd, 0.035 * peak_c)
            )
            if int(iso_ap.sum()) >= 16:
                w_iso = net_all[iso_ap]
                ws = float(w_iso.sum()) or 1.0
                mxx = float(np.sum(w_iso * (xx_g[iso_ap] - cx) ** 2) / ws)
                myy = float(np.sum(w_iso * (yy_g[iso_ap] - cy) ** 2) / ws)
                mxy = float(np.sum(w_iso * (xx_g[iso_ap] - cx) * (yy_g[iso_ap] - cy)) / ws)
                tmp = math.sqrt(max(((mxx - myy) / 2.0) ** 2 + mxy ** 2, 0.0))
                l1 = (mxx + myy) / 2.0 + tmp
                l2 = max((mxx + myy) / 2.0 - tmp, 1e-12)
                axis_q = float(np.clip(math.sqrt(l2) / math.sqrt(max(l1, 1e-12)), 0.15, 1.0))
                pa_deg = float(math.degrees(0.5 * math.atan2(2.0 * mxy, mxx - myy)))
            stats['centroid_x'] = float(cx + ox)
            stats['centroid_y'] = float(cy + oy)
            stats['axis_ratio'] = axis_q
            stats['ellipticity'] = float(1.0 - axis_q)
            stats['position_angle'] = pa_deg
            r_circ, prof_circ, _ = self.radial_profile(gray, cx, cy, mask=mask, bg=bg, axis_ratio=1.0, pa_deg=0.0)
            Rp_circ = self.petrosian_radius(r_circ, prof_circ)
            seg = self.segmentation_map(gray, mask, cx, cy, bg, bg_sd, r_circ, prof_circ, Rp_circ)
        elif int(seg.sum()) >= 30:
            # 다중 덩어리/먼지띠 분할 은하(예: 측면 나선 NGC 891)도 광시야 배경 원에 희석되지 않도록 본체(seg) 2차 모멘트로 축비·중심 갱신
            ys_s, xs_s = np.nonzero(seg)
            w_s = np.clip(gray[seg] - bg, 0.0, None)
            ws = float(w_s.sum())
            if ws > 0:
                cx = float(np.sum(xs_s * w_s) / ws)
                cy = float(np.sum(ys_s * w_s) / ws)
                mxx = float(np.sum(w_s * (xs_s - cx) ** 2) / ws)
                myy = float(np.sum(w_s * (ys_s - cy) ** 2) / ws)
                mxy = float(np.sum(w_s * (xs_s - cx) * (ys_s - cy)) / ws)
                tmp = math.sqrt(max(((mxx - myy) / 2.0) ** 2 + mxy ** 2, 0.0))
                l1 = (mxx + myy) / 2.0 + tmp
                l2 = max((mxx + myy) / 2.0 - tmp, 1e-12)
                axis_q = float(np.clip(math.sqrt(l2) / math.sqrt(max(l1, 1e-12)), 0.15, 1.0))
                pa_deg = float(math.degrees(0.5 * math.atan2(2.0 * mxy, mxx - myy)))
                stats['centroid_x'] = float(cx + ox)
                stats['centroid_y'] = float(cy + oy)
                stats['axis_ratio'] = axis_q
                stats['ellipticity'] = float(1.0 - axis_q)
                stats['position_angle'] = pa_deg

        # 단일 중심핵 은하(타원/정규나선, n_nuc == 1) 또는 고경사 측면 원반(axis_q < 0.44)은 등광도 타원 고리(b/a, PA) 사용,
        # 다중 덩어리/이중핵(불규칙/병합, n_nuc >= 2)은 원형 고리로 비모수 일관성 유지
        use_ell_rings = (n_nuc == 1) or (axis_q < 0.44)
        q_prof = axis_q if use_ell_rings else 1.0
        pa_prof = pa_deg if use_ell_rings else 0.0
        if q_prof < 0.97:
            r, prof, cum = self.radial_profile(gray, cx, cy, mask=mask, bg=bg, axis_ratio=q_prof, pa_deg=pa_prof)
            Rp = self.petrosian_radius(r, prof) or Rp_circ
        else:
            r, prof, Rp = r_circ, prof_circ, Rp_circ

        # SDSS 방식: 2·Rp 구경 안에서 누적 광량 반경
        aperture = mask
        if Rp:
            r_ell_grid = self._elliptical_radius_grid(gray.shape, cx, cy, axis_ratio=q_prof, pa_deg=pa_prof)
            ap = r_ell_grid <= 2.0 * Rp
            if (mask & ap).sum() >= 9:
                aperture = mask & ap
        ra, pa_, ca = self.radial_profile(gray, cx, cy, mask=aperture, bg=bg, axis_ratio=q_prof, pa_deg=pa_prof)
        R20 = self.radius_at_fraction(ra, ca, 0.2)
        R50 = self.radius_at_fraction(ra, ca, 0.5)
        R80 = self.radius_at_fraction(ra, ca, 0.8)
        R90 = self.radius_at_fraction(ra, ca, 0.9)
        C_cas = 5 * math.log10(R80 / R20) if R20 and R80 and R20 > 0 else None
        C_sdss = R90 / R50 if R50 and R90 and R50 > 0 else None

        A = self.asymmetry(gray, seg, cx, cy, bg, bg_sd)
        S = self.smoothness(gray, seg, bg, Rp or (R90 or 0) * 0.7)
        G = self.gini(np.clip(gray[seg] - bg, 0, None))
        M20 = self.m20(gray, seg, bg)
        sersic = self.sersic_fit(ra, pa_)
        W_spiral = self.spiral_winding(gray, cx, cy, R50, bg, bg_sd, axis_ratio=q_prof, pa_deg=pa_prof)

        # 천체사진 후보정(강한 커브/Asinh 스트레칭)된 JPG/PNG 매끄러운 타원은하의 중심핵 압축 보정
        if (linearize == 'auto' and n_nuc == 1 and A is not None and A <= 0.14
                and W_spiral < 0.045 and (S is None or S <= 0.09) and axis_q >= 0.30):
            seg_net = np.clip(gray[seg] - bg, 0.0, None)
            if seg_net.size >= 30:
                p995 = float(np.percentile(seg_net, 99.5))
                p80 = float(np.percentile(seg_net, 80.0))
                if p80 > 0 and (p995 / p80) < 3.1:
                    u_roi = np.clip((gray - bg) / max(p995, 1e-6), 0.0, 1.15)
                    gray_de = bg + (np.sinh(3.2 * u_roi) / math.sinh(3.2)) * p995
                    r_d, prof_d, _ = self.radial_profile(gray_de, cx, cy, mask=mask, bg=bg, axis_ratio=axis_q, pa_deg=pa_deg)
                    Rp_d = self.petrosian_radius(r_d, prof_d) or Rp
                    ap_d = mask
                    if Rp_d:
                        ap_try = self._elliptical_radius_grid(gray.shape, cx, cy, axis_ratio=axis_q, pa_deg=pa_deg) <= 2.0 * Rp_d
                        if (mask & ap_try).sum() >= 9:
                            ap_d = mask & ap_try
                    ra, pa_, ca = self.radial_profile(gray_de, cx, cy, mask=ap_d, bg=bg, axis_ratio=axis_q, pa_deg=pa_deg)
                    R20 = self.radius_at_fraction(ra, ca, 0.2) or R20
                    R50 = self.radius_at_fraction(ra, ca, 0.5) or R50
                    R80 = self.radius_at_fraction(ra, ca, 0.8) or R80
                    R90 = self.radius_at_fraction(ra, ca, 0.9) or R90
                    C_cas = 5 * math.log10(R80 / R20) if R20 and R80 and R20 > 0 else C_cas
                    C_sdss = R90 / R50 if R50 and R90 and R50 > 0 else C_sdss
                    sersic = self.sersic_fit(ra, pa_) or sersic
                    G = self.gini(np.clip(gray_de[seg] - bg, 0, None)) or G
                    M20 = self.m20(gray_de, seg, bg) or M20

        metrics = {
            'R20_px': R20, 'R50_px': R50, 'R80_px': R80, 'R90_px': R90, 'R_petro_px': Rp,
            'C_cas': C_cas, 'C_sdss': C_sdss, 'asymmetry': A, 'smoothness': S,
            'gini': G, 'm20': M20, 'sersic_n': sersic['n'] if sersic else None,
            'sersic_Re_px': sersic['R_e'] if sersic else None,
            'W_spiral': W_spiral, 'axis_ratio': float(axis_q),
            'n_nuclei': n_nuc, 'seg_pixels': int(seg.sum()),
            'stars_masked': int(n_stars_masked),
        }
        morph = self.classify_morphology(metrics)
        snr = stats.get('snr')
        peak_sig = (float(np.max(gray[mask])) - bg) / bg_sd if mask.any() and bg_sd > 0 else 0.0
        if (snr is not None and np.isfinite(snr) and snr < 5) or stats.get('net_flux', 0) <= 0 \
                or stats.get('std', 0) < 1e-6 or metrics['seg_pixels'] < 9 or peak_sig < 5:
            morph = {'class': '유의미한 천체 없음 (배경/잡음)', 'class_en': 'No significant source',
                     'class_3': '유의미한 천체 없음', 'scores': {},
                     'reasons': ['영역 S/N=%.1f, 최대 밝기 유의도 %.1fσ, 분할 영역 %d픽셀 → 형태 지수를 신뢰할 수 없음'
                                 % (snr if snr is not None else float('nan'), peak_sig, metrics['seg_pixels']),
                                 '은하가 영역 안에 들어오도록 다시 그려 보세요.']}
            metrics['significant'] = False
        else:
            metrics['significant'] = True
        est_phys = self.estimate_physical_priors(stats, metrics, morph)
        return {
            'stats': stats, 'metrics': metrics, 'morphology': morph,
            'profile': {'r': ra, 'I': pa_, 'cum': ca}, 'sersic': sersic,
            'segmentation': seg, 'crop_offset': (ox, oy), 'cutout': gray - bg,
            'nuclei': [(x + ox, y + oy, v) for x, y, v in nuclei[:8]],
            'ml_features': self.to_ml_features(stats, metrics, morph),
            'estimated_physics': est_phys,
        }

    def estimate_physical_priors(self, stats, metrics, morph):
        """형태 지수(C, Sérsic n, A, G, M20) 및 선택적 RGB 색지수로부터 SDSS DR18 경험적 물리량(질량·sSFR·D4000·σ_v) 추정.
        단색(L필터/FITS) 이미지이거나 분광 데이터가 없을 때 위상공간·GEI v3·AI 분류의 평균값 대체 편향을 방지합니다."""
        if not metrics.get('significant', True):
            return {}
        cls_en = morph.get('class_en', 'Unknown')
        C = float(metrics.get('C_sdss') or 2.5)
        n = float(metrics.get('sersic_n') or (3.4 if cls_en == 'Early-type' else 1.5))
        ur_rgb = self.estimate_ur_from_rgb(stats.get('color_GR')) if not stats.get('is_monochrome') else None

        if cls_en == 'Early-type':
            ur = float(np.clip(ur_rgb if ur_rgb is not None else (2.58 + 0.16 * (C - 2.9)), 2.35, 3.05))
            log_mass = float(np.clip(10.95 + 0.32 * (C - 2.9) + 0.08 * (n - 3.0), 10.35, 11.85))
            d4000 = float(np.clip(1.82 + 0.22 * (ur - 2.55), 1.65, 2.10))
            log_ssfr = float(np.clip(-11.85 - 0.55 * (ur - 2.55) - 0.12 * (log_mass - 11.0), -13.2, -11.25))
            vel_disp = float(np.clip(10 ** (2.22 + 0.28 * (log_mass - 11.0)), 125.0, 340.0))
            oh = float(np.clip(9.06 + 0.12 * (log_mass - 11.0), 8.90, 9.22))
        elif cls_en == 'Irregular':
            ur = float(np.clip(ur_rgb if ur_rgb is not None else (1.32 + 0.15 * (C - 2.0)), 0.95, 1.75))
            log_mass = float(np.clip(9.30 + 0.35 * (C - 2.0), 8.50, 10.10))
            d4000 = float(np.clip(1.15 + 0.22 * (ur - 1.32), 1.00, 1.35))
            log_ssfr = float(np.clip(-9.35 - 0.45 * (ur - 1.32), -10.0, -8.75))
            vel_disp = float(np.clip(10 ** (1.68 + 0.24 * (log_mass - 9.3)), 30.0, 95.0))
            oh = float(np.clip(8.42 + 0.28 * (log_mass - 9.3), 7.95, 8.80))
        elif cls_en == 'Merger candidate':
            ur = float(np.clip(ur_rgb if ur_rgb is not None else 1.72, 1.15, 2.45))
            log_mass = float(np.clip(10.55 + 0.25 * (C - 2.5), 9.80, 11.35))
            d4000 = float(np.clip(1.28 + 0.25 * (ur - 1.72), 1.08, 1.65))
            log_ssfr = float(np.clip(-9.55 - 0.55 * (ur - 1.72), -10.6, -8.65))
            vel_disp = float(np.clip(10 ** (2.10 + 0.25 * (log_mass - 10.5)), 85.0, 240.0))
            oh = float(np.clip(8.88 + 0.20 * (log_mass - 10.5), 8.50, 9.12))
        else:  # Late-type (Spiral / Disk)
            ur = float(np.clip(ur_rgb if ur_rgb is not None else (1.82 + 0.28 * (C - 2.3)), 1.30, 2.35))
            log_mass = float(np.clip(10.38 + 0.38 * (C - 2.3) + 0.08 * (n - 1.3), 9.45, 11.15))
            d4000 = float(np.clip(1.34 + 0.30 * (ur - 1.82), 1.12, 1.64))
            log_ssfr = float(np.clip(-10.05 - 0.65 * (ur - 1.82), -10.85, -9.35))
            vel_disp = float(np.clip(10 ** (1.98 + 0.26 * (log_mass - 10.4)), 55.0, 185.0))
            oh = float(np.clip(8.86 + 0.25 * (log_mass - 10.4), 8.35, 9.10))

        log_sfr = float(log_mass + log_ssfr)
        return {
            'log_mass': round(log_mass, 3),
            'log_sfr': round(log_sfr, 3),
            'log_ssfr': round(log_ssfr, 3),
            'color_ur': round(ur, 3),
            'd4000_n': round(d4000, 3),
            'velDisp': round(vel_disp, 1),
            'metallicity': round(oh, 3),
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
