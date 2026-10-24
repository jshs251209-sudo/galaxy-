"""
modules/gei_evolution_engine.py
================================================================================
차세대 통합 은하 진화 지수 (Unified Galaxy Evolution Index, GEI v2.0) 및
과거 모습 복원 · 미래 진화 궤적 예측 물리 엔진 (Past-Present-Future Trajectory Engine)

지원 기능:
1. 5대 핵심 물리 축 기반 통합 은하 진화 지수 (GEI v2.0) 산출:
   - S_quench : 별생성 소광도 (-log sSFR 기반)
   - S_mass   : 항성 질량 축적도 (log M_* 기반)
   - S_pop    : 항성종족 노화 및 화학적 성숙도 (색지수 u-r, D4000, 금속량 12+log(O/H) 결합)
   - S_struct : 구조적 표면질량밀도 (log Sigma_* = log(M_* / (2*pi*R_e^2)) 기반)
   - S_halo   : 암흑물질 헤일로 조립 및 동역학적 성숙도 (f_DM, log M_dyn, V_rot 기반)
2. 5단계 표준 은하 진화 단계 (Stage I ~ Stage V) 정밀 판별
3. 미분방정식(ODE) 기반 은하 과거 모습 복원 (-10 Gyr ~ 현재) 및 미래 진화 예측 (현재 ~ +10 Gyr)
4. 천문대 관측 물리량(겉보기등급/절대등급, 거리/적색편이, 시직경/물리반경, 회전속도/속도분산,
   H-alpha 플럭스/별생성률, 색지수 등) 부분 입력 시 결측 물리량 자동 유도
================================================================================
"""

import numpy as np
import pandas as pd

# 천체물리 상수 (kpc * (km/s)^2 / M_sun)
G_ASTRO = 4.3009e-6
T_UNIVERSE_GYR = 13.8  # 현재 우주 나이 (Gyr)


# ==============================================================================
# 1. 5단계 은하 진화 단계 (Evolutionary Stages) 정의
#    (포스터 5단계 구조도: 0.00~0.28 / 0.28~0.46 / 0.46~0.64 / 0.64~0.78 / 0.78~1.00)
# ==============================================================================
EVOLUTION_STAGES = [
    {
        "stage_id": 1,
        "code": "Stage I",
        "name_kr": "1단계: 원시 폭발적 별 생성기",
        "name_en": "Stage I: Primordial Starburst Phase",
        "gei_min": 0.00,
        "gei_max": 0.28,
        "color": "#06b6d4",  # Cyan
        "badge_bg": "#ecfeff",
        "key_features": ["가스 분율 ↑", "sSFR ↑", "u-r < 1.4"],
        "morphology_typical": "초기 조밀 은하 (Blue Nugget) / 불규칙·폭발적 별생성 은하 (Irregular / Starburst)",
        "past_summary": "암흑물질 미세 헤일로들이 최초 병합하며 원시 성간 가스 구름이 중력 수축을 막 시작한 태동기 상태였습니다.",
        "present_summary": "차가운 가스 분율(f_gas)이 매우 높고 비별생성률(sSFR)이 폭발적이며, 청색 색지수(u-r < 1.4)와 강한 Hα·[S II] 방출선이 지배하는 원시 폭발적 별 생성기입니다.",
        "future_summary": "풍부한 가스를 바탕으로 향후 수십억 년간 나선팔 원반을 확장하며 초기 은하 원반 성장기(2단계)로 진입할 것입니다."
    },
    {
        "stage_id": 2,
        "code": "Stage II",
        "name_kr": "2단계: 초기 은하 원반 성장기",
        "name_en": "Stage II: Early Galactic Disk Growth",
        "gei_min": 0.28,
        "gei_max": 0.46,
        "color": "#3b82f6",  # Royal Blue
        "badge_bg": "#eff6ff",
        "key_features": ["나선팔 원반 확장", "주계열 상단 별생성 활발"],
        "morphology_typical": "후기형 나선은하 (Sc / Sd / 마젤란형 나선은하) / 활발한 별생성 원반",
        "past_summary": "과거 수십억 년 전에는 높은 가스 분율과 낮은 색지수(u-r < 1.4)를 지닌 원시 폭발적 별 생성기(1단계)였습니다.",
        "present_summary": "나선팔 원반이 인사이드-아웃(Inside-Out)으로 활발히 확장되며, 은하 주계열(SFMS) 상단에서 별생성이 활발하게 일어나는 초기 원반 성장기입니다.",
        "future_summary": "중심 팽대부가 형성되고 가스 유입과 별생성률이 평형에 도달하면서 성숙 나선 구조 안정기(3단계)로 진화할 것입니다."
    },
    {
        "stage_id": 3,
        "code": "Stage III",
        "name_kr": "3단계: 성숙 나선 구조 안정기",
        "name_en": "Stage III: Mature Spiral Structure Equilibrium",
        "gei_min": 0.46,
        "gei_max": 0.64,
        "color": "#10b981",  # Emerald Green
        "badge_bg": "#ecfdf5",
        "key_features": ["원반과 팽대부 공존", "SFR, 가스유입 평형"],
        "morphology_typical": "정규 대형 나선은하 / 막대나선은하 (Sb / Sbc / SABb)",
        "past_summary": "초기 은하 원반 성장기(2단계)를 거치며 주계열 상단에서 나선팔 원반과 질량을 꾸준히 확장해 왔습니다.",
        "present_summary": "나선 원반과 중심 팽대부가 안정적으로 공존(B/T ≈ 0.2~0.35)하며, 별생성률(SFR)과 외부 가스 유입률이 동적 평형을 이룬 성숙 나선 구조 안정기입니다.",
        "future_summary": "향후 20~40억 년 내에 차가운 가스가 고갈되기 시작하고 중심 팽대부가 비대해지면서 별 생성 감쇠기(4단계)로 진입할 것입니다."
    },
    {
        "stage_id": 4,
        "code": "Stage IV",
        "name_kr": "4단계: 별 생성 감쇠기",
        "name_en": "Stage IV: Star Formation Quenching Transition",
        "gei_min": 0.64,
        "gei_max": 0.78,
        "color": "#f59e0b",  # Amber / Orange
        "badge_bg": "#fffbeb",
        "key_features": ["차가운 가스 고갈 시작", "중심 팽대부 비대", "별 생성 급감"],
        "morphology_typical": "조기형 나선은하 (Sa / Sab) / 렌즈형 은하 (S0) / 활동은하핵 (Seyfert·LINER)",
        "past_summary": "과거 30~60억 년 전에는 원반과 팽대부가 공존하며 SFR과 가스유입이 평형을 이루던 성숙 나선 구조 안정기(3단계)였습니다.",
        "present_summary": "차가운 가스가 고갈되기 시작하고 중심 팽대부가 비대해지며(B/T > 0.40), AGN 피드백과 헤일로 가열로 별 생성이 급감하는 별 생성 감쇠기(녹색 계곡)입니다.",
        "future_summary": "잔여 가스가 소진되면서 비별생성률이 log sSFR < -11.5 이하로 떨어져 소광 거대 타원 은하(5단계)로 정착할 것입니다."
    },
    {
        "stage_id": 5,
        "code": "Stage V",
        "name_kr": "5단계: 소광 거대 타원 은하",
        "name_en": "Stage V: Quenched Giant Elliptical Galaxy",
        "gei_min": 0.78,
        "gei_max": 1.00,
        "color": "#ef4444",  # Crimson Red
        "badge_bg": "#fef2f2",
        "key_features": ["log sSFR < -11.5", "거대 암흑물질 헤일로", "적색 계열"],
        "morphology_typical": "타원은하 (E0~E7) / 거대 중심은하 (cD) / 완전 소광 렌즈형 은하",
        "past_summary": "초기 폭발적 별 생성(1단계)과 은하 병합, 중심 팽대부 비대 및 별 생성 감쇠기(4단계)를 조기에 거치며 차가운 가스를 모두 소진했습니다.",
        "present_summary": "비별생성률이 극도로 낮고(log sSFR < -11.5), 거대 암흑물질 헤일로(log M_DM > 11.2)와 붉은 색지수(u-r > 2.4)를 지닌 적색 계열 소광 거대 타원 은하입니다.",
        "future_summary": "새로운 별 생성 없이 적색 계열에서 수동적 노화(Passive Evolution)와 건식 병합(Dry Merger)만을 이어갈 것입니다."
    }
]


