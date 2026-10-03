# -*- coding: utf-8 -*-
"""
🌌 GalaxyEvolution Studio v4 — 사진/FITS 위에 영역을 그려서 분석하는 은하 분석 플랫폼
=====================================================================================
Ginga(STScI)의 이미지 뷰어 철학 + 은하 진화 분석 파이프라인

두 가지 분석 모드
  🖼️ 은하 이미지 분석 : 영역 측광 · 비모수 형태(CAS, Gini–M20) · Sérsic · 형태 분류 · AI
  🌈 분광 분석       : 분광 사진 ROI → 1D 스펙트럼 → 파장 교정 → 방출선(블렌드 분리) → 물리량 · BPT · AI

입력: JPG/PNG/TIFF/BMP, FITS(2D 영상 · 1D 스펙트럼 · SDSS spec 테이블), CSV/TXT 스펙트럼,
      SDSS 좌표 → 실제 은하 사진, 내장 데모(모의 은하/분광 사진/스펙트럼), SDSS 대표 은하

실행: streamlit run app.py
"""

import os
import io
import json
import hashlib
import datetime
import warnings

import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from PIL import Image, ImageEnhance

import matplotlib
matplotlib.use('Agg')
from matplotlib import colormaps as mpl_colormaps

from modules import canvas_compat  # noqa: F401  (st_canvas import 전에 반드시 로드)

try:
    from streamlit_drawable_canvas import st_canvas
    CANVAS_OK, CANVAS_ERR = True, ''
except Exception as _e:  # pragma: no cover
    CANVAS_OK, CANVAS_ERR = False, str(_e)

try:
    from astropy.io import fits
    FITS_OK = True
except Exception:  # pragma: no cover
    FITS_OK = False

from modules.spectrum_engine import (SpectrumROIExtractor, WavelengthCalibrator, EmissionLineFitter,
                                     MockSpectrumGenerator, LINE_LIST, ABSORPTION_LIST)
from modules.image_analyzer import GalaxyImageAnalyzer, RegionGeometry, synthetic_galaxy_image
from modules.physics_calculator import PhysicsCalculator
from modules.phase_space_mapper import PhaseSpaceMapper
from modules.ml_predictor import GalaxyPredictor, FEATURE_LABELS_KO
from modules.sdss_fetcher import SDSSFetcher
from modules.report_generator import ReportGenerator

warnings.filterwarnings('ignore', category=RuntimeWarning)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MASTER_CSV = os.path.join(BASE_DIR, 'galaxy_master_complete_all.csv')
MODEL_DIR = os.path.join(BASE_DIR, 'output', 'models')

PALETTE = ['#ff4b4b', '#22d3ee', '#a3e635', '#facc15', '#c084fc', '#fb923c', '#f472b6', '#34d399']
MAX_SIDE = 4000          # 분석용 원본 최대 변 길이 (메모리 보호)
CANVAS_MAX_W = 760
CANVAS_MAX_H = 720

CMAPS = {'회색 (Gray)': 'gray', 'Viridis': 'viridis', 'Inferno': 'inferno', 'Magma': 'magma',
         'Plasma': 'plasma', 'Hot': 'hot', 'Cubehelix': 'cubehelix', 'Bone': 'bone',
         'Jet': 'jet', 'Coolwarm': 'coolwarm'}
STRETCHES = {'선형 (linear)': 'linear', '로그 (log)': 'log', '제곱근 (sqrt)': 'sqrt',
             '제곱 (squared)': 'squared', 'asinh': 'asinh', '히스토그램 평활 (histeq)': 'histeq'}
CUTS = {'zscale (Ginga 기본)': 'zscale', '백분위 (percentile)': 'percentile', '최소-최대 (minmax)': 'minmax'}
TOOLS = {'▭ 사각형': 'rect', '◯ 원': 'circle', '✏️ 올가미': 'freedraw', '⬠ 다각형': 'polygon',
         '／ 직선': 'line', '📍 픽셀값': 'point', '✋ 이동·수정': 'transform'}
FLUX_UNITS = {'임의 단위 (사진 픽셀값)': None, 'SDSS (10⁻¹⁷ erg/s/cm²/Å)': 1e-17, 'erg/s/cm²/Å': 1.0}
MODE_IMAGE = '🖼️ 은하 이미지 분석 (측광·형태)'
MODE_SPEC = '🌈 분광 분석 (분광 사진·스펙트럼)'

st.set_page_config(page_title='GalaxyEvolution Studio', page_icon='🌌', layout='wide',
                   initial_sidebar_state='expanded')

