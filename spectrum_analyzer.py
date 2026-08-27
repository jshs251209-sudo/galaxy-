import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from scipy.signal import find_peaks
from PIL import Image

# Constants for Rest-frame wavelengths (Angstroms)
LINES = {
    "H_beta": 4861.33,
    "OIII_5007": 5006.84,
    "H_alpha": 6562.82,
    "NII_6584": 6583.41
}

def generate_mock_spectrum():
    # Wavelength range 4000 to 7000 A
    wavelength = np.linspace(4000, 7000, 3000)
    
    # Continuum + Noise
    continuum = 10 * np.exp(-(wavelength - 4000) / 2000)
    noise = np.random.normal(0, 0.5, len(wavelength))
    
    # Emission lines
    flux = continuum + noise
    
    def gaussian(x, mu, amp, sigma):
        return amp * np.exp(-((x - mu) ** 2) / (2 * sigma ** 2))
    
    # Add key lines
    flux += gaussian(wavelength, LINES["H_beta"], 15, 2.0)
    flux += gaussian(wavelength, LINES["OIII_5007"], 20, 2.0)
    flux += gaussian(wavelength, LINES["H_alpha"], 40, 2.0)
    flux += gaussian(wavelength, LINES["NII_6584"], 10, 2.0)
    
    return pd.DataFrame({"wavelength": wavelength, "flux": flux})

def extract_spectrum_from_image(image, min_wav=4000, max_wav=7000):
    # Convert image to grayscale numpy array
    gray = np.array(image.convert('L'))
    
    # Assume spectrum is vertical or horizontal.
    # We find the brightest line by summing axes
    col_sum = np.sum(gray, axis=0)
    row_sum = np.sum(gray, axis=1)
    
    # Check orientation (which axis has the sharper peak)
    if np.max(col_sum) / (np.median(col_sum) + 1e-5) > np.max(row_sum) / (np.median(row_sum) + 1e-5):
        # Vertical spectrum
        center = np.argmax(col_sum)
        slice_width = 10
        start = max(0, center - slice_width)
        end = min(gray.shape[1], center + slice_width)
        flux = np.sum(gray[:, start:end], axis=1)
    else:
        # Horizontal spectrum
        center = np.argmax(row_sum)
        slice_width = 10
        start = max(0, center - slice_width)
        end = min(gray.shape[0], center + slice_width)
        flux = np.sum(gray[start:end, :], axis=0)
        
    # Scale to wavelengths
    wavelength = np.linspace(min_wav, max_wav, len(flux))
    return pd.DataFrame({"wavelength": wavelength, "flux": flux})

def detect_lines(df):
    results = {}
    x = df["wavelength"].values
    y = df["flux"].values
    
    # Find peaks globally
    peaks, properties = find_peaks(y, height=5, prominence=2)
    peak_wavs = x[peaks]
    
    # Match with expected lines within a tolerance
    tolerance = 10  # Angstroms
    
    for name, expected_wav in LINES.items():
        # Find closest peak
        distances = np.abs(peak_wavs - expected_wav)
        if len(distances) > 0 and np.min(distances) <= tolerance:
            idx = np.argmin(distances)
            peak_idx = peaks[idx]
            
            # Simple integration (sum around peak)
            window = 10
            start_idx = max(0, peak_idx - window)
            end_idx = min(len(y), peak_idx + window)
            
            # Subtract continuum (simple linear interpolation)
            cont_level = (y[start_idx] + y[end_idx-1]) / 2
            line_flux = np.sum(y[start_idx:end_idx] - cont_level) * (x[1] - x[0])
            
            results[name] = {
                "detected_wavelength": x[peak_idx],
                "flux": line_flux if line_flux > 0 else 0
            }
        else:
            results[name] = None
            
    return results

def calculate_properties(lines_data):
    # N2 Index: log10([NII] / H_alpha)
    n2_ratio = None
    metallicity = None
    bpt_class = "알 수 없음 (Unknown)"
    
    if lines_data.get("H_alpha") and lines_data.get("NII_6584"):
        ha_flux = lines_data["H_alpha"]["flux"]
        nii_flux = lines_data["NII_6584"]["flux"]
        
        if ha_flux > 0:
            n2_ratio = np.log10(nii_flux / ha_flux)
            # Pettini & Pagel 2004: 12 + log(O/H) = 8.90 + 0.57 * N2
            metallicity = 8.90 + 0.57 * n2_ratio
            
            if n2_ratio < -0.2:
                bpt_class = "별생성 은하 (Star-Forming)"
            else:
                bpt_class = "활동은하핵 (AGN)"
                
    return n2_ratio, metallicity, bpt_class

