# -*- coding: utf-8 -*-
"""
🌌 GalaxyEvolution Studio v3 — Ginga-inspired 이미지 기반 천체 분석
===================================================================
핵심: 사진/FITS 업로드 → 이미지 조정 → 다중 영역 그리기 → 비교 분석
Ginga 참고: FITS 지원, 컬러맵, 자동 Cut Levels, 다중 ROI, 줌/팬
"""

import streamlit as st
import numpy as np
import pandas as pd
import os, sys, datetime, io
from PIL import Image, ImageEnhance

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from modules.spectrum_engine import (
    SpectrumROIExtractor, WavelengthCalibrator,
    EmissionLineFitter, MockSpectrumGenerator
)
from modules.physics_calculator import PhysicsCalculator
from modules.phase_space_mapper import PhaseSpaceMapper
from modules.ml_predictor import GalaxyPredictor
from modules.sdss_fetcher import SDSSFetcher
from modules.report_generator import ReportGenerator

from streamlit_drawable_canvas import st_canvas
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# FITS 지원
try:
    from astropy.io import fits as astropy_fits
    HAS_ASTROPY = True
except ImportError:
    HAS_ASTROPY = False

MASTER_CSV = os.path.join(PROJECT_ROOT, "galaxy_master_complete_all.csv")
MODEL_DIR = os.path.join(PROJECT_ROOT, "output", "models")

# ── 페이지 설정 ────────────────────────────────────────
st.set_page_config(
    page_title="🌌 GalaxyEvolution Studio",
    page_icon="🌌", layout="wide",
    initial_sidebar_state="expanded"
)

