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
    
    # 1. BPT 라인 비율 (이것은 분류를 위한 기본 비율이므로 유지)
    df['log_nii_ha'] = np.log10(df['nii_6584_flux'] / df['h_alpha_flux'])
    df['log_oiii_hb'] = np.log10(df['oiii_5007_flux'] / df['h_beta_flux'])
    
    # 2. 은하 형태 (Galaxy Type) 추론 - Galaxy Zoo 실제 관측 데이터 사용
    df['galaxy_type'] = 'Unclassified/Uncertain'
    if 'gz_spiral' in df.columns:
        df.loc[df['gz_spiral'] == 1, 'galaxy_type'] = '나선은하 (Spiral)'
        df.loc[df['gz_elliptical'] == 1, 'galaxy_type'] = '타원은하 (Elliptical)'
        df.loc[df['gz_p_mg'] > 0.5, 'galaxy_type'] = '병합은하 (Merger)'
        df.loc[df['gz_uncertain'] == 1, 'galaxy_type'] = '불확실 (Uncertain)'
    
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
    
    # Physical DataFrame (관측/제공된 물리량)
    physical_cols = [
        'specObjID', 'ra', 'dec', 'galaxy_type', 'z', 'zErr', 'veldisp', 'velDispErr',
        'u', 'g', 'r', 'i', 'phot_z',
        'err_u', 'err_g', 'err_r', 'err_i', 'err_z',
        'petroRad_u', 'petroRad_g', 'petroRad_r', 'petroRad_i', 'petroRad_z',
        'petroR50_u', 'petroR50_g', 'petroR50_r', 'petroR50_i', 'petroR50_z',
        'petroR90_u', 'petroR90_g', 'petroR90_r', 'petroR90_i', 'petroR90_z',
        'extinction_u', 'extinction_g', 'extinction_r', 'extinction_i', 'extinction_z',
        'log_stellar_mass', 'lgm_tot_p16', 'lgm_tot_p84',
        'log_sfr', 'sfr_tot_p16', 'sfr_tot_p84',
        'gz_p_el', 'gz_p_cs', 'gz_p_edge', 'gz_p_mg', 'gz_spiral', 'gz_elliptical', 'gz_uncertain'
    ]
    # 존재하는 컬럼만 선택
    physical_cols = [c for c in physical_cols if c in df_sample.columns]
    df_physical = df_sample[physical_cols]
    
    # Chemical DataFrame (제공된 스펙트럼 라인)
    chemical_cols = [
        'specObjID', 'metallicity_oh', 'oh_p16', 'oh_p84', 'd4000_n', 'd4000_n_err', 'bptclass',
        'h_alpha_flux', 'h_alpha_flux_err', 'h_alpha_eqw', 'h_alpha_eqw_err',
        'h_beta_flux', 'h_beta_flux_err', 'h_beta_eqw', 'h_beta_eqw_err',
        'oiii_5007_flux', 'oiii_5007_flux_err', 'oiii_5007_eqw', 'oiii_5007_eqw_err',
        'nii_6584_flux', 'nii_6584_flux_err', 'nii_6584_eqw', 'nii_6584_eqw_err',
        'sii_6717_flux', 'sii_6717_flux_err', 
        'oii_3726_flux', 'oii_3726_flux_err',
        'log_nii_ha', 'log_oiii_hb'
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