st.set_page_config(page_title="천체 스펙트럼 분석기", layout="wide")

st.title("🌌 천체 스펙트럼 분석기 (Astronomical Spectrum Analyzer)")
st.write("1D 관측 스펙트럼(파장 vs 플럭스)을 업로드하거나 모의 스펙트럼을 생성하여 자동 분석을 수행합니다.")

st.sidebar.header("데이터 입력")
uploaded_file = st.sidebar.file_uploader("CSV 또는 이미지 파일 업로드", type=["csv", "jpg", "jpeg", "png"])
use_mock = st.sidebar.button("모의 스펙트럼 생성 (Generate Mock Spectrum)")

st.sidebar.subheader("사진 파장 보정 설정 (이미지 전용)")
img_min_wav = st.sidebar.number_input("최소 파장 (Å)", min_value=1000, max_value=10000, value=4000, step=100)
img_max_wav = st.sidebar.number_input("최대 파장 (Å)", min_value=1000, max_value=10000, value=7000, step=100)

if "spectrum_data" not in st.session_state:
    st.session_state.spectrum_data = None

if uploaded_file is not None:
    try:
        if uploaded_file.name.lower().endswith('.csv'):
            df = pd.read_csv(uploaded_file)
            if "wavelength" in df.columns and "flux" in df.columns:
                st.session_state.spectrum_data = df
                st.sidebar.success("CSV 파일 업로드 성공!")
            else:
                st.sidebar.error("CSV 파일에 'wavelength'와 'flux' 열이 필요합니다.")
        elif uploaded_file.name.lower().endswith(('.jpg', '.jpeg', '.png')):
            image = Image.open(uploaded_file)
            st.session_state.spectrum_data = extract_spectrum_from_image(image, img_min_wav, img_max_wav)
            st.sidebar.success("사진에서 스펙트럼 추출 성공!")
            st.sidebar.image(image, caption="업로드된 원본 이미지", use_column_width=True)
    except Exception as e:
        st.sidebar.error(f"파일을 처리하는 중 오류가 발생했습니다: {e}")

if use_mock:
    st.session_state.spectrum_data = generate_mock_spectrum()
    st.sidebar.success("모의 스펙트럼 생성 완료!")

if st.session_state.spectrum_data is not None:
    df = st.session_state.spectrum_data
    
    st.subheader("스펙트럼 시각화")
    fig = px.line(df, x="wavelength", y="flux", labels={"wavelength": "파장 (Å)", "flux": "플럭스 (Flux)"}, title="관측 스펙트럼")
    fig.update_layout(template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)
    
    if st.button("자동 분석 (Auto Analyze)"):
        st.subheader("🔍 분석 결과")
        
        with st.spinner("방출선 감지 및 플럭스 계산 중..."):
            lines_data = detect_lines(df)
            
            col1, col2, col3, col4 = st.columns(4)
            cols = [col1, col2, col3, col4]
            
            for i, (line, data) in enumerate(lines_data.items()):
                with cols[i]:
                    if data:
                        st.metric(label=f"{line} (Å)", value=f"{data['detected_wavelength']:.2f}", delta=f"플럭스: {data['flux']:.2f}")
                    else:
                        st.metric(label=f"{line} (Å)", value="미검출")
                        
            st.divider()
            
            st.subheader("⚗️ 화학 조성 및 BPT 분류")
            n2_ratio, metallicity, bpt_class = calculate_properties(lines_data)
            
            if metallicity is not None:
                c1, c2, c3 = st.columns(3)
                c1.info(f"**[NII]/Hα 비율 (N2 Index):** {n2_ratio:.3f}")
                c2.success(f"**금속함량 (12 + log(O/H)):** {metallicity:.3f} (Pettini & Pagel 2004)")
                c3.warning(f"**BPT 분류:** {bpt_class}")
            else:
                st.error("H-alpha 및 [NII] 방출선이 모두 검출되지 않아 물리량을 계산할 수 없습니다.")

else:
    st.info("왼쪽 사이드바에서 데이터를 업로드하거나 모의 스펙트럼을 생성해주세요.")