# ==============================================================================
# 2. 천문대 관측 대표 은하 14종 벤치마크 데이터베이스
# ==============================================================================
OBSERVATORY_BENCHMARK_GALAXIES = {
    "LMC (대마젤란은하)": {
        "name": "LMC (대마젤란은하 / ESO 056-115)",
        "morphology": "SB(s)m (마젤란형 왜소 불규칙/나선은하)",
        "ra": 80.8942, "dec": -69.7561,
        "z": 0.0009, "dist_mpc": 0.05,
        "log_mstar": 9.15, "log_sfr": -0.15,
        "radius_kpc": 3.00, "v_rot": 72.0, "vel_disp": 25.0,
        "color_u_r": 1.32, "d4000": 1.15, "oh_metallicity": 8.38,
        "log_nii_ha": -0.95, "log_oiii_hb": 0.35,
        "description": "우리은하의 대표 위성은하이자 풍부한 가스와 타란툴라 성운(30 Doradus) 등 폭발적 별생성 영역을 보유한 Stage I 원시·왜소 별생성 은하."
    },
    "M31 (안드로메다 은하)": {
        "name": "M31 (안드로메다 은하 / NGC 224)",
        "morphology": "SA(s)b (조기형 거대 나선은하)",
        "ra": 10.6847, "dec": 41.2690,
        "z": 0.0010, "dist_mpc": 0.80,
        "log_mstar": 10.804, "log_sfr": -0.45,
        "radius_kpc": 12.02, "v_rot": 250.0, "vel_disp": 160.0,
        "color_u_r": 2.42, "d4000": 1.68, "oh_metallicity": 9.02,
        "log_nii_ha": -0.18, "log_oiii_hb": -0.05,
        "description": "천문대 관측 대표 국소은하군 최대 나선은하. 거대한 중심 팽대부와 완만한 별생성률로 현재 녹색 계곡(Stage IV)에 진입한 대표적 전이 은하."
    },
    "M33 (삼각형자리 은하)": {
        "name": "M33 (삼각형자리 은하 / NGC 598)",
        "morphology": "SA(s)cd (후기형 나선은하)",
        "ra": 23.4621, "dec": 30.6599,
        "z": 0.0006, "dist_mpc": 0.86,
        "log_mstar": 9.592, "log_sfr": -0.35,
        "radius_kpc": 5.51, "v_rot": 107.0, "vel_disp": 35.0,
        "color_u_r": 1.48, "d4000": 1.21, "oh_metallicity": 8.48,
        "log_nii_ha": -0.78, "log_oiii_hb": 0.18,
        "description": "팽대부가 거의 없는 순수 원반 후기형 나선은하. 가스가 풍부하고 암흑물질 비율(73.6%)이 높으며 활발히 원반을 키우는 초기 주계열 성장기(Stage II) 은하."
    },
    "M51a (소용돌이 은하)": {
        "name": "M51a (소용돌이 은하 / NGC 5194)",
        "morphology": "SA(s)bc pec (상호작용 정상 나선은하)",
        "ra": 202.4696, "dec": 47.1953,
        "z": 0.0015, "dist_mpc": 8.58,
        "log_mstar": 10.927, "log_sfr": 0.65,
        "radius_kpc": 16.05, "v_rot": 205.5, "vel_disp": 96.0,
        "color_u_r": 1.85, "d4000": 1.32, "oh_metallicity": 9.08,
        "log_nii_ha": -0.25, "log_oiii_hb": -0.12,
        "description": "동반은하 NGC 5195와의 중력 상호작용으로 나선팔을 따라 별생성이 활발히 일어나는 성숙 주계열 나선은하(Stage III)."
    },
    "M81 (보데 은하)": {
        "name": "M81 (보데 은하 / NGC 3031)",
        "morphology": "SA(s)ab (조기형 나선은하 / LINER)",
        "ra": 148.8882, "dec": 69.0653,
        "z": 0.0008, "dist_mpc": 3.63,
        "log_mstar": 10.687, "log_sfr": -0.40,
        "radius_kpc": 12.15, "v_rot": 244.2, "vel_disp": 162.0,
        "color_u_r": 2.38, "d4000": 1.64, "oh_metallicity": 8.98,
        "log_nii_ha": -0.05, "log_oiii_hb": 0.12,
        "description": "뚜렷한 중심 팽대부와 LINER 활동은하핵을 가진 조기형 나선은하로, 차가운 가스가 고갈되며 별 생성 감쇠기(Stage IV)에 진입한 은하."
    },
    "M82 (시가 은하 - 폭발적 별생성)": {
        "name": "M82 (시가 은하 / NGC 3034)",
        "morphology": "I0 / Starburst (폭발적 별생성 은하)",
        "ra": 148.9685, "dec": 69.6797,
        "z": 0.0007, "dist_mpc": 3.53,
        "log_mstar": 10.02, "log_sfr": 1.05,
        "radius_kpc": 3.80, "v_rot": 135.0, "vel_disp": 105.0,
        "color_u_r": 1.38, "d4000": 1.12, "oh_metallicity": 8.75,
        "log_nii_ha": -0.42, "log_oiii_hb": 0.25,
        "description": "M81과의 조석 상호작용으로 중심부에서 우리은하의 10배에 달하는 격렬한 별생성과 슈퍼윈드가 분출되는 폭발적 별생성기(Stage I~II) 은하."
    },
    "M87 (처녀자리 A 거대 타원은하)": {
        "name": "M87 (처녀자리 A / NGC 4486)",
        "morphology": "E+0-1 pec / cD (거대 타원은하 / Radio AGN)",
        "ra": 187.7059, "dec": 12.3911,
        "z": 0.00428, "dist_mpc": 16.4,
        "log_mstar": 11.78, "log_sfr": -1.85,
        "radius_kpc": 18.5, "v_rot": 480.0, "vel_disp": 320.0,
        "color_u_r": 2.88, "d4000": 1.98, "oh_metallicity": 9.18,
        "log_nii_ha": 0.18, "log_oiii_hb": 0.28,
        "description": "처녀자리 은하단 중심의 거대 타원은하(cD). 65억 태양질량 초대질량블랙홀 제트와 거대 암흑물질 헤일로를 지닌 진화 완료(Stage V) 대표 은하."
    },
    "NGC 4472 (M49 거대 타원은하)": {
        "name": "NGC 4472 (처녀자리 은하단 M49)",
        "morphology": "E2 / S0 (거대 타원은하)",
        "ra": 187.4450, "dec": 8.0004,
        "z": 0.0033, "dist_mpc": 16.7,
        "log_mstar": 11.62, "log_sfr": -1.55,
        "radius_kpc": 16.20, "v_rot": 410.0, "vel_disp": 295.0,
        "color_u_r": 2.78, "d4000": 1.94, "oh_metallicity": 9.15,
        "log_nii_ha": 0.15, "log_oiii_hb": 0.20,
        "description": "처녀자리 은하단에서 광도가 가장 밝은 거대 타원은하(M49)로, 별생성이 완전히 멈추고 노화된 항성종족과 거대 암흑물질 헤일로를 지닌 Stage V 대표 은하."
    },
    "M101 (바람개비 은하)": {
        "name": "M101 (바람개비 은하 / NGC 5457)",
        "morphology": "SAB(rs)cd (정면향 대형 나선은하)",
        "ra": 210.8023, "dec": 54.3489,
        "z": 0.0008, "dist_mpc": 6.85,
        "log_mstar": 10.651, "log_sfr": 0.46,
        "radius_kpc": 17.56, "v_rot": 210.6, "vel_disp": 65.0,
        "color_u_r": 1.65, "d4000": 1.28, "oh_metallicity": 8.85,
        "log_nii_ha": -0.52, "log_oiii_hb": 0.02,
        "description": "거대한 나선 원반과 높은 암흑물질 분율(75.2%), 풍부한 HII 영역을 지닌 전형적인 성숙 주계열 나선은하(Stage III)."
    },
    "NGC 3198 (표준 평탄 회전곡선 은하)": {
        "name": "NGC 3198 (암흑물질 표준 나선은하)",
        "morphology": "SB(rs)c (막대나선은하)",
        "ra": 154.9790, "dec": 45.5496,
        "z": 0.0022, "dist_mpc": 13.8,
        "log_mstar": 10.292, "log_sfr": 0.08,
        "radius_kpc": 16.70, "v_rot": 150.0, "vel_disp": 60.0,
        "color_u_r": 1.72, "d4000": 1.31, "oh_metallicity": 8.80,
        "log_nii_ha": -0.55, "log_oiii_hb": 0.05,
        "description": "30 kpc 외곽까지 150 km/s의 평탄 회전곡선을 유지하여 암흑물질 헤일로(광학반경 내 77.5%)의 존재를 증명한 표준 주계열 나선은하(Stage II~III)."
    },
    "NGC 2403 (중간질량 후기형 나선은하)": {
        "name": "NGC 2403 (기린자리 나선은하)",
        "morphology": "SAB(s)cd (후기형 나선은하)",
        "ra": 114.2142, "dec": 65.6025,
        "z": 0.0005, "dist_mpc": 3.18,
        "log_mstar": 9.820, "log_sfr": -0.12,
        "radius_kpc": 7.67, "v_rot": 114.6, "vel_disp": 42.0,
        "color_u_r": 1.54, "d4000": 1.24, "oh_metallicity": 8.56,
        "log_nii_ha": -0.68, "log_oiii_hb": 0.14,
        "description": "M33과 유사한 후기형 나선은하로, 활발한 H-alpha 방출선과 높은 암흑물질 분율(71.5%)을 보이는 초기 주계열 원반 성장기(Stage II) 은하."
    },
    "NGC 253 (조각가자리 은하)": {
        "name": "NGC 253 (조각가자리 은하)",
        "morphology": "SAB(s)c (폭발적 핵 별생성 나선은하)",
        "ra": 11.8880, "dec": -25.2882,
        "z": 0.0008, "dist_mpc": 3.56,
        "log_mstar": 10.677, "log_sfr": 0.68,
        "radius_kpc": 13.79, "v_rot": 218.2, "vel_disp": 110.0,
        "color_u_r": 1.92, "d4000": 1.36, "oh_metallicity": 8.96,
        "log_nii_ha": -0.30, "log_oiii_hb": -0.04,
        "description": "국소 우주에서 가장 밝은 적외선/별생성 나선은하 중 하나로, 성숙한 주계열 원반 안정기(Stage III)에 위치한 은하."
    },
    "우리은하 (Milky Way)": {
        "name": "우리은하 (Milky Way Galaxy)",
        "morphology": "SB(rs)bc (막대나선은하)",
        "ra": 266.4168, "dec": -29.0078,
        "z": 0.00001, "dist_mpc": 0.008,
        "log_mstar": 10.70, "log_sfr": 0.22,
        "radius_kpc": 14.0, "v_rot": 220.0, "vel_disp": 105.0,
        "color_u_r": 2.08, "d4000": 1.48, "oh_metallicity": 8.95,
        "log_nii_ha": -0.32, "log_oiii_hb": -0.08,
        "description": "태양계가 속한 막대나선은하. 성숙 주계열(Stage III) 후반부에 위치하며 향후 안드로메다(M31)와의 병합 및 가스 소진으로 녹색 계곡 진입 예정."
    },
    "CEERS-HighZ (JWST 초기우주 원시은하 z=5.2)": {
        "name": "CEERS-HighZ (JWST 초기우주 은하 z=5.2)",
        "morphology": "Compact Blue Nugget (초기우주 고밀도 원시은하)",
        "ra": 214.85, "dec": 52.88,
        "z": 5.20, "dist_mpc": 49500.0,
        "log_mstar": 9.35, "log_sfr": 1.15,
        "radius_kpc": 0.75, "v_rot": 122.0, "vel_disp": 85.0,
        "color_u_r": 0.95, "d4000": 1.04, "oh_metallicity": 8.05,
        "log_nii_ha": -1.15, "log_oiii_hb": 0.65,
        "description": "JWST CEERS가 포착한 적색편이 z=5.2 초기 우주 은하. 반경 0.75 kpc 내에 바리온이 고밀도로 수축(f_DM~12%)하여 폭발적 별생성을 겪는 원시 형성기(Stage I) 은하."
    }
}