st.markdown("""
<style>
.block-container {padding-top: 1.4rem; padding-bottom: 3rem;}
.hero {background: linear-gradient(120deg, #0b1023 0%, #1e1b4b 45%, #312e81 100%);
       border: 1px solid #3730a3; border-radius: 16px; padding: 18px 24px; margin-bottom: 14px;}
.hero h1 {margin: 0; font-size: 1.85rem; color: #e0e7ff;}
.hero p {margin: 4px 0 0 0; color: #a5b4fc; font-size: 0.95rem;}
.step {background: #111827; border-left: 4px solid #6366f1; border-radius: 8px;
       padding: 8px 14px; margin: 10px 0 8px 0; font-weight: 600; color: #e0e7ff;}
.roi-chip {display: inline-block; padding: 2px 10px; border-radius: 999px; font-size: 0.82rem;
           font-weight: 700; color: #0b1023; margin-right: 6px;}
.small-note {color: #94a3b8; font-size: 0.82rem;}
div[data-testid="stMetricValue"] {font-size: 1.25rem;}
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
#                       캐시된 리소스
# ═══════════════════════════════════════════════════════════
@st.cache_resource(show_spinner='SDSS 배경 데이터 로딩 중...')
def get_mapper():
    return PhaseSpaceMapper(MASTER_CSV)


@st.cache_resource(show_spinner='AI 모델 로딩 중...')
def get_predictor():
    return GalaxyPredictor(MODEL_DIR, master_csv=MASTER_CSV)


calc = PhysicsCalculator()
fitter = EmissionLineFitter()
extractor = SpectrumROIExtractor()
reporter = ReportGenerator(os.path.join(BASE_DIR, 'output', 'reports'))


def fnum(v, fmt='%.2f', default='—'):
    """None/NaN/inf 안전 포맷"""
    if v is None:
        return default
    try:
        f = float(v)
    except (TypeError, ValueError):
        return str(v)
    if not np.isfinite(f):
        return default
    return fmt % f


def valid(v):
    try:
        return v is not None and np.isfinite(float(v))
    except (TypeError, ValueError):
        return False


def hex_rgba(hx, a=0.15):
    hx = hx.lstrip('#')
    if len(hx) != 6:
        return 'rgba(255,75,75,%.2f)' % a
    return 'rgba(%d,%d,%d,%.2f)' % (int(hx[0:2], 16), int(hx[2:4], 16), int(hx[4:6], 16), a)


# ═══════════════════════════════════════════════════════════
#                    입력 파일 로딩 (FITS/이미지/CSV)
# ═══════════════════════════════════════════════════════════
def _header_dict(h):
    out = {}
    try:
        for k, v in h.items():
            if k and isinstance(v, (int, float, str, bool)):
                out[str(k)] = v
    except Exception:
        pass
    return out


def _pixel_scale_from_header(hd):
    for k in ('CD1_1', 'CDELT1'):
        if k in hd:
            try:
                ps = abs(float(hd[k])) * 3600.0
                if 0.01 < ps < 100:
                    return ps
            except Exception:
                pass
    for k in ('PIXSCALE', 'SECPIX', 'PIXSCAL1'):
        if k in hd:
            try:
                return float(hd[k])
            except Exception:
                pass
    return None


def _cap_size(arr):
    h, w = arr.shape[:2]
    if max(h, w) <= MAX_SIDE:
        return arr, 1.0
    f = MAX_SIDE / max(h, w)
    if arr.dtype == np.uint8:
        img = Image.fromarray(arr)
        img = img.resize((int(w * f), int(h * f)), Image.LANCZOS)
        return np.array(img), f
    from scipy import ndimage
    return ndimage.zoom(arr, f, order=1), f


def _spectrum_from_df(df):
    num = df.apply(pd.to_numeric, errors='coerce')
    num = num.dropna(axis=1, how='all')
    cols = [str(c) for c in num.columns]
    low = [c.lower() for c in cols]
    wcol = next((cols[i] for i, c in enumerate(low) if any(k in c for k in ('wave', 'lam', 'wl', 'angstrom'))), None)
    fcol = next((cols[i] for i, c in enumerate(low) if any(k in c for k in ('flux', 'f_lam', 'intens', 'counts'))), None)
    if wcol is None or fcol is None:
        if num.shape[1] < 2:
            return None
        wcol, fcol = cols[0], cols[1]
    num.columns = cols
    d = num[[wcol, fcol]].dropna()
    if len(d) < 10:
        return None
    w, f = d[wcol].values.astype(float), d[fcol].values.astype(float)
    if np.nanmax(w) < 50:          # μm → Å
        w = w * 1e4
    elif np.nanmax(w) < 1500:      # nm → Å
        w = w * 10.0
    o = np.argsort(w)
    return w[o], f[o]


@st.cache_data(show_spinner='파일 해석 중...', max_entries=4)
def load_source(data: bytes, name: str) -> dict:
    """업로드 파일 → {'kind': 'image'|'spectrum', ...}"""
    lname = name.lower()
    out = {'name': name, 'notes': []}
    is_fits = lname.endswith(('.fits', '.fit', '.fts', '.fits.gz', '.fit.gz', '.fz')) or data[:6] == b'SIMPLE'
    if is_fits:
        if not FITS_OK:
            raise RuntimeError('astropy 가 설치되어 있지 않아 FITS 를 읽을 수 없습니다.')
        img, img_hdr, spec, z_hint, unit_hint, spec_hdr = None, {}, None, None, None, {}
        with fits.open(io.BytesIO(data), memmap=False) as hdul:
            for hdu in hdul:
                d = hdu.data
                if d is None:
                    continue
                if isinstance(hdu, (fits.BinTableHDU, fits.TableHDU)):
                    names = {n.lower(): n for n in d.columns.names}
                    if spec is None and 'flux' in names:
                        wkey = next((names[k] for k in ('loglam', 'wave', 'wavelength', 'lambda', 'lam') if k in names), None)
                        if wkey is not None:
                            w = np.asarray(d[wkey], dtype=float).ravel()
                            f = np.asarray(d[names['flux']], dtype=float).ravel()
                            if wkey.lower() == 'loglam':
                                w = 10 ** w
                                unit_hint = 'sdss'
                            spec = (w, f)
                            spec_hdr = _header_dict(hdu.header)
                    if z_hint is None and 'z' in names and len(d) > 0:
                        try:
                            z_hint = float(np.asarray(d[names['z']]).ravel()[0])
                        except Exception:
                            pass
                else:
                    arr = np.asarray(d)
                    while arr.ndim > 2:
                        arr = arr[0]
                    if arr.ndim == 2 and min(arr.shape) == 1:
                        arr = arr.ravel()
                    if arr.ndim == 2 and img is None:
                        img = arr.astype(float)
                        img_hdr = _header_dict(hdu.header)
                    elif arr.ndim == 1 and spec is None and arr.size > 10:
                        w = WavelengthCalibrator.calibrate_from_fits_header(hdu.header, arr.size)
                        if w is not None:
                            spec = (w, arr.astype(float))
                            spec_hdr = _header_dict(hdu.header)
                            bunit = str(hdu.header.get('BUNIT', ''))
                            if '1e-17' in bunit.lower() or '10^-17' in bunit:
                                unit_hint = 'sdss'
        if img is not None:
            img = np.where(np.isfinite(img), img, np.nan)
            img, f = _cap_size(np.nan_to_num(img, nan=float(np.nanmedian(img))))
            if f != 1.0:
                out['notes'].append('대형 FITS → 분석용으로 %.2f배 축소' % f)
            out.update({'kind': 'image', 'raw': img, 'header': img_hdr, 'is_fits': True,
                        'pixel_scale': (_pixel_scale_from_header(img_hdr) or 0) / f or None})
            return out
        if spec is not None:
            w, f = spec
            m = np.isfinite(w) & np.isfinite(f)
            o = np.argsort(w[m])
            out.update({'kind': 'spectrum', 'wave': w[m][o], 'flux': f[m][o], 'header': spec_hdr,
                        'z_hint': z_hint, 'unit_hint': unit_hint})
            return out
        raise RuntimeError('FITS 안에서 2D 영상이나 1D 스펙트럼을 찾지 못했습니다.')

    if lname.endswith(('.csv', '.txt', '.dat', '.tsv')):
        txt = data.decode('utf-8', errors='ignore')
        try:
            df = pd.read_csv(io.StringIO(txt), sep=None, engine='python', comment='#')
            try:
                float(str(df.columns[0]))
                df = pd.read_csv(io.StringIO(txt), sep=None, engine='python', comment='#', header=None)
            except ValueError:
                pass
        except Exception as e:
            raise RuntimeError('텍스트 스펙트럼 파싱 실패: %s' % e)
        sp = _spectrum_from_df(df)
        if sp is None:
            raise RuntimeError('파장/플럭스 두 열을 찾지 못했습니다 (예: wavelength,flux).')
        out.update({'kind': 'spectrum', 'wave': sp[0], 'flux': sp[1], 'header': {}, 'z_hint': None,
                    'unit_hint': None})
        return out

    img = Image.open(io.BytesIO(data))
    img.load()
    if img.mode in ('I;16', 'I;16B', 'I;16L', 'I', 'F'):
        arr = np.asarray(img, dtype=float)
        out['notes'].append('16/32비트 과학 영상으로 인식 (선형 데이터)')
    else:
        arr = np.asarray(img.convert('RGB'), dtype=np.uint8)
    arr, f = _cap_size(arr)
    if f != 1.0:
        out['notes'].append('대형 이미지 → 분석용으로 %.2f배 축소' % f)
    out.update({'kind': 'image', 'raw': arr, 'header': {}, 'is_fits': False, 'pixel_scale': None})
    return out


# ═══════════════════════════════════════════════════════════
#                 Ginga 스타일 표시 엔진
# ═══════════════════════════════════════════════════════════
def _sample(data, n=500_000):
    v = data[np.isfinite(data)].ravel()
    if v.size > n:
        v = v[:: v.size // n]
    return v


def compute_limits(data, method, p_lo=0.5, p_hi=99.5):
    v = _sample(data)
    if v.size == 0:
        return 0.0, 1.0
    if method == 'zscale':
        try:
            from astropy.visualization import ZScaleInterval
            lo, hi = ZScaleInterval().get_limits(v)
        except Exception:
            lo, hi = np.percentile(v, [1, 99.5])
    elif method == 'percentile':
        lo, hi = np.percentile(v, [p_lo, p_hi])
    else:
        lo, hi = float(v.min()), float(v.max())
    if hi <= lo:
        hi = lo + 1.0
    return float(lo), float(hi)


def apply_stretch(x, mode):
    x = np.clip(x, 0, 1)
    if mode == 'log':
        return np.log10(1000 * x + 1) / np.log10(1001)
    if mode == 'sqrt':
        return np.sqrt(x)
    if mode == 'squared':
        return x ** 2
    if mode == 'asinh':
        return np.arcsinh(10 * x) / np.arcsinh(10)
    if mode == 'histeq':
        hist, edges = np.histogram(x.ravel(), bins=1024, range=(0, 1))
        cdf = np.cumsum(hist).astype(float)
        cdf /= cdf[-1] if cdf[-1] > 0 else 1
        return np.interp(x, edges[:-1], cdf)
    return x


def to_gray(raw):
    if raw.ndim == 3:
        r = raw[..., :3].astype(float)
        return 0.299 * r[..., 0] + 0.587 * r[..., 1] + 0.114 * r[..., 2]
    return raw.astype(float)


@st.cache_data(show_spinner=False, max_entries=12)
def render_display(sig: str, _raw: np.ndarray, opts: tuple) -> Image.Image:
    """원본 → 화면 표시용 RGB (분석에는 사용하지 않음)"""
    o = dict(opts)
    raw = _raw
    if raw.ndim == 2 or o['force_gray']:
        data = to_gray(raw)
        lo, hi = compute_limits(data, o['cut'], o['p_lo'], o['p_hi'])
        x = (data - lo) / (hi - lo)
        x = apply_stretch(np.nan_to_num(x, nan=0.0), o['stretch'])
        rgb = mpl_colormaps[o['cmap']](x)[..., :3]
    else:
        rgb = raw[..., :3].astype(float) / 255.0
        if o['stretch'] != 'linear':
            rgb = apply_stretch(rgb, o['stretch'])
    if o['invert']:
        rgb = 1.0 - rgb
    img = Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8))
    if o['brightness'] != 1.0:
        img = ImageEnhance.Brightness(img).enhance(o['brightness'])
    if o['contrast'] != 1.0:
        img = ImageEnhance.Contrast(img).enhance(o['contrast'])
    return img


# ═══════════════════════════════════════════════════════════
#                       세션 상태
# ═══════════════════════════════════════════════════════════
def init_state():
    ss = st.session_state
    ss.setdefault('analysis_type', MODE_IMAGE)
    ss.setdefault('R', None)           # 분석 결과
    ss.setdefault('demo', None)        # 데모/SDSS 입력 소스
    ss.setdefault('canvas_reset', 0)
    ss.setdefault('n_objs', 0)
    ss.setdefault('last_sig', None)
    ss.setdefault('flux_unit_idx', 0)
    # 라디오 위젯이 만들어지기 전에만 analysis_type 을 바꿀 수 있으므로 예약값을 여기서 반영
    if ss.get('_pending_mode') in (MODE_IMAGE, MODE_SPEC):
        ss['analysis_type'] = ss.pop('_pending_mode')
    else:
        ss.pop('_pending_mode', None)


def set_demo(d, mode=None):
    if d is not None:
        d['uid'] = datetime.datetime.now().strftime('%H%M%S%f')
    st.session_state['demo'] = d
    st.session_state['R'] = None
    st.session_state['n_objs'] = 0
    if mode:
        st.session_state['_pending_mode'] = mode


# ── 사이드바 버튼 콜백 (위젯 생성 전에 실행되므로 상태 변경이 안전) ──
def cb_demo_galaxy(kind=None):
    kind = kind or st.session_state.get('demo_gkind', 'spiral')
    set_demo({'kind': 'image', 'img': synthetic_galaxy_image(kind), 'name': '모의 %s 은하' % kind,
              'pixel_scale': 0.396}, MODE_IMAGE)


def cb_demo_spec_image(kind=None):
    kind = kind or st.session_state.get('demo_skind', 'star_forming')
    img, w0, w1 = MockSpectrumGenerator().generate_spectrum_image(kind)
    set_demo({'kind': 'image', 'img': img, 'name': '모의 분광사진 %s' % kind, 'calib': (w0, w1)}, MODE_SPEC)


def cb_demo_spec_1d(kind=None):
    kind = kind or st.session_state.get('demo_skind', 'star_forming')
    np.random.seed(None)
    df = MockSpectrumGenerator().generate(kind, z=0.05)
    set_demo({'kind': 'spectrum', 'wave': df['wavelength'].values, 'flux': df['flux'].values,
              'name': '모의 스펙트럼 %s' % kind, 'z_hint': 0.05, 'unit_hint': 'sdss'}, MODE_SPEC)


def cb_sdss_cutout(ra, dec, scale, label):
    img = SDSSFetcher(timeout=20).get_cutout_image(ra, dec, scale=scale, width=512, height=512)
    if img is None:
        st.session_state['sdss_error'] = 'SDSS 사진 불러오기 실패 (네트워크 연결 또는 좌표를 확인하세요)'
        return
    set_demo({'kind': 'image', 'img': img.convert('RGB'), 'name': 'SDSS %s' % label, 'pixel_scale': scale},
             MODE_IMAGE)


def cb_sample(name=None):
    samples = SDSSFetcher().get_sample_galaxies()
    name = name or st.session_state.get('sample_pick') or samples[0]['name']
    s = dict(next(x for x in samples if x['name'] == name))
    st.session_state['R'] = {'mode': 'sample', 'name': s['name'], 'base': s, 'source_sig': 'sample',
                             'time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}


# ═══════════════════════════════════════════════════════════
#                         사이드바
# ═══════════════════════════════════════════════════════════
def sidebar(mode):
    cfg = {}
    with st.sidebar:
        st.markdown('## 🌌 GalaxyEvolution Studio')
        st.caption('Ginga 스타일 뷰어 + 은하 진화 분석')

        # ── 표시 (Ginga) ──────────────────────────────
        with st.expander('🎨 이미지 표시 (Ginga 스타일)', expanded=False):
            st.caption('※ 표시 설정은 보기 전용 — 분석은 항상 **원본 데이터**로 수행됩니다.')
            cfg['cut'] = CUTS[st.selectbox('자동 컷 레벨', list(CUTS))]
            if cfg['cut'] == 'percentile':
                c1, c2 = st.columns(2)
                cfg['p_lo'] = c1.number_input('하한 %', 0.0, 50.0, 0.5, 0.5)
                cfg['p_hi'] = c2.number_input('상한 %', 50.0, 100.0, 99.5, 0.5)
            else:
                cfg['p_lo'], cfg['p_hi'] = 0.5, 99.5
            cfg['stretch'] = STRETCHES[st.selectbox('밝기 분포 (stretch)', list(STRETCHES))]
            cfg['cmap'] = CMAPS[st.selectbox('컬러맵 (흑백/FITS 영상)', list(CMAPS))]
            cfg['force_gray'] = st.checkbox('컬러 사진도 흑백+컬러맵으로 표시', value=False)
            cfg['invert'] = st.checkbox('색 반전 (네거티브)', value=False)
            cfg['brightness'] = st.slider('밝기', 0.2, 3.0, 1.0, 0.05)
            cfg['contrast'] = st.slider('대비', 0.2, 3.0, 1.0, 0.05)

        # ── 그리기 ────────────────────────────────────
        with st.expander('✏️ 영역 그리기 옵션', expanded=False):
            cfg['stroke_width'] = st.slider('선 두께', 1, 8, 2)
            cfg['freedraw_area'] = st.checkbox('올가미(자유곡선)를 닫힌 영역으로 해석', value=True,
                                               help='끄면 그린 선을 따라가는 붓 영역으로 처리')
            cfg['canvas_scale'] = st.slider('캔버스 최대 폭(px)', 400, 1000, CANVAS_MAX_W, 20)

        # ── 분광 설정 ─────────────────────────────────
        if mode == MODE_SPEC:
            with st.expander('🌈 분광 추출 · 파장 교정', expanded=True):
                cfg['disp_axis'] = {'자동 (영역 모양)': 'auto', '가로 (x축)': 'horizontal',
                                    '세로 (y축)': 'vertical'}[st.selectbox('분산 방향', ['자동 (영역 모양)', '가로 (x축)', '세로 (y축)'])]
                cfg['line_width'] = st.slider('직선 ROI 적분 폭 (px)', 1, 60, 10)
                cfg['linearize'] = st.checkbox('8비트 사진 감마(sRGB) 보정', value=True,
                                               help='JPG/PNG 는 밝기가 비선형 인코딩되어 있어 선 세기 비가 왜곡됩니다.')
                cal = st.radio('파장 교정 방식', ['이미지 양 끝 파장 지정', '기준점 (픽셀 ↔ 파장)'])
                cfg['calib_method'] = 'range' if cal.startswith('이미지') else 'points'
                demo = st.session_state.get('demo') or {}
                d_lo, d_hi = demo.get('calib', (4000.0, 7000.0))
                if cfg['calib_method'] == 'range':
                    c1, c2 = st.columns(2)
                    cfg['lam_start'] = c1.number_input('왼쪽/위쪽 끝 (Å)', 1000.0, 30000.0, float(d_lo), 10.0,
                                                       key='lam_start_%s' % demo.get('name', ''))
                    cfg['lam_end'] = c2.number_input('오른쪽/아래쪽 끝 (Å)', 1000.0, 30000.0, float(d_hi), 10.0,
                                                     key='lam_end_%s' % demo.get('name', ''))
                    st.caption('거꾸로 찍힌 사진은 왼쪽 값을 더 크게 입력하세요.')
                else:
                    st.caption('Ginga 뷰어(아래)에서 마우스를 올려 알려진 선의 픽셀 좌표를 읽고 입력하세요.')
                    pts = st.data_editor(pd.DataFrame({'픽셀 좌표': [100.0, 500.0], '파장(Å)': [4861.3, 6562.8]}),
                                         num_rows='dynamic', key='calib_pts', width='stretch')
                    cfg['calib_points'] = [(float(a), float(b)) for a, b in pts.dropna().values.tolist()]
                    with st.popover('📚 기준선 목록'):
                        ref = WavelengthCalibrator().lamp_lines
                        st.dataframe(pd.DataFrame({'선': list(ref), '파장(Å)': list(ref.values())}),
                                     hide_index=True, width='stretch')
            with st.expander('🔬 방출선 분석 설정', expanded=True):
                cfg['auto_z'] = st.checkbox('적색편이 자동 추정', value=True)
                cfg['z'] = st.number_input('적색편이 z (수동/초기값)', 0.0, 3.0, 0.0, 0.001, format='%.4f')
                cfg['z_max'] = st.slider('자동 추정 최대 z', 0.05, 1.0, 0.4, 0.05)
                cfg['smooth'] = st.slider('평활화 창 (1=끔)', 1, 31, 1, 2)
                cfg['snr'] = st.slider('검출 S/N 임계값', 2.0, 10.0, 3.0, 0.5)
                cfg['cont_method'] = {'이동 중앙값 (권장)': 'median', '다항식': 'poly'}[
                    st.selectbox('연속선 모델', ['이동 중앙값 (권장)', '다항식'])]
                cfg['flux_unit'] = st.selectbox('플럭스 단위', list(FLUX_UNITS),
                                                index=int(st.session_state.get('flux_unit_idx', 0)),
                                                help='임의 단위면 비율 기반 양(BPT·금속량·소광)만 계산하고 SFR 은 생략합니다.')

        # ── 보조 물리량 ───────────────────────────────
        with st.expander('🧪 보조 물리량 (선택 입력)', expanded=False):
            st.caption('알고 있는 값을 넣으면 위상공간 매핑·GEI·AI 분류가 정확해집니다.')
            aux = {}
            if st.checkbox('항성질량 log M★ 입력'):
                aux['log_mass'] = st.number_input('log M★ (M☉)', 6.0, 13.0, 10.3, 0.05)
            if st.checkbox('색지수 u−r 입력'):
                aux['color_ur'] = st.number_input('u − r (mag)', -0.5, 4.5, 2.0, 0.05)
            if mode == MODE_IMAGE:
                if st.checkbox('적색편이 z 입력'):
                    aux['z'] = st.number_input('z', 0.0, 3.0, 0.05, 0.001, format='%.4f')
                if st.checkbox('별생성률 log SFR 입력'):
                    aux['log_sfr'] = st.number_input('log SFR (M☉/yr)', -5.0, 4.0, 0.0, 0.05)
                if st.checkbox('금속량 12+log(O/H) 입력'):
                    aux['metallicity'] = st.number_input('12+log(O/H)', 7.0, 9.8, 8.7, 0.01)
                cfg['use_rgb_color'] = st.checkbox('u−r 미입력 시 RGB 색으로 대략 추정', value=True)
                ps_known = st.checkbox('픽셀 스케일(″/px) 알고 있음',
                                       value=bool((st.session_state.get('demo') or {}).get('pixel_scale')))
                cfg['pixel_scale'] = st.number_input('픽셀 스케일 (″/px)', 0.01, 60.0,
                                                     float((st.session_state.get('demo') or {}).get('pixel_scale') or 0.396),
                                                     0.01) if ps_known else None
            cfg['aux'] = aux

        # ── 데모 / 외부 데이터 ────────────────────────
        st.markdown('### 🧪 바로 체험하기')
        c1, c2 = st.columns(2)
        c1.selectbox('모의 은하', ['spiral', 'elliptical', 'merger', 'irregular'], key='demo_gkind',
                     format_func=lambda k: {'spiral': '나선', 'elliptical': '타원',
                                            'merger': '병합', 'irregular': '불규칙'}[k],
                     label_visibility='collapsed')
        c2.button('🌀 모의 은하 사진', width='stretch', on_click=cb_demo_galaxy)
        c1, c2 = st.columns(2)
        c1.selectbox('모의 분광', ['star_forming', 'agn_seyfert', 'elliptical'], key='demo_skind',
                     format_func=lambda k: {'star_forming': '별생성', 'agn_seyfert': 'AGN',
                                            'elliptical': '타원'}[k], label_visibility='collapsed')
        c2.button('🌈 모의 분광 사진', width='stretch', on_click=cb_demo_spec_image)
        st.button('📈 모의 1D 스펙트럼 (z=0.05)', width='stretch', on_click=cb_demo_spec_1d)

        with st.expander('🔭 SDSS 실제 은하 사진 불러오기'):
            st.caption('SDSS SkyServer 이미지 컷아웃 (인터넷 필요)')
            samples = SDSSFetcher().get_sample_galaxies()
            names = ['직접 좌표 입력'] + [s['name'] for s in samples]
            pick = st.selectbox('대상', names)
            if pick == '직접 좌표 입력':
                ra = st.number_input('RA (°)', 0.0, 360.0, 185.4788, 0.0001, format='%.4f')
                dec = st.number_input('Dec (°)', -90.0, 90.0, 4.4737, 0.0001, format='%.4f')
            else:
                s = next(x for x in samples if x['name'] == pick)
                ra, dec = float(s['ra']), float(s['dec'])
                st.caption('RA %.4f°, Dec %.4f°' % (ra, dec))
            scale = st.slider('스케일 (″/px)', 0.1, 3.0, 0.4, 0.05)
            label = pick if pick != '직접 좌표 입력' else '%.3f,%.3f' % (ra, dec)
            st.button('📥 사진 가져오기', width='stretch', on_click=cb_sdss_cutout, args=(ra, dec, scale, label))
            if st.session_state.get('sdss_error'):
                st.error(st.session_state.pop('sdss_error'))

        with st.expander('⭐ SDSS 대표 은하 물리량으로 분석'):
            samples = SDSSFetcher().get_sample_galaxies()
            pick2 = st.selectbox('대표 은하', [s['name'] for s in samples], key='sample_pick')
            st.button('이 은하 분석', width='stretch', on_click=cb_sample)

        if st.session_state.get('demo') is not None:
            st.button('✖ 데모/외부 입력 해제', width='stretch', on_click=set_demo, args=(None,))

        st.markdown('---')
        pred = get_predictor()
        if pred.is_loaded:
            st.caption('🧠 AI 모델: %s (%d 특성)' % ('대체 모델(경량)' if pred.is_fallback else '사전학습 RF 11분류',
                                                 len(pred.trained_features)))
        else:
            st.caption('🧠 AI 모델 없음')
        if not CANVAS_OK:
            st.error('streamlit-drawable-canvas 미설치: pip install streamlit-drawable-canvas')
    cfg.setdefault('aux', {})
    return cfg


# ═══════════════════════════════════════════════════════════
#                      ROI 유틸리티
# ═══════════════════════════════════════════════════════════
def parse_rois(objects, shape, scale, point_radius):
    rois, probes = [], []
    n = 0
    for o in objects or []:
        t = o.get('type')
        if t not in ('rect', 'circle', 'ellipse', 'line', 'path', 'polygon', 'polyline'):
            continue
        kind, g = RegionGeometry.object_to_shape(o, scale)
        if kind is None:
            continue
        if kind == 'circle' and g['rx'] * scale <= point_radius + 0.6 and g['ry'] * scale <= point_radius + 0.6:
            probes.append({'x': g['cx'], 'y': g['cy']})
            continue
        if kind == 'polygon' and len(g['points']) < 2:
            continue
        n += 1
        color = o.get('stroke') if isinstance(o.get('stroke'), str) and o.get('stroke', '').startswith('#') \
            else PALETTE[(n - 1) % len(PALETTE)]
        rois.append({'label': 'ROI-%d' % n, 'color': color, 'kind': kind, 'geom': g, 'obj': o,
                     'desc': describe_roi(kind, g)})
    return rois, probes


def describe_roi(kind, g):
    name = {'rect': '사각형', 'circle': '원/타원', 'line': '직선', 'polygon': '다각형/올가미'}.get(kind, kind)
    if kind == 'circle':
        return '%s (중심 %.0f,%.0f · 반경 %.0f×%.0f px)' % (name, g['cx'], g['cy'], g['rx'], g['ry'])
    if kind == 'line':
        return '%s (%.0f,%.0f → %.0f,%.0f)' % (name, g['x1'], g['y1'], g['x2'], g['y2'])
    pts = np.array(g['points'])
    return '%s (x %.0f–%.0f, y %.0f–%.0f px)' % (name, pts[:, 0].min(), pts[:, 0].max(), pts[:, 1].min(), pts[:, 1].max())


def roi_mask(roi, shape, freedraw_area=True):
    m, _ = RegionGeometry.object_to_mask(roi['obj'], shape, roi['_scale'],
                                         freedraw_as='area' if freedraw_area else 'stroke')
    return m


def roi_outline(roi):
    """Plotly 오버레이용 외곽선 좌표 (원본 픽셀)"""
    k, g = roi['kind'], roi['geom']
    if k == 'circle':
        t = np.linspace(0, 2 * np.pi, 90)
        a = np.radians(g.get('angle', 0))
        x = g['cx'] + g['rx'] * np.cos(t) * np.cos(a) - g['ry'] * np.sin(t) * np.sin(a)
        y = g['cy'] + g['rx'] * np.cos(t) * np.sin(a) + g['ry'] * np.sin(t) * np.cos(a)
        return x, y
    if k == 'line':
        return np.array([g['x1'], g['x2']]), np.array([g['y1'], g['y2']])
    pts = list(g['points'])
    if k == 'rect' or g.get('closed') or k == 'polygon':
        pts = pts + [pts[0]]
    p = np.array(pts)
    return p[:, 0], p[:, 1]


# ═══════════════════════════════════════════════════════════
#                  분광 추출 · 교정 · 분석
# ═══════════════════════════════════════════════════════════
def spectral_gray(raw, linearize=True):
    if raw.dtype == np.uint8 and linearize:
        lin = (raw.astype(float) / 255.0) ** 2.2 * 255.0
        return lin.mean(axis=2) if lin.ndim == 3 else lin
    return raw.mean(axis=2).astype(float) if raw.ndim == 3 else raw.astype(float)


def calibrate_coords(coords, axis, H, W, cfg):
    N = W if axis == 'horizontal' else H
    if cfg.get('calib_method') == 'points':
        pts = [(p, l) for p, l in cfg.get('calib_points', []) if np.isfinite(p) and np.isfinite(l)]
        if len(pts) >= 2 and len(set(p for p, _ in pts)) >= 2:
            p, l = np.array(pts).T
            deg = 1 if len(pts) < 4 else 2
            return np.polyval(np.polyfit(p, l, deg), coords)
    a, b = cfg.get('lam_start', 4000.0), cfg.get('lam_end', 7000.0)
    return a + (np.asarray(coords, float) / max(N - 1, 1)) * (b - a)


def extract_roi_spectrum(gray, roi, cfg):
    H, W = gray.shape
    k, g = roi['kind'], roi['geom']
    pref = cfg.get('disp_axis', 'auto')
    if k == 'line':
        axis = pref if pref != 'auto' else ('horizontal' if abs(g['x2'] - g['x1']) >= abs(g['y2'] - g['y1']) else 'vertical')
        _, f = extractor.extract_from_line(gray, g['x1'], g['y1'], g['x2'], g['y2'], width=cfg.get('line_width', 10))
        if len(f) < 5:
            return None
        coords = np.linspace(g['x1'], g['x2'], len(f)) if axis == 'horizontal' else np.linspace(g['y1'], g['y2'], len(f))
    else:
        mask = roi_mask(roi, gray.shape, cfg.get('freedraw_area', True))
        if mask is None or mask.sum() < 5:
            return None
        ys, xs = np.nonzero(mask)
        bw, bh = np.ptp(xs) + 1, np.ptp(ys) + 1
        axis = pref if pref != 'auto' else ('horizontal' if bw >= bh else 'vertical')
        _, f = extractor.extract_from_mask(gray, mask, axis)
        if len(f) < 5:
            return None
        coords = (xs.min() if axis == 'horizontal' else ys.min()) + np.arange(len(f))
    wave = calibrate_coords(coords, axis, H, W, cfg)
    o = np.argsort(wave)
    return {'wave': wave[o], 'flux': np.asarray(f, float)[o], 'axis': axis, 'coords': coords[o]}


def run_spectrum_fit(wave, flux, cfg, unit_scale):
    notes = []
    wave = np.asarray(wave, float)
    flux = np.asarray(flux, float)
    flux_s = fitter.smooth(flux, cfg.get('smooth', 1)) if cfg.get('smooth', 1) > 1 else flux
    z = float(cfg.get('z', 0.0))
    z_est = None
    if cfg.get('auto_z', True):
        z_est = fitter.estimate_redshift(wave, flux_s, 0.0, cfg.get('z_max', 0.4))
        if z_est:
            z = z_est['z']
        else:
            notes.append('적색편이 자동 추정 실패(일치하는 방출선 패턴 없음) → 입력값 z=%.4f 사용' % z)
    fit = fitter.fit_all_lines(wave, flux_s, z=z, continuum_method=cfg.get('cont_method', 'median'),
                               snr_threshold=cfg.get('snr', 3.0))
    lines = fitter.extract_line_fluxes(fit)
    phys = calc.compute_all(lines, z=z, flux_scale=unit_scale or 1.0)
    if unit_scale is None:
        phys['log_sfr'] = None
        notes.append('플럭스가 임의 단위 → 비율 기반 양(BPT·금속량·소광)만 신뢰 가능, SFR 생략')
    elif z <= 0:
        notes.append('z=0 → 거리를 알 수 없어 SFR 을 계산하지 않았습니다 (z 입력 필요)')
    rest = wave / (1 + z)
    if not (rest.min() < 6563 < rest.max()) and not (rest.min() < 4861 < rest.max()):
        notes.append('정지 파장 범위(%.0f–%.0f Å)에 Hα·Hβ 가 없습니다 → 파장 교정/적색편이 확인' % (rest.min(), rest.max()))
    if not lines:
        notes.append('방출선이 검출되지 않았습니다 (S/N 임계값↓, 평활화↑, 교정 확인).')
    if fit.get('error'):
        notes.append('피팅 오류: %s' % fit['error'])
    if phys.get('metallicity_warning'):
        notes.append(phys['metallicity_warning'])
    fits_ = fit.get('fits') or {}
    base = dict(phys)
    base.update({
        'z': z, 'd4000_n': fit.get('d4000'),
        'h_alpha_eqw': (fits_.get('H_alpha') or {}).get('ew'),
        'oiii_5007_eqw': (fits_.get('OIII_5007') or {}).get('ew'),
    })
    return {'wave': wave, 'flux': flux, 'flux_s': flux_s, 'fit': fit, 'lines': lines, 'base': base,
            'z': z, 'z_est': z_est, 'notes': notes}


# ═══════════════════════════════════════════════════════════
#                 물리량 통합 (보조 입력 반영)
# ═══════════════════════════════════════════════════════════
def finalize_props(base, aux, prefer_aux=False):
    p = {k: v for k, v in (base or {}).items()}
    for k, v in (aux or {}).items():
        if v is None:
            continue
        if prefer_aux or not valid(p.get(k)):
            p[k] = v
    if valid(p.get('log_mass')):
        p['log_stellar_mass'] = p['lgm_tot_p50'] = p['log_mass']
    elif valid(p.get('log_stellar_mass')):
        p['log_mass'] = p['log_stellar_mass']
    if valid(p.get('color_ur')):
        p['color_u_r'] = p['color_ur']
    elif valid(p.get('color_u_r')):
        p['color_ur'] = p['color_u_r']
    if valid(p.get('metallicity')):
        p['metallicity_oh'] = p['oh_p50'] = p['metallicity']
    if valid(p.get('log_sfr')):
        p['sfr_tot_p50'] = p['log_sfr']
    if valid(p.get('log_sfr')) and valid(p.get('log_mass')):
        p['log_ssfr'] = p['log_sfr'] - p['log_mass']
    if all(valid(p.get(k)) for k in ('log_mass', 'log_ssfr', 'metallicity', 'color_ur')):
        gei = calc.calculate_gei(p['log_mass'], p['log_ssfr'], p['metallicity'], p['color_ur'])
        stg = calc.diagnose_evolution_stage(gei)
        p.update({'gei': gei, 'gei_score': gei, 'evolution_stage': stg['stage'],
                  'evolution_stage_en': stg['stage_en'], 'evolution_color': stg['color']})
    else:
        # 필요한 4개 값이 없으면 GEI 를 표시하지 않음 (부분 입력으로 만든 잘못된 값 방지)
        if not valid(p.get('gei')):
            for k in ('gei', 'gei_score', 'evolution_stage'):
                p.pop(k, None)
    return p


# ═══════════════════════════════════════════════════════════
#                         그림 함수
# ═══════════════════════════════════════════════════════════
def dark(fig, h=380, title=None):
    fig.update_layout(template='plotly_dark', height=h, margin=dict(l=10, r=10, t=40 if title else 20, b=10),
                      title=title, legend=dict(orientation='h', y=-0.18))
    return fig


def mpl_colorscale(name, n=16):
    """matplotlib 컬러맵 → Plotly colorscale (Plotly 에 없는 bone/cubehelix 등도 지원)"""
    try:
        cmap = mpl_colormaps[name]
    except Exception:
        cmap = mpl_colormaps['gray']
    return [[i / (n - 1), 'rgb(%d,%d,%d)' % tuple(int(255 * c) for c in cmap(i / (n - 1))[:3])] for i in range(n)]


def fig_pixel_viewer(raw, rois, probes, cfg):
    gray = to_gray(raw)
    H, W = gray.shape
    step = max(1, int(np.ceil(max(H, W) / 700)))
    sub = gray[::step, ::step]
    lo, hi = compute_limits(gray, cfg.get('cut', 'zscale'), cfg.get('p_lo', 0.5), cfg.get('p_hi', 99.5))
    fig = go.Figure(go.Heatmap(
        z=sub, x=np.arange(0, W, step), y=np.arange(0, H, step), zmin=lo, zmax=hi,
        colorscale=mpl_colorscale(cfg.get('cmap', 'gray')),
        hovertemplate='x=%{x}  y=%{y}<br>값=%{z:.4g}<extra></extra>', colorbar=dict(title='값')))
    for r in rois:
        x, y = roi_outline(r)
        fig.add_trace(go.Scatter(x=x, y=y, mode='lines', line=dict(color=r['color'], width=2),
                                 name=r['label'], hoverinfo='name'))
        fig.add_annotation(x=float(np.mean(x)), y=float(np.min(y)), text=r['label'], showarrow=False,
                           font=dict(color=r['color'], size=12), yshift=10)
    if probes:
        fig.add_trace(go.Scatter(x=[p['x'] for p in probes], y=[p['y'] for p in probes], mode='markers',
                                 marker=dict(symbol='x', size=10, color='#fde047'), name='픽셀값'))
    fig.update_yaxes(autorange='reversed', scaleanchor='x', constrain='domain')
    fig.update_xaxes(constrain='domain')
    return dark(fig, 560, '픽셀 뷰어 — 확대(드래그)·마우스 오버로 좌표/값 확인 (원본 데이터)')


def fig_histogram(raw, cfg):
    gray = to_gray(raw)
    v = _sample(gray, 300_000)
    lo, hi = compute_limits(gray, cfg.get('cut', 'zscale'), cfg.get('p_lo', 0.5), cfg.get('p_hi', 99.5))
    fig = go.Figure(go.Histogram(x=v, nbinsx=200, marker_color='#818cf8'))
    fig.add_vline(x=lo, line=dict(color='#22d3ee', dash='dash'), annotation_text='하한')
    fig.add_vline(x=hi, line=dict(color='#f472b6', dash='dash'), annotation_text='상한')
    fig.update_yaxes(type='log', title='픽셀 수')
    fig.update_xaxes(title='픽셀 값')
    return dark(fig, 320, '픽셀 값 분포와 현재 컷 레벨')


def fig_cutout(res, label):
    cut = res['cutout']
    seg = res['segmentation']
    ox, oy = res['crop_offset']
    stt, m = res['stats'], res['metrics']
    step = max(1, int(np.ceil(max(cut.shape) / 420)))
    sd = stt.get('background_std') or 1.0
    z = np.arcsinh(np.clip(cut, 0, None) / (3 * sd))[::step, ::step]
    xs = ox + np.arange(0, cut.shape[1], step)
    ys = oy + np.arange(0, cut.shape[0], step)
    fig = go.Figure(go.Heatmap(z=z, x=xs, y=ys, colorscale='Inferno', showscale=False,
                               hovertemplate='x=%{x} y=%{y}<br>asinh 밝기=%{z:.2f}<extra></extra>'))
    fig.add_trace(go.Contour(z=seg[::step, ::step].astype(float), x=xs, y=ys, showscale=False,
                             contours=dict(start=0.5, end=0.5, size=1, coloring='none'),
                             line=dict(color='#22d3ee', width=1.5), name='분할 영역', hoverinfo='skip'))
    cx, cy = stt['centroid_x'], stt['centroid_y']
    for key, name, col in (('R50_px', 'R50', '#a3e635'), ('R90_px', 'R90', '#facc15'), ('R_petro_px', 'R_Petro', '#f472b6')):
        R = m.get(key)
        if R:
            fig.add_shape(type='circle', x0=cx - R, x1=cx + R, y0=cy - R, y1=cy + R,
                          line=dict(color=col, dash='dot', width=1.5))
            fig.add_annotation(x=cx + R * 0.707, y=cy - R * 0.707, text=name, showarrow=False,
                               font=dict(color=col, size=11))
    if res.get('nuclei'):
        fig.add_trace(go.Scatter(x=[n[0] for n in res['nuclei']], y=[n[1] for n in res['nuclei']], mode='markers',
                                 marker=dict(symbol='x', size=9, color='#38bdf8'), name='밝은 핵/덩어리'))
    fig.add_trace(go.Scatter(x=[cx], y=[cy], mode='markers', marker=dict(symbol='cross', size=12, color='white'),
                             name='광도 중심'))
    fig.update_yaxes(autorange='reversed', scaleanchor='x', constrain='domain')
    return dark(fig, 430, '%s 형태 지도 (청록=분할영역, 점선=R50/R90/Petrosian)' % label)


def fig_profile(res):
    pr = res['profile']
    r, I = np.asarray(pr['r']), np.asarray(pr['I'])
    ok = I > 0
    fig = go.Figure(go.Scatter(x=r[ok], y=I[ok], mode='markers+lines', name='관측 프로파일',
                               marker=dict(color='#60a5fa', size=5)))
    s = res.get('sersic')
    if s:
        fig.add_trace(go.Scatter(x=s['model_r'], y=s['model_I'], mode='lines', name='Sérsic n=%.2f' % s['n'],
                                 line=dict(color='#f472b6', dash='dash')))
    m = res['metrics']
    for key, name, col in (('R50_px', 'R50', '#a3e635'), ('R90_px', 'R90', '#facc15'), ('R_petro_px', 'Rp', '#f472b6')):
        if m.get(key):
            fig.add_vline(x=m[key], line=dict(color=col, dash='dot'), annotation_text=name)
    fig.update_yaxes(type='log', title='평균 밝기 (배경 제거)')
    fig.update_xaxes(title='중심 거리 (px)')
    return dark(fig, 430, '반경 밝기 프로파일')


def fig_gini_m20(entries, sel_label):
    x = np.linspace(-3.0, 0.0, 50)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=-0.14 * x + 0.33, mode='lines', line=dict(color='#f87171', dash='dash'),
                             name='병합 경계 (Lotz+08)'))
    xe = np.linspace(-3.0, -1.68, 30)
    fig.add_trace(go.Scatter(x=xe, y=0.14 * xe + 0.80, mode='lines', line=dict(color='#fbbf24', dash='dot'),
                             name='E/S0/Sa | Sb–Irr'))
    for e in entries:
        m = e['res'].get('metrics', {})
        if m.get('gini') is None or m.get('m20') is None:
            continue
        big = e['label'] == sel_label
        fig.add_trace(go.Scatter(x=[m['m20']], y=[m['gini']], mode='markers+text', text=[e['label']],
                                 textposition='top center', name=e['label'],
                                 marker=dict(size=16 if big else 11, color=e['color'], symbol='star' if big else 'circle',
                                             line=dict(color='white', width=1))))
    fig.add_annotation(x=-0.6, y=0.68, text='병합', showarrow=False, font=dict(color='#f87171'))
    fig.add_annotation(x=-2.5, y=0.62, text='조기형', showarrow=False, font=dict(color='#fbbf24'))
    fig.add_annotation(x=-2.4, y=0.40, text='만기형', showarrow=False, font=dict(color='#60a5fa'))
    fig.update_xaxes(title='M20', range=[0.0, -3.0])
    fig.update_yaxes(title='Gini', range=[0.3, 0.8])
    return dark(fig, 400, 'Gini–M20 형태 진단도')


def fig_ca(entries, sel_label):
    fig = go.Figure()
    fig.add_shape(type='rect', x0=0.0, x1=0.35, y0=3.5, y1=5.5, fillcolor='rgba(239,68,68,0.10)', line_width=0)
    fig.add_shape(type='rect', x0=0.0, x1=0.35, y0=2.0, y1=3.5, fillcolor='rgba(59,130,246,0.10)', line_width=0)
    fig.add_shape(type='rect', x0=0.35, x1=1.5, y0=1.0, y1=5.5, fillcolor='rgba(244,63,94,0.10)', line_width=0)
    fig.add_annotation(x=0.1, y=5.2, text='타원 (높은 C, 낮은 A)', showarrow=False, font=dict(color='#fca5a5'))
    fig.add_annotation(x=0.12, y=2.3, text='원반·나선', showarrow=False, font=dict(color='#93c5fd'))
    fig.add_annotation(x=0.9, y=5.2, text='병합·불규칙 (A > 0.35)', showarrow=False, font=dict(color='#fda4af'))
    for e in entries:
        m = e['res'].get('metrics', {})
        if m.get('C_cas') is None or m.get('asymmetry') is None:
            continue
        big = e['label'] == sel_label
        fig.add_trace(go.Scatter(x=[m['asymmetry']], y=[m['C_cas']], mode='markers+text', text=[e['label']],
                                 textposition='top center', name=e['label'],
                                 marker=dict(size=16 if big else 11, color=e['color'], symbol='star' if big else 'circle',
                                             line=dict(color='white', width=1))))
    fig.update_xaxes(title='비대칭도 A', range=[0, 1.5])
    fig.update_yaxes(title='집중도 C = 5 log(R80/R20)', range=[1.0, 5.5])
    return dark(fig, 400, 'CAS 진단도 (Conselice 2003)')


def fig_spectrum(entry, title='스펙트럼'):
    w, f, fs = entry['wave'], entry['flux'], entry['flux_s']
    fit, z = entry['fit'], entry['z']
    fig = go.Figure()
    if entry.get('smoothed', False) or not np.allclose(f, fs):
        fig.add_trace(go.Scatter(x=w, y=f, mode='lines', name='원본', line=dict(color='#475569', width=1)))
    fig.add_trace(go.Scatter(x=w, y=fs, mode='lines', name='플럭스', line=dict(color='#60a5fa', width=1.4)))
    cont = fit.get('continuum')
    if cont is not None and len(cont) == len(w):
        fig.add_trace(go.Scatter(x=w, y=cont, mode='lines', name='연속선', line=dict(color='#f59e0b', dash='dash')))
        model = np.array(cont, dtype=float).copy()
        for n, i in (fit.get('fits') or {}).items():
            c_obs = i['center'] * (1 + z)
            s_obs = i['sigma'] * (1 + z)
            model += i['amplitude'] * np.exp(-(w - c_obs) ** 2 / (2 * s_obs ** 2))
        if fit.get('fits'):
            fig.add_trace(go.Scatter(x=w, y=model, mode='lines', name='가우시안 모델',
                                     line=dict(color='#f472b6', width=1.6)))
    ymax = float(np.nanmax(fs)) if len(fs) else 1.0
    detected = set((fit.get('fits') or {}).keys())
    for n, (lam, lab) in LINE_LIST.items():
        lo = lam * (1 + z)
        if w.min() <= lo <= w.max():
            hit = n in detected
            fig.add_vline(x=lo, line=dict(color='#22c55e' if hit else '#334155', width=1, dash='solid' if hit else 'dot'))
            if hit:
                fig.add_annotation(x=lo, y=ymax, text=lab, showarrow=False, textangle=-90, yshift=10,
                                   font=dict(color='#86efac', size=10))
    for n, (lam, lab) in ABSORPTION_LIST.items():
        lo = lam * (1 + z)
        if w.min() <= lo <= w.max():
            fig.add_vline(x=lo, line=dict(color='#7c3aed', width=1, dash='dot'))
    fig.update_xaxes(title='관측 파장 (Å)')
    fig.update_yaxes(title='플럭스')
    return dark(fig, 430, '%s  (z = %.4f · 초록=검출된 방출선, 보라=흡수선 위치)' % (title, z))


# ═══════════════════════════════════════════════════════════
#                      공통 결과 패널
# ═══════════════════════════════════════════════════════════
def render_phase_space(p, key):
    mapper = get_mapper()
    if mapper.df.empty:
        st.warning('SDSS 마스터 데이터(galaxy_master_complete_all.csv)를 찾지 못했습니다.')
        return
    g = lambda k: p.get(k) if valid(p.get(k)) else None
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(mapper.plot_bpt(g('log_nii_ha'), g('log_oiii_hb')), width='stretch', key=key + 'bpt')
        st.plotly_chart(mapper.plot_mzr(g('log_mass'), g('metallicity')), width='stretch', key=key + 'mzr')
    with c2:
        st.plotly_chart(mapper.plot_sfms(g('log_mass'), g('log_sfr')), width='stretch', key=key + 'sfms')
        st.plotly_chart(mapper.plot_color_mass(g('log_mass'), g('color_ur')), width='stretch', key=key + 'cm')
    missing = [n for n, k in (('항성질량', 'log_mass'), ('SFR', 'log_sfr'), ('금속량', 'metallicity'),
                              ('u−r', 'color_ur'), ('BPT 비', 'log_nii_ha')) if g(k) is None]
    if missing:
        st.caption('★ 표시가 없는 도표: %s 값이 없음 → 사이드바 「보조 물리량」에서 입력 가능' % ', '.join(missing))
    if all(g(k) is not None for k in ('log_mass', 'log_sfr', 'metallicity')):
        with st.expander('🧊 3D 기본 금속량 관계 (FMR)'):
            st.plotly_chart(mapper.plot_3d_fmr(g('log_mass'), g('log_sfr'), g('metallicity')), width='stretch',
                            key=key + 'fmr')

    st.markdown('#### 📐 SDSS 은하 10만 개 중 대상의 위치')
    pr = mapper.percentile_ranks(p)
    cA, cB = st.columns([3, 2])
    with cA:
        if not pr.empty:
            fig = go.Figure(go.Bar(x=pr['백분위(%)'], y=pr['물리량'], orientation='h',
                                   marker=dict(color=pr['백분위(%)'], colorscale='Turbo', cmin=0, cmax=100),
                                   text=['%.0f%%' % v for v in pr['백분위(%)']], textposition='outside'))
            fig.add_vline(x=50, line=dict(color='#94a3b8', dash='dot'))
            fig.update_xaxes(range=[0, 108], title='백분위 (%) — 50=중앙값')
            st.plotly_chart(dark(fig, 60 + 34 * len(pr)), width='stretch', key=key + 'pct')
        else:
            st.info('비교할 물리량이 없습니다.')
    with cB:
        if not pr.empty:
            st.dataframe(pr, hide_index=True, width='stretch')
        ms = mapper.sfms_offset(g('log_mass'), g('log_sfr'))
        if ms:
            st.metric('별생성 주계열 대비 ΔMS', '%+.2f dex' % ms['delta_ms'], ms['state'], delta_color='off')

    sim = mapper.find_similar(p, k=10)
    if sim:
        st.markdown('#### 🧬 물리량이 가장 비슷한 SDSS 은하 10개')
        c1, c2 = st.columns([3, 2])
        with c1:
            st.dataframe(sim['neighbors'], hide_index=True, width='stretch', height=300)
        with c2:
            if sim['vote'] is not None and len(sim['vote']):
                v = sim['vote']
                fig = go.Figure(go.Pie(labels=list(v.index), values=list(v.values), hole=0.45))
                st.plotly_chart(dark(fig, 300, '유사 은하 유형 투표 (kNN)'), width='stretch', key=key + 'vote')
            st.caption('사용 특성: ' + ', '.join(sim['features_used']))


def render_ai(p, key):
    pred = get_predictor()
    if not pred.is_loaded:
        st.warning('AI 모델을 불러오지 못했습니다: %s' % (pred.load_error or ''))
        return None
    tp = pred.predict_galaxy_type(p)
    cl = pred.predict_evolution_cluster(p)
    cov = tp.get('coverage', {})
    c1, c2, c3, c4 = st.columns(4)
    c1.metric('예측 은하 유형', tp['predicted_class'].split(' (')[0])
    c2.metric('신뢰도', '%.1f%%' % (tp['confidence'] * 100))
    c3.metric('입력 특성 커버리지', '%.0f%%' % (cov.get('weighted', 0) * 100),
              '%d / %d 특성' % (cov.get('n_provided', 0), cov.get('n_total', 0)), delta_color='off')
    c4.metric('진화 군집', cl['cluster_name'].split(' (')[0])
    if cov.get('weighted', 0) < 0.3:
        st.warning('⚠️ 모델이 중요하게 쓰는 특성이 대부분 비어 있어(평균값 대체) 예측이 불확실합니다. '
                   '사이드바 「보조 물리량」을 입력하면 정확도가 올라갑니다.')
    if pred.is_fallback:
        st.info('사전학습 모델 파일이 없어 SDSS 마스터 데이터로 학습한 경량 대체 모델을 사용 중입니다.')
    cA, cB = st.columns(2)
    with cA:
        st.plotly_chart(pred.create_probability_chart(tp['probabilities']), width='stretch', key=key + 'prob')
    with cB:
        ex = pred.explain_local(p)
        st.plotly_chart(pred.create_local_explanation_chart(ex, tp['predicted_class']), width='stretch',
                        key=key + 'xai')
    cA, cB = st.columns(2)
    with cA:
        if valid(p.get('gei')):
            st.plotly_chart(pred.create_evolution_gauge(float(p['gei'])), width='stretch', key=key + 'gei')
            st.caption('진화 단계: **%s** — 질량·sSFR·금속량·색의 가중 합 (0=젊음, 100=진화 완료)' % p.get('evolution_stage', '-'))
        else:
            st.info('GEI 계산에는 log M★, log SFR, 금속량, u−r 이 모두 필요합니다.')
        if cl.get('membership'):
            mem = cl['membership']
            fig = go.Figure(go.Bar(x=[pred.CLUSTER_NAMES.get(i, str(i)).split(' (')[0] for i in range(len(mem))],
                                   y=[m * 100 for m in mem],
                                   marker_color=[pred.CLUSTER_COLORS.get(i, '#64748b') for i in range(len(mem))]))
            fig.update_yaxes(title='소속도 (%)')
            st.plotly_chart(dark(fig, 280, '진화 군집 소속도'), width='stretch', key=key + 'mem')
    with cB:
        st.plotly_chart(pred.create_feature_importance_chart(pred.get_feature_importance(p)), width='stretch',
                        key=key + 'imp')
    return {'type': tp, 'cluster': cl}


def render_report(R, p, ai, extra, key):
    mapper = get_mapper()
    pr = mapper.percentile_ranks(p) if not mapper.df.empty else pd.DataFrame()
    sim = mapper.find_similar(p, k=10) if not mapper.df.empty else None
    ms = mapper.sfms_offset(p.get('log_mass') if valid(p.get('log_mass')) else None,
                            p.get('log_sfr') if valid(p.get('log_sfr')) else None) if not mapper.df.empty else None
    a = {
        'target_name': R.get('name', '대상'), 'analysis_datetime': R.get('time'),
        'input_mode': {'image': '이미지 영역 분석', 'spectrum': '분광 분석', 'sample': 'SDSS 대표 은하'}[R['mode']],
        'ebv': p.get('ebv'), 'log_sfr': p.get('log_sfr'), 'metallicity': p.get('metallicity'),
        'metallicity_method': p.get('metallicity_method', 'N/A'), 'bpt_class': p.get('bpt_class', '미상'),
        'bpt_class_en': p.get('bpt_class_en'), 'sii_bpt_class': p.get('sii_bpt_class'),
        'electron_density': p.get('electron_density'), 'log_nii_ha': p.get('log_nii_ha'),
        'log_oiii_hb': p.get('log_oiii_hb'), 'd4000': p.get('d4000_n'),
        'log_mass': p.get('log_mass'), 'color_ur': p.get('color_ur'), 'z': p.get('z'),
        'gei_score': p.get('gei'), 'evolution_stage': p.get('evolution_stage', '미상'),
        'percentiles': pr.to_dict('records') if not pr.empty else None, 'sfms': ms,
        'similar_vote': sim['vote'].to_dict() if sim and sim['vote'] is not None else None,
    }
    if ai:
        a.update({'predicted_type': ai['type']['predicted_class'], 'confidence': ai['type']['confidence'],
                  'top_3_types': ai['type']['top_3'], 'evolution_cluster': ai['cluster']['cluster_name'],
                  'feature_coverage': ai['type'].get('coverage', {}).get('weighted')})
    a.update(extra or {})
    md = reporter.generate_markdown(a)
    html = reporter.generate_html(md)
    card = reporter.generate_summary_card(a)
    cols = st.columns(len(card['metrics']))
    for c, m in zip(cols, card['metrics']):
        c.metric(m['label'], m['value'], m.get('delta'), delta_color='off')
    fname = 'galaxy_report_%s' % datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    c1, c2, c3 = st.columns(3)
    c1.download_button('📄 Markdown 보고서', md.encode('utf-8'), fname + '.md', 'text/markdown', width='stretch',
                       key=key + 'dmd')
    c2.download_button('🌐 HTML 보고서', html.encode('utf-8'), fname + '.html', 'text/html', width='stretch',
                       key=key + 'dhtml')
    clean = {k: (float(v) if isinstance(v, (np.floating, np.integer)) else v) for k, v in p.items()
             if isinstance(v, (int, float, str, bool, np.floating, np.integer)) or v is None}
    c3.download_button('🧾 물리량 JSON', json.dumps(clean, ensure_ascii=False, indent=2, default=str).encode('utf-8'),
                       fname + '.json', 'application/json', width='stretch', key=key + 'djson')
    with st.expander('보고서 미리보기', expanded=True):
        st.markdown(md)


# ═══════════════════════════════════════════════════════════
#                  이미지 모드 결과
# ═══════════════════════════════════════════════════════════
def image_base_props(e, cfg):
    res = e['res']
    base = dict(res.get('ml_features', {}))
    ps = cfg.get('pixel_scale')
    m = res.get('metrics', {})
    if ps:
        if m.get('R50_px'):
            base['petroR50_r'] = m['R50_px'] * ps
        if m.get('R90_px'):
            base['petroR90_r'] = m['R90_px'] * ps
    else:
        base.pop('petroR50_r', None)
        base.pop('petroR90_r', None)
    notes = []
    aux = cfg.get('aux', {})
    if 'color_ur' not in aux and cfg.get('use_rgb_color', True) and res['stats'].get('color_GR') is not None:
        base['color_ur'] = GalaxyImageAnalyzer.estimate_ur_from_rgb(res['stats']['color_GR'])
        notes.append('u−r 은 RGB 사진 색(G−R)에서 추정한 근사값입니다 (교정되지 않은 필터).')
    return base, notes


def render_image_results(R, cfg):
    entries = [e for e in R['rois'] if not e['res'].get('error')]
    bad = [e for e in R['rois'] if e['res'].get('error')]
    for e in bad:
        st.warning('%s: %s' % (e['label'], e['res']['error']))
    if not entries:
        return
    labels = [e['label'] for e in entries]
    sel = st.selectbox('상세히 볼 영역', labels, key='sel_img_roi',
                       format_func=lambda l: '%s — %s' % (l, next(x['desc'] for x in entries if x['label'] == l)))
    e = next(x for x in entries if x['label'] == sel)
    res = e['res']
    stt, m, morph = res['stats'], res['metrics'], res['morphology']
    base, notes = image_base_props(e, cfg)
    p = finalize_props(base, cfg.get('aux', {}), prefer_aux=True)

    c = st.columns(7)
    c[0].metric('형태 판정', morph['class'].split(' (')[0])
    c[1].metric('집중도 C=R90/R50', fnum(m.get('C_sdss')))
    c[2].metric('비대칭도 A', fnum(m.get('asymmetry')))
    c[3].metric('Gini', fnum(m.get('gini')))
    c[4].metric('M20', fnum(m.get('m20')))
    c[5].metric('Sérsic n', fnum(m.get('sersic_n')))
    c[6].metric('S/N', fnum(stt.get('snr'), '%.0f'))

    tabs = st.tabs(['🌀 형태 · 측광', '📊 영역 비교', '📈 위상공간', '🧠 AI 분류', '📑 보고서'])
    with tabs[0]:
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(fig_cutout(res, e['label']), width='stretch', key='cut_' + sel)
        with c2:
            st.plotly_chart(fig_profile(res), width='stretch', key='prof_' + sel)
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(fig_gini_m20(entries, sel), width='stretch', key='gm_' + sel)
        with c2:
            st.plotly_chart(fig_ca(entries, sel), width='stretch', key='ca_' + sel)
        c1, c2 = st.columns([2, 3])
        with c1:
            sc = morph.get('scores', {})
            if sc:
                fig = go.Figure(go.Bar(x=[v * 100 for v in sc.values()], y=list(sc.keys()), orientation='h',
                                       marker_color=['#ef4444', '#3b82f6', '#22c55e', '#f43f5e'],
                                       text=['%.0f%%' % (v * 100) for v in sc.values()], textposition='outside'))
                fig.update_xaxes(range=[0, 110])
                st.plotly_chart(dark(fig, 260, '형태 점수'), width='stretch', key='ms_' + sel)
            st.markdown('**판정 근거**')
            for r in morph.get('reasons', []):
                st.markdown('- ' + r)
        with c2:
            ps = cfg.get('pixel_scale')
            rows = [
                ('픽셀 수 / 분할영역 픽셀', '%d / %d' % (stt['n_pix'], m.get('seg_pixels', 0))),
                ('배경 (중앙값 ± σ)', '%s ± %s' % (fnum(stt['background'], '%.3g'), fnum(stt['background_std'], '%.3g'))),
                ('순 플럭스 (배경 제거)', fnum(stt['net_flux'], '%.4g')),
                ('기기 등급 −2.5 log F', fnum(stt.get('inst_mag'), '%.3f')),
                ('광도 중심 (x, y)', '%.1f, %.1f' % (stt['centroid_x'], stt['centroid_y'])),
                ('최대 밝기 위치', '%d, %d' % (stt['peak_x'], stt['peak_y'])),
                ('타원율 e / 축비 b/a', '%.3f / %.3f' % (stt['ellipticity'], stt['axis_ratio'])),
                ('방위각 PA', '%.1f°' % stt['position_angle']),
                ('R50 / R90', '%s / %s px' % (fnum(m.get('R50_px'), '%.1f'), fnum(m.get('R90_px'), '%.1f'))
                 + ((' (%.2f″ / %.2f″)' % (m['R50_px'] * ps, m['R90_px'] * ps)) if ps and m.get('R50_px') and m.get('R90_px') else '')),
                ('Petrosian 반경', fnum(m.get('R_petro_px'), '%.1f px')),
                ('CAS 집중도 C', fnum(m.get('C_cas'))),
                ('매끄러움 S', fnum(m.get('smoothness'), '%.3f')),
                ('밝은 핵/덩어리 수', str(m.get('n_nuclei', '-'))),
            ]
            if stt.get('color_BR') is not None:
                rows.append(('RGB 색 프록시 B−R / G−R', '%.3f / %.3f' % (stt['color_BR'], stt['color_GR'])))
            st.dataframe(pd.DataFrame(rows, columns=['항목', '값']), hide_index=True, width='stretch', height=500)
        st.caption('JPG/PNG 는 sRGB 감마를 해제해 근사 선형 광량으로 계산합니다. 정량 분석에는 FITS 를 권장합니다. '
                   '포화(saturation)된 별/핵이 있으면 집중도와 Gini 가 과소평가될 수 있습니다.')

    with tabs[1]:
        rows = []
        for x in entries:
            s, mm = x['res']['stats'], x['res']['metrics']
            rows.append({'영역': x['label'], '종류': x['desc'].split(' (')[0], '픽셀 수': s['n_pix'],
                         '순 플럭스': s['net_flux'], '기기등급': s.get('inst_mag'), 'S/N': s.get('snr'),
                         'C': mm.get('C_sdss'), 'A': mm.get('asymmetry'), 'Gini': mm.get('gini'), 'M20': mm.get('m20'),
                         'Sérsic n': mm.get('sersic_n'), 'G−R': s.get('color_GR'),
                         '형태': x['res']['morphology']['class'].split(' (')[0]})
        df = pd.DataFrame(rows)
        st.dataframe(df.style.format(precision=3), hide_index=True, width='stretch')
        num_cols = [c for c in ['순 플럭스', '기기등급', 'S/N', 'C', 'A', 'Gini', 'M20', 'Sérsic n', 'G−R'] if df[c].notna().any()]
        if num_cols:
            metric = st.selectbox('비교할 지표', num_cols, key='cmp_metric')
            fig = go.Figure(go.Bar(x=df['영역'], y=df[metric], marker_color=[x['color'] for x in entries],
                                   text=[fnum(v, '%.3g') for v in df[metric]], textposition='outside'))
            st.plotly_chart(dark(fig, 330, '영역별 %s' % metric), width='stretch', key='cmpbar')
        if len(entries) >= 2 and all(x['res']['stats'].get('inst_mag') is not None for x in entries[:2]):
            d = entries[1]['res']['stats']['inst_mag'] - entries[0]['res']['stats']['inst_mag']
            st.caption('%s 대비 %s 밝기 차: Δm = %+.3f 등급 (플럭스비 %.3f)' % (entries[0]['label'], entries[1]['label'],
                                                                     d, 10 ** (-0.4 * d)))
        st.download_button('⬇️ 영역 비교표 CSV', df.to_csv(index=False).encode('utf-8-sig'), 'roi_comparison.csv',
                           'text/csv', key='dl_cmp')

    with tabs[2]:
        render_phase_space(p, 'img_' + sel)
    with tabs[3]:
        st.caption('이미지에서 추정한 형태 특성(집중도, deV 비율, 타원/나선/병합 점수 등)을 학습 특성에 대응시켜 예측합니다.')
        ai = render_ai(p, 'img_' + sel)
    with tabs[4]:
        phot = {'영역': e['desc'], '순 플럭스': fnum(stt['net_flux'], '%.4g'), 'S/N': fnum(stt.get('snr'), '%.1f'),
                '집중도 C': fnum(m.get('C_sdss')), '비대칭도 A': fnum(m.get('asymmetry')),
                'Gini / M20': '%s / %s' % (fnum(m.get('gini')), fnum(m.get('m20'))),
                'Sérsic n': fnum(m.get('sersic_n')), '타원율': fnum(stt['ellipticity'], '%.3f')}
        render_report(R, p, ai, {'morphology': morph, 'photometry': phot, 'roi_description': e['desc'],
                                 'notes': notes + R.get('notes', [])}, 'img_rep_' + sel)


# ═══════════════════════════════════════════════════════════
#                  분광 모드 결과
# ═══════════════════════════════════════════════════════════
def render_spectrum_results(R, cfg):
    entries = R['rois']
    labels = [e['label'] for e in entries]
    sel = st.selectbox('상세히 볼 스펙트럼', labels, key='sel_spec_roi',
                       format_func=lambda l: '%s — %s' % (l, next(x['desc'] for x in entries if x['label'] == l))) \
        if len(entries) > 1 else labels[0]
    e = next(x for x in entries if x['label'] == sel)
    fitd = e['fit']
    p = finalize_props(e['base'], cfg.get('aux', {}), prefer_aux=False)
    nfit = len(fitd.get('fits') or {})

    c = st.columns(7)
    c[0].metric('적색편이 z', fnum(e['z'], '%.4f'), '자동 추정' if e.get('z_est') else '입력값', delta_color='off')
    c[1].metric('검출 방출선', '%d 개' % nfit)
    c[2].metric('E(B−V)', fnum(p.get('ebv'), '%.3f'))
    c[3].metric('log SFR', fnum(p.get('log_sfr')))
    c[4].metric('12+log(O/H)', fnum(p.get('metallicity'), '%.3f'))
    c[5].metric('BPT 분류', p.get('bpt_class', '—'))
    c[6].metric('D4000', fnum(p.get('d4000_n')))
    for n in e['notes']:
        st.info(n)

    tab_names = ['🌈 스펙트럼 · 방출선', '📈 위상공간', '🧠 AI 분류', '📑 보고서']
    if len(entries) > 1:
        tab_names.insert(1, '🗺️ 영역별 비교 (공간 분해 BPT)')
    tabs = st.tabs(tab_names)
    ti = 0
    with tabs[ti]:
        st.plotly_chart(fig_spectrum(e, '%s 스펙트럼' % e['label']), width='stretch', key='spec_' + sel)
        lt = fitd.get('line_table')
        c1, c2 = st.columns([3, 2])
        with c1:
            if lt is not None and not lt.empty:
                st.dataframe(lt.drop(columns=['key']).style.format({'적분플럭스': '{:.4g}', '오차': '{:.2g}'}, precision=2),
                             hide_index=True, width='stretch')
            else:
                st.info('검출된 방출선이 없습니다.')
        with c2:
            rows = [
                ('Balmer 감소율 Hα/Hβ', fnum(p.get('balmer_decrement'), '%.2f') + ' (이론 2.86)'),
                ('E(B−V) 성간 소광', fnum(p.get('ebv'), '%.3f mag')),
                ('log([NII]/Hα)', fnum(p.get('log_nii_ha'), '%.3f')),
                ('log([OIII]/Hβ)', fnum(p.get('log_oiii_hb'), '%.3f')),
                ('log([SII]/Hα)', fnum(p.get('log_sii_ha'), '%.3f')),
                ('[NII]-BPT', p.get('bpt_class', '—')),
                ('[SII]-BPT (Kewley 06)', p.get('sii_bpt_class', '—')),
                ('금속량 N2 / O3N2', '%s / %s' % (fnum(p.get('metallicity_n2'), '%.3f'), fnum(p.get('metallicity_o3n2'), '%.3f'))),
                ('전자밀도 n_e [SII]', fnum(p.get('electron_density'), '%.0f cm⁻³')),
                ('Hα 등가폭', fnum(p.get('h_alpha_eqw'), '%.1f Å')),
                ('D4000_n', fnum(p.get('d4000_n'), '%.3f')),
            ]
            st.dataframe(pd.DataFrame(rows, columns=['물리량', '값']), hide_index=True, width='stretch', height=420)
        spec_df = pd.DataFrame({'wavelength_A': e['wave'], 'flux': e['flux'], 'flux_smoothed': e['flux_s']})
        c1, c2 = st.columns(2)
        c1.download_button('⬇️ 스펙트럼 CSV', spec_df.to_csv(index=False).encode('utf-8'), '%s_spectrum.csv' % sel,
                           'text/csv', width='stretch', key='dl_spec_' + sel)
        if lt is not None and not lt.empty:
            c2.download_button('⬇️ 방출선 표 CSV', lt.to_csv(index=False).encode('utf-8-sig'), '%s_lines.csv' % sel,
                               'text/csv', width='stretch', key='dl_lines_' + sel)
        st.caption('스마트폰/카메라 분광 사진은 센서의 파장별 감도가 달라 Hα/Hβ 비(소광)가 왜곡될 수 있습니다. '
                   '근접 선([NII]-Hα-[NII], [SII] 쌍)은 공통 폭·속도 다중 가우시안으로 동시 분리합니다.')
    if len(entries) > 1:
        ti += 1
        with tabs[ti]:
            rows = []
            mapper = get_mapper()
            fig = mapper.plot_bpt(None, None)
            for x in entries:
                b = x['base']
                rows.append({'영역': x['label'], '검출 선': len(x['fit'].get('fits') or {}), 'z': x['z'],
                             'log[NII]/Hα': b.get('log_nii_ha'), 'log[OIII]/Hβ': b.get('log_oiii_hb'),
                             'E(B−V)': b.get('ebv'), '12+log(O/H)': b.get('metallicity'), 'BPT': b.get('bpt_class')})
                if valid(b.get('log_nii_ha')) and valid(b.get('log_oiii_hb')):
                    fig.add_trace(go.Scatter(x=[b['log_nii_ha']], y=[b['log_oiii_hb']], mode='markers+text',
                                             text=[x['label']], textposition='top center', name=x['label'],
                                             marker=dict(size=15, symbol='star', color=x['color'],
                                                         line=dict(color='white', width=1))))
            st.dataframe(pd.DataFrame(rows).style.format(precision=3), hide_index=True, width='stretch')
            st.plotly_chart(fig, width='stretch', key='bpt_multi')
            ov = go.Figure()
            for x in entries:
                f = x['flux_s']
                norm = np.nanmedian(np.abs(f)) or 1.0
                ov.add_trace(go.Scatter(x=x['wave'], y=f / norm, mode='lines', name=x['label'],
                                        line=dict(color=x['color'], width=1.3)))
            ov.update_xaxes(title='관측 파장 (Å)')
            ov.update_yaxes(title='정규화 플럭스')
            st.plotly_chart(dark(ov, 360, '영역별 스펙트럼 겹쳐보기'), width='stretch', key='ov_multi')
            st.caption('긴 슬릿 분광 사진에서 은하 중심핵과 원반을 각각 선택하면 영역별 전리 상태(AGN vs 별생성)를 비교할 수 있습니다.')
    ti += 1
    with tabs[ti]:
        render_phase_space(p, 'spec_' + sel)
    ti += 1
    with tabs[ti]:
        ai = render_ai(p, 'spec_' + sel)
    ti += 1
    with tabs[ti]:
        lt = fitd.get('line_table')
        render_report(R, p, ai, {'line_table': lt.to_dict('records') if lt is not None and not lt.empty else None,
                                 'emission_lines': e['lines'], 'roi_description': e['desc'],
                                 'notes': e['notes']}, 'spec_rep_' + sel)


def render_sample_results(R, cfg):
    s = R['base']
    base = dict(s)
    calc_bpt = calc.classify_bpt(s.get('log_nii_ha'), s.get('log_oiii_hb'))
    base.update({'bpt_class': calc_bpt['class'], 'bpt_class_en': calc_bpt['class_en']})
    p = finalize_props(base, cfg.get('aux', {}), prefer_aux=True)
    c = st.columns(6)
    c[0].metric('대상', s['name'].split(' (')[0])
    c[1].metric('log M★', fnum(p.get('log_mass')))
    c[2].metric('log SFR', fnum(p.get('log_sfr')))
    c[3].metric('12+log(O/H)', fnum(p.get('metallicity'), '%.2f'))
    c[4].metric('u−r', fnum(p.get('color_ur')))
    c[5].metric('BPT', p.get('bpt_class', '—'))
    if s.get('description'):
        st.caption(s['description'])
    tabs = st.tabs(['📈 위상공간', '🧠 AI 분류', '📑 보고서'])
    with tabs[0]:
        render_phase_space(p, 'smp_')
    with tabs[1]:
        ai = render_ai(p, 'smp_')
    with tabs[2]:
        render_report(R, p, ai, {}, 'smp_rep_')


def render_results(cfg):
    R = st.session_state.get('R')
    if not R:
        return
    st.markdown('---')
    st.markdown('## 📊 분석 결과 — %s' % R.get('name', ''))
    st.caption('분석 시각 %s · 사이드바의 보조 물리량을 바꾸면 위상공간/AI/보고서가 즉시 갱신됩니다.' % R.get('time', ''))
    if R['mode'] == 'image':
        render_image_results(R, cfg)
    elif R['mode'] == 'spectrum':
        render_spectrum_results(R, cfg)
    elif R['mode'] == 'sample':
        render_sample_results(R, cfg)


# ═══════════════════════════════════════════════════════════
#                 입력 소스 결정 + 그리기 단계
# ═══════════════════════════════════════════════════════════
def resolve_source():
    up = st.file_uploader('📤 사진·FITS·스펙트럼 파일 업로드',
                          type=['png', 'jpg', 'jpeg', 'tif', 'tiff', 'bmp', 'webp', 'fits', 'fit', 'fts', 'gz', 'fz',
                                'csv', 'txt', 'dat'],
                          help='은하 사진(JPG/PNG/FITS), 분광 사진, 1D 스펙트럼(FITS/CSV, SDSS spec 파일 포함)')
    if up is not None:
        data = up.getvalue()
        sig = hashlib.md5(data).hexdigest()[:16]
        try:
            src = dict(load_source(data, up.name))
        except Exception as ex:
            st.error('파일을 읽을 수 없습니다: %s' % ex)
            return None
        src['sig'] = sig
        if st.session_state.get('demo') is not None:
            st.caption('ℹ️ 업로드한 파일이 데모/SDSS 입력보다 우선합니다 (업로드 파일을 지우면 데모로 돌아갑니다).')
        return src
    d = st.session_state.get('demo')
    if d is None:
        return None
    dsig = 'demo_%s_%s' % (d['name'], d.get('uid', ''))
    if d['kind'] == 'image':
        arr = np.asarray(d['img'].convert('RGB'), dtype=np.uint8)
        return {'kind': 'image', 'raw': arr, 'name': d['name'], 'sig': dsig, 'header': {},
                'is_fits': False, 'pixel_scale': d.get('pixel_scale'), 'notes': []}
    return {'kind': 'spectrum', 'wave': d['wave'], 'flux': d['flux'], 'name': d['name'], 'sig': dsig,
            'header': {}, 'z_hint': d.get('z_hint'), 'unit_hint': d.get('unit_hint'), 'notes': []}


def stage_canvas(src, cfg, mode):
    raw = src['raw']
    H, W = raw.shape[:2]
    sig = src['sig']
    opts = tuple(sorted({k: cfg[k] for k in ('cut', 'p_lo', 'p_hi', 'stretch', 'cmap', 'force_gray', 'invert',
                                              'brightness', 'contrast')}.items()))
    disp = render_display(sig, raw, opts)

    max_w = cfg.get('canvas_scale', CANVAS_MAX_W)
    cw = min(max_w, W) if W >= 480 else min(max_w, 480)
    scale = cw / W
    ch = int(round(H * scale))
    if ch > CANVAS_MAX_H:
        scale = CANVAS_MAX_H / H
        cw, ch = int(round(W * scale)), CANVAS_MAX_H
    bg = disp.resize((max(cw, 1), max(ch, 1)), Image.LANCZOS if scale < 1 else Image.NEAREST)

    info = '**%s** · %d×%d px · %s' % (src['name'], W, H, 'FITS (선형 과학 데이터)' if src.get('is_fits')
                                         else ('RGB 사진' if raw.ndim == 3 else '흑백/16비트 영상'))
    if src.get('pixel_scale'):
        info += ' · %.3f″/px' % src['pixel_scale']
    st.markdown(info)
    for n in src.get('notes', []):
        st.caption('ℹ️ ' + n)

    st.markdown('<div class="step">② 분석할 영역을 그리세요 — 여러 개를 그리면 비교 분석됩니다</div>',
                unsafe_allow_html=True)
    tool_label = st.segmented_control('그리기 도구', list(TOOLS), default='▭ 사각형' if mode == MODE_SPEC else '◯ 원',
                                      key='draw_tool', label_visibility='collapsed')
    tool = TOOLS.get(tool_label or '◯ 원', 'circle')
    hints = {'rect': '드래그해서 사각형', 'circle': '중심에서 드래그해서 원', 'freedraw': '대상 둘레를 따라 그리면 닫힌 영역',
             'polygon': '클릭으로 꼭짓점, 더블클릭/우클릭으로 닫기', 'line': '분광 띠를 따라 직선 (적분 폭은 사이드바)',
             'point': '클릭한 픽셀의 원본 값을 표시', 'transform': '그린 도형을 선택해 이동·크기·회전 수정'}
    st.caption('💡 ' + hints[tool] + ' · 캔버스 아래 도구막대: ↶ 실행취소 ↷ 다시실행 🗑 전체삭제')

    col_cv, col_side = st.columns([3, 2], gap='medium')
    canvas_res = None
    with col_cv:
        if not CANVAS_OK:
            st.error('그리기 컴포넌트를 불러오지 못했습니다: %s' % CANVAS_ERR)
            st.image(bg)
        else:
            nxt = PALETTE[st.session_state.get('n_objs', 0) % len(PALETTE)]
            canvas_res = st_canvas(
                fill_color=hex_rgba(nxt, 0.12), stroke_width=cfg.get('stroke_width', 2), stroke_color=nxt,
                background_image=bg, update_streamlit=True, height=ch, width=cw, drawing_mode=tool,
                point_display_radius=4, display_toolbar=True,
                key='canvas_%s_%d' % (sig, st.session_state.get('canvas_reset', 0)))
    objects = (canvas_res.json_data or {}).get('objects', []) if canvas_res is not None and canvas_res.json_data else []
    st.session_state['n_objs'] = len(objects)
    rois, probes = parse_rois(objects, raw.shape, scale, 4)
    for r in rois:
        r['_scale'] = scale

    with col_side:
        st.markdown('**🎯 선택된 영역 (%d개)**' % len(rois))
        if not rois and not probes:
            st.info('왼쪽 이미지 위에 영역을 그리면 여기에 실시간 미리보기가 나타납니다.')
        if mode == MODE_IMAGE and rois:
            an = GalaxyImageAnalyzer(cfg.get('pixel_scale') or 0.396)
            lin = an.linearize_image(raw, 'auto')
            rows = []
            for r in rois:
                mk = roi_mask(r, raw.shape, cfg.get('freedraw_area', True))
                s = an.region_stats(lin, mk) if mk is not None else {'n_pix': 0}
                rows.append({'영역': r['label'], '픽셀': s.get('n_pix', 0), '평균': s.get('mean'),
                             '순플럭스': s.get('net_flux'), 'S/N': s.get('snr')})
            st.dataframe(pd.DataFrame(rows).style.format(precision=3), hide_index=True, width='stretch')
            for r in rois:
                st.markdown('<span class="roi-chip" style="background:%s">%s</span><span class="small-note">%s</span>'
                            % (r['color'], r['label'], r['desc']), unsafe_allow_html=True)
        if mode == MODE_SPEC and rois:
            gray = spectral_gray(raw, cfg.get('linearize', True))
            fig = go.Figure()
            for r in rois:
                sp = extract_roi_spectrum(gray, r, cfg)
                if sp is None:
                    continue
                fig.add_trace(go.Scatter(x=sp['wave'], y=sp['flux'], mode='lines', name=r['label'],
                                         line=dict(color=r['color'], width=1.3)))
            for n in ('H_beta', 'OIII_5007', 'H_alpha'):
                lam = LINE_LIST[n][0] * (1 + cfg.get('z', 0))
                fig.add_vline(x=lam, line=dict(color='#334155', dash='dot'))
            fig.update_xaxes(title='파장 (Å, 현재 교정)')
            st.plotly_chart(dark(fig, 300), width='stretch', key='live_spec')
            for r in rois:
                st.markdown('<span class="roi-chip" style="background:%s">%s</span><span class="small-note">%s</span>'
                            % (r['color'], r['label'], r['desc']), unsafe_allow_html=True)
        if probes:
            st.markdown('**📍 픽셀 값 (원본)**')
            prow = []
            for pnt in probes:
                x, y = int(np.clip(round(pnt['x']), 0, W - 1)), int(np.clip(round(pnt['y']), 0, H - 1))
                v = raw[y, x]
                prow.append({'x': x, 'y': y, '값': ', '.join('%.4g' % t for t in np.atleast_1d(v))})
            st.dataframe(pd.DataFrame(prow), hide_index=True, width='stretch')

        c1, c2 = st.columns(2)
        run = c1.button('🔬 분석 실행', type='primary', width='stretch', disabled=not rois)
        if c2.button('🗑️ 영역 모두 지우기', width='stretch'):
            st.session_state['canvas_reset'] = st.session_state.get('canvas_reset', 0) + 1
            st.session_state['n_objs'] = 0
            st.rerun()

    with st.expander('🔍 Ginga 뷰어 — 픽셀 값 · 히스토그램 · 단면 · 헤더', expanded=False):
        vt = st.tabs(['픽셀 뷰어', '히스토그램', '단면 (Cuts)', 'FITS 헤더'])
        with vt[0]:
            st.plotly_chart(fig_pixel_viewer(raw, rois, probes, cfg), width='stretch', key='pixview')
        with vt[1]:
            st.plotly_chart(fig_histogram(raw, cfg), width='stretch', key='hist')
        with vt[2]:
            lines = [r for r in rois if r['kind'] == 'line']
            if not lines:
                st.info('「／ 직선」 도구로 선을 그리면 그 선을 따른 밝기 단면이 표시됩니다.')
            else:
                fig = go.Figure()
                for r in lines:
                    g = r['geom']
                    d, v = GalaxyImageAnalyzer.line_cut(raw, g['x1'], g['y1'], g['x2'], g['y2'])
                    fig.add_trace(go.Scatter(x=d, y=v, mode='lines', name=r['label'], line=dict(color=r['color'])))
                fig.update_xaxes(title='선을 따른 거리 (px)')
                fig.update_yaxes(title='픽셀 값')
                st.plotly_chart(dark(fig, 330, '선 단면 프로파일'), width='stretch', key='cuts')
        with vt[3]:
            hd = src.get('header') or {}
            if hd:
                st.dataframe(pd.DataFrame({'키': list(hd), '값': [str(v) for v in hd.values()]}), hide_index=True,
                             width='stretch', height=360)
            else:
                st.info('FITS 헤더 없음 (일반 이미지)')

    if run and rois:
        with st.spinner('선택한 %d개 영역 분석 중...' % len(rois)):
            if mode == MODE_IMAGE:
                analyze_image_rois(src, rois, cfg)
            else:
                analyze_spectrum_rois(src, rois, cfg)


def analyze_image_rois(src, rois, cfg):
    raw = src['raw']
    an = GalaxyImageAnalyzer(cfg.get('pixel_scale') or 0.396)
    out = []
    for r in rois:
        mk = roi_mask(r, raw.shape, cfg.get('freedraw_area', True))
        if r['kind'] == 'line':
            res = {'stats': {}, 'error': '직선은 면적이 없어 형태 분석 대상이 아닙니다 (Ginga 뷰어 「단면」 탭 참고).'}
        elif mk is None or mk.sum() < 9:
            res = {'stats': {}, 'error': '영역이 너무 작습니다.'}
        else:
            try:
                res = an.analyze(raw, mk, linearize='auto')
            except Exception as ex:
                res = {'stats': {}, 'error': '분석 오류: %s' % ex}
        out.append({'label': r['label'], 'color': r['color'], 'kind': r['kind'], 'desc': r['desc'], 'res': res})
    st.session_state['R'] = {'mode': 'image', 'name': src['name'], 'rois': out, 'source_sig': src['sig'],
                             'time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'notes': []}


def analyze_spectrum_rois(src, rois, cfg):
    raw = src['raw']
    gray = spectral_gray(raw, cfg.get('linearize', True))
    unit = FLUX_UNITS.get(cfg.get('flux_unit'), None)
    out = []
    for r in rois:
        sp = extract_roi_spectrum(gray, r, cfg)
        if sp is None:
            continue
        ent = run_spectrum_fit(sp['wave'], sp['flux'], cfg, unit)
        ent.update({'label': r['label'], 'color': r['color'], 'desc': r['desc'] + ' · 분산축 ' +
                    ('가로' if sp['axis'] == 'horizontal' else '세로')})
        out.append(ent)
    if not out:
        st.error('선택한 영역에서 스펙트럼을 추출하지 못했습니다.')
        return
    st.session_state['R'] = {'mode': 'spectrum', 'name': src['name'], 'rois': out, 'source_sig': src['sig'],
                             'time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}


def stage_spectrum_file(src, cfg):
    w, f = np.asarray(src['wave'], float), np.asarray(src['flux'], float)
    st.markdown('**%s** · 1D 스펙트럼 · %d 점 · %.0f–%.0f Å' % (src['name'], len(w), w.min(), w.max()))
    if src.get('z_hint') is not None:
        st.caption('파일에 기록된 적색편이 z = %.5f (사이드바 자동 추정을 끄고 이 값을 입력해도 됩니다)' % src['z_hint'])
    st.markdown('<div class="step">② 분석할 파장 구간을 선택하세요 (1D 영역 선택)</div>', unsafe_allow_html=True)
    lo, hi = st.slider('파장 범위 (Å)', float(w.min()), float(w.max()), (float(w.min()), float(w.max())),
                       key='wrange_' + src['sig'])
    m = (w >= lo) & (w <= hi)
    prev = go.Figure(go.Scatter(x=w, y=f, mode='lines', line=dict(color='#334155', width=1), name='전체'))
    prev.add_trace(go.Scatter(x=w[m], y=f[m], mode='lines', line=dict(color='#60a5fa', width=1.3), name='선택 구간'))
    st.plotly_chart(dark(prev, 300), width='stretch', key='spec_preview')
    if st.button('🔬 분석 실행', type='primary', disabled=m.sum() < 20):
        unit = FLUX_UNITS.get(cfg.get('flux_unit'), None)
        cfg2 = dict(cfg)
        if src.get('z_hint') is not None and not cfg.get('z'):
            cfg2['z'] = float(src['z_hint'])            # 자동 추정 실패 시 파일의 z 사용
        ent = run_spectrum_fit(w[m], f[m], cfg2, unit)
        ent.update({'label': '스펙트럼', 'color': PALETTE[0], 'desc': '%.0f–%.0f Å 구간' % (lo, hi)})
        st.session_state['R'] = {'mode': 'spectrum', 'name': src['name'], 'rois': [ent], 'source_sig': src['sig'],
                                 'time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}


def landing():
    st.markdown('<div class="step">시작하기</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown('#### 🖼️ 은하 사진 분석')
        st.markdown('- 은하 사진/FITS 업로드\n- 원·올가미로 은하 영역 선택\n- 집중도·비대칭도·Gini–M20·Sérsic → **형태 분류**\n'
                    '- 여러 영역 밝기/색 비교')
    with c2:
        st.markdown('#### 🌈 분광 분석')
        st.markdown('- 분광 사진에서 띠를 사각형/직선으로 선택\n- 파장 교정 → 방출선 자동 검출·블렌드 분리\n'
                    '- 소광·SFR·금속량·BPT·전자밀도\n- 중심핵 vs 원반 **공간 분해 BPT**')
    with c3:
        st.markdown('#### 🧠 위상공간 · AI')
        st.markdown('- SDSS 10만 은하 위에 대상 표시\n- 백분위·주계열 오프셋·유사 은하 10개\n'
                    '- 11종 유형 AI 분류 + 개별 근거(XAI)\n- 보고서(MD/HTML) 자동 생성')
    st.info('👈 파일이 없다면 사이드바 **「바로 체험하기」**에서 모의 은하/분광 사진 또는 SDSS 실제 은하 사진을 불러오세요.')


# ═══════════════════════════════════════════════════════════
#                            main
# ═══════════════════════════════════════════════════════════
def main():
    init_state()
    st.markdown('<div class="hero"><h1>🌌 GalaxyEvolution Studio</h1>'
                '<p>사진·FITS 위에 영역을 그리면 → 측광 · 형태 · 분광 · 물리량 · SDSS 위상공간 · AI 분류까지 한 번에</p></div>',
                unsafe_allow_html=True)

    st.markdown('<div class="step">① 분석 종류를 고르고 파일을 올리세요</div>', unsafe_allow_html=True)
    mode = st.radio('분석 종류', [MODE_IMAGE, MODE_SPEC], key='analysis_type', horizontal=True,
                    label_visibility='collapsed')
    src = resolve_source()

    # 새 입력 소스 감지 → 이전 결과/영역 초기화, 소스에 맞는 기본값 설정 (사이드바 위젯 생성 전)
    if src is not None and st.session_state.get('last_sig') != src['sig']:
        st.session_state['last_sig'] = src['sig']
        R = st.session_state.get('R')
        if R and R.get('source_sig') not in (src['sig'], 'sample'):
            st.session_state['R'] = None
        st.session_state['n_objs'] = 0
        st.session_state['flux_unit_idx'] = 1 if src.get('unit_hint') == 'sdss' else 0
    if src is not None and src['kind'] == 'spectrum' and mode != MODE_SPEC:
        st.session_state['_pending_mode'] = MODE_SPEC     # 1D 스펙트럼은 분광 모드에서만 처리
        st.rerun()

    cfg = sidebar(mode)

    if src is None:
        landing()
    elif src['kind'] == 'spectrum':
        stage_spectrum_file(src, cfg)
    else:
        stage_canvas(src, cfg, mode)

    R = st.session_state.get('R')
    if R and R['mode'] in ('image', 'spectrum') and (src is None or R.get('source_sig') != src['sig']):
        st.session_state['R'] = None
    render_results(cfg)


main()
