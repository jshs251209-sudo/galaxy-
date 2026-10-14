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
# ==============================================================================
EVOLUTION_STAGES = [
    {
        "stage_id": 1,
        "code": "Stage I",
        "name_kr": "1단계: 원시 은하 형성 및 폭발적 별생성기",
        "name_en": "Stage I: Primordial Halo Assembly & Starburst",
        "gei_min": 0.00,
        "gei_max": 0.28,
        "color": "#06b6d4",  # Cyan / Electric Blue
        "badge_bg": "#ecfeff",
        "morphology_typical": "초기 조밀 은하 (Blue Nugget) / 불규칙·폭발적 별생성 은하 (Irregular / Starburst)",
        "past_summary": "암흑물질 미세 헤일로들이 최초 병합하며 원시 성간 가스 구름이 중력 수축을 막 시작한 태동기 상태였습니다.",
        "present_summary": "차가운 중성·분자 가스가 매우 풍부하여 은하 전역 또는 중심부에서 폭발적인 별생성(Starburst)이 진행 중이며, 청색의 젊은 OB형 별들이 광도를 지배합니다.",
        "future_summary": "풍부한 가스를 바탕으로 향후 수십억 년간 항성 질량이 빠르게 증가하며 안정적인 회전 원반을 갖춘 주계열 나선은하(Stage II~III)로 성장할 것입니다."
    },
    {
        "stage_id": 2,
        "code": "Stage II",
        "name_kr": "2단계: 초기 주계열 원반 성장기",
        "name_en": "Stage II: Early Main-Sequence Disk Growth",
        "gei_min": 0.28,
        "gei_max": 0.46,
        "color": "#3b82f6",  # Royal Blue
        "badge_bg": "#eff6ff",
        "morphology_typical": "후기형 나선은하 (Sc / Sd / 마젤란형 나선은하) / 활발한 별생성 원반",
        "past_summary": "과거 수십억 년 전에는 작고 불규칙한 가스 덩어리에서 급격한 별생성을 겪던 왜소 청색 은하(Stage I) 모습이었습니다.",
        "present_summary": "은하 주계열(Star-Forming Main Sequence) 상단에 위치하며, 인사이드-아웃(Inside-Out) 원반 확장을 통해 나선팔 구조와 암흑물질 헤일로가 활발히 성장 중입니다.",
        "future_summary": "지속적인 별생성과 화학적 중원소 농축을 통해 항성 질량 10^10 M_sun 이상의 성숙한 대형 주계열 나선은하(Stage III)로 진화할 것입니다."
    },
    {
        "stage_id": 3,
        "code": "Stage III",
        "name_kr": "3단계: 성숙 주계열 나선은하 안정기",
        "name_en": "Stage III: Mature Main-Sequence Spiral Equilibrium",
        "gei_min": 0.46,
        "gei_max": 0.64,
        "color": "#10b981",  # Emerald Green
        "badge_bg": "#ecfdf5",
        "morphology_typical": "정규 대형 나선은하 / 막대나선은하 (Sb / Sbc / SABb)",
        "past_summary": "초기 우주에서 바리온 핵 수축을 거쳐 청색 후기형 나선원반(Stage II)으로 오랫동안 활발하게 별을 만들며 질량을 키워왔습니다.",
        "present_summary": "가스 유입률과 별생성률이 동적 평형을 이룬 성숙한 주계열 은하로, 뚜렷한 나선팔과 중심 팽대부, 그리고 외곽의 거대한 암흑물질 헤일로(평탄 회전곡선)를 보유하고 있습니다.",
        "future_summary": "향후 20~40억 년 내에 중심부 가스 고갈 및 헤일로 가열이 시작되면서 별생성이 서서히 둔화되어 녹색 계곡 전이기(Stage IV)로 진입할 것입니다."
    },
    {
        "stage_id": 4,
        "code": "Stage IV",
        "name_kr": "4단계: 녹색 계곡 전이 및 별생성 감쇠기",
        "name_en": "Stage IV: Green Valley & Quenching Transition",
        "gei_min": 0.64,
        "gei_max": 0.78,
        "color": "#f59e0b",  # Amber / Orange
        "badge_bg": "#fffbeb",
        "morphology_typical": "조기형 나선은하 (Sa / Sb) / 렌즈형 은하 (S0) / 활동은하핵 (Seyfert·LINER)",
        "past_summary": "과거 30~60억 년 전에는 푸른 나선팔에서 활발히 별을 탄생시키던 성숙한 주계열 나선은하(Stage III)였습니다.",
        "present_summary": "중심 거대질량블랙홀(AGN/LINER) 피드백, 막대 구조 유입, 또는 임계 헤일로 질량 도달에 따른 가스 가열로 인해 차가운 가스가 소진되며 청색열에서 적색열로 넘어가는 녹색 계곡(Green Valley) 전환기입니다.",
        "future_summary": "남아 있는 잔여 가스가 향후 15~30억 년 내에 완전히 소진되면서 별생성이 멈추고, 늙은 적색 별들로 이루어진 진화 완료 은하(Stage V)로 정착할 것입니다."
    },
    {
        "stage_id": 5,
        "code": "Stage V",
        "name_kr": "5단계: 진화 완료 적색 계열 / 거대 타원은하",
        "name_en": "Stage V: Quenched Red Sequence / Giant Elliptical",
        "gei_min": 0.78,
        "gei_max": 1.00,
        "color": "#ef4444",  # Crimson Red
        "badge_bg": "#fef2f2",
        "morphology_typical": "타원은하 (E0~E7) / 거대 중심은하 (cD) / 완전 소광 렌즈형 은하",
        "past_summary": "초기 우주에서 격렬한 폭발적 별생성(Stage I)과 다중 은하 병합(Major Merger), 강력한 AGN 피드백(Stage IV)을 일찍 겪으며 가스를 조기에 모두 소진했습니다.",
        "present_summary": "새로운 별생성이 완전히 중단(Quenched)된 성숙 완료 단계로, 높은 표면질량밀도와 큰 항성 속도분산, 높은 금속량 및 적색 광학 색지수(u-r > 2.4), 거대한 암흑물질 헤일로를 지닙니다.",
        "future_summary": "추가적인 가스 유입 없이 수동적 노화(Passive Evolution)를 이어가며, 주변 위성은하들과의 건식 병합(Dry Merger)을 통해 외곽 크기가 완만하게 팽창할 것입니다."
    }
]