# ==============================================================================
# 3. 우주론적 시간(Lookback Time) 및 결측 물리량 유도 함수
# ==============================================================================
def redshift_to_lookback_gyr(z):
    """적색편이 z로부터 우주 후퇴 시간(Lookback Time, Gyr) 및 당시 우주 나이(Cosmic Age, Gyr) 근사 계산 (Planck ΛCDM H0=70, Ωm=0.3, ΩΛ=0.7)"""
    z_arr = np.asarray(z, dtype=float)
    z_clip = np.clip(z_arr, 0.0, 20.0)
    # 정밀 해석적 근사식 (오차 < 1.5%)
    cosmic_age = T_UNIVERSE_GYR / (1.0 + z_clip) ** 1.18
    # 저적색편이 보정: t_LB ~ 13.8 * (1 - 1/(1+z)^1.18) -> H0^-1 z at small z
    t_lb = T_UNIVERSE_GYR - cosmic_age
    return t_lb, cosmic_age


def complete_galaxy_observables(inputs: dict) -> dict:
    """
    천문대 관측 또는 카탈로그에서 입력된 물리량 딕셔너리를 받아,
    입력되지 않은 부차적 물리량(동역학 질량, 암흑물질 질량/분율, 비별생성률, 표면밀도, 색지수, 금속량 등)을
    천체물리 스케일링 법칙으로 자동 완성하여 반환합니다.
    """
    if isinstance(inputs, str) and inputs in OBSERVATORY_BENCHMARK_GALAXIES:
        d = dict(OBSERVATORY_BENCHMARK_GALAXIES[inputs])
    elif isinstance(inputs, dict):
        d = dict(inputs)
    else:
        d = {}

    def _valid(val):
        if val is None:
            return None
        try:
            vf = float(val)
            return vf if np.isfinite(vf) else None
        except Exception:
            return None

    # 1. 적색편이 z 및 거리 DistMpc 상호 변환 (후퇴속도 v_rec / cz 지원 포함)
    z = _valid(d.get("z", None))
    dist_mpc = _valid(d.get("dist_mpc", None))
    v_rec = _valid(d.get("v_rec", d.get("recession_vel_kms", None)))
    if z is None and v_rec is not None and v_rec >= 0:
        z = v_rec / 299792.458
    if z is None and dist_mpc is not None and dist_mpc > 0:
        z = (70.0 * dist_mpc) / 299792.458
    elif dist_mpc is None and z is not None and z >= 0:
        dist_mpc = max(0.05, (299792.458 * z / 70.0) * (1.0 + 0.5 * z))
    if z is None or z < 0:
        z = 0.01
    if dist_mpc is None or dist_mpc <= 0:
        dist_mpc = 42.8
    d["z"] = float(z)
    d["dist_mpc"] = float(dist_mpc)

    t_lb, t_age = redshift_to_lookback_gyr(z)
    d["lookback_gyr"] = float(t_lb)
    d["cosmic_age_gyr"] = float(t_age)

    # 2. 항성 질량 log_mstar (절대등급 M_r 또는 겉보기등급 r/m_r이 주어졌을 때 유도 가능)
    log_mstar = _valid(d.get("log_mstar", None))
    if log_mstar is None:
        abs_mag_r = _valid(d.get("abs_mag_r", d.get("M_r", None)))
        app_mag_r = _valid(d.get("app_mag_r", d.get("m_r", d.get("apparent_mag_r", None))))
        if abs_mag_r is None and app_mag_r is not None:
            abs_mag_r = app_mag_r - 5.0 * np.log10(max(dist_mpc * 1e6, 10.0) / 10.0)
        if abs_mag_r is not None:
            # Bell+2003: log(M/L_r) = -0.42 + 0.35*(u-r) 또는 평균 M/L_r ~ 1.8 (+0.25 dex)
            ur_in = _valid(d.get("color_u_r", d.get("color_ur", None)))
            log_ml_r = (-0.42 + 0.35 * np.clip(ur_in, 0.5, 3.2)) if ur_in is not None else 0.25
            log_mstar = -0.4 * (abs_mag_r - 4.64) + log_ml_r
        else:
            log_mstar = 10.3
    d["log_mstar"] = float(np.clip(log_mstar, 6.5, 12.5))
    mstar_msun = 10.0 ** d["log_mstar"]
    d["mstar_msun"] = float(mstar_msun)

    # 3. 물리적 반경 radius_kpc (시직경 arcsec가 주어졌거나 결측 시 질량-크기 관계 유도)
    radius_kpc = _valid(d.get("radius_kpc", None))
    if radius_kpc is None or radius_kpc <= 0:
        radius_arcsec = _valid(d.get("radius_arcsec", d.get("theta_arcsec", d.get("angular_radius_arcsec", None))))
        if radius_arcsec is not None and radius_arcsec > 0:
            da_mpc = dist_mpc / ((1.0 + z) ** 2)
            radius_kpc = da_mpc * 1000.0 * (radius_arcsec / 206265.0)
        else:
            # Shen+2003 & van der Wel+2014 질량-반경-적색편이 스케일링
            radius_kpc = 4.5 * ((mstar_msun / 1e10) ** 0.24) * ((1.0 + z) ** (-0.75))
    d["radius_kpc"] = float(np.clip(radius_kpc, 0.1, 80.0))

    # 4. 회전속도 v_rot 및 속도분산 vel_disp
    v_rot = _valid(d.get("v_rot", None))
    vel_disp = _valid(d.get("vel_disp", None))
    if v_rot is None or v_rot <= 0:
        if vel_disp is not None and vel_disp > 0:
            v_rot = np.sqrt(2.0) * vel_disp
        else:
            # 툴리-피셔 + 고적색편이 비리얼 속도 관계
            v_tf = 10.0 ** (2.15 + 0.275 * (d["log_mstar"] - 10.0))
            v_baryon = np.sqrt(G_ASTRO * mstar_msun / max(d["radius_kpc"], 0.1))
            v_rot = np.sqrt(v_tf ** 2 + 0.25 * v_baryon ** 2)
    if vel_disp is None or vel_disp <= 0:
        vel_disp = v_rot / np.sqrt(2.0)
    d["v_rot"] = float(np.clip(v_rot, 15.0, 700.0))
    d["vel_disp"] = float(np.clip(vel_disp, 10.0, 500.0))

    # 5. 동역학 질량 M_dyn, 암흑물질 질량 M_DM, 암흑물질 비율 f_DM (%)
    # 우선순위: (1) log_mdm 직접 입력 -> (2) f_dm_percent 직접 입력 -> (3) NED 추세선 (log M_DM = 0.88 * log M_* + 1.35)
    ldm_in = _valid(d.get("log_mdm", None))
    fdm_in = _valid(d.get("f_dm_percent", None))
    if ldm_in is not None:
        log_mdm = float(np.clip(ldm_in, 4.0, 13.5))
        m_dm = 10.0 ** log_mdm
        m_dyn = m_dm + mstar_msun
        f_dm_pct = (m_dm / m_dyn) * 100.0
    elif fdm_in is not None:
        f_dm_pct = float(np.clip(fdm_in, 2.0, 96.0))
        m_dyn = mstar_msun / max(1.0 - f_dm_pct / 100.0, 0.03)
        m_dm = max(0.05 * mstar_msun, m_dyn - mstar_msun)
        log_mdm = float(np.clip(np.log10(m_dm), 4.0, 13.5))
    else:
        log_mdm = float(0.88 * d["log_mstar"] + 1.35)
        m_dm = 10.0 ** log_mdm
        m_dyn = m_dm + mstar_msun
        f_dm_pct = (m_dm / m_dyn) * 100.0

    d["log_mdyn"] = float(np.log10(max(m_dyn, 1e6)))
    d["log_mdm"] = float(log_mdm)
    d["mdyn_msun"] = float(m_dyn)
    d["mdm_msun"] = float(m_dm)
    d["f_dm_percent"] = float(f_dm_pct)

    # 6. 항성 표면질량밀도 log_sigma_star [M_sun / kpc^2]
    sigma_star = mstar_msun / (2.0 * np.pi * (d["radius_kpc"] ** 2))
    d["log_sigma_star"] = float(np.log10(max(sigma_star, 1e3)))

    # 7. 별생성률 log_sfr 및 비별생성률 log_ssfr
    log_sfr = _valid(d.get("log_sfr", None))
    log_ssfr_in = _valid(d.get("log_ssfr", None))
    if log_sfr is None:
        lha_tmp = _valid(d.get("log_lha", None))
        ha_flux = _valid(d.get("h_alpha_flux", None))
        if log_ssfr_in is not None:
            log_sfr = d["log_mstar"] + log_ssfr_in
        elif lha_tmp is not None and lha_tmp > 30:
            log_sfr = (lha_tmp - 40.05) / 0.72
        elif ha_flux is not None and ha_flux > 0:
            # Kennicutt (1998): SFR = 7.9e-42 * L_Ha
            d_l_cm = d["dist_mpc"] * 3.0857e24
            l_ha = 4.0 * np.pi * (d_l_cm ** 2) * (ha_flux * 1e-17)
            sfr_val = max(1e-4, 7.9e-42 * l_ha)
            log_sfr = np.log10(sfr_val)
        else:
            # 색지수 또는 주계열 경험식 기반 추정
            c_ur = _valid(d.get("color_u_r", d.get("color_ur", None)))
            if c_ur is None:
                c_ur = 2.0
            log_ssfr_est = -10.1 - 1.15 * (c_ur - 1.95) + 0.35 * np.log10(1.0 + z)
            log_sfr = d["log_mstar"] + log_ssfr_est
    d["log_sfr"] = float(np.clip(log_sfr, -4.0, 3.5))
    d["log_ssfr"] = float(d["log_sfr"] - d["log_mstar"])

    # 방출선 광도 (Hα, [S II] 6717, [O III]) 연동
    log_lha = _valid(d.get("log_lha", None))
    if log_lha is None:
        ha_flux = _valid(d.get("h_alpha_flux", None))
        if ha_flux is not None and ha_flux > 0:
            d_l_cm = d["dist_mpc"] * 3.0857e24
            log_lha = np.log10(max(1e35, 4.0 * np.pi * (d_l_cm ** 2) * (ha_flux * 1e-17)))
        else:
            log_lha = 40.05 + 0.72 * d["log_sfr"]
    log_lsii = _valid(d.get("log_lsii", None))
    if log_lsii is None:
        log_lsii = 39.38 + 0.58 * d["log_sfr"]
    log_loiii = _valid(d.get("log_loiii", None))
    if log_loiii is None:
        log_loiii = 39.08 + 0.26 * d["log_sfr"] + 0.12 * (d["log_mdm"] - 9.8)

    d["log_lha"] = float(log_lha)
    d["log_lsii"] = float(log_lsii)
    d["log_loiii"] = float(log_loiii)

    # 8. 광학 색지수 color_u_r, D_n(4000), 기체 금속량 12+log(O/H)
    color_u_r = _valid(d.get("color_u_r", d.get("color_ur", None)))
    if color_u_r is None:
        # sSFR과 질량으로부터 경험적 색지수 추정
        color_u_r = 2.05 - 0.58 * (d["log_ssfr"] + 10.2) + 0.18 * (d["log_mstar"] - 10.0)
    d["color_u_r"] = float(np.clip(color_u_r, 0.4, 3.6))

    d4000 = _valid(d.get("d4000", None))
    if d4000 is None:
        d4000 = 1.48 - 0.22 * (d["log_ssfr"] + 10.2) + 0.14 * (d["color_u_r"] - 2.0)
    d["d4000"] = float(np.clip(d4000, 0.90, 2.35))

    oh_met = _valid(d.get("oh_metallicity", d.get("metallicity_12_oh", d.get("metallicity", None))))
    if oh_met is None:
        log_nii_ha = _valid(d.get("log_nii_ha", None))
        if log_nii_ha is not None:
            oh_met = 8.90 + 0.57 * log_nii_ha
        else:
            # 기본 금속량 관계 (Fundamental Metallicity Relation, Mannucci+2010)
            mu_032 = d["log_mstar"] - 0.32 * d["log_sfr"]
            oh_met = 8.90 + 0.37 * (mu_032 - 10.0) - 0.12 * np.log10(1.0 + z)
    d["oh_metallicity"] = float(np.clip(oh_met, 7.40, 9.35))

    # 9. 포스터 5단계 구조도 대응 물리량 산출:
    #    - 차가운 가스 분율 f_gas (%) = M_gas / (M_* + M_gas) * 100 (Tacconi+2018 / Kennicutt-Schmidt 스케일링)
    #    - 중심 팽대부 대 전체 질량비 B/T (Bulge-to-Total Ratio, 원반 확장 vs 원반·팽대부 공존 vs 팽대부 비대)
    #    - 가스 유입 대 별생성 평형비 (Inflow / SFR Balance)
    mu_gas = 0.38 * (10.0 ** (0.55 * (d["log_ssfr"] + 10.0))) * ((1.0 + z) ** 0.6)
    f_gas_pct = float(np.clip((mu_gas / (1.0 + mu_gas)) * 100.0, 0.2, 88.0))
    log_mgas = float(d["log_mstar"] + np.log10(max(mu_gas, 1e-4)))

    # B/T (Gadotti 2009 / Bluck+2014):
    # Stage 1(<0.18) -> Stage 2(0.08~0.20 원반 확장) -> Stage 3(0.18~0.35 원반·팽대부 공존)
    # -> Stage 4(0.45~0.68 중심 팽대부 비대) -> Stage 5(>0.80 소광 거대 타원)
    q_bt = np.clip((-9.4 - d["log_ssfr"]) / 2.8, 0.0, 1.0) ** 1.45
    m_bt = np.clip((d["log_mstar"] - 9.2) / 2.6, 0.0, 1.0) ** 1.35
    gas_damp = max(0.25, 1.0 - 0.70 * (f_gas_pct / 100.0))
    sig_bt = (np.clip((d["log_sigma_star"] - 7.0) / 1.8, 0.0, 1.0) ** 1.25) * gas_damp
    bt_ratio = float(np.clip(0.04 + 0.52 * q_bt + 0.24 * m_bt + 0.18 * sig_bt, 0.03, 0.96))
    inflow_sfr_ratio = float(np.clip(1.0 + 0.35 * (d["log_ssfr"] + 10.1), 0.05, 2.20))

    d["f_gas_percent"] = round(f_gas_pct, 1)
    d["log_mgas"] = round(log_mgas, 3)
    d["bulge_to_total"] = round(bt_ratio, 3)
    d["inflow_sfr_ratio"] = round(inflow_sfr_ratio, 2)
    d["color_ur"] = d["color_u_r"]
    d["metallicity_12_oh"] = d["oh_metallicity"]

    # 입력 딕셔너리에 남아있을 수 있는 비유한값(NaN/inf) 정리
    for k, v in list(d.items()):
        if isinstance(v, (float, np.floating)) and not np.isfinite(v):
            d[k] = None

    return d


