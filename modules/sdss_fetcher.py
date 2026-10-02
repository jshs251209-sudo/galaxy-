import requests
import numpy as np
import pandas as pd
from io import StringIO, BytesIO
from PIL import Image
import os

class SDSSFetcher:
    """천체 영상 및 데이터 실시간 인출 엔진 (SDSS SkyServer DR18)"""
    
    SKYSERVER_URL = 'https://skyserver.sdss.org/dr18/SkyServerWS/SearchTools/SqlSearch'
    CUTOUT_URL = 'https://skyserver.sdss.org/dr18/SkyServerWS/ImgCutout/getjpeg'
    SPECTRUM_URL = 'https://dr18.sdss.org/optical/spectrum/view/data/format=csv/spec=lite'
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
    
    def get_cutout_image(self, ra: float, dec: float, scale: float = 0.4, width: int = 256, height: int = 256) -> Image.Image | None:
        """특정 좌표(RA, Dec)의 SDSS 컬러 광학 영상을 가져옴.
        Uses: https://skyserver.sdss.org/dr18/SkyServerWS/ImgCutout/getjpeg?ra={ra}&dec={dec}&scale={scale}&width={width}&height={height}
        Returns: PIL Image or None on failure.
        Handle timeout and HTTP errors gracefully.
        """
        try:
            params = {
                'ra': ra,
                'dec': dec,
                'scale': scale,
                'width': width,
                'height': height
            }
            response = requests.get(self.CUTOUT_URL, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            image = Image.open(BytesIO(response.content))
            return image
        except requests.exceptions.RequestException as e:
            print(f"이미지 다운로드 중 오류 발생 (네트워크 오류): {e}")
            return None
        except Exception as e:
            print(f"이미지 처리 중 오류 발생: {e}")
            return None

    def search_by_coordinates(self, ra: float, dec: float, radius_arcmin: float = 1.0) -> pd.DataFrame | None:
        """좌표 반경 검색으로 주변 천체 정보 조회.
        SQL query using fGetNearbyObjEq and joining with galSpecLine, galSpecExtra.
        Return DataFrame with key columns: objID, ra, dec, z, lgm_tot_p50, sfr_tot_p50, oh_p50,
        h_alpha_flux, h_beta_flux, oiii_5007_flux, nii_6584_flux, velDisp, d4000_n, petroR50_r,
        modelMag_u, modelMag_g, modelMag_r, modelMag_i
        """
        sql = f"""
        SELECT 
            p.objID, p.ra, p.dec, s.z, 
            e.lgm_tot_p50, e.sfr_tot_p50, e.oh_p50,
            l.h_alpha_flux, l.h_beta_flux, l.oiii_5007_flux, l.nii_6584_flux, 
            s.velDisp, e.d4000_n, p.petroR50_r,
            p.modelMag_u, p.modelMag_g, p.modelMag_r, p.modelMag_i
        FROM fGetNearbyObjEq({ra}, {dec}, {radius_arcmin}) n
        JOIN PhotoObj p ON n.objID = p.objID
        LEFT JOIN SpecObj s ON p.objID = s.bestObjID
        LEFT JOIN galSpecLine l ON s.specObjID = l.specObjID
        LEFT JOIN galSpecExtra e ON s.specObjID = e.specObjID
        """
        return self._execute_sql(sql)

    def search_by_objid(self, objid: int) -> pd.DataFrame | None:
        """특정 objID로 천체 상세 조회."""
        sql = f"""
        SELECT 
            p.objID, p.ra, p.dec, s.z, 
            e.lgm_tot_p50, e.sfr_tot_p50, e.oh_p50,
            l.h_alpha_flux, l.h_beta_flux, l.oiii_5007_flux, l.nii_6584_flux, 
            s.velDisp, e.d4000_n, p.petroR50_r,
            p.modelMag_u, p.modelMag_g, p.modelMag_r, p.modelMag_i
        FROM PhotoObj p
        LEFT JOIN SpecObj s ON p.objID = s.bestObjID
        LEFT JOIN galSpecLine l ON s.specObjID = l.specObjID
        LEFT JOIN galSpecExtra e ON s.specObjID = e.specObjID
        WHERE p.objID = {objid}
        """
        return self._execute_sql(sql)

    def search_by_plate_mjd_fiber(self, plate: int, mjd: int, fiber: int) -> pd.DataFrame | None:
        """분광 식별자(Plate-MJD-Fiber)로 천체 조회."""
        sql = f"""
        SELECT 
            p.objID, p.ra, p.dec, s.z, 
            e.lgm_tot_p50, e.sfr_tot_p50, e.oh_p50,
            l.h_alpha_flux, l.h_beta_flux, l.oiii_5007_flux, l.nii_6584_flux, 
            s.velDisp, e.d4000_n, p.petroR50_r,
            p.modelMag_u, p.modelMag_g, p.modelMag_r, p.modelMag_i
        FROM SpecObj s
        JOIN PhotoObj p ON p.objID = s.bestObjID
        LEFT JOIN galSpecLine l ON s.specObjID = l.specObjID
        LEFT JOIN galSpecExtra e ON s.specObjID = e.specObjID
        WHERE s.plate = {plate} AND s.mjd = {mjd} AND s.fiberID = {fiber}
        """
        return self._execute_sql(sql)

    def fetch_spectrum_data(self, plate: int, mjd: int, fiber: int) -> pd.DataFrame | None:
        """분광 데이터(wavelength, flux) CSV를 가져옴.
        URL: https://dr18.sdss.org/optical/spectrum/view/data/format=csv/spec=lite?plateid={plate}&mjd={mjd}&fiberid={fiber}
        Returns DataFrame with 'wavelength' and 'flux' columns.
        """
        try:
            params = {
                'plateid': plate,
                'mjd': mjd,
                'fiberid': fiber
            }
            response = requests.get(self.SPECTRUM_URL, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            df = pd.read_csv(StringIO(response.text))
            
            if 'wavelength' in df.columns and 'flux' in df.columns:
                return df[['wavelength', 'flux']]
            
            return df
        except requests.exceptions.RequestException as e:
            print(f"스펙트럼 다운로드 중 오류 발생 (네트워크 오류): {e}")
            return None
        except Exception as e:
            print(f"스펙트럼 데이터 처리 중 오류 발생: {e}")
            return None

    def _execute_sql(self, sql: str) -> pd.DataFrame | None:
        """내부 SQL 실행 헬퍼.
        params = {'cmd': sql, 'format': 'csv'}
        Parse response, skip comment lines starting with '#'.
        Handle errors.
        """
        try:
            params = {'cmd': sql, 'format': 'csv'}
            response = requests.get(self.SKYSERVER_URL, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            # 응답에서 주석(comment) 줄 제거
            lines = [line for line in response.text.split('\n') if not line.startswith('#') and line.strip()]
            
            if not lines:
                return None
            
            csv_data = '\n'.join(lines)
            df = pd.read_csv(StringIO(csv_data))
            
            if 'error' in df.columns.str.lower() or df.empty:
                return None
            
            return df
        except requests.exceptions.RequestException as e:
            print(f"SQL 실행 중 오류 발생 (네트워크 오류): {e}")
            return None
        except Exception as e:
            print(f"데이터 파싱 중 오류 발생: {e}")
            return None

    def get_sample_galaxies(self) -> list[dict]:
        """예제/데모용 대표 은하 목록 반환 (오프라인에서도 작동).
        Return list of dicts with pre-defined benchmark galaxies:
        """
        return [
            {
                'name': 'M31 (안드로메다 나선은하)', 'ra': 10.6847, 'dec': 41.2687, 'type': 'Spiral',
                'log_mass': 10.8, 'log_sfr': -0.5, 'metallicity': 8.9, 'color_ur': 2.1,
                'log_nii_ha': -0.5, 'log_oiii_hb': -0.3, 'velDisp': 160.0, 'd4000_n': 1.6, 'z': 0.001
            },
            {
                'name': 'M87 (처녀자리 A 거대타원은하)', 'ra': 187.7059, 'dec': 12.3911, 'type': 'Elliptical',
                'log_mass': 11.5, 'log_sfr': -2.0, 'metallicity': 9.2, 'color_ur': 2.8,
                'log_nii_ha': 0.1, 'log_oiii_hb': 0.2, 'velDisp': 350.0, 'd4000_n': 2.0, 'z': 0.004
            },
            {
                'name': 'M82 (시가 은하 - Starburst)', 'ra': 148.9685, 'dec': 69.6797, 'type': 'Starburst',
                'log_mass': 10.0, 'log_sfr': 1.0, 'metallicity': 8.5, 'color_ur': 1.5,
                'log_nii_ha': -0.6, 'log_oiii_hb': -0.4, 'velDisp': 100.0, 'd4000_n': 1.1, 'z': 0.0007
            },
            {
                'name': 'NGC 1275 (페르세우스 A - 세이퍼트)', 'ra': 49.9507, 'dec': 41.5117, 'type': 'Seyfert',
                'log_mass': 11.2, 'log_sfr': 0.5, 'metallicity': 9.0, 'color_ur': 2.3,
                'log_nii_ha': 0.2, 'log_oiii_hb': 0.8, 'velDisp': 250.0, 'd4000_n': 1.5, 'z': 0.017
            },
            {
                'name': 'Arp 220 (병합은하 ULIRG)', 'ra': 233.7381, 'dec': 23.5033, 'type': 'Merger',
                'log_mass': 10.6, 'log_sfr': 1.8, 'metallicity': 8.7, 'color_ur': 1.9,
                'log_nii_ha': -0.1, 'log_oiii_hb': -0.5, 'velDisp': 180.0, 'd4000_n': 1.3, 'z': 0.018
            }
        ]
