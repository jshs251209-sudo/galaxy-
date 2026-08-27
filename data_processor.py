import pandas as pd
import numpy as np
import config
import os

def process_data(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    원시 은하 데이터를 로드하여 물리적 특성을 도출하고 엑셀 파일로 분리 저장합니다.
    """
    df = df_raw.copy()
    
    # 기본 필터링 (물리적으로 의미있는 값)
    df = df[df['lgm_tot_p50'] > 0].copy()
    df = df[df['petroR50_r'] > 0].copy()
    
    # 1. 색상 지수 계산
    df['u_g'] = df['u'] - df['g']
    df['g_r'] = df['g'] - df['r']
    
    # 2. 집중도 지수 (Concentration Index) 계산
    df['concentration_index'] = df['petroR90_r'] / df['petroR50_r']
    
    # 3. 표면 밝기 (Surface Brightness) 계산
    # r-band surface brightness: mu = r + 2.5 * log10(2 * pi * R50^2)
    df['surface_brightness_r'] = df['r'] + 2.5 * np.log10(2 * np.pi * (df['petroR50_r'] ** 2))
    
    # 4. Balmer Decrement 및 Dust E(B-V)
    # Halpha / Hbeta 
    balmer_ratio = df['h_alpha_flux'] / df['h_beta_flux']
    intrinsic_ratio = 2.86
    balmer_ratio = np.maximum(balmer_ratio, intrinsic_ratio)
    
    # k(lambda) values (Calzetti or similar, simplified)
    k_ha = 2.53
    k_hb = 3.61
    df['dust_ebv'] = (2.5 / (k_hb - k_ha)) * np.log10(balmer_ratio / intrinsic_ratio)
    
    # 5. BPT 라인 비율
    df['log_nii_ha'] = np.log10(df['nii_6584_flux'] / df['h_alpha_flux'])
    df['log_oiii_hb'] = np.log10(df['oiii_5007_flux'] / df['h_beta_flux'])
    
    # 6. 이해하기 쉬운 단순 물리량 추가
    # 우주론적 거리 (단위: Mpc, H0 = 70 km/s/Mpc 가정)
    df['distance_mpc'] = df['z'] * 300000 / 70
    # 겉보기 등급 (Apparent Magnitude)
    df['app_mag_r'] = df['r']
    df['app_mag_g'] = df['g']
    # 절대 등급 (Absolute Magnitude: M = m - 5*log10(d in pc) + 5)
    # distance_mpc를 pc 단위로 변환하기 위해 1e6 곱함
    df['abs_mag_r'] = df['r'] - 5 * np.log10(df['distance_mpc'] * 1e6) + 5
    
    # 7. 동역학적 질량 및 암흑물질 비율 추정
    # petroR50_r은 arcsec 단위. 물리적 크기 Re (kpc)로 변환:
    # Re(kpc) = (petroR50_r / 206265) * distance_mpc * 1000
    df['Re_kpc'] = (df['petroR50_r'] / 206265.0) * df['distance_mpc'] * 1000.0
    
    # 비리얼 정리: M_dyn = 5 * sigma^2 * Re / G (G = 4.3009e-6 kpc (km/s)^2 / M_sun)
    G = 4.3009e-6
    # velDisp 단위는 km/s
    df['dyn_mass_msun'] = (5.0 * (df['velDisp'] ** 2) * df['Re_kpc']) / G
    
    # lgm_tot_p50 는 log(M_star / M_sun). 선형 스케일로 변환.
    df['stellar_mass_msun'] = 10 ** df['lgm_tot_p50']
    
    # 암흑물질 비율 (f_DM = 1 - M_star / M_dyn)
    # M_dyn이 0이거나 NaN일 경우 대비, 물리적으로 불가능한 값(M_star > M_dyn) 방어
    df['dark_matter_fraction'] = 1.0 - (df['stellar_mass_msun'] / df['dyn_mass_msun'])
    # 0 이하로 떨어지는 경우(에러 또는 바리온 중심 모델) 0으로 하한
    df['dark_matter_fraction'] = np.where(df['dark_matter_fraction'] < 0, 0, df['dark_matter_fraction'])
    
    # 동역학적 질량도 log 스케일로 저장
    df['log_dyn_mass'] = np.log10(df['dyn_mass_msun'].replace(0, np.nan))
    
    # 8. 은하 형태 (Galaxy Type) 추론
    # SDSS에서는 통상적으로 집중도(Concentration) 2.6을 기준으로 타원/나선 은하를 구분합니다.
    df['galaxy_type'] = np.where(df['concentration_index'] >= 2.6, '타원은하 (Elliptical)', '나선은하 (Spiral)')
    
    # 이름 변경
    rename_dict = {
        'lgm_tot_p50': 'log_stellar_mass',
        'sfr_tot_p50': 'log_sfr',
        'oh_p50': 'metallicity_oh',
        'velDisp': 'veldisp'
    }
    df = df.rename(columns=rename_dict)
    
    # 무한대 값을 NaN으로
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    
    print(f"마스터 데이터셋 생성 중... (총 {len(df)}개)")
    df.to_csv(config.MASTER_DATASET_FILE, index=False)
    
    # 전체 데이터(약 10만 개)를 그대로 사용
    df_sample = df.copy()
    print(f"전체 {len(df_sample)}개의 은하를 물리/화학 엑셀 파일로 분리하여 저장합니다. (10만 개 저장 시 시간이 다소 소요될 수 있습니다.)")
    
    # Physical DataFrame
    physical_cols = [
        'specObjID', 'ra', 'dec', 'galaxy_type', 'distance_mpc', 
        'app_mag_r', 'app_mag_g', 'abs_mag_r',
        'log_stellar_mass', 'log_sfr', 'veldisp', 'z',
        'petroRad_r', 'petroR50_r', 'petroR90_r', 'concentration_index',
        'surface_brightness_r', 'u_g', 'g_r',
        'Re_kpc', 'dyn_mass_msun', 'log_dyn_mass', 'dark_matter_fraction'
    ]
    # 존재하는 컬럼만 선택
    physical_cols = [c for c in physical_cols if c in df_sample.columns]
    df_physical = df_sample[physical_cols]
    
    # Chemical DataFrame
    chemical_cols = [
        'specObjID', 'metallicity_oh', 'd4000_n',
        'h_alpha_flux', 'h_beta_flux', 'h_gamma_flux',
        'oiii_5007_flux', 'nii_6584_flux', 'sii_6717_flux', 'oii_3726_flux',
        'log_nii_ha', 'log_oiii_hb', 'dust_ebv'
    ]
    chemical_cols = [c for c in chemical_cols if c in df_sample.columns]
    df_chemical = df_sample[chemical_cols]
    
    # 엑셀/CSV 저장 (EXPORT_EXCEL 플래그에 따라)
    print("데이터 저장 중입니다...")
    if config.EXPORT_EXCEL:
        df_physical.to_excel(config.PHYSICAL_EXCEL_FILE, index=False, na_rep='')
        df_chemical.to_excel(config.CHEMICAL_EXCEL_FILE, index=False, na_rep='')
    else:
        csv_physical = config.PHYSICAL_EXCEL_FILE.replace('.xlsx', '.csv')
        csv_chemical = config.CHEMICAL_EXCEL_FILE.replace('.xlsx', '.csv')
        df_physical.to_csv(csv_physical, index=False)
        df_chemical.to_csv(csv_chemical, index=False)
    print("저장 완료!")
    
    return df

if __name__ == "__main__":
    if os.path.exists(config.RAW_SDSS_FILE):
        df_raw = pd.read_csv(config.RAW_SDSS_FILE)
        process_data(df_raw)
    else:
        print(f"원시 데이터 파일이 존재하지 않습니다: {config.RAW_SDSS_FILE}")