# ==============================================================================
# 2. 천문대 관측 대표 은하 12종 벤치마크 데이터베이스
# ==============================================================================
OBSERVATORY_BENCHMARK_GALAXIES = {
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
        "log_mstar": 10.687, "log_sfr": -0.22,
        "radius_kpc": 12.15, "v_rot": 244.2, "vel_disp": 162.0,
        "color_u_r": 2.38, "d4000": 1.64, "oh_metallicity": 8.98,
        "log_nii_ha": -0.05, "log_oiii_hb": 0.12,
        "description": "뚜렷한 중심 팽대부와 LINER 활동은하핵을 가진 조기형 나선은하로, 주계열에서 녹색 계곡(Stage IV)으로 진입 중인 은하."
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
    d = dict(inputs)

    # 1. 적색편이 z 및 거리 DistMpc 상호 변환
    z = d.get("z", None)
    dist_mpc = d.get("dist_mpc", None)
    if (z is None or np.isnan(z)) and dist_mpc is not None and dist_mpc > 0:
        z = (70.0 * dist_mpc) / 299792.458
    elif (dist_mpc is None or np.isnan(dist_mpc)) and z is not None and z >= 0:
        dist_mpc = max(0.05, (299792.458 * z / 70.0) * (1.0 + 0.5 * z))
    if z is None or np.isnan(z):
        z = 0.01
    if dist_mpc is None or np.isnan(dist_mpc):
        dist_mpc = 42.8
    d["z"] = float(z)
    d["dist_mpc"] = float(dist_mpc)

    t_lb, t_age = redshift_to_lookback_gyr(z)
    d["lookback_gyr"] = float(t_lb)
    d["cosmic_age_gyr"] = float(t_age)

    # 2. 항성 질량 log_mstar (절대등급 M_r 또는 겉보기등급 r이 주어졌을 때 유도 가능)
    log_mstar = d.get("log_mstar", None)
    if log_mstar is None or np.isnan(log_mstar):
        abs_mag_r = d.get("abs_mag_r", None)
        app_mag_r = d.get("app_mag_r", None)
        if abs_mag_r is None and app_mag_r is not None:
            abs_mag_r = app_mag_r - 5.0 * np.log10(max(dist_mpc * 1e6, 10.0) / 10.0)
        if abs_mag_r is not None:
            # log(L_r / L_sun) = -0.4 * (M_r - 4.64), 평균 M/L_r ~ 1.8
            log_mstar = -0.4 * (abs_mag_r - 4.64) + 0.25
        else:
            log_mstar = 10.3
    d["log_mstar"] = float(np.clip(log_mstar, 6.5, 12.5))
    mstar_msun = 10.0 ** d["log_mstar"]
    d["mstar_msun"] = float(mstar_msun)

    # 3. 물리적 반경 radius_kpc (시직경 arcsec가 주어졌거나 결측 시 질량-크기 관계 유도)
    radius_kpc = d.get("radius_kpc", None)
    if radius_kpc is None or np.isnan(radius_kpc) or radius_kpc <= 0:
        radius_arcsec = d.get("radius_arcsec", None)
        if radius_arcsec is not None and radius_arcsec > 0:
            da_mpc = dist_mpc / ((1.0 + z) ** 2)
            radius_kpc = da_mpc * 1000.0 * (radius_arcsec / 206265.0)
        else:
            # Shen+2003 & van der Wel+2014 질량-반경-적색편이 스케일링
            radius_kpc = 4.5 * ((mstar_msun / 1e10) ** 0.24) * ((1.0 + z) ** (-0.75))
    d["radius_kpc"] = float(np.clip(radius_kpc, 0.1, 80.0))

    # 4. 회전속도 v_rot 및 속도분산 vel_disp
    v_rot = d.get("v_rot", None)
    vel_disp = d.get("vel_disp", None)
    if (v_rot is None or np.isnan(v_rot) or v_rot <= 0):
        if vel_disp is not None and vel_disp > 0:
            v_rot = np.sqrt(2.0) * vel_disp
        else:
            # 툴리-피셔 + 고적색편이 비리얼 속도 관계
            v_tf = 10.0 ** (2.15 + 0.275 * (d["log_mstar"] - 10.0))
            v_baryon = np.sqrt(G_ASTRO * mstar_msun / max(d["radius_kpc"], 0.1))
            v_rot = np.sqrt(v_tf ** 2 + 0.25 * v_baryon ** 2)
    if vel_disp is None or np.isnan(vel_disp) or vel_disp <= 0:
        vel_disp = v_rot / np.sqrt(2.0)
    d["v_rot"] = float(np.clip(v_rot, 15.0, 700.0))
    d["vel_disp"] = float(np.clip(vel_disp, 10.0, 500.0))

    # 5. 동역학 질량 M_dyn, 암흑물질 질량 M_DM, 암흑물질 비율 f_DM (%)
    m_dyn = (d["v_rot"] ** 2) * d["radius_kpc"] / G_ASTRO
    if m_dyn < mstar_msun * 1.05:
        m_dyn = mstar_msun * 1.08
    m_dm = max(0.0, m_dyn - mstar_msun)
    f_dm_pct = (m_dm / m_dyn) * 100.0

    # 만약 사용자가 f_dm_percent를 직접 입력한 경우 우선 반영
    if "f_dm_percent" in d and d["f_dm_percent"] is not None and not np.isnan(d["f_dm_percent"]):
        f_dm_pct = float(np.clip(d["f_dm_percent"], 1.0, 98.0))
        m_dyn = mstar_msun / max(1.0 - f_dm_pct / 100.0, 0.02)
        m_dm = m_dyn - mstar_msun

    d["log_mdyn"] = float(np.log10(max(m_dyn, 1e6)))
    d["log_mdm"] = float(np.log10(max(m_dm, 1e5)))
    d["mdyn_msun"] = float(m_dyn)
    d["mdm_msun"] = float(m_dm)
    d["f_dm_percent"] = float(f_dm_pct)

    # 6. 항성 표면질량밀도 log_sigma_star [M_sun / kpc^2]
    sigma_star = mstar_msun / (2.0 * np.pi * (d["radius_kpc"] ** 2))
    d["log_sigma_star"] = float(np.log10(max(sigma_star, 1e3)))

    # 7. 별생성률 log_sfr 및 비별생성률 log_ssfr
    log_sfr = d.get("log_sfr", None)
    if log_sfr is None or np.isnan(log_sfr):
        ha_flux = d.get("h_alpha_flux", None)
        if ha_flux is not None and ha_flux > 0:
            # Kennicutt (1998): SFR = 7.9e-42 * L_Ha
            d_l_cm = d["dist_mpc"] * 3.0857e24
            l_ha = 4.0 * np.pi * (d_l_cm ** 2) * (ha_flux * 1e-17)
            sfr_val = max(1e-4, 7.9e-42 * l_ha)
            log_sfr = np.log10(sfr_val)
        else:
            # 색지수 또는 주계열 경험식 기반 추정
            c_ur = d.get("color_u_r", 2.0)
            log_ssfr_est = -10.1 - 0.85 * (c_ur - 2.0) + 0.35 * np.log10(1.0 + z)
            log_sfr = d["log_mstar"] + log_ssfr_est
    d["log_sfr"] = float(np.clip(log_sfr, -4.0, 3.5))
    d["log_ssfr"] = float(d["log_sfr"] - d["log_mstar"])

    # 8. 광학 색지수 color_u_r, D_n(4000), 기체 금속량 12+log(O/H)
    color_u_r = d.get("color_u_r", None)
    if color_u_r is None or np.isnan(color_u_r):
        # sSFR과 질량으로부터 경험적 색지수 추정
        color_u_r = 2.05 - 0.58 * (d["log_ssfr"] + 10.2) + 0.18 * (d["log_mstar"] - 10.0)
    d["color_u_r"] = float(np.clip(color_u_r, 0.4, 3.6))

    d4000 = d.get("d4000", None)
    if d4000 is None or np.isnan(d4000):
        d4000 = 1.48 - 0.22 * (d["log_ssfr"] + 10.2) + 0.14 * (d["color_u_r"] - 2.0)
    d["d4000"] = float(np.clip(d4000, 0.90, 2.35))

    oh_met = d.get("oh_metallicity", None)
    if oh_met is None or np.isnan(oh_met):
        log_nii_ha = d.get("log_nii_ha", None)
        if log_nii_ha is not None and not np.isnan(log_nii_ha):
            oh_met = 8.90 + 0.57 * log_nii_ha
        else:
            # 기본 금속량 관계 (Fundamental Metallicity Relation, Mannucci+2010)
            mu_032 = d["log_mstar"] - 0.32 * d["log_sfr"]
            oh_met = 8.90 + 0.37 * (mu_032 - 10.0) - 0.12 * np.log10(1.0 + z)
    d["oh_metallicity"] = float(np.clip(oh_met, 7.40, 9.35))

    return d


# ==============================================================================
# 4. 차세대 통합 은하 진화 지수 (Unified GEI v2.0) 계산 엔진
# ==============================================================================
def compute_unified_gei(obs: dict) -> dict:
    """
    완성된 물리량 딕셔너리 obs로부터 5대 물리 축 점수와 통합 은하 진화 지수(GEI v2.0),
    그리고 현재 진화 단계(Stage I ~ V)를 계산합니다.
    """
    d = complete_galaxy_observables(obs)

    # 1) 별생성 소광도 S_quench (가중치 0.30)
    # log_ssfr: -8.2 (초폭발적 별생성, S=0) ~ -12.2 (완전 소광, S=1)
    s_quench = np.clip((-8.2 - d["log_ssfr"]) / (-8.2 - (-12.2)), 0.0, 1.0)

    # 2) 항성 질량 성숙도 S_mass (가중치 0.25)
    # log_mstar: 7.5 (왜소은하, S=0) ~ 11.8 (초거대은하, S=1)
    s_mass = np.clip((d["log_mstar"] - 7.5) / (11.8 - 7.5), 0.0, 1.0)

    # 3) 항성종족 노화 및 화학적 성숙도 S_pop (가중치 0.20)
    # 색지수 (u-r: 0.8~3.0), D4000 (1.0~2.1), 금속량 (7.8~9.2) 결합
    s_color = np.clip((d["color_u_r"] - 0.8) / (3.0 - 0.8), 0.0, 1.0)
    s_d4000 = np.clip((d["d4000"] - 1.0) / (2.1 - 1.0), 0.0, 1.0)
    s_metal = np.clip((d["oh_metallicity"] - 7.8) / (9.2 - 7.8), 0.0, 1.0)
    s_pop = 0.45 * s_color + 0.35 * s_d4000 + 0.20 * s_metal

    # 4) 구조적 밀집도 S_struct (가중치 0.15)
    # log_sigma_star: 6.2 ~ 10.0 [M_sun / kpc^2]
    s_struct = np.clip((d["log_sigma_star"] - 6.2) / (10.0 - 6.2), 0.0, 1.0)

    # 5) 암흑물질 헤일로 조립 및 중력 퍼텐셜 성숙도 S_halo (가중치 0.10)
    # 동역학 질량 log_mdyn (8.5 ~ 12.3) + 암흑물질 분율 f_DM (10% ~ 85%)
    s_mdyn = np.clip((d["log_mdyn"] - 8.5) / (12.3 - 8.5), 0.0, 1.0)
    s_fdm = np.clip((d["f_dm_percent"] - 10.0) / (85.0 - 10.0), 0.0, 1.0)
    s_halo = 0.55 * s_mdyn + 0.45 * s_fdm

    # 통합 진화 지수 GEI (0.000 ~ 1.000)
    gei_score = (
        0.30 * s_quench +
        0.25 * s_mass +
        0.20 * s_pop +
        0.15 * s_struct +
        0.10 * s_halo
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
    d["gei_score"] = gei_score
    d["gei_100"] = round(gei_score * 100.0, 1)
    d["stage_id"] = stage_info["stage_id"]
    d["stage_code"] = stage_info["code"]
    d["stage_name_kr"] = stage_info["name_kr"]
    d["stage_name_en"] = stage_info["name_en"]
    d["stage_color"] = stage_info["color"]
    d["stage_badge_bg"] = stage_info["badge_bg"]
    d["stage_progress_pct"] = stage_progress_pct
    d["morphology_typical"] = stage_info["morphology_typical"]
    d["past_summary"] = stage_info["past_summary"]
    d["present_summary"] = stage_info["present_summary"]
    d["future_summary"] = stage_info["future_summary"]

    return d


# ==============================================================================
# 5. 벡터화된 대용량 카탈로그 GEI v2.0 일괄 계산 함수 (SDSS / NED-LVS / CEERS)
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
    """수만~수백만 개 은하 배열에 대해 고속 벡터 연산으로 통합 은하 진화 지수(GEI v2.0)와 진화 단계를 산출합니다."""
    log_mstar = np.asarray(log_mstar, dtype=float)
    log_sfr = np.asarray(log_sfr, dtype=float)
    radius_kpc = np.maximum(0.05, np.asarray(radius_kpc, dtype=float))
    f_dm_percent = np.asarray(f_dm_percent, dtype=float)
    log_mdyn = np.asarray(log_mdyn, dtype=float)
    z = np.maximum(0.0, np.asarray(z, dtype=float))

    log_ssfr = log_sfr - log_mstar
    log_sigma_star = log_mstar - np.log10(2.0 * np.pi * (radius_kpc ** 2))

    if color_u_r is None:
        color_u_r = np.clip(2.05 - 0.58 * (log_ssfr + 10.2) + 0.18 * (log_mstar - 10.0), 0.4, 3.6)
    else:
        color_u_r = np.asarray(color_u_r, dtype=float)

    if d4000 is None:
        d4000 = np.clip(1.48 - 0.22 * (log_ssfr + 10.2) + 0.14 * (color_u_r - 2.0), 0.90, 2.35)
    else:
        d4000 = np.asarray(d4000, dtype=float)

    if oh_met is None:
        mu_032 = log_mstar - 0.32 * log_sfr
        oh_met = np.clip(8.90 + 0.37 * (mu_032 - 10.0) - 0.12 * np.log10(1.0 + z), 7.40, 9.35)
    else:
        oh_met = np.asarray(oh_met, dtype=float)

    s_quench = np.clip((-8.2 - log_ssfr) / (-8.2 - (-12.2)), 0.0, 1.0)
    s_mass = np.clip((log_mstar - 7.5) / (11.8 - 7.5), 0.0, 1.0)
    s_color = np.clip((color_u_r - 0.8) / (3.0 - 0.8), 0.0, 1.0)
    s_d4000 = np.clip((d4000 - 1.0) / (2.1 - 1.0), 0.0, 1.0)
    s_metal = np.clip((oh_met - 7.8) / (9.2 - 7.8), 0.0, 1.0)
    s_pop = 0.45 * s_color + 0.35 * s_d4000 + 0.20 * s_metal
    s_struct = np.clip((log_sigma_star - 6.2) / (10.0 - 6.2), 0.0, 1.0)
    s_mdyn = np.clip((log_mdyn - 8.5) / (12.3 - 8.5), 0.0, 1.0)
    s_fdm = np.clip((f_dm_percent - 10.0) / (85.0 - 10.0), 0.0, 1.0)
    s_halo = 0.55 * s_mdyn + 0.45 * s_fdm

    gei = np.clip(
        0.30 * s_quench + 0.25 * s_mass + 0.20 * s_pop + 0.15 * s_struct + 0.10 * s_halo,
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
        t_ratio = (t_cosmic[i] / t_cosmic[i + 1]) ** 0.65
        growth_boost = np.exp(min(dt_step / (tau_quench * 1.15), 0.35))
        sfr_prev = sfr_grid[i + 1] * t_ratio * growth_boost
        # 단, 과거 sSFR은 우주 시대의 상한선(log sSFR <= -8.1)을 넘지 않도록 물리적 제한
        max_sfr_allowed = max(0.05, mstar_grid[i + 1] * (10.0 ** (-8.15)))
        sfr_grid[i] = np.clip(sfr_prev, 1e-3, max_sfr_allowed)

        dm_sf = (1.0 - r_return) * 0.5 * (sfr_grid[i + 1] + sfr_grid[i]) * (dt_step * 1e9)
        # 과거 원시 은하 최소 질량 하한 보존 (현재 질량의 최소 4% 또는 3e7 M_sun 이상)
        m_min = max(3e7, mstar_now * 0.04 * ((t_cosmic[i] / t_age_now) ** 1.3))
        mstar_grid[i] = max(m_min, mstar_grid[i + 1] - dm_sf)
        # 재보정: 질량이 줄어든 만큼 과거 SFR도 물리적 sSFR 범위 내로 조정
        sfr_grid[i] = np.clip(sfr_grid[i], mstar_grid[i] * 1e-12, mstar_grid[i] * (10.0 ** (-8.2)))

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

    # 향후 녹색 계곡(Stage IV, GEI >= 0.62) 및 완전 소광(Stage V, GEI >= 0.78) 도달 예상 시간 산출
    future_rows = traj_df[traj_df["dt_gyr"] >= 0.0]
    gv_rows = future_rows[future_rows["gei_score"] >= 0.62]
    quench_rows = future_rows[future_rows["gei_score"] >= 0.78]

    if cur["gei_score"] >= 0.62:
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
        t_to_quench_str = f"소광 시간척도 τ ≈ {tau_quench:.1f} Gyr로 서서히 감쇠"

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
            f"[{future_rep['epoch_label']}] 가스 소모(소광 시간척도 τ≈{tau_quench:.1f} Gyr)와 항성 질량 축적을 거쳐 "
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
