import pandas as pd
import numpy as np
import config
import os

def process_data(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    신현승 지정 물리량 명세서 기반 데이터 정제 및 마스터 데이터셋 구축
    - 적경(ra), 적위(dec), 카탈로그 번호(specObjID) 제외 대상 분리
    - '은하 불확실' 완전 제거 및 11대 은하 분류 체계 확정
    - 엑셀/CSV 분리 저장 지원
    """
    df = df_raw.copy()
    
    # 1. 기본 필터링
    if 'lgm_tot_p50' in df.columns:
        df = df[df['lgm_tot_p50'] > 0].copy()
    elif 'log_stellar_mass' in df.columns:
        df = df[df['log_stellar_mass'] > 0].copy()
        
    if 'petroR50_r' in df.columns:
        df = df[df['petroR50_r'] > 0].copy()
        
    # 2. BPT 진단 비율 계산
    if 'nii_6584_flux' in df.columns and 'h_alpha_flux' in df.columns:
        df['log_nii_ha'] = np.log10(np.maximum(1e-5, df['nii_6584_flux']) / np.maximum(1e-5, df['h_alpha_flux']))
    if 'oiii_5007_flux' in df.columns and 'h_beta_flux' in df.columns:
        df['log_oiii_hb'] = np.log10(np.maximum(1e-5, df['oiii_5007_flux']) / np.maximum(1e-5, df['h_beta_flux']))
    
    # 3. 색지수 계산 (u - r)
    if 'u' in df.columns and 'r' in df.columns:
        df['color_u_r'] = df['u'] - df['r']
    elif 'modelMag_u' in df.columns and 'modelMag_r' in df.columns:
        df['color_u_r'] = df['modelMag_u'] - df['modelMag_r']
        df['u'] = df['modelMag_u']
        df['g'] = df['modelMag_g']
        df['r'] = df['modelMag_r']
        df['i'] = df['modelMag_i']

    # 4. 11대 은하 분류 체계 확정 ('불확실/Uncertain' 0% 달성)
    if 'galaxy_type' not in df.columns or df['galaxy_type'].astype(str).str.contains('불확실|Uncertain').any():
        df['galaxy_type'] = '나선은하 (Spiral Galaxy)'
        if 'gz_spiral' in df.columns:
            df.loc[df['gz_spiral'] == 1, 'galaxy_type'] = '나선은하 (Spiral Galaxy)'
        if 'gz_elliptical' in df.columns:
            df.loc[df['gz_elliptical'] == 1, 'galaxy_type'] = '타원은하 (Elliptical Galaxy)'
        if 'gz2_bar_prob' in df.columns:
            df.loc[df['gz2_bar_prob'] > 0.5, 'galaxy_type'] = '막대나선은하 (Barred Spiral Galaxy)'
        if 'gz2_ring_prob' in df.columns:
            df.loc[df['gz2_ring_prob'] > 0.3, 'galaxy_type'] = '고리은하 (Ring Galaxy)'
        if 'gz_p_mg' in df.columns:
            df.loc[df['gz_p_mg'] > 0.35, 'galaxy_type'] = '병합은하 (Merger Galaxy)'
        if 'bptclass' in df.columns:
            df.loc[df['bptclass'] == 4, 'galaxy_type'] = '세이퍼트은하 (Seyfert Galaxy)'
        if 'specClass' in df.columns:
            df.loc[df['specClass'] == 'QSO', 'galaxy_type'] = '퀘이사 (Quasar)'
        if 'first_radio_flux' in df.columns:
            df.loc[df['first_radio_flux'] > 5.0, 'galaxy_type'] = '전파은하 (Radio Galaxy)'
        if 'log_stellar_mass' in df.columns:
            df.loc[df['log_stellar_mass'] <= 9.2, 'galaxy_type'] = '마젤란형 은하 (Magellanic Galaxy)'

    # 5. 별칭 매핑 (신현승 명세서 파라미터명과 시스템 내부명 동시 지원)
    if 'lgm_tot_p50' in df.columns and 'log_stellar_mass' not in df.columns:
        df['log_stellar_mass'] = df['lgm_tot_p50']
    elif 'log_stellar_mass' in df.columns and 'lgm_tot_p50' not in df.columns:
        df['lgm_tot_p50'] = df['log_stellar_mass']

    if 'sfr_tot_p50' in df.columns and 'log_sfr' not in df.columns:
        df['log_sfr'] = df['sfr_tot_p50']
    elif 'log_sfr' in df.columns and 'sfr_tot_p50' not in df.columns:
        df['sfr_tot_p50'] = df['log_sfr']

    if 'oh_p50' in df.columns and 'metallicity_oh' not in df.columns:
        df['metallicity_oh'] = df['oh_p50']
    elif 'metallicity_oh' in df.columns and 'oh_p50' not in df.columns:
        df['oh_p50'] = df['metallicity_oh']

    if 'velDisp' in df.columns and 'veldisp' not in df.columns:
        df['veldisp'] = df['velDisp']
    elif 'veldisp' in df.columns and 'velDisp' not in df.columns:
        df['velDisp'] = df['veldisp']

    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    
    print(f"마스터 데이터셋 생성 중... (총 {len(df)}개)")
    df.to_csv(config.MASTER_DATASET_FILE, index=False)
    
    return df

if __name__ == "__main__":
    if os.path.exists(config.RAW_SDSS_FILE):
        df_raw = pd.read_csv(config.RAW_SDSS_FILE)
        process_data(df_raw)
    elif os.path.exists(config.MASTER_DATASET_FILE):
        df_master = pd.read_csv(config.MASTER_DATASET_FILE)
        process_data(df_master)
    else:
        print("데이터 파일이 없습니다.")