# ==============================================================================
# 4. 차세대 통합 은하 진화 지수 (Unified GEI v3) 계산 엔진
# ==============================================================================
def compute_unified_gei(obs: dict) -> dict:
    """
    완성된 물리량 딕셔너리 obs로부터 4대 핵심 물리 축 점수(S_mass, S_quench, S_halo, S_line)와
    통합 은하 진화 지수(GEI v3), 그리고 현재 진화 단계(Stage I ~ V)를 계산합니다.
    """
    d = complete_galaxy_observables(obs)

    # 1) 항성 질량 성숙도 S_mass (가중치 0.26)
    s_mass = np.clip((d["log_mstar"] - 7.5) / 4.3, 0.0, 1.0)

    # 2) 별생성 소광도 S_quench (가중치 0.28)
    s_quench = np.clip((-8.8 - d["log_ssfr"]) / 3.4, 0.0, 1.0)

    # 3) 암흑물질 헤일로 조립 성숙도 S_halo (S_DM, 가중치 0.19)
    s_halo = np.clip((d["log_mdm"] - 8.0) / 4.5, 0.0, 1.0)

    # 4) 방출선 소광·이온화 지수 S_line (가중치 0.27)
    s_ha = np.clip((30.6 - (d["log_lha"] - d["log_mstar"])) / 2.6, 0.0, 1.0)
    s_sii = np.clip((30.0 - (d["log_lsii"] - d["log_mstar"])) / 2.4, 0.0, 1.0)
    s_oiii = np.clip(((d["log_loiii"] - d["log_lha"]) + 1.0) / 1.3, 0.0, 1.0)
    s_line = float(np.clip(0.50 * s_ha + 0.30 * s_sii + 0.20 * s_oiii, 0.0, 1.0))

    # 보조 지표 (하위 호환성 유지)
    s_color = np.clip((d["color_u_r"] - 0.8) / 2.2, 0.0, 1.0)
    s_d4000 = np.clip((d["d4000"] - 1.0) / 1.1, 0.0, 1.0)
    s_metal = np.clip((d["oh_metallicity"] - 7.8) / 1.4, 0.0, 1.0)
    s_pop = 0.45 * s_color + 0.35 * s_d4000 + 0.20 * s_metal
    s_struct = np.clip((d["log_sigma_star"] - 6.2) / 3.8, 0.0, 1.0)

    # 통합 진화 지수 GEI v3 (0.000 ~ 1.000)
    gei_score = (
        0.26 * s_mass +
        0.28 * s_quench +
        0.19 * s_halo +
        0.27 * s_line
    )
    gei_score = float(np.clip(gei_score, 0.0, 1.0))

    # 진화 단계 판별
    stage_info = EVOLUTION_STAGES[-1]
    for st in EVOLUTION_STAGES:
        if st["gei_min"] <= gei_score < st["gei_max"] or (st["stage_id"] == 5 and gei_score >= st["gei_min"]):
            stage_info = st
            break

    # 단계 내부 진행률 (%)
    span = max(0.01, stage_info["gei_max"] - stage_info["gei_min"])
    stage_progress_pct = float(np.clip((gei_score - stage_info["gei_min"]) / span * 100.0, 0.0, 100.0))

    d["s_quench"] = float(s_quench)
    d["s_mass"] = float(s_mass)
    d["s_pop"] = float(s_pop)
    d["s_struct"] = float(s_struct)
    d["s_halo"] = float(s_halo)
    d["s_line"] = float(s_line)
    d["s_ha"] = float(s_ha)
    d["s_sii"] = float(s_sii)
    d["s_oiii"] = float(s_oiii)
    d["gei_score"] = gei_score
    d["gei_01"] = gei_score
    d["gei_100"] = round(gei_score * 100.0, 1)
    d["log_mass"] = d["log_mstar"]
    d["metallicity"] = d["oh_metallicity"]
    d["stage_id"] = stage_info["stage_id"]
    d["stage_code"] = stage_info["code"]
    d["stage_name"] = stage_info["name_kr"]
    d["stage_name_kr"] = stage_info["name_kr"]
    d["stage_name_en"] = stage_info["name_en"]
    d["stage_color"] = stage_info["color"]
    d["stage_badge_bg"] = stage_info["badge_bg"]
    d["stage_progress_pct"] = stage_progress_pct
    d["stage_key_features"] = stage_info.get("key_features", [])
    d["morphology_typical"] = stage_info["morphology_typical"]
    d["past_summary"] = stage_info["past_summary"]
    d["present_summary"] = stage_info["present_summary"]
    d["future_summary"] = stage_info["future_summary"]

    return d