# ── CSS ────────────────────────────────────────────────
st.markdown("""
<style>
    .stApp { background-color: #0e1117; }
    .main-header {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        padding: 1rem 1.5rem; border-radius: 12px; margin-bottom: 0.8rem;
        border: 1px solid #1e3a5f;
    }
    .main-header h1 { color: #e2e8f0; font-size: 1.6rem; margin: 0; }
    .main-header p { color: #94a3b8; margin: 0.2rem 0 0 0; font-size: 0.85rem; }
    .step-label {
        background: #1e293b; border-radius: 8px; padding: 0.5rem 0.8rem;
        border-left: 4px solid #3b82f6; margin: 0.8rem 0 0.4rem 0;
        color: #e2e8f0; font-weight: 600; font-size: 1rem;
    }
    .roi-card {
        background: #1e293b; border-radius: 8px; padding: 0.6rem;
        border: 1px solid #334155; margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# ── 캐시 로더 ──────────────────────────────────────────
@st.cache_resource
def load_mapper():
    return PhaseSpaceMapper(MASTER_CSV)

@st.cache_resource
def load_predictor():
    return GalaxyPredictor(MODEL_DIR)

@st.cache_resource
def load_calculator():
    return PhysicsCalculator()


def safe_fmt(val, fmt):
    if val is None:
        return "—"
    try:
        if isinstance(val, float) and (np.isnan(val) or np.isinf(val)):
            return "—"
        return fmt % val
    except (TypeError, ValueError):
        return "—"


# ═══════════════════════════════════════════════════════
#                FITS / 이미지 로딩 엔진
# ═══════════════════════════════════════════════════════
COLORMAPS = {
    'Gray': 'gray', 'Viridis': 'viridis', 'Inferno': 'inferno',
    'Plasma': 'plasma', 'Hot': 'hot', 'Jet': 'jet',
    'Cubehelix': 'cubehelix', 'Bone': 'bone',
}


def load_fits_as_array(file_bytes):
    """FITS 파일 → numpy 2D 배열 (첫 번째 이미지 HDU)"""
    hdu_list = astropy_fits.open(io.BytesIO(file_bytes))
    data = None
    header = None
    for hdu in hdu_list:
        if hdu.data is not None and hdu.data.ndim >= 2:
            data = hdu.data.astype(float)
            header = hdu.header
            break
    hdu_list.close()
    if data is None:
        return None, None
    # 3D cube → 첫 슬라이스
    if data.ndim == 3:
        data = data[0]
    return data, header


def apply_cut_levels(data, method='zscale', low_pct=1, high_pct=99):
    """Ginga 스타일 자동 Cut Levels 적용"""
    if method == 'minmax':
        vmin, vmax = np.nanmin(data), np.nanmax(data)
    elif method == 'percentile':
        vmin = np.nanpercentile(data, low_pct)
        vmax = np.nanpercentile(data, high_pct)
    elif method == 'zscale':
        # zscale 근사: 중앙 25% 사용
        center = data[data.shape[0] // 4: 3 * data.shape[0] // 4,
                       data.shape[1] // 4: 3 * data.shape[1] // 4]
        center_clean = center[np.isfinite(center)]
        if len(center_clean) > 10:
            med = np.median(center_clean)
            std = np.std(center_clean)
            vmin = med - 2.5 * std
            vmax = med + 2.5 * std
        else:
            vmin, vmax = np.nanmin(data), np.nanmax(data)
    else:  # 'manual'
        vmin = np.nanpercentile(data, low_pct)
        vmax = np.nanpercentile(data, high_pct)

    clipped = np.clip(data, vmin, vmax)
    if vmax > vmin:
        normed = (clipped - vmin) / (vmax - vmin)
    else:
        normed = np.zeros_like(clipped)
    return normed


def array_to_pil(data_norm, colormap='gray', invert=False, brightness=1.0, contrast=1.0):
    """정규화된 2D 배열 → PIL Image (컬러맵 적용)"""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.cm as cm

    if invert:
        data_norm = 1.0 - data_norm

    cmap = cm.get_cmap(colormap)
    rgba = cmap(data_norm)
    rgb = (rgba[:, :, :3] * 255).astype(np.uint8)
    img = Image.fromarray(rgb)

    if brightness != 1.0:
        img = ImageEnhance.Brightness(img).enhance(brightness)
    if contrast != 1.0:
        img = ImageEnhance.Contrast(img).enhance(contrast)

    return img


def load_regular_image(uploaded):
    """일반 이미지 (JPG/PNG 등) 로드"""
    return Image.open(uploaded).convert('RGB')


# ═══════════════════════════════════════════════════════
#                 세션 초기화
# ═══════════════════════════════════════════════════════
def init_session():
    defaults = {
        'spectrum_df': None, 'emission_lines': None,
        'physics_results': None, 'target_properties': None,
        'analysis_complete': False, 'target_name': '업로드 천체',
        'draw_mode': '🔲 사각형', 'min_wave': 4000, 'max_wave': 7000,
        'redshift': 0.0, 'fits_data': None, 'fits_header': None,
        'roi_spectra': [],  # 다중 ROI 스펙트럼 목록
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ═══════════════════════════════════════════════════════
#              사이드바: Ginga 스타일 컨트롤 패널
# ═══════════════════════════════════════════════════════
def render_sidebar():
    st.sidebar.markdown("## 🔧 이미지 & 분석 설정")

    # ── 이미지 조정 (Ginga 참고) ──
    st.sidebar.markdown("### 🎨 이미지 조정 (Ginga-style)")

    cut_method = st.sidebar.selectbox(
        "Cut Levels (밝기 범위)",
        ["zscale", "percentile", "minmax"],
        index=0, key="cut_method",
        help="Ginga의 자동 밝기 조정 알고리즘"
    )

    if cut_method == "percentile":
        pct_cols = st.sidebar.columns(2)
        st.session_state['low_pct'] = pct_cols[0].number_input(
            "Low %", 0, 50, 1, key="low_pct_input")
        st.session_state['high_pct'] = pct_cols[1].number_input(
            "High %", 50, 100, 99, key="high_pct_input")

    colormap = st.sidebar.selectbox(
        "컬러맵 (Colormap)", list(COLORMAPS.keys()), index=0, key="cmap_sel"
    )
    st.session_state['colormap'] = COLORMAPS[colormap]

    invert = st.sidebar.checkbox("색상 반전", value=False, key="invert_chk")
    st.session_state['invert'] = invert

    brightness = st.sidebar.slider("밝기", 0.2, 3.0, 1.0, 0.1, key="bright_sl")
    st.session_state['brightness'] = brightness
    contrast = st.sidebar.slider("대비", 0.2, 3.0, 1.0, 0.1, key="contrast_sl")
    st.session_state['contrast'] = contrast

    st.sidebar.markdown("---")

    # ── 그리기 모드 ──
    st.sidebar.markdown("### ✏️ 그리기 도구")
    draw_mode = st.sidebar.radio(
        "ROI 선택 방식",
        ["🔲 사각형", "📏 라인", "✏️ 자유 그리기", "⭕ 원형"],
        index=0, key="draw_radio"
    )
    st.session_state['draw_mode'] = draw_mode

    st.sidebar.markdown("---")

    # ── 파장/적색편이 ──
    st.sidebar.markdown("### 🌈 스펙트럼 설정")
    c1, c2 = st.sidebar.columns(2)
    st.session_state['min_wave'] = c1.number_input("최소 λ(Å)", 3000, 10000, 4000, 100, key="minw")
    st.session_state['max_wave'] = c2.number_input("최대 λ(Å)", 3000, 10000, 7000, 100, key="maxw")
    st.session_state['redshift'] = st.sidebar.slider("적색편이 z", 0.0, 0.3, 0.0, 0.005, key="z_sl")

    st.sidebar.markdown("---")

    # ── 데모 ──
    st.sidebar.markdown("### 🧪 테스트 도구")
    mock_type = st.sidebar.selectbox("모의 유형",
        ["star_forming (별생성)", "agn_seyfert (AGN)", "elliptical (타원)"],
        key="mock_sel")
    if st.sidebar.button("🧬 모의 스펙트럼 생성", use_container_width=True):
        mock = MockSpectrumGenerator()
        df = mock.generate(mock_type.split(" (")[0])
        st.session_state['spectrum_df'] = df
        st.session_state['target_name'] = '모의 %s' % mock_type.split("(")[1].rstrip(")")
        st.session_state['analysis_complete'] = False
        st.session_state['roi_spectra'] = []

    sdss = SDSSFetcher()
    samples = sdss.get_sample_galaxies()
    sel = st.sidebar.selectbox("샘플 은하", [s['name'] for s in samples], key="samp_sel")
    if st.sidebar.button("📥 샘플 로드", use_container_width=True):
        sample = next(s for s in samples if s['name'] == sel)
        _load_sample_props(sample)

    # ── 다중 ROI 관리 ──
    if st.session_state.get('roi_spectra'):
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 📦 저장된 ROI (%d개)" % len(st.session_state['roi_spectra']))
        if st.sidebar.button("🗑️ 모든 ROI 초기화", use_container_width=True):
            st.session_state['roi_spectra'] = []
            st.session_state['spectrum_df'] = None
            st.session_state['analysis_complete'] = False


def _load_sample_props(sample):
    props = dict(sample)
    props['log_stellar_mass'] = props['log_mass']
    props['lgm_tot_p50'] = props['log_mass']
    props['sfr_tot_p50'] = props['log_sfr']
    props['metallicity_oh'] = props['metallicity']
    props['oh_p50'] = props['metallicity']
    props['color_u_r'] = props['color_ur']
    calc = load_calculator()
    ssfr = calc.calculate_log_ssfr(props['log_sfr'], props['log_mass'])
    props['log_ssfr'] = ssfr if ssfr is not None else -10.5
    bpt = calc.classify_bpt(props['log_nii_ha'], props['log_oiii_hb'])
    props['bpt_class'] = bpt['class']
    props['bpt_class_en'] = bpt['class_en']
    gei = calc.calculate_gei(props['log_mass'], props['log_ssfr'],
                             props['metallicity'], props['color_ur'])
    props['gei_score'] = gei
    stage = calc.diagnose_evolution_stage(gei)
    props['evolution_stage'] = stage['stage']
    props['evolution_stage_en'] = stage['stage_en']
    st.session_state['target_name'] = sample['name']
    st.session_state['target_properties'] = props
    st.session_state['physics_results'] = props
    st.session_state['analysis_complete'] = True
    st.session_state['spectrum_df'] = None
    st.session_state['roi_spectra'] = []


# ═══════════════════════════════════════════════════════
#       STEP 1: 이미지 업로드 + FITS 처리 + 영역 그리기
# ═══════════════════════════════════════════════════════
def render_step1():
    st.markdown('<div class="step-label">📷 STEP 1 — 이미지 업로드 & 영역 선택</div>',
                unsafe_allow_html=True)

    # FITS 지원 추가
    accepted = ["jpg", "jpeg", "png", "bmp", "tiff"]
    if HAS_ASTROPY:
        accepted.extend(["fits", "fit", "fts", "fits.gz"])

    uploaded = st.file_uploader(
        "천체 이미지 업로드 (JPG/PNG/FITS)",
        type=accepted, key="main_uploader"
    )

    if uploaded is None:
        st.markdown("""
        > 📸 **사진 또는 FITS 파일을 업로드**하면 이미지 위에 분석 영역을 그릴 수 있습니다.
        >
        > 지원 포맷: **JPG, PNG, TIFF, FITS** (Ginga 호환)
        >
        > 💡 사이드바에서 **이미지 조정**(컬러맵, 밝기/대비, Cut Levels)을 설정하세요.
        """)
        # 이미 로드된 스펙트럼 표시
        if st.session_state.get('spectrum_df') is not None:
            _show_spectrum_and_analyze()
        return

    # ── 파일 종류 판별 & 로드 ──
    fname = uploaded.name.lower()
    is_fits = fname.endswith(('.fits', '.fit', '.fts', '.fits.gz'))

    if is_fits and HAS_ASTROPY:
        raw_bytes = uploaded.read()
        fits_data, fits_header = load_fits_as_array(raw_bytes)
        if fits_data is None:
            st.error("FITS 파일에서 이미지 데이터를 찾을 수 없습니다.")
            return
        st.session_state['fits_data'] = fits_data
        st.session_state['fits_header'] = fits_header

        # FITS 메타데이터 표시
        with st.expander("📋 FITS 헤더 정보", expanded=False):
            if fits_header:
                info_keys = ['NAXIS1', 'NAXIS2', 'BITPIX', 'OBJECT',
                             'TELESCOP', 'INSTRUME', 'EXPTIME', 'FILTER',
                             'DATE-OBS', 'RA', 'DEC', 'CTYPE1', 'CTYPE2']
                rows = []
                for k in info_keys:
                    if k in fits_header:
                        rows.append({'키': k, '값': str(fits_header[k]),
                                     '설명': fits_header.comments.get(k, '')})
                if rows:
                    st.table(pd.DataFrame(rows))
                st.caption("이미지 크기: %d × %d px" % (fits_data.shape[1], fits_data.shape[0]))

        # 이미지 조정 적용
        cut = st.session_state.get('cut_method', 'zscale') or 'zscale'
        low_p = st.session_state.get('low_pct', 1)
        high_p = st.session_state.get('high_pct', 99)
        normed = apply_cut_levels(fits_data, cut, low_p, high_p)
        cmap = st.session_state.get('colormap', 'gray')
        inv = st.session_state.get('invert', False)
        brt = st.session_state.get('brightness', 1.0)
        ctr = st.session_state.get('contrast', 1.0)
        image = array_to_pil(normed, cmap, inv, brt, ctr)
        img_array = np.array(image)

    else:
        image = load_regular_image(uploaded)
        img_array = np.array(image)

        # 일반 이미지도 밝기/대비 적용
        brt = st.session_state.get('brightness', 1.0)
        ctr = st.session_state.get('contrast', 1.0)
        if brt != 1.0 or ctr != 1.0:
            adj = image.copy()
            if brt != 1.0:
                adj = ImageEnhance.Brightness(adj).enhance(brt)
            if ctr != 1.0:
                adj = ImageEnhance.Contrast(adj).enhance(ctr)
            image = adj
            img_array = np.array(image)

    # ── 캔버스 + ROI ──
    _render_canvas_with_roi(image, img_array)


def _render_canvas_with_roi(image, img_array):
    """캔버스 표시 + 다중 ROI 처리"""
    img_w, img_h = image.size

    draw_mode_label = st.session_state.get('draw_mode', '🔲 사각형')
    if "사각형" in draw_mode_label:
        drawing_mode = "rect"
    elif "라인" in draw_mode_label:
        drawing_mode = "line"
    elif "원형" in draw_mode_label:
        drawing_mode = "circle"
    else:
        drawing_mode = "freedraw"

    col_canvas, col_result = st.columns([3, 2])

    with col_canvas:
        # 인라인 모드 버튼
        mc = st.columns(4)
        modes = [("🔲 사각형", "rect"), ("📏 라인", "line"),
                 ("✏️ 자유", "freedraw"), ("⭕ 원형", "circle")]
        for i, (label, mode) in enumerate(modes):
            if mc[i].button(label, use_container_width=True,
                            type="primary" if drawing_mode == mode else "secondary"):
                st.session_state['draw_mode'] = label
                st.rerun()

        # 캔버스 크기
        canvas_w = min(700, img_w)
        scale = canvas_w / img_w
        canvas_h = int(img_h * scale)

        st.caption("이미지 위에 분석 영역을 그려주세요 (여러 개 그릴 수 있습니다)")

        canvas_result = st_canvas(
            fill_color="rgba(59, 130, 246, 0.10)",
            stroke_width=2 if drawing_mode != "freedraw" else 3,
            stroke_color="#3b82f6",
            background_image=image,
            drawing_mode=drawing_mode,
            height=canvas_h,
            width=canvas_w,
            key="main_canvas",
        )

    with col_result:
        if canvas_result.json_data is not None:
            objects = canvas_result.json_data.get("objects", [])
            if objects:
                _process_multi_roi(objects, img_array, scale)
            else:
                st.info("⬅️ 이미지 위에 영역을 그려주세요.")
                st.markdown("""
                **그리기 도구:**
                - 🔲 **사각형**: 드래그로 영역 지정
                - 📏 **라인**: 시작~끝 선분
                - ✏️ **자유**: 펜으로 그리기
                - ⭕ **원형**: 원형 영역
                """)
        else:
            st.info("⬅️ 이미지 위에 분석 영역을 그려주세요.")


# ═══════════════════════════════════════════════════════
#              다중 ROI 처리 + 비교
# ═══════════════════════════════════════════════════════
ROI_COLORS = ['#60a5fa', '#f87171', '#4ade80', '#facc15', '#c084fc', '#fb923c']


def _process_multi_roi(objects, img_array, scale):
    """모든 그린 영역에서 스펙트럼 추출 → 비교 표시"""
    roi = SpectrumROIExtractor()
    min_w = st.session_state.get('min_wave', 4000)
    max_w = st.session_state.get('max_wave', 7000)

    spectra = []
    for idx, obj in enumerate(objects):
        obj_type = obj.get("type", "")
        color = ROI_COLORS[idx % len(ROI_COLORS)]
        label = "ROI-%d" % (idx + 1)

        try:
            if obj_type == "rect":
                x1 = int(obj["left"] / scale)
                y1 = int(obj["top"] / scale)
                x2 = int((obj["left"] + obj["width"]) / scale)
                y2 = int((obj["top"] + obj["height"]) / scale)
                pix, flux = roi.extract_from_rect(img_array, x1, y1, x2, y2)
            elif obj_type == "line":
                x1 = int((obj.get("x1", 0) + obj["left"]) / scale)
                y1 = int((obj.get("y1", 0) + obj["top"]) / scale)
                x2 = int((obj.get("x2", 0) + obj["left"]) / scale)
                y2 = int((obj.get("y2", 0) + obj["top"]) / scale)
                pix, flux = roi.extract_from_line(img_array, x1, y1, x2, y2)
            elif obj_type == "path":
                mask = np.zeros(img_array.shape[:2], dtype=bool)
                for pt in obj.get("path", []):
                    if len(pt) >= 3:
                        px, py = int(pt[1] / scale), int(pt[2] / scale)
                        r = 5
                        mask[max(0, py-r):min(mask.shape[0], py+r),
                             max(0, px-r):min(mask.shape[1], px+r)] = True
                pix, flux = roi.extract_from_mask(img_array, mask)
            elif obj_type == "circle":
                cx = int((obj["left"] + obj.get("radius", 50)) / scale)
                cy = int((obj["top"] + obj.get("radius", 50)) / scale)
                radius = int(obj.get("radius", 50) / scale)
                yy, xx = np.ogrid[:img_array.shape[0], :img_array.shape[1]]
                circle_mask = ((xx - cx)**2 + (yy - cy)**2) <= radius**2
                pix, flux = roi.extract_from_mask(img_array, circle_mask)
            else:
                continue

            cal = WavelengthCalibrator()
            wavelength = cal.calibrate_from_range(len(flux), min_w, max_w)
            df = pd.DataFrame({'wavelength': wavelength, 'flux': flux})
            spectra.append({'label': label, 'color': color, 'df': df, 'type': obj_type})

        except Exception as e:
            st.warning("%s 추출 실패: %s" % (label, str(e)))

    if not spectra:
        st.warning("추출된 스펙트럼이 없습니다.")
        return

    st.session_state['roi_spectra'] = spectra

    # ── 스펙트럼 비교 그래프 ──
    st.markdown("**📊 추출된 스펙트럼 (%d개 ROI)**" % len(spectra))
    fig = go.Figure()
    for sp in spectra:
        fig.add_trace(go.Scatter(
            x=sp['df']['wavelength'], y=sp['df']['flux'],
            mode='lines', line=dict(color=sp['color'], width=1.5),
            name=sp['label']
        ))

    ref_lines = {'Hα': 6562.82, 'Hβ': 4861.33, '[OIII]': 5006.84, '[NII]': 6583.41}
    for name, wav in ref_lines.items():
        fig.add_vline(x=wav, line_dash="dot", line_color="rgba(255,255,255,0.2)",
                      annotation_text=name, annotation_font_size=9)

    fig.update_layout(
        template='plotly_dark', height=280,
        margin=dict(l=40, r=10, t=20, b=30),
        xaxis_title="파장 (Å)", yaxis_title="플럭스",
        legend=dict(orientation="h", yanchor="bottom", y=1.02)
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── 분석할 ROI 선택 ──
    if len(spectra) > 1:
        selected_roi = st.selectbox(
            "분석할 ROI 선택", [sp['label'] for sp in spectra],
            key="roi_select"
        )
        sel_sp = next(sp for sp in spectra if sp['label'] == selected_roi)
    else:
        sel_sp = spectra[0]

    st.session_state['spectrum_df'] = sel_sp['df']
    st.info("**%s** 선택됨 (%s, %d 포인트)" % (
        sel_sp['label'], sel_sp['type'], len(sel_sp['df'])))

    if st.button("🔬 선택 영역 자동 분석", use_container_width=True, type="primary"):
        _run_full_analysis(sel_sp['df'])


# ═══════════════════════════════════════════════════════
#            분석 실행 & 결과 표시
# ═══════════════════════════════════════════════════════
def _run_full_analysis(df):
    z = st.session_state.get('redshift', 0.0)
    with st.spinner("방출선 감지 중..."):
        fitter = EmissionLineFitter()
        result = fitter.fit_all_lines(df['wavelength'].values, df['flux'].values, z=z)

    lines = {}
    if result:
        fits_r = result.get('fits', {})
        peaks_r = result.get('peaks', {})
        for lname in ['H_alpha', 'H_beta', 'OIII_5007', 'NII_6584']:
            if isinstance(fits_r, dict) and lname in fits_r and fits_r[lname]:
                if 'integrated_flux' in fits_r[lname]:
                    lines[lname] = fits_r[lname]['integrated_flux']
            elif isinstance(peaks_r, dict) and lname in peaks_r and peaks_r[lname]:
                if 'flux' in peaks_r[lname]:
                    lines[lname] = peaks_r[lname]['flux']

    st.session_state['emission_lines'] = lines
    calc = load_calculator()
    physics = calc.compute_all(lines, z=z if z > 0 else 0.05)
    if physics:
        st.session_state['physics_results'] = physics
        st.session_state['target_properties'] = physics
        st.session_state['analysis_complete'] = True
    st.rerun()


def _show_spectrum_and_analyze():
    df = st.session_state['spectrum_df']
    st.markdown('<div class="step-label">📊 STEP 2 — 스펙트럼 & 방출선 분석</div>',
                unsafe_allow_html=True)
    _plot_full_spectrum(df)
    if not st.session_state.get('analysis_complete'):
        if st.button("🔬 방출선 자동 감지 & 물리량 추출",
                     use_container_width=True, type="primary"):
            _run_full_analysis(df)
        return
    _show_analysis_results()


def _plot_full_spectrum(df):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['wavelength'], y=df['flux'],
        mode='lines', line=dict(color='#60a5fa', width=1.5), name='스펙트럼'
    ))
    for name, wav in {'Hβ': 4861.33, '[OIII]': 5006.84, 'Hα': 6562.82, '[NII]': 6583.41}.items():
        fig.add_vline(x=wav, line_dash="dot", line_color="rgba(255,255,255,0.3)",
                      annotation_text=name, annotation_position="top")
    fig.update_layout(
        template='plotly_dark', title="관측 스펙트럼",
        xaxis_title="파장 (Å)", yaxis_title="플럭스",
        height=350, margin=dict(l=50, r=20, t=40, b=40)
    )
    st.plotly_chart(fig, use_container_width=True)


def _show_analysis_results():
    pr = st.session_state.get('physics_results', {})
    if not pr:
        return

    st.markdown('<div class="step-label">⚗️ STEP 3 — 추출된 천체물리량</div>',
                unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("E(B-V)", safe_fmt(pr.get('ebv'), "%.3f"))
    c2.metric("log(SFR)", safe_fmt(pr.get('log_sfr'), "%.2f"))
    c3.metric("12+log(O/H)", safe_fmt(pr.get('metallicity'), "%.3f"))
    c4.metric("BPT 분류", str(pr.get('bpt_class', '—')))
    gei = pr.get('gei', pr.get('gei_score'))
    c5.metric("GEI", safe_fmt(gei, "%.1f") if gei else "—")

    tab_ps, tab_ai, tab_rpt = st.tabs(["📊 위상공간 매핑", "🧠 AI 분류", "📑 보고서"])
    with tab_ps:
        _render_phase_space(pr)
    with tab_ai:
        _render_ai_diagnosis(pr)
    with tab_rpt:
        _render_report(pr)


# ═══════════════════════════════════════════════════════
#              위상공간 / AI / 보고서  (동일)
# ═══════════════════════════════════════════════════════
def _render_phase_space(props):
    mapper = load_mapper()
    if mapper.df.empty:
        st.warning("마스터 데이터를 로드할 수 없습니다.")
        return
    nii = props.get('log_nii_ha')
    oiii = props.get('log_oiii_hb')
    mass = props.get('log_mass', props.get('log_stellar_mass', props.get('lgm_tot_p50')))
    sfr = props.get('log_sfr', props.get('sfr_tot_p50'))
    met = props.get('metallicity', props.get('metallicity_oh', props.get('oh_p50')))
    col_ur = props.get('color_ur', props.get('color_u_r'))

    charts = st.multiselect("표시할 도표",
        ["2×2 종합", "BPT", "SFMS", "MZR", "색-질량", "3D FMR"],
        default=["2×2 종합"], key="chart_sel"
    )
    tp = {'log_nii_ha': nii, 'log_oiii_hb': oiii, 'log_mass': mass,
          'log_sfr': sfr, 'metallicity': met, 'color_ur': col_ur}
    if "2×2 종합" in charts:
        st.plotly_chart(mapper.plot_summary_4panel(tp), use_container_width=True)
    if "BPT" in charts:
        st.plotly_chart(mapper.plot_bpt(nii, oiii), use_container_width=True)
    if "SFMS" in charts:
        st.plotly_chart(mapper.plot_sfms(mass, sfr), use_container_width=True)
    if "MZR" in charts:
        st.plotly_chart(mapper.plot_mzr(mass, met), use_container_width=True)
    if "색-질량" in charts:
        st.plotly_chart(mapper.plot_color_mass(mass, col_ur), use_container_width=True)
    if "3D FMR" in charts:
        st.plotly_chart(mapper.plot_3d_fmr(mass, sfr, met), use_container_width=True)


def _render_ai_diagnosis(props):
    predictor = load_predictor()
    calc = load_calculator()
    if not predictor.is_loaded:
        st.error("ML 모델 파일이 없습니다.")
        return
    type_r = predictor.predict_galaxy_type(props)
    cluster_r = predictor.predict_evolution_cluster(props)
    col_t, col_c = st.columns([3, 2])
    with col_t:
        st.markdown("#### 🏷️ 11대 은하 유형 분류")
        if type_r and type_r.get('predicted_class'):
            st.markdown("**예측:** `%s` (신뢰도 %.1f%%)" % (
                type_r['predicted_class'], type_r['confidence'] * 100))
            if 'probabilities' in type_r:
                st.plotly_chart(predictor.create_probability_chart(type_r['probabilities']),
                               use_container_width=True)
    with col_c:
        st.markdown("#### 🌀 진화 군집 & GEI")
        if cluster_r and cluster_r.get('cluster_name'):
            st.markdown("**군집:** %s" % cluster_r['cluster_name'])
        gei = props.get('gei', props.get('gei_score'))
        if gei is not None:
            st.plotly_chart(predictor.create_evolution_gauge(gei), use_container_width=True)
            stage = calc.diagnose_evolution_stage(gei)
            st.info("**진화 단계:** %s (%s)" % (stage['stage'], stage['stage_en']))
    st.markdown("---")
    st.markdown("#### 🔍 피처 기여도 (XAI)")
    imp = predictor.get_feature_importance(props)
    if imp and 'top_features' in imp:
        st.plotly_chart(predictor.create_feature_importance_chart(imp), use_container_width=True)


def _render_report(props):
    predictor = load_predictor()
    calc = load_calculator()
    rg = ReportGenerator(os.path.join(PROJECT_ROOT, "output"))
    analysis = {
        'target_name': st.session_state.get('target_name', '대상 천체'),
        'analysis_datetime': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'input_mode': '이미지 ROI 분석',
        'ebv': props.get('ebv'), 'log_sfr': props.get('log_sfr'),
        'metallicity': props.get('metallicity'), 'metallicity_method': 'N2/O3N2',
        'log_nii_ha': props.get('log_nii_ha'), 'log_oiii_hb': props.get('log_oiii_hb'),
        'bpt_class': props.get('bpt_class', ''),
        'log_mass': props.get('log_mass', props.get('log_stellar_mass')),
        'color_ur': props.get('color_ur', props.get('color_u_r')),
        'z': props.get('z'),
    }
    if predictor.is_loaded:
        tr = predictor.predict_galaxy_type(props)
        cr = predictor.predict_evolution_cluster(props)
        if tr:
            analysis['predicted_type'] = tr.get('predicted_class', '')
            analysis['confidence'] = tr.get('confidence', 0)
            analysis['top_3_types'] = tr.get('top_3', [])
        if cr:
            analysis['evolution_cluster'] = cr.get('cluster_name', '')
    gei = props.get('gei', props.get('gei_score'))
    if gei is not None:
        analysis['gei_score'] = gei
        stage = calc.diagnose_evolution_stage(gei)
        analysis['evolution_stage'] = stage['stage']

    summary = rg.generate_summary_card(analysis)
    if summary and 'metrics' in summary:
        cols = st.columns(len(summary['metrics']))
        for i, m in enumerate(summary['metrics']):
            cols[i].metric(m.get('label', ''), m.get('value', '—'), delta=m.get('delta'))

    md = rg.generate_markdown(analysis)
    with st.expander("📄 보고서 미리보기", expanded=True):
        st.markdown(md)
    c1, c2 = st.columns(2)
    c1.download_button("📥 Markdown", md, "galaxy_report.md", "text/markdown",
                       use_container_width=True)
    c2.download_button("📥 HTML", rg.generate_html(md), "galaxy_report.html", "text/html",
                       use_container_width=True)


# ═══════════════════════════════════════════════════════
#                    메인
# ═══════════════════════════════════════════════════════
def main():
    init_session()

    st.markdown("""
    <div class="main-header">
        <h1>🌌 GalaxyEvolution Studio</h1>
        <p>이미지/FITS 업로드 → 영역 선택 → 자동 분석  |  Ginga-inspired 뷰어 + SDSS 빅데이터 AI 진단</p>
    </div>
    """, unsafe_allow_html=True)

    render_sidebar()
    render_step1()

    if st.session_state.get('analysis_complete'):
        if st.session_state.get('spectrum_df') is not None:
            _show_spectrum_and_analyze()
        else:
            _show_analysis_results()

    st.markdown("---")
    st.caption(
        "🌌 GalaxyEvolution Studio v3.0 | "
        "Ginga-inspired FITS viewer + ROI analysis | "
        "YSC 과학탐구대회 — 은하 진화 다차원 분석"
    )


if __name__ == "__main__":
    main()
