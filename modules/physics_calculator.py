import math
import numpy as np
from typing import Dict, Optional, Tuple, Union

class PhysicsCalculator:
    """천체물리량 계산 엔진"""
    
    # Physical constants
    SOLAR_LUMINOSITY = 3.828e33  # erg/s
    BALMER_DECREMENT_CASE_B = 2.86  # Theoretical Halpha/Hbeta ratio (Case B recombination)
    CARDELLI_RV = 3.1  # Total-to-selective extinction ratio
    
    def calculate_balmer_decrement(self, ha_flux: float, hb_flux: float) -> Optional[float]:
        """Calculate observed Balmer decrement ratio Halpha/Hbeta"""
        if not ha_flux or not hb_flux or hb_flux <= 0:
            return None
        return ha_flux / hb_flux
    
    def calculate_ebv(self, ha_flux: float, hb_flux: float) -> Optional[float]:
        """Calculate color excess E(B-V) from Balmer decrement.
        E(B-V) = 2.5 / (k_Hbeta - k_Halpha) * log10((Halpha/Hbeta)_obs / 2.86)
        where k_Halpha = 2.53, k_Hbeta = 3.61 (Cardelli et al. 1989)
        Return max(0, E(B-V))"""
        balmer = self.calculate_balmer_decrement(ha_flux, hb_flux)
        if not balmer or balmer <= 0:
            return None
        
        k_halpha = 2.53
        k_hbeta = 3.61
        try:
            ebv = (2.5 / (k_hbeta - k_halpha)) * math.log10(balmer / self.BALMER_DECREMENT_CASE_B)
            return max(0.0, ebv)
        except Exception:
            return None

    def correct_extinction(self, flux: float, wavelength: float, ebv: float) -> Optional[float]:
        """Apply dust extinction correction to a flux measurement.
        Use Cardelli (1989) extinction law.
        flux_corrected = flux * 10^(0.4 * k_lambda * E(B-V))"""
        if flux is None or ebv is None or wavelength is None:
            return None
        
        # 근사적인 k_lambda 매핑 (Angstrom)
        if 6500 <= wavelength <= 6600:
            k_lambda = 2.53  # H_alpha, [NII]
        elif 4800 <= wavelength <= 4900:
            k_lambda = 3.61  # H_beta
        elif 4950 <= wavelength <= 5050:
            k_lambda = 3.50  # [OIII] 5007
        else:
            k_lambda = 3.0
            
        try:
            return flux * (10 ** (0.4 * k_lambda * ebv))
        except Exception:
            return None
    
    def calculate_luminosity_distance(self, z: float, H0: float = 70.0) -> Optional[float]:
        """Simple luminosity distance in cm for low-z: D_L ≈ c*z/H0 * (1+z/2) * Mpc_to_cm"""
        if z is None or z < 0:
            return None
        c_kms = 299792.458  # km/s
        mpc_to_cm = 3.08567758e24
        try:
            dl_mpc = (c_kms * z / H0) * (1 + z/2)
            return dl_mpc * mpc_to_cm
        except Exception:
            return None

    def calculate_sfr_halpha(self, ha_flux_corrected: float, z: float = 0.05) -> Optional[float]:
        """Calculate Star Formation Rate from corrected Halpha luminosity.
        1. Convert flux to luminosity: L = 4*pi*D_L^2 * flux (using z and H0=70 km/s/Mpc)
        2. Apply Kennicutt (1998): SFR = 7.9e-42 * L(Halpha) [M_sun/yr]
        Return log10(SFR)"""
        if not ha_flux_corrected or ha_flux_corrected <= 0 or not z:
            return None
            
        dl_cm = self.calculate_luminosity_distance(z)
        if not dl_cm:
            return None
            
        try:
            luminosity = 4 * math.pi * (dl_cm ** 2) * ha_flux_corrected
            sfr = 7.9e-42 * luminosity
            if sfr <= 0:
                return None
            return math.log10(sfr)
        except Exception:
            return None

    def calculate_metallicity_n2(self, nii_flux: float, ha_flux: float) -> Optional[float]:
        """Pettini & Pagel (2004) N2 method.
        N2 = log10([NII]6584 / Halpha)
        12 + log(O/H) = 8.90 + 0.57 * N2"""
        if not nii_flux or not ha_flux or ha_flux <= 0 or nii_flux <= 0:
            return None
        try:
            n2 = math.log10(nii_flux / ha_flux)
            return 8.90 + 0.57 * n2
        except Exception:
            return None

    def calculate_metallicity_o3n2(self, oiii_flux: float, hb_flux: float, nii_flux: float, ha_flux: float) -> Optional[float]:
        """Pettini & Pagel (2004) O3N2 method.
        O3N2 = log10(([OIII]/Hbeta) / ([NII]/Halpha))
        12 + log(O/H) = 8.73 - 0.32 * O3N2"""
        if not all([oiii_flux, hb_flux, nii_flux, ha_flux]):
            return None
        if hb_flux <= 0 or ha_flux <= 0 or oiii_flux <= 0 or nii_flux <= 0:
            return None
        try:
            o3_hb = oiii_flux / hb_flux
            n2_ha = nii_flux / ha_flux
            if o3_hb <= 0 or n2_ha <= 0:
                return None
            o3n2 = math.log10(o3_hb / n2_ha)
            return 8.73 - 0.32 * o3n2
        except Exception:
            return None

    def classify_bpt(self, log_nii_ha: float, log_oiii_hb: float) -> dict:
        """BPT diagram classification using Kauffmann (2003) and Kewley (2001) lines.
        Kauffmann: log([OIII]/Hb) = 0.61 / (log([NII]/Ha) - 0.05) + 1.3
        Kewley: log([OIII]/Hb) = 0.61 / (log([NII]/Ha) - 0.47) + 1.19
        Returns: {
            'class': str (별생성 은하/복합 은하/세이퍼트 AGN/LINER),
            'class_en': str (Star-Forming/Composite/Seyfert/LINER),
            'kauffmann_distance': float,
            'kewley_distance': float
        }"""
        default_res = {
            'class': '미분류',
            'class_en': 'Unclassified',
            'kauffmann_distance': np.nan,
            'kewley_distance': np.nan
        }
        
        if log_nii_ha is None or log_oiii_hb is None or math.isnan(log_nii_ha) or math.isnan(log_oiii_hb):
            return default_res

        x = log_nii_ha
        y = log_oiii_hb

        # Kauffmann boundary
        y_kauff = np.nan
        if x < 0.05:
            y_kauff = 0.61 / (x - 0.05) + 1.3
        
        # Kewley boundary
        y_kewley = np.nan
        if x < 0.47:
            y_kewley = 0.61 / (x - 0.47) + 1.19
            
        kauff_dist = y - y_kauff if not math.isnan(y_kauff) else np.nan
        kewley_dist = y - y_kewley if not math.isnan(y_kewley) else np.nan
        
        cls = '미분류'
        cls_en = 'Unclassified'
        
        if x < 0.05 and y < y_kauff:
            cls, cls_en = '별생성 은하', 'Star-Forming'
        elif x < 0.47 and y < y_kewley:
            # Between Kauffmann and Kewley
            if x >= 0.05 or y >= y_kauff:
                cls, cls_en = '복합 은하', 'Composite'
            else:
                cls, cls_en = '별생성 은하', 'Star-Forming'
        else:
            # AGN or LINER
            # Seyfert/LINER separation: log([OIII]/Hb) = 1.05 * log([NII]/Ha) + 0.45
            liner_boundary = 1.05 * x + 0.45
            if y > liner_boundary:
                cls, cls_en = '세이퍼트 AGN', 'Seyfert'
            else:
                cls, cls_en = 'LINER', 'LINER'
                
        return {
            'class': cls,
            'class_en': cls_en,
            'kauffmann_distance': kauff_dist,
            'kewley_distance': kewley_dist
        }

    def calculate_log_ssfr(self, log_sfr: float, log_mass: float) -> Optional[float]:
        """Specific star formation rate: log(sSFR) = log(SFR) - log(M*)"""
        if log_sfr is None or log_mass is None:
            return None
        return log_sfr - log_mass

    def calculate_gei(self, log_mass: float, log_ssfr: float, metallicity: float, color_ur: float,
                      mass_range: tuple = (8.0, 12.5), ssfr_range: tuple = (-13.0, -8.0),
                      z_range: tuple = (7.5, 9.5), color_range: tuple = (1.0, 3.5)) -> Optional[float]:
        """Galaxy Evolution Index (0-100 scale).
        GEI = (0.30*norm_mass + 0.30*norm_ssfr_inv + 0.20*norm_z + 0.20*norm_color) * 100
        Higher GEI = more evolved (older, redder, metal-rich, quenched)"""
        if any(v is None or math.isnan(v) for v in [log_mass, log_ssfr, metallicity, color_ur]):
            return None
            
        def normalize(val: float, min_val: float, max_val: float) -> float:
            norm = (val - min_val) / (max_val - min_val)
            return max(0.0, min(1.0, norm))

        norm_mass = normalize(log_mass, mass_range[0], mass_range[1])
        
        # sSFR 역산 (작을수록 진화됨)
        norm_ssfr_inv = 1.0 - normalize(log_ssfr, ssfr_range[0], ssfr_range[1])
        
        norm_z = normalize(metallicity, z_range[0], z_range[1])
        norm_color = normalize(color_ur, color_range[0], color_range[1])
        
        gei = (0.30 * norm_mass + 0.30 * norm_ssfr_inv + 0.20 * norm_z + 0.20 * norm_color) * 100
        return gei

    def diagnose_evolution_stage(self, gei: float) -> dict:
        """Interpret GEI score into evolution stage.
        0-25: 초기 형성기 (Early Formation) - Blue, high SFR
        25-45: 성장기 (Growth Phase) - Active star formation
        45-65: 전이기 (Transition/Green Valley) - Declining SFR  
        65-85: 성숙기 (Mature Phase) - Mostly quenched
        85-100: 진화 완료 (Fully Evolved) - Red & dead
        Returns: {'stage': str, 'stage_en': str, 'description': str, 'color': str (hex)}"""
        if gei is None or math.isnan(gei):
            return {
                'stage': '알 수 없음', 
                'stage_en': 'Unknown', 
                'description': '진화 지수를 계산할 수 없습니다.', 
                'color': '#808080'
            }
            
        if gei <= 25:
            return {'stage': '초기 형성기', 'stage_en': 'Early Formation', 'description': 'Blue, high SFR', 'color': '#0000FF'}
        elif gei <= 45:
            return {'stage': '성장기', 'stage_en': 'Growth Phase', 'description': 'Active star formation', 'color': '#00BFFF'}
        elif gei <= 65:
            return {'stage': '전이기', 'stage_en': 'Transition/Green Valley', 'description': 'Declining SFR', 'color': '#00FF00'}
        elif gei <= 85:
            return {'stage': '성숙기', 'stage_en': 'Mature Phase', 'description': 'Mostly quenched', 'color': '#FFA500'}
        else:
            return {'stage': '진화 완료', 'stage_en': 'Fully Evolved', 'description': 'Red & dead', 'color': '#FF0000'}

    def classify_sii_bpt(self, log_sii_ha: float, log_oiii_hb: float) -> dict:
        """[SII]-BPT (Kewley et al. 2006): SF / Seyfert / LINER"""
        res = {'class': '미분류', 'class_en': 'Unclassified'}
        if log_sii_ha is None or log_oiii_hb is None or not np.isfinite(log_sii_ha) or not np.isfinite(log_oiii_hb):
            return res
        x, y = log_sii_ha, log_oiii_hb
        if x < 0.32 and y < 0.72 / (x - 0.32) + 1.30:
            return {'class': '별생성 은하', 'class_en': 'Star-Forming'}
        if y > 1.89 * x + 0.76:
            return {'class': '세이퍼트 AGN', 'class_en': 'Seyfert'}
        return {'class': 'LINER', 'class_en': 'LINER'}

    @staticmethod
    def electron_density_sii(sii6717: float, sii6731: float) -> Optional[float]:
        """[SII]6717/6731 비 → 전자밀도 n_e (cm^-3), Sanders+2016 (T=10^4 K) 근사식"""
        if not sii6717 or not sii6731 or sii6731 <= 0:
            return None
        R = sii6717 / sii6731
        a, b, c = 0.4315, 2107.0, 627.1
        if R >= 1.449:
            return 1.0  # 저밀도 한계
        if R <= 0.4375:
            return 1e5  # 고밀도 한계
        try:
            ne = (c * R - a * b) / (a - R)
            return float(max(ne, 1.0))
        except Exception:
            return None

    def compute_all(self, emission_lines: dict, z: float = 0.05,
                    log_mass: Optional[float] = None, color_ur: Optional[float] = None,
                    flux_scale: float = 1.0) -> dict:
        """Master function: given emission line fluxes dict, compute ALL physical properties.
        Input: {'H_alpha': float, 'H_beta': float, 'OIII_5007': float, 'NII_6584': float, ...}
        flux_scale: 입력 플럭스 단위 → erg/s/cm² 변환 계수 (예: SDSS 1e-17). 비율 기반 양에는 영향 없음.
        Output: comprehensive dict with all computed quantities."""
        def g(k):
            v = emission_lines.get(k)
            return float(v) * flux_scale if v is not None and v > 0 else None

        ha, hb, oiii, nii = g('H_alpha'), g('H_beta'), g('OIII_5007'), g('NII_6584')
        sii1, sii2 = g('SII_6717'), g('SII_6731')

        ebv = self.calculate_ebv(ha, hb)
        balmer = self.calculate_balmer_decrement(ha, hb)

        # Extinction correction
        ha_corr = self.correct_extinction(ha, 6563.0, ebv) if ebv else ha
        hb_corr = self.correct_extinction(hb, 4861.0, ebv) if ebv else hb
        oiii_corr = self.correct_extinction(oiii, 5007.0, ebv) if ebv else oiii
        nii_corr = self.correct_extinction(nii, 6584.0, ebv) if ebv else nii

        # SFR & Metallicity
        log_sfr = self.calculate_sfr_halpha(ha_corr, z)
        metal_n2 = self.calculate_metallicity_n2(nii_corr, ha_corr)
        metal_o3n2 = self.calculate_metallicity_o3n2(oiii_corr, hb_corr, nii_corr, ha_corr)

        # BPT Classification
        if nii_corr and ha_corr and nii_corr > 0 and ha_corr > 0:
            log_nii_ha = math.log10(nii_corr / ha_corr)
        else:
            log_nii_ha = np.nan
        if oiii_corr and hb_corr and oiii_corr > 0 and hb_corr > 0:
            log_oiii_hb = math.log10(oiii_corr / hb_corr)
        else:
            log_oiii_hb = np.nan
        sii_tot = (sii1 or 0) + (sii2 or 0)
        log_sii_ha = math.log10(sii_tot / ha) if sii_tot > 0 and ha else np.nan

        bpt_info = self.classify_bpt(log_nii_ha, log_oiii_hb)
        sii_bpt = self.classify_sii_bpt(log_sii_ha, log_oiii_hb)
        n_e = self.electron_density_sii(sii1, sii2)

        # 통합 금속량: O3N2 우선, N2 보조 (AGN 은 강선 금속량 보정식 적용 불가 → 표시만)
        best_metallicity = metal_o3n2 if metal_o3n2 is not None else metal_n2
        metallicity_method = 'O3N2 (PP04)' if metal_o3n2 is not None else ('N2 (PP04)' if metal_n2 is not None else '-')

        results = {
            'ebv': ebv,
            'balmer_decrement': balmer,
            'log_sfr': log_sfr,
            'metallicity': best_metallicity,
            'metallicity_oh': best_metallicity,
            'oh_p50': best_metallicity,
            'metallicity_n2': metal_n2,
            'metallicity_o3n2': metal_o3n2,
            'metallicity_method': metallicity_method,
            'log_nii_ha': log_nii_ha,
            'log_oiii_hb': log_oiii_hb,
            'log_sii_ha': log_sii_ha,
            'bpt_class': bpt_info['class'],
            'bpt_class_en': bpt_info['class_en'],
            'sii_bpt_class': sii_bpt['class'],
            'sii_bpt_class_en': sii_bpt['class_en'],
            'electron_density': n_e,
            'kauffmann_distance': bpt_info['kauffmann_distance'],
            'kewley_distance': bpt_info['kewley_distance'],
            'z': z,
            'ha_flux_corr': ha_corr,
        }
        if bpt_info['class_en'] in ('Seyfert', 'LINER', 'Composite') and best_metallicity is not None:
            results['metallicity_warning'] = 'AGN/복합 은하는 강선 금속량 보정식의 적용 범위를 벗어납니다 (참고값).'

        if log_mass is not None:
            results['log_mass'] = log_mass
            results['log_stellar_mass'] = log_mass
        if color_ur is not None:
            results['color_ur'] = color_ur
            results['color_u_r'] = color_ur

        # Evolution Index
        met_for_gei = best_metallicity if best_metallicity is not None else metal_n2
        if log_mass is not None and color_ur is not None and log_sfr is not None and met_for_gei is not None:
            log_ssfr = self.calculate_log_ssfr(log_sfr, log_mass)
            gei = self.calculate_gei(log_mass, log_ssfr, met_for_gei, color_ur)
            stage_info = self.diagnose_evolution_stage(gei)
            results.update({
                'log_ssfr': log_ssfr,
                'gei': gei,
                'gei_score': gei,
                'evolution_stage': stage_info['stage'],
                'evolution_stage_en': stage_info['stage_en'],
                'evolution_desc': stage_info['description'],
                'evolution_color': stage_info['color']
            })

        return results