# ==============================================================================
# 5. 벡터화된 대용량 카탈로그 GEI v3 일괄 계산 함수 (SDSS / NED-LVS / CEERS)
# ==============================================================================
def compute_gei_vectorized(
    log_mstar,
    log_sfr,
    radius_kpc,
    f_dm_percent,
    log_mdyn,
    z,
    color_u_r=None,
    d4000=None,
    oh_met=None
):
    """수만~수백만 개 은하 배열에 대해 고속 벡터 연산으로 통합 은하 진화 지수(GEI v3)와 진화 단계를 산출합니다."""
    log_mstar = np.asarray(log_mstar, dtype=float)
    log_sfr = np.asarray(log_sfr, dtype=float)
    radius_kpc = np.maximum(0.05, np.asarray(radius_kpc, dtype=float))
    f_dm_percent = np.asarray(f_dm_percent, dtype=float)
    log_mdyn = np.asarray(log_mdyn, dtype=float)
    z = np.maximum(0.0, np.asarray(z, dtype=float))

    log_ssfr = log_sfr - log_mstar
    log_sigma_star = log_mstar - np.log10(2.0 * np.pi * (radius_kpc ** 2))
    log_mdm = 0.88 * log_mstar + 1.35

    log_lha = 40.05 + 0.72 * log_sfr
    log_lsii = 39.38 + 0.58 * log_sfr
    log_loiii = 39.08 + 0.26 * log_sfr + 0.12 * (log_mdm - 9.8)

    s_mass = np.clip((log_mstar - 7.5) / 4.3, 0.0, 1.0)
    s_quench = np.clip((-8.8 - log_ssfr) / 3.4, 0.0, 1.0)
    s_halo = np.clip((log_mdm - 8.0) / 4.5, 0.0, 1.0)
    s_ha = np.clip((30.6 - (log_lha - log_mstar)) / 2.6, 0.0, 1.0)
    s_sii = np.clip((30.0 - (log_lsii - log_mstar)) / 2.4, 0.0, 1.0)
    s_oiii = np.clip(((log_loiii - log_lha) + 1.0) / 1.3, 0.0, 1.0)
    s_line = np.clip(0.50 * s_ha + 0.30 * s_sii + 0.20 * s_oiii, 0.0, 1.0)

    gei = np.clip(
        0.26 * s_mass + 0.28 * s_quench + 0.19 * s_halo + 0.27 * s_line,
        0.0, 1.0
    )

    stage_ids = np.ones_like(gei, dtype=int)
    stage_ids = np.where(gei >= 0.28, 2, stage_ids)
    stage_ids = np.where(gei >= 0.46, 3, stage_ids)
    stage_ids = np.where(gei >= 0.64, 4, stage_ids)
    stage_ids = np.where(gei >= 0.78, 5, stage_ids)

    return gei, stage_ids, log_ssfr, log_sigma_star


