import pandas as pd
import requests
import io
import time
import numpy as np
import config
import os

def fetch_sdss_data() -> pd.DataFrame:
    """
    SDSS SkyServer DR18 SQL API를 호출하여 적색편이 구간별로 은하 데이터를 수집합니다.
    """
    print("SDSS 데이터 수집 시작 (목표: 10만 개)...")
    
    # 0.02 to 0.20
    z_min = config.REDSHIFT_MIN
    z_max = config.REDSHIFT_MAX
    step = 0.015
    
    all_data = []
    total_fetched = 0
    
    # Redshift bins
    z_bins = np.arange(z_min, z_max + step, step)
    
    for i in range(len(z_bins) - 1):
        current_z_min = z_bins[i]
        current_z_max = z_bins[i+1]
        
        if total_fetched >= config.TARGET_GALAXIES:
            break
            
        limit = config.TARGET_GALAXIES - total_fetched
        
        sql_query = f"""
        SELECT TOP {limit}
            s.specObjID, s.ra, s.dec, s.z, s.velDisp, s.velDispErr,
            p.u, p.g, p.r, p.i, p.z as phot_z,
            p.petroRad_r, p.petroR50_r, p.petroR90_r,
            l.h_alpha_flux, l.h_alpha_flux_err,
            l.h_beta_flux, l.h_beta_flux_err,
            l.h_gamma_flux, l.h_gamma_flux_err,
            l.oiii_5007_flux, l.oiii_5007_flux_err,
            l.nii_6584_flux, l.nii_6584_flux_err,
            l.sii_6717_flux, l.sii_6717_flux_err,
            l.oii_3726_flux, l.oii_3726_flux_err,
            e.lgm_tot_p50, e.sfr_tot_p50, e.oh_p50, e.bptclass,
            indx.d4000_n
        FROM SpecObj s
        JOIN PhotoObj p ON s.bestObjID = p.objID
        JOIN galSpecLine l ON s.specObjID = l.specObjID
        JOIN galSpecExtra e ON s.specObjID = e.specObjID
        JOIN galSpecIndx indx ON s.specObjID = indx.specObjID
        WHERE s.class = 'GALAXY'
          AND s.zWarning = 0
          AND s.z >= {current_z_min:.4f} AND s.z < {current_z_max:.4f}
          AND l.h_alpha_flux > 0 AND l.h_beta_flux > 0
          AND l.oiii_5007_flux > 0 AND l.nii_6584_flux > 0
          AND p.petroR50_r > 0
        """
        
        params = {
            "cmd": sql_query,
            "format": config.SDSS_QUERY_FORMAT
        }
        
        print(f"[{current_z_min:.4f} ~ {current_z_max:.4f}] 적색편이 구간 데이터 요청 중...")
        
        try:
            response = requests.get(config.SDSS_SKYSERVER_URL, params=params, timeout=120)
            response.raise_for_status()
            
            if response.text.startswith("ERROR"):
                print(f"SDSS API 에러 발생: {response.text}")
                continue
                
            df = pd.read_csv(io.StringIO(response.text), skiprows=1)
            
            if not df.columns.str.contains('specObjID').any():
                df = pd.read_csv(io.StringIO(response.text), skiprows=2)
                
            if len(df.columns) == 1 and ',' in response.text:
                df = pd.read_csv(io.StringIO(response.text))
                
            if df.empty:
                print("이 구간에서는 수집된 데이터가 없습니다.")
                continue
                
            all_data.append(df)
            total_fetched += len(df)
            print(f"현재 구간 수집: {len(df)}개, 누적 수집: {total_fetched}개")
            
        except Exception as e:
            print(f"요청 중 오류 발생: {e}")
            
        time.sleep(1) # 잠시 대기
        
    if len(all_data) == 0:
        print("수집된 데이터가 없습니다. 빈 DataFrame을 반환합니다.")
        return pd.DataFrame()
        
    final_df = pd.concat(all_data, ignore_index=True)
    
    # 10만개까지만 자르기
    if len(final_df) > config.TARGET_GALAXIES:
        final_df = final_df.head(config.TARGET_GALAXIES)
        
    print(f"최종 데이터 수집 완료: 총 {len(final_df)} 개")
    final_df.to_csv(config.RAW_SDSS_FILE, index=False)
    
    return final_df

if __name__ == "__main__":
    fetch_sdss_data()
