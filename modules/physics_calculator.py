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
        
        # 근사적인 k_lambda 매핑 (Angstrom, Cardelli 1989 R_V=3.1)
        if 6500 <= wavelength <= 6600:
            k_lambda = 2.53  # H_alpha, [NII]
        elif 6700 <= wavelength <= 6750:
            k_lambda = 2.46  # [SII] 6717, 6731
        elif 4800 <= wavelength <= 4900:
            k_lambda = 3.61  # H_beta
        elif 4950 <= wavelength <= 5050:
            k_lambda = 3.50  # [OIII] 5007
        elif 3700 <= wavelength <= 3750:
            k_lambda = 4.77  # [OII] 3727
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
            # SDSS 관습 단위(1e-17 erg/s/cm^2)가 스케일링 없이 큰 숫자(>1e-5)로 들어온 경우 자동 환산
            f_cgs = ha_flux_corrected * 1e-17 if ha_flux_corrected > 1e-5 else ha_flux_corrected
            luminosity = 4 * math.pi * (dl_cm ** 2) * f_cgs
            sfr = 7.9e-42 * luminosity
            if sfr <= 0 or not math.isfinite(sfr):
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

    def calculate_gei(self, log_mass: float, log_ssfr: float, metallicity: Optional[float] = None,
                      color_ur: Optional[float] = None, log_mdm: Optional[float] = None,
                      log_lha: Optional[float] = None, log_lsii: Optional[float] = None,
                      log_loiii: Optional[float] = None, **kwargs) -> Optional[float]:
        """Galaxy Evolution Index GEI v3 (0-100 scale).
        GEI = (0.26*S_mass + 0.28*S_quench + 0.19*S_DM + 0.27*S_line) * 100
        Higher GEI = more evolved (massive, quenched, halo-grown, emission-quenched/AGN)"""
        if any(v is None or math.isnan(v) for v in [log_mass, log_ssfr]):
            return None

        def clamp01(val: float) -> float:
            return max(0.0, min(1.0, float(val)))

        log_sfr = log_mass + log_ssfr
        mdm = float(log_mdm) if (log_mdm is not None and not math.isnan(log_mdm)) else (0.88 * log_mass + 1.35)
        lha = float(log_lha) if (log_lha is not None and not math.isnan(log_lha)) else (40.05 + 0.72 * log_sfr)
        lsii = float(log_lsii) if (log_lsii is not None and not math.isnan(log_lsii)) else (39.38 + 0.58 * log_sfr)
        loiii = float(log_loiii) if (log_loiii is not None and not math.isnan(log_loiii)) else (39.08 + 0.26 * log_sfr + 0.12 * (mdm - 9.8))

        s_mass = clamp01((log_mass - 7.5) / 4.3)
        s_quench = clamp01((-8.8 - log_ssfr) / 3.4)
        s_halo = clamp01((mdm - 8.0) / 4.5)
        s_ha = clamp01((30.6 - (lha - log_mass)) / 2.6)
        s_sii = clamp01((30.0 - (lsii - log_mass)) / 2.4)
        s_oiii = clamp01(((loiii - lha) + 1.0) / 1.3)
        s_line = clamp01(0.50 * s_ha + 0.30 * s_sii + 0.20 * s_oiii)

        gei = (0.26 * s_mass + 0.28 * s_quench + 0.19 * s_halo + 0.27 * s_line) * 100.0
        return gei

    def diagnose_evolution_stage(self, gei: float) -> dict:
        """Interpret GEI v3 score into 5 evolution stages (supports both 0-1 and 0-100 scales).
        0-28  (0.00-0.28): 1단계 (원시 폭발적 별 생성기) — 가스 분율 ↑, sSFR ↑, u-r < 1.4
        28-46 (0.28-0.46): 2단계 (초기 은하 원반 성장기) — 나선팔 원반 확장, 주계열 상단 별생성 활발
        46-64 (0.46-0.64): 3단계 (성숙 나선 구조 안정기) — 원반과 팽대부 공존, SFR·가스유입 평형
        64-78 (0.64-0.78): 4단계 (별 생성 감쇠기) — 차가운 가스 고갈 시작, 중심 팽대부 비대, 별 생성 급감
        78-100(0.78-1.00): 5단계 (소광 거대 타원 은하) — log sSFR < -11.5, 거대 암흑물질 헤일로, 적색 계열
        Returns: {'stage': str, 'stage_en': str, 'description': str, 'color': str (hex)}"""
        if gei is None or math.isnan(gei):
            return {
                'stage': '알 수 없음',
                'stage_en': 'Unknown',
                'description': '진화 지수를 계산할 수 없습니다.',
                'color': '#808080'
            }

        score_100 = gei * 100.0 if gei <= 1.0 else gei
        if score_100 < 28.0:
            return {'stage': '1단계 (원시 폭발적 별 생성기)', 'stage_en': 'Stage I: Primordial Starburst Phase', 'description': '가스 분율 ↑ · sSFR ↑ · u-r < 1.4', 'color': '#06b6d4'}
        elif score_100 < 46.0:
            return {'stage': '2단계 (초기 은하 원반 성장기)', 'stage_en': 'Stage II: Early Galaxy Disk Growth Phase', 'description': '나선팔 원반 확장 · 주계열 상단 별생성 활발', 'color': '#3b82f6'}
        elif score_100 < 64.0:
            return {'stage': '3단계 (성숙 나선 구조 안정기)', 'stage_en': 'Stage III: Mature Spiral Structure Equilibrium', 'description': '원반과 팽대부 공존 · SFR, 가스유입 평형', 'color': '#10b981'}
        elif score_100 < 78.0:
            return {'stage': '4단계 (별 생성 감쇠기)', 'stage_en': 'Stage IV: Star Formation Quenching Phase', 'description': '차가운 가스 고갈 시작 · 중심 팽대부 비대 · 별 생성 급감', 'color': '#f59e0b'}
        else:
            return {'stage': '5단계 (소광 거대 타원 은하)', 'stage_en': 'Stage V: Quenched Giant Elliptical Galaxy', 'description': 'log sSFR < -11.5 · 거대 암흑물질 헤일로 · 적색 계열', 'color': '#ef4444'}

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
                    flux_scale: float = 1.0, d4000: Optional[float] = None,
                    absorption_fits: Optional[dict] = None) -> dict:
        """Master function: given emission line fluxes dict (and optional D4000 / absorption lines),
        compute ALL physical properties including quiescent elliptical galaxy diagnostics.
        Input: {'H_alpha': float, 'H_beta': float, 'OIII_5007': float, 'NII_6584': float, ...}
        flux_scale: 입력 플럭스 단위 → erg/s/cm² 변환 계수 (예: SDSS 1e-17). 비율 기반 양에는 영향 없음.
        Output: comprehensive dict with all computed quantities."""
        emission_lines = emission_lines or {}
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
        sii1_corr = self.correct_extinction(sii1, 6717.0, ebv) if ebv else sii1
        sii2_corr = self.correct_extinction(sii2, 6731.0, ebv) if ebv else sii2

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
        sii_tot_corr = (sii1_corr or 0) + (sii2_corr or 0)
        log_sii_ha = math.log10(sii_tot_corr / ha_corr) if sii_tot_corr > 0 and ha_corr and ha_corr > 0 else np.nan

        bpt_info = self.classify_bpt(log_nii_ha, log_oiii_hb)
        sii_bpt = self.classify_sii_bpt(log_sii_ha, log_oiii_hb)
        n_e = self.electron_density_sii(sii1, sii2)

        # 소광 타원/조기형 은하 흡수선·D4000 분광 진단 (방출선이 없거나 약해 BPT 미분류인 경우)
        abs_dict = absorption_fits or {}
        tot_abs_ew = float(sum(v.get('ew_abs', 0.0) for v in abs_dict.values() if isinstance(v, dict)))
        d4_valid = (d4000 is not None and np.isfinite(d4000))
        is_quiescent_spec = (
            bpt_info['class_en'] == 'Unclassified'
            and ((d4_valid and float(d4000) >= 1.50) or tot_abs_ew >= 5.5)
        )
        stellar_pop = None
        quiescent_priors = {}
        if is_quiescent_spec:
            if not math.isnan(log_nii_ha) and log_nii_ha >= -0.10:
                bpt_info = {
                    'class': '조기형 LINER / 소광 타원은하',
                    'class_en': 'Quiescent/LINER',
                    'kauffmann_distance': bpt_info['kauffmann_distance'],
                    'kewley_distance': bpt_info['kewley_distance'],
                }
            else:
                bpt_info = {
                    'class': '소광 타원은하 (흡수선 우세)',
                    'class_en': 'Quiescent Elliptical',
                    'kauffmann_distance': bpt_info['kauffmann_distance'],
                    'kewley_distance': bpt_info['kewley_distance'],
                }
            d4_use = float(d4000) if d4_valid else float(np.clip(1.52 + 0.025 * tot_abs_ew, 1.55, 2.05))
            stellar_pop = '노령 항성종족 (D4000=%.2f, 흡수선 EW=%.1fÅ)' % (d4_use, tot_abs_ew)
            est_ur = float(np.clip(2.58 + 0.55 * (d4_use - 1.78), 2.35, 3.05))
            est_mass = float(np.clip(11.08 + 0.50 * (d4_use - 1.78) + 0.012 * max(tot_abs_ew - 8.0, 0.0), 10.45, 11.85))
            est_ssfr = float(np.clip(-11.90 - 0.80 * (d4_use - 1.78), -13.3, -11.30))
            est_sfr = float(est_mass + est_ssfr)
            est_vdisp = float(np.clip(10 ** (2.23 + 0.28 * (est_mass - 11.0)), 135.0, 340.0))
            est_oh = float(np.clip(9.07 + 0.12 * (est_mass - 11.0), 8.92, 9.22))
            quiescent_priors = {
                'log_mass': round(est_mass, 3),
                'log_sfr': round(est_sfr, 3),
                'log_ssfr': round(est_ssfr, 3),
                'color_ur': round(est_ur, 3),
                'd4000_n': round(d4_use, 3),
                'velDisp': round(est_vdisp, 1),
                'metallicity': round(est_oh, 3),
            }

        # 통합 금속량: O3N2 우선, N2 보조 (AGN 은 강선 금속량 보정식 적용 불가 → 표시만)
        best_metallicity = metal_o3n2 if metal_o3n2 is not None else metal_n2
        metallicity_method = 'O3N2 (PP04)' if metal_o3n2 is not None else ('N2 (PP04)' if metal_n2 is not None else '-')
        if best_metallicity is None and is_quiescent_spec and quiescent_priors.get('metallicity') is not None:
            best_metallicity = quiescent_priors['metallicity']
            metallicity_method = 'D4000·흡수선 경험식 (조기형)'

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
            'd4000_n': float(d4000) if d4_valid else None,
            'total_absorption_ew': tot_abs_ew,
            'is_quiescent_spectrum': bool(is_quiescent_spec),
            'stellar_population': stellar_pop,
            'quiescent_priors': quiescent_priors,
        }
        if bpt_info['class_en'] in ('Seyfert', 'LINER', 'Composite', 'Quiescent/LINER') and (metal_o3n2 is not None or metal_n2 is not None):
            results['metallicity_warning'] = 'AGN/복합/LINER 은하는 강선 금속량 보정식의 적용 범위를 벗어납니다 (참고값).'

        if log_mass is not None and np.isfinite(log_mass):
            results['log_mass'] = log_mass
            results['log_stellar_mass'] = log_mass
        elif is_quiescent_spec and quiescent_priors.get('log_mass') is not None:
            log_mass = quiescent_priors['log_mass']
            results['log_mass'] = log_mass
            results['log_stellar_mass'] = log_mass
        else:
            log_mass = None
        if color_ur is not None and np.isfinite(color_ur):
            results['color_ur'] = color_ur
            results['color_u_r'] = color_ur
        elif is_quiescent_spec and quiescent_priors.get('color_ur') is not None:
            color_ur = quiescent_priors['color_ur']
            results['color_ur'] = color_ur
            results['color_u_r'] = color_ur
        else:
            color_ur = None

        if (log_sfr is None or not np.isfinite(log_sfr)) and is_quiescent_spec and quiescent_priors.get('log_sfr') is not None:
            log_sfr = quiescent_priors['log_sfr']
            results['log_sfr'] = log_sfr
            results['velDisp'] = quiescent_priors.get('velDisp')

        # Evolution Index (GEI v3)
        met_for_gei = best_metallicity if best_metallicity is not None else metal_n2
        if log_mass is not None and log_sfr is not None and np.isfinite(log_sfr):
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