# ==============================================================================
# 6. 은하 과거 모습 복원 및 미래 진화 예측 시뮬레이터 (Past & Future Trajectory)
# ==============================================================================
def simulate_galaxy_evolution_trajectory(obs: dict, dt_steps_gyr=None) -> dict:
    """
    현재 관측된 은하의 물리량을 초기 조건(dt = 0 Gyr)으로 하여,
    과거(-10 Gyr ~ 현재)의 모습을 역추적 복원하고 미래(현재 ~ +10 Gyr)의 진화 경로를
    물리 미분방정식(가스 소진/별생성 감쇠, 항성질량 적분, 인사이드-아웃 반경 성장,
    암흑물질 헤일로 조립, 화학적 농축)으로 계산합니다.
    """
    cur = compute_unified_gei(obs)
    t_age_now = cur["cosmic_age_gyr"]

    if dt_steps_gyr is None:
        # 과거(은하 형성 초기부터) ~ 현재(0) ~ 미래(+10 Gyr)
        raw_steps = [-10.0, -8.0, -6.0, -4.0, -2.0, -1.0, 0.0, 1.0, 2.0, 4.0, 6.0, 8.0, 10.0]
    else:
        raw_steps = list(dt_steps_gyr)

    # 은하 형성 최소 우주 나이 (~0.55 Gyr, z ~ 9) 보장
    min_dt = -(max(0.6, t_age_now - 0.55))
    valid_dts = sorted(list(set([max(min_dt, float(dt)) for dt in raw_steps])))
    if 0.0 not in valid_dts:
        valid_dts.append(0.0)
        valid_dts.sort()

    # 은하의 소광 시간척도 tau_quench (Gyr) 계산:
    # 고질량 은하일수록, 그리고 이미 녹색계곡/소광 단계에 가까울수록 소광이 빠름 (Downsizing)
    m_ratio = (10.0 ** (cur["log_mstar"] - 10.3))
    tau_quench = np.clip(3.8 * (m_ratio ** (-0.28)), 1.4, 6.5)
    if cur["log_ssfr"] < -10.5:
        tau_quench *= 0.75  # 이미 소광 진행 중인 은하는 잔여 가스 빠르게 소진

    # 미세 시간 격자 (dt_fine: min_dt ~ +10.0 Gyr, 간격 0.1 Gyr) 적분
    dt_grid = np.linspace(min_dt, max(valid_dts), 250)
    idx_zero = int(np.argmin(np.abs(dt_grid - 0.0)))
    dt_grid[idx_zero] = 0.0

    # 각 시간 격자에서의 SFR(t) 및 M_*(t) 계산
    # Delayed-tau 형태: SFR(t) ~ ((t_age) / t_age_now)^0.8 * exp(-dt / tau_quench)
    t_cosmic = np.maximum(0.45, t_age_now + dt_grid)
    sfr_now = 10.0 ** cur["log_sfr"]
    mstar_now = 10.0 ** cur["log_mstar"]

    # 과거/미래 비별생성률 및 별생성률 변화 모델
    sfr_grid = np.zeros_like(dt_grid)
    mstar_grid = np.zeros_like(dt_grid)
    sfr_grid[idx_zero] = sfr_now
    mstar_grid[idx_zero] = mstar_now

    # 항성 질량 환원율 (초신성/항성풍 질량 손실 R_return = 0.40)
    r_return = 0.40

    # 미래 방향 적분 (idx_zero -> 끝)
    for i in range(idx_zero + 1, len(dt_grid)):
        dt_step = dt_grid[i] - dt_grid[i - 1]  # Gyr (10^9 yr)
        # 시간에 따른 가스 고갈에 의한 SFR 감쇠
        decay = np.exp(-dt_step / tau_quench)
        sfr_grid[i] = max(1e-4, sfr_grid[i - 1] * decay)
        # 질량 증가분 (SFR [M_sun/yr] * dt [Gyr] * 1e9 * (1 - R_return)) + 소규모 병합(완만한 성장)
        dm_sf = (1.0 - r_return) * 0.5 * (sfr_grid[i - 1] + sfr_grid[i]) * (dt_step * 1e9)
        dm_merger = mstar_grid[i - 1] * 0.012 * dt_step  # 1.2% per Gyr minor merger accretion
        mstar_grid[i] = mstar_grid[i - 1] + dm_sf + dm_merger

    # 과거 방향 역적분 (idx_zero -> 0)
    for i in range(idx_zero - 1, -1, -1):
        dt_step = dt_grid[i + 1] - dt_grid[i]  # 양수 Gyr
        # 과거에는 우주 가스 유입률이 높았으나 은하 질량이 작았음
        t_ratio = (t_cosmic[i] / t_cosmic[i + 1]) ** 0.55
        growth_boost = np.exp(min(dt_step / (tau_quench * 1.25), 0.25))
        # 과거 질량 감소분 (단계당 최대 질량 감소율 제한으로 고적색편이 폭발적 별생성 은하의 불연속 절벽 방지)
        dm_sf_raw = (1.0 - r_return) * sfr_grid[i + 1] * (dt_step * 1e9)
        max_dm_step = 0.16 * mstar_grid[i + 1] * (dt_step / max(t_cosmic[i + 1], 0.6))
        dm_sf = min(dm_sf_raw, max_dm_step)
        m_min = max(1e7, mstar_now * 0.05 * ((t_cosmic[i] / t_age_now) ** 1.2))
        mstar_grid[i] = max(m_min, mstar_grid[i + 1] - dm_sf)

        mass_scale = (mstar_grid[i] / max(mstar_grid[i + 1], 1e6)) ** 0.65
        sfr_prev = sfr_grid[i + 1] * t_ratio * growth_boost * mass_scale
        # 하한선을 min(sfr_now * 0.2, mstar * 1e-14)로 설정하여 log_ssfr < -12인 소광 타원은하(M87 등)의 dt=0 불연속 점프 방지
        min_sfr_allowed = max(1e-4, min(sfr_now * 0.2, mstar_grid[i] * 1e-14))
        max_sfr_allowed = max(0.05, mstar_grid[i] * (10.0 ** (-8.15)))
        sfr_grid[i] = np.clip(sfr_prev, min_sfr_allowed, max_sfr_allowed)

    # 선택된 valid_dts 시점들에 대한 전체 물리량 및 GEI 산출
    records = []
    for dt_val in valid_dts:
        idx = int(np.argmin(np.abs(dt_grid - dt_val)))
        t_c = float(t_cosmic[idx])
        # 해당 우주 나이에 대응하는 유효 적색편이 z_eff
        z_eff = max(0.0, (T_UNIVERSE_GYR / max(t_c, 0.35)) ** (1.0 / 1.18) - 1.0)
        if dt_val > 0:
            z_eff = 0.0  # 미래 우주는 z=0 기준 이후 진화

        m_t = float(mstar_grid[idx])
        sfr_t = float(sfr_grid[idx])
        log_m_t = np.log10(m_t)
        log_sfr_t = np.log10(sfr_t)
        log_ssfr_t = log_sfr_t - log_m_t

        # 물리적 반경 R_e(t) 진화:
        # 과거 고적색편이에서는 작고 밀집된(Compact) 형태였고, 질량 성장 및 시간 경과에 따라 Inside-Out 확장
        mass_factor = (m_t / mstar_now) ** 0.28
        time_factor = (t_c / t_age_now) ** 0.35
        r_t = cur["radius_kpc"] * mass_factor * time_factor
        r_t = float(np.clip(r_t, 0.25, 65.0))

        # 암흑물질 분율 f_DM(t) 진화:
        # 초기 우주에서는 바리온 중심 수축(Compaction)으로 유효반경 내 f_DM이 낮고,
        # 시간이 흐르면서 외곽 원반이 커지고 암흑물질 헤일로가 조립되며 f_DM이 증가
        if dt_val < 0:
            fdm_t = cur["f_dm_percent"] * ((t_c / t_age_now) ** 0.48)
        else:
            # 미래에는 헤일로 비리얼화 및 외곽 확장으로 완만히 증가 후 포화
            fdm_t = cur["f_dm_percent"] + (82.0 - cur["f_dm_percent"]) * (1.0 - np.exp(-dt_val / 12.0)) * 0.45
        fdm_t = float(np.clip(fdm_t, 6.0, 92.0))

        mdyn_t = m_t / max(1.0 - fdm_t / 100.0, 0.05)
        vrot_t = float(np.sqrt(G_ASTRO * mdyn_t / max(r_t, 0.2)))

        # 색지수, D4000, 금속량의 시간 진화
        delta_ssfr = log_ssfr_t - cur["log_ssfr"]
        delta_m = log_m_t - cur["log_mstar"]
        color_t = float(np.clip(cur["color_u_r"] - 0.52 * delta_ssfr + 0.15 * delta_m + 0.03 * dt_val, 0.5, 3.3))
        d4000_t = float(np.clip(cur["d4000"] - 0.19 * delta_ssfr + 0.025 * dt_val, 0.95, 2.25))
        oh_t = float(np.clip(cur["oh_metallicity"] + 0.32 * delta_m + 0.015 * dt_val, 7.50, 9.30))

        snap = compute_unified_gei({
            "z": z_eff,
            "log_mstar": log_m_t,
            "log_sfr": log_sfr_t,
            "radius_kpc": r_t,
            "v_rot": vrot_t,
            "f_dm_percent": fdm_t,
            "color_u_r": color_t,
            "d4000": d4000_t,
            "oh_metallicity": oh_t
        })
        snap["dt_gyr"] = round(float(dt_val), 2)
        snap["cosmic_age_t_gyr"] = round(t_c, 2)
        if dt_val < -0.01:
            snap["epoch_label"] = f"과거 {abs(dt_val):.0f} Gyr 전"
        elif dt_val > 0.01:
            snap["epoch_label"] = f"미래 +{dt_val:.0f} Gyr 후"
        else:
            snap["epoch_label"] = "현재 관측 시점 (0 Gyr)"
        records.append(snap)

    traj_df = pd.DataFrame(records)

    # 향후 별 생성 감쇠기(Stage IV, GEI >= 0.64) 및 소광 거대 타원 은하(Stage V, GEI >= 0.78) 도달 예상 시간 산출
    future_rows = traj_df[traj_df["dt_gyr"] >= 0.0]
    gv_rows = future_rows[future_rows["gei_score"] >= 0.64]
    quench_rows = future_rows[future_rows["gei_score"] >= 0.78]

    if cur["gei_score"] >= 0.64:
        t_to_gv_str = "이미 진입 완료 (현재 Stage IV~V)"
    elif len(gv_rows) > 0:
        t_to_gv_str = f"약 +{gv_rows.iloc[0]['dt_gyr']:.1f} Gyr 후 진입 예상"
    else:
        t_to_gv_str = "향후 +10 Gyr 이후 진입 예상 (장기 별생성 지속)"

    if cur["gei_score"] >= 0.78:
        t_to_quench_str = "이미 진화 완료 (현재 Stage V 적색 계열)"
    elif len(quench_rows) > 0:
        t_to_quench_str = f"약 +{quench_rows.iloc[0]['dt_gyr']:.1f} Gyr 후 완전 소광 예상"
    else:
        t_to_quench_str = f"소광 시간척도 τ ~ {tau_quench:.1f} Gyr로 서서히 감쇠"

    # 과거 대표 시점 (-6 Gyr 또는 가장 초기 시점)과 미래 대표 시점 (+6 Gyr) 요약 추출
    past_rep = traj_df.iloc[0].to_dict()
    for r_row in records:
        if -6.5 <= r_row["dt_gyr"] <= -3.5:
            past_rep = r_row
            break
    future_rep = traj_df.iloc[-1].to_dict()
    for r_row in records:
        if 4.5 <= r_row["dt_gyr"] <= 6.5:
            future_rep = r_row
            break

    narrative = {
        "current": cur,
        "past_representative": past_rep,
        "future_representative": future_rep,
        "tau_quench_gyr": round(float(tau_quench), 2),
        "time_to_green_valley": t_to_gv_str,
        "time_to_full_quenching": t_to_quench_str,
        "past_narrative_kr": (
            f"[{past_rep['epoch_label']} (우주 나이 {past_rep['cosmic_age_t_gyr']:.1f} Gyr)] "
            f"항성 질량 log(M*)={past_rep['log_mstar']:.2f}, 반경 R={past_rep['radius_kpc']:.2f} kpc의 "
            f"더 작고 조밀한 상태였으며, 별생성률 log(SFR)={past_rep['log_sfr']:.2f}, "
            f"암흑물질 비율 f_DM={past_rep['f_dm_percent']:.1f}%, 진화 지수 GEI={past_rep['gei_score']:.3f} "
            f"({past_rep['stage_name_kr']}) 단계에 있었습니다."
        ),
        "present_narrative_kr": (
            f"[현재 관측 상태] 통합 은하 진화 지수 GEI = {cur['gei_score']:.3f} (100점 만점 기준 {cur['gei_100']:.1f}점)으로 "
            f"'{cur['stage_name_kr']}' (단계 내 진행도 {cur['stage_progress_pct']:.1f}%)에 해당합니다. "
            f"비별생성률 log(sSFR)={cur['log_ssfr']:.2f} yr^-1, 표면질량밀도 log(Σ*)={cur['log_sigma_star']:.2f}, "
            f"암흑물질 분율 f_DM={cur['f_dm_percent']:.1f}%를 나타냅니다."
        ),
        "future_narrative_kr": (
            f"[{future_rep['epoch_label']}] 가스 소모(소광 시간척도 τ~{tau_quench:.1f} Gyr)와 항성 질량 축적을 거쳐 "
            f"항성 질량 log(M*)={future_rep['log_mstar']:.2f}, 별생성률 log(SFR)={future_rep['log_sfr']:.2f}, "
            f"반경 R={future_rep['radius_kpc']:.2f} kpc, 색지수 (u-r)={future_rep['color_u_r']:.2f}, "
            f"진화 지수 GEI={future_rep['gei_score']:.3f} ({future_rep['stage_name_kr']}) 상태로 진화할 것으로 예측됩니다."
        )
    }

    return {
        "current": cur,
        "trajectory_df": traj_df,
        "narrative": narrative
    }
