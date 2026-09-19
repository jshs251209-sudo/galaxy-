"""
은하 물리량 및 화학적 조성 상관관계 분석 프로그램
(Galaxy Physical Properties & Chemical Abundance Correlation Analyzer)

- 주요 분석 변수:
  1. 항성질량 (Stellar Mass, M*) vs 별 생성률 (SFR) -> Star-forming Main Sequence (SFMS)
  2. 항성질량 (Stellar Mass, M*) vs 금속함량 (Metallicity, 12 + log(O/H)) -> Mass-Metallicity Relation (MZR)
  3. 별 생성률 (SFR) vs 금속함량 (Metallicity, 12 + log(O/H)) -> Fundamental Metallicity Relation (FMR) 관점
  4. 광도, 회전속도, 방출선(H-alpha, [O III], [N II]) 등 추가 변수 지원
"""

import os
import sys

# Windows 콘솔 utf-8 인코딩 안전 설정
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

import numpy as np
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns

# ==============================================================================
# 0. 그래프 스타일 설정 (Colab / Windows 범용 호환)
# ==============================================================================
def setup_plot_style():
    """그래프 폰트 및 스타일 초기화"""
    plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Malgun Gothic', 'NanumGothic']
    plt.rcParams['axes.unicode_minus'] = False
    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
    sns.set_palette("tab10")

# ==============================================================================
# 1. 가상 데이터(Mock Data) 생성기 (실제 관측 천문학 모델 기반)
# ==============================================================================
def generate_synthetic_galaxy_data(n_samples: int = 1200, random_state: int = 42) -> pd.DataFrame:
    """
    테스트용 가상 은하 관측 데이터를 생성합니다.
    천문학적 관측 사실(SFMS, MZR 등)을 기반으로 사실적인 분산과 은하 분류를 모사합니다.
    ※ 주의: 이 데이터는 테스트용이며 실제 연구 결론 도출에는 사용할 수 없습니다.
    """
    np.random.seed(random_state)
    
    # 은하 유형 비율: Star-forming (70%), Composite (15%), AGN (15%)
    types = np.random.choice(['Star-forming', 'Composite', 'AGN'], size=n_samples, p=[0.70, 0.15, 0.15])
    
    # 1. 항성질량 log(M* / M_sun): 관측 은하의 전형적인 범위 (8.5 ~ 11.5)
    log_mass = np.random.normal(loc=10.0, scale=0.6, size=n_samples)
    log_mass = np.clip(log_mass, 8.2, 11.8)
    
    # 2. 별 생성률 log(SFR / [M_sun/yr]):
    # Star-forming Main Sequence (SFMS): log(SFR) ~ 0.7 * (log_mass - 10.0) + 0.1 + noise
    log_sfr = np.zeros(n_samples)
    for i, gtype in enumerate(types):
        if gtype == 'Star-forming':
            mean_sfr = 0.72 * (log_mass[i] - 10.0) + 0.15
            noise = np.random.normal(0, 0.28)
            log_sfr[i] = mean_sfr + noise
        elif gtype == 'Composite':
            mean_sfr = 0.50 * (log_mass[i] - 10.0) - 0.2
            noise = np.random.normal(0, 0.35)
            log_sfr[i] = mean_sfr + noise
        else: # AGN
            mean_sfr = 0.40 * (log_mass[i] - 10.0) - 0.5
            noise = np.random.normal(0, 0.45)
            log_sfr[i] = mean_sfr + noise
            
    # 3. 금속함량 12 + log(O/H):
    # Tremonti et al. (2004) MZR 곡선 근사: 질량이 커질수록 금속함량 증가 후 포화 (~9.1)
    metallicity = 9.05 - 0.09 * np.maximum(0, 11.4 - log_mass)**2 + np.random.normal(0, 0.08, size=n_samples)
    metallicity = np.clip(metallicity, 7.8, 9.3)
    
    # 4. 회전속도 v_rot (km/s): Tully-Fisher 관계 (v_rot ~ M*^0.25)
    v_rot = 180.0 * (10**(log_mass - 10.0))**0.25 + np.random.normal(0, 20.0, size=n_samples)
    v_rot = np.clip(v_rot, 40.0, 350.0)
    
    # 5. 광도 log(L / L_sun): r-band 광도
    log_lum = 0.95 * log_mass + np.random.normal(0, 0.15, size=n_samples)
    
    # 6. 방출선 플럭스 (10^-17 erg/s/cm^2 단위 모사)
    h_alpha = np.maximum(10.0, 10**(log_sfr + 2.5) + np.random.normal(0, 20.0, size=n_samples))
    h_beta = h_alpha / 2.86 + np.random.normal(0, 5.0, size=n_samples)
    oiii_5007 = np.maximum(5.0, h_beta * np.where(types=='AGN', 3.5, 0.8) + np.random.normal(0, 10.0, size=n_samples))
    nii_6584 = np.maximum(5.0, h_alpha * np.where(types=='AGN', 0.8, 0.3) + np.random.normal(0, 10.0, size=n_samples))
    
    df = pd.DataFrame({
        'galaxy_id': [f"MOCK_{i+1:05d}" for i in range(n_samples)],
        'galaxy_type': types,
        'stellar_mass': 10**log_mass,    # Linear scale (M_sun)
        'log_stellar_mass': log_mass,    # Log scale log10(M*/M_sun)
        'sfr': 10**log_sfr,              # Linear scale (M_sun/yr)
        'log_sfr': log_sfr,              # Log scale log10(SFR)
        'metallicity': metallicity,      # 12 + log(O/H)
        'rotation_velocity': v_rot,      # km/s
        'log_luminosity': log_lum,       # log10(L/L_sun)
        'flux_h_alpha': h_alpha,
        'flux_h_beta': h_beta,
        'flux_oiii_5007': oiii_5007,
        'flux_nii_6584': nii_6584
    })
    
    mask_nan = np.random.rand(n_samples) < 0.03
    df.loc[mask_nan, 'metallicity'] = np.nan
    
    return df

# ==============================================================================
# 2. 데이터 자동 정제 및 전처리 엔진
# ==============================================================================
class GalaxyDataProcessor:
    """은하 관측 데이터 로딩, 컬럼 매핑, 단위 확인, 로그 변환 및 전처리 클래스"""
    
    COLUMN_SYNONYMS = {
        'stellar_mass': ['stellar_mass', 'mstar', 'mass', 'm_star', 'lgm_tot_p50', 'log_mass', 'log_stellar_mass'],
        'sfr': ['sfr', 'sfr_tot_p50', 'star_formation_rate', 'log_sfr', 'logsfr'],
        'metallicity': ['metallicity', 'oh_p50', '12+log(o/h)', '12_log_oh', 'z_gas', 'gas_metallicity'],
        'rotation_velocity': ['rotation_velocity', 'v_rot', 'vrot', 'v_circ', 'veldisp'],
        'luminosity': ['luminosity', 'log_luminosity_r', 'log_luminosity', 'lum_r', 'abs_mag_r'],
        'galaxy_type': ['galaxy_type', 'bptclass', 'class_activity', 'type', 'morphology']
    }
    
    def __init__(self, filepath: str = None, df: pd.DataFrame = None):
        self.raw_filepath = filepath
        self.is_synthetic = False
        self.matched_columns = {}
        self.processed_df = None
        
        if df is not None:
            self.raw_df = df.copy()
        elif filepath and os.path.exists(filepath):
            print(f"[*] 지정된 CSV 파일 로딩: '{filepath}'")
            self.raw_df = pd.read_csv(filepath)
            self.is_synthetic = False
        else:
            print("[!] CSV 파일이 지정되지 않았거나 찾을 수 없습니다.")
            print("[*] 테스트용 가상 은하 관측 데이터를 자동으로 생성합니다...")
            self.raw_df = generate_synthetic_galaxy_data(n_samples=1200)
            self.is_synthetic = True
            synthetic_save_path = "synthetic_galaxies_test.csv"
            self.raw_df.to_csv(synthetic_save_path, index=False)
            print(f"[*] 생성된 가상 데이터를 '{synthetic_save_path}'에 저장했습니다.")
            
    def inspect_and_map_columns(self):
        """열 이름 매핑 및 식별"""
        print("\n" + "="*70)
        print(" [Step 1] 데이터 열(Column) 검사 및 자동 매핑")
        print("="*70)
        print(f"- 원본 데이터 크기: {self.raw_df.shape[0]} 행 x {self.raw_df.shape[1]} 열")
        print(f"- 데이터 컬럼 목록: {list(self.raw_df.columns)}")
        
        lower_cols = {str(col).lower().strip(): col for col in self.raw_df.columns}
        
        for standard_key, synonyms in self.COLUMN_SYNONYMS.items():
            for syn in synonyms:
                if syn.lower() in lower_cols:
                    matched = lower_cols[syn.lower()]
                    self.matched_columns[standard_key] = matched
                    break
                    
        print("\n[*] 매핑된 주요 변수:")
        for k, v in self.matched_columns.items():
            print(f"  - {k.ljust(18)} : '{v}'")
            
        if 'stellar_mass' not in self.matched_columns or 'sfr' not in self.matched_columns or 'metallicity' not in self.matched_columns:
            missing = [k for k in ['stellar_mass', 'sfr', 'metallicity'] if k not in self.matched_columns]
            print(f"\n[경고] 핵심 변수 중 다음 항목이 매핑되지 않았습니다: {missing}")
            
    def clean_and_transform(self) -> pd.DataFrame:
        """데이터 정제, 결측치/비수치값 제거 및 로그 변환"""
        print("\n" + "="*70)
        print(" [Step 2] 데이터 정제, 단위 검토 및 변환")
        print("="*70)
        
        df = self.raw_df.copy()
        
        # 1. 대상 변수 추출
        target_vars = [v for v in self.matched_columns.values()]
        
        # 2. 비수치값 및 결측값 제거
        init_n = len(df)
        for col in target_vars:
            if col != self.matched_columns.get('galaxy_type'):
                df[col] = pd.to_numeric(df[col], errors='coerce')
                
        df = df.dropna(subset=[col for col in target_vars if col != self.matched_columns.get('galaxy_type')])
        valid_num_n = len(df)
        print(f"- 초기 샘플 수: {init_n:,} 개")
        print(f"- 결측값/비수치값 제거 후: {valid_num_n:,} 개 (제거: {init_n - valid_num_n:,} 개)")
        
        # 3. 로그 변환 검토 및 표준 변수 생성
        # (1) 항성질량 (Stellar Mass)
        mass_col = self.matched_columns.get('stellar_mass')
        if mass_col:
            med_val = df[mass_col].median()
            if med_val > 50.0:
                print(f"[*] 항성질량 '{mass_col}': 선형 척도(Linear scale, 중앙값={med_val:.2e} M_sun) 감지")
                print("    -> 천문학 표준인 log10(M* / M_sun)으로 자동 로그 변환합니다.")
                df = df[df[mass_col] > 0]
                df['log_mass'] = np.log10(df[mass_col])
            else:
                print(f"[*] 항성질량 '{mass_col}': 이미 로그 척도(Log scale, 중앙값={med_val:.2f})로 확인되었습니다.")
                df['log_mass'] = df[mass_col]
        
        # (2) 별 생성률 (SFR)
        sfr_col = self.matched_columns.get('sfr')
        if sfr_col:
            is_already_log = 'log' in sfr_col.lower() or df[sfr_col].min() < -0.5
            if not is_already_log and (df[sfr_col].min() >= 0 and df[sfr_col].median() > 0.05):
                print(f"[*] 별 생성률 '{sfr_col}': 선형 척도(Linear scale, M_sun/yr) 감지")
                print("    -> log10(SFR / [M_sun/yr])으로 자동 로그 변환합니다 (SFR > 0 조건 적용).")
                df = df[df[sfr_col] > 0]
                df['log_sfr'] = np.log10(df[sfr_col])
            else:
                print(f"[*] 별 생성률 '{sfr_col}': 이미 로그 척도(Log scale, 중앙값={df[sfr_col].median():.2f})로 확인되었습니다.")
                df['log_sfr'] = df[sfr_col]
                
        # (3) 금속함량 (Metallicity)
        met_col = self.matched_columns.get('metallicity')
        if met_col:
            print(f"[*] 금속함량 '{met_col}': 기체상 산소 존재비 12 + log(O/H) 단위 (중앙값={df[met_col].median():.2f})")
            df['metallicity_clean'] = df[met_col]
            df = df[(df['metallicity_clean'] >= 6.5) & (df['metallicity_clean'] <= 9.8)]
            
        # (4) 은하 유형 컬럼 정리
        type_col = self.matched_columns.get('galaxy_type')
        if type_col and type_col in df.columns:
            df['galaxy_type_clean'] = df[type_col].astype(str)
            print(f"[*] 은하 유형 분류 확인됨: {df['galaxy_type_clean'].unique()[:5]}")
        else:
            df['galaxy_type_clean'] = 'All'
            
        # 4. 무한대(Inf) 값 제거
        df = df.replace([np.inf, -np.inf], np.nan).dropna(subset=['log_mass', 'log_sfr', 'metallicity_clean'])
        
        self.processed_df = df
        final_n = len(df)
        print(f"\n[결과] 분석 가능한 최종 유효 표본 수 (Final N): {final_n:,} 개")
        print("="*70)
        
        return self.processed_df


# ==============================================================================
# 3. 통계적 상관관계 및 회귀분석 계산 엔진
# ==============================================================================
def calculate_statistics(x: np.ndarray, y: np.ndarray) -> dict:
    """
    두 변수 x, y 사이의 Pearson, Spearman 상관계수 및 선형 회귀 분석을 수행합니다.
    """
    mask = ~np.isnan(x) & ~np.isnan(y) & ~np.isinf(x) & ~np.isinf(y)
    x_val = x[mask]
    y_val = y[mask]
    n = len(x_val)
    
    if n < 3:
        return {'n': n, 'pearson_r': np.nan, 'pearson_p': np.nan,
                'spearman_rho': np.nan, 'spearman_p': np.nan,
                'slope': np.nan, 'intercept': np.nan, 'r_squared': np.nan}
        
    p_r, p_p = stats.pearsonr(x_val, y_val)
    s_rho, s_p = stats.spearmanr(x_val, y_val)
    reg = stats.linregress(x_val, y_val)
    r2 = reg.rvalue ** 2
    
    return {
        'n': n,
        'pearson_r': p_r,
        'pearson_p': p_p,
        'spearman_rho': s_rho,
        'spearman_p': s_p,
        'slope': reg.slope,
        'intercept': reg.intercept,
        'std_err': reg.stderr,
        'r_squared': r2
    }

def format_p_value(p: float) -> str:
    """p-value를 학술적 표기법으로 포맷팅"""
    if np.isnan(p):
        return "N/A"
    if p < 1e-10:
        return "< 1e-10 (***)"
    elif p < 0.001:
        return f"{p:.2e} (***)"
    elif p < 0.01:
        return f"{p:.4f} (**)"
    elif p < 0.05:
        return f"{p:.4f} (*)"
    else:
        return f"{p:.4f} (ns, p>=0.05)"


# ==============================================================================
# 4. 시각화 엔진 (고해상도 산점도 및 회귀선)
# ==============================================================================
class GalaxyVisualizer:
    """천문학 논문/탐구보고서 규격의 고해상도 시각화 클래스"""
    
    def __init__(self, output_dir: str = "output_plots"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        setup_plot_style()
        
    def plot_single_relation(self, df: pd.DataFrame, x_col: str, y_col: str,
                             x_label: str, y_label: str, title: str, filename: str,
                             hue_col: str = None) -> dict:
        """
        단일 변수 쌍에 대한 고해상도 산점도 및 회귀선 플롯을 생성하고 저장합니다.
        """
        x = df[x_col].values
        y = df[y_col].values
        stats_dict = calculate_statistics(x, y)
        
        fig, ax = plt.subplots(figsize=(8, 6), dpi=300)
        
        # 샘플 수가 너무 많으면 밀도 가시성을 위해 산점도 투명도 및 크기 조절
        alpha_val = max(0.1, min(0.6, 500.0 / len(df)))
        s_val = max(5, min(30, int(15000 / len(df))))
        
        if hue_col and hue_col in df.columns and df[hue_col].nunique() > 1:
            # 유형이 너무 많으면 상위 5개만 hue로 표시
            top_types = df[hue_col].value_counts().head(5).index
            df_plot = df.copy()
            df_plot[hue_col] = df_plot[hue_col].apply(lambda v: v if v in top_types else 'Other')
            sns.scatterplot(data=df_plot, x=x_col, y=y_col, hue=hue_col,
                            alpha=alpha_val, s=s_val, edgecolor='none', ax=ax)
            ax.legend(title="Galaxy Type", frameon=True, loc='lower right')
        else:
            ax.scatter(x, y, alpha=alpha_val, s=s_val, color='#1f77b4', edgecolors='none', label='Observed Galaxies')
            
        # 선형 회귀선 표시
        if not np.isnan(stats_dict['slope']):
            x_line = np.linspace(np.min(x), np.max(x), 100)
            y_line = stats_dict['slope'] * x_line + stats_dict['intercept']
            ax.plot(x_line, y_line, color='#d62728', linestyle='--', linewidth=2.2,
                    label=f"Fit: y = {stats_dict['slope']:.2f}x + {stats_dict['intercept']:.2f}")
            
        # 통계 텍스트 박스
        stat_box_text = (
            f"{title}\n"
            f"-------------------------------\n"
            f"N = {stats_dict['n']:,}\n"
            f"Pearson r = {stats_dict['pearson_r']:.3f}\n"
            f"  p-value = {format_p_value(stats_dict['pearson_p'])}\n"
            f"Spearman rho = {stats_dict['spearman_rho']:.3f}\n"
            f"  p-value = {format_p_value(stats_dict['spearman_p'])}\n"
            f"R^2 = {stats_dict['r_squared']:.3f}\n"
            f"Fit: y = {stats_dict['slope']:.2f}x + {stats_dict['intercept']:.2f}"
        )
        
        ax.text(0.04, 0.96, stat_box_text, transform=ax.transAxes,
                fontsize=10, verticalalignment='top',
                bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.9, edgecolor='#888888'))
        
        ax.set_xlabel(x_label, fontsize=12, fontweight='bold')
        ax.set_ylabel(y_label, fontsize=12, fontweight='bold')
        ax.set_title(f"Galaxy Relation: {title}", fontsize=14, fontweight='bold', pad=12)
        ax.grid(True, linestyle=':', alpha=0.6)
        
        save_path = os.path.join(self.output_dir, filename)
        plt.tight_layout()
        plt.savefig(save_path, dpi=300)
        plt.close()
        
        print(f"[저장 완료] 산점도: {save_path}")
        return stats_dict

    def plot_three_core_relations(self, df: pd.DataFrame, filename: str = "three_core_relations.png"):
        """3대 핵심 관계(SFMS, MZR, FMR)를 3분할 서브플롯으로 한눈에 시각화"""
        fig, axes = plt.subplots(1, 3, figsize=(20, 6), dpi=300)
        
        pairs = [
            ('log_mass', 'log_sfr', r"$\log_{10}(M_* / M_\odot)$", r"$\log_{10}(\mathrm{SFR} / [M_\odot\,\mathrm{yr}^{-1}])$",
             "Mass vs SFR (SFMS)", axes[0]),
            ('log_mass', 'metallicity_clean', r"$\log_{10}(M_* / M_\odot)$", r"$12 + \log(\mathrm{O/H})$",
             "Mass vs Metallicity (MZR)", axes[1]),
            ('log_sfr', 'metallicity_clean', r"$\log_{10}(\mathrm{SFR} / [M_\odot\,\mathrm{yr}^{-1}])$", r"$12 + \log(\mathrm{O/H})$",
             "SFR vs Metallicity (FMR Plane)", axes[2])
        ]
        
        alpha_val = max(0.1, min(0.5, 500.0 / len(df)))
        s_val = max(4, min(25, int(15000 / len(df))))
        
        for x_col, y_col, xl, yl, title, ax in pairs:
            x = df[x_col].values
            y = df[y_col].values
            st = calculate_statistics(x, y)
            
            ax.scatter(x, y, alpha=alpha_val, s=s_val, color='#2b5c8f', edgecolors='none')
            
            if not np.isnan(st['slope']):
                x_grid = np.linspace(np.min(x), np.max(x), 100)
                y_grid = st['slope'] * x_grid + st['intercept']
                ax.plot(x_grid, y_grid, color='#c93b2b', linestyle='--', linewidth=2.0)
                
            text_str = (
                f"N = {st['n']:,}\n"
                f"Pearson r = {st['pearson_r']:.3f}\n"
                f"Spearman rho = {st['spearman_rho']:.3f}\n"
                f"p-val = {format_p_value(st['pearson_p'])}\n"
                f"R^2 = {st['r_squared']:.3f}"
            )
            ax.text(0.05, 0.95, text_str, transform=ax.transAxes,
                    fontsize=9.5, verticalalignment='top',
                    bbox=dict(boxstyle='round,pad=0.4', facecolor='white', alpha=0.88, edgecolor='#cccccc'))
            
            ax.set_xlabel(xl, fontsize=11, fontweight='bold')
            ax.set_ylabel(yl, fontsize=11, fontweight='bold')
            ax.set_title(title, fontsize=12, fontweight='bold')
            ax.grid(True, linestyle=':', alpha=0.6)
            
        save_path = os.path.join(self.output_dir, filename)
        plt.tight_layout()
        plt.savefig(save_path, dpi=300)
        plt.close()
        print(f"[저장 완료] 3대 핵심 관계 종합 플롯: {save_path}")

# ==============================================================================
# 5. 표본 크기 검증 엔진 (Sample Size Convergence Test)
# ==============================================================================
def run_sample_size_test(df: pd.DataFrame,
                         relation: tuple = ('log_mass', 'log_sfr'),
                         sample_sizes: list = [100, 300, 500, 1000],
                         n_trials: int = 15,
                         output_dir: str = "output_plots") -> pd.DataFrame:
    """
    표본 크기 N에 따라 상관계수(r, rho)가 어떻게 변화하고 수렴하는지 검증합니다.
    """
    print("\n" + "="*70)
    print(" [Step 4] 표본 크기(Sample Size)에 따른 상관계수 수렴성 검증")
    print("="*70)
    
    x_col, y_col = relation
    total_n = len(df)
    valid_sizes = [s for s in sample_sizes if s <= total_n]
    if not valid_sizes:
        valid_sizes = [min(50, total_n), min(100, total_n)]
        
    print(f"- 전체 데이터 크기: {total_n:,} 개")
    print(f"- 테스트할 표본 크기 단계: {valid_sizes}")
    print(f"- 각 크기당 반복 표본추출 횟수(Trials): {n_trials} 회")
    
    results = []
    
    for size in valid_sizes:
        r_list = []
        rho_list = []
        p_list = []
        r2_list = []
        
        for trial in range(n_trials):
            sub_df = df.sample(n=size, replace=(size > total_n), random_state=42 + trial * 7)
            st = calculate_statistics(sub_df[x_col].values, sub_df[y_col].values)
            r_list.append(st['pearson_r'])
            rho_list.append(st['spearman_rho'])
            p_list.append(st['pearson_p'])
            r2_list.append(st['r_squared'])
            
        results.append({
            'Sample_Size_N': size,
            'Pearson_r_mean': np.mean(r_list),
            'Pearson_r_std': np.std(r_list),
            'Spearman_rho_mean': np.mean(rho_list),
            'Spearman_rho_std': np.std(rho_list),
            'R2_mean': np.mean(r2_list),
            'p_value_median': np.median(p_list)
        })
        
    res_df = pd.DataFrame(results)
    
    print("\n[표본 크기별 상관계수 수렴 결과표]")
    print("-" * 75)
    print(f"{'N':>6} | {'Pearson r (mean +- std)':>24} | {'Spearman rho (mean +- std)':>24} | {'R2 mean':>8}")
    print("-" * 75)
    for _, row in res_df.iterrows():
        print(f"{int(row['Sample_Size_N']):6d} | {row['Pearson_r_mean']:7.3f} +- {row['Pearson_r_std']:6.3f}         | {row['Spearman_rho_mean']:7.3f} +- {row['Spearman_rho_std']:6.3f}          | {row['R2_mean']:7.3f}")
    print("-" * 75)
    
    # 수렴 그래프 생성
    fig, ax = plt.subplots(figsize=(9, 5), dpi=300)
    
    ax.errorbar(res_df['Sample_Size_N'], res_df['Pearson_r_mean'], yerr=res_df['Pearson_r_std'],
                fmt='-o', color='#1f77b4', capsize=5, capthick=1.5, linewidth=2, markersize=6,
                label=r'Pearson $r$ (mean $\pm 1\sigma$)')
    ax.errorbar(res_df['Sample_Size_N'], res_df['Spearman_rho_mean'], yerr=res_df['Spearman_rho_std'],
                fmt='--s', color='#ff7f0e', capsize=5, capthick=1.5, linewidth=2, markersize=6,
                label=r'Spearman $\rho$ (mean $\pm 1\sigma$)')
    
    ax.set_xlabel('Sample Size (N)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Correlation Coefficient', fontsize=12, fontweight='bold')
    ax.set_title(f'Convergence of Correlation vs Sample Size ({x_col} vs {y_col})', fontsize=13, fontweight='bold')
    ax.legend(fontsize=11, loc='best')
    ax.grid(True, linestyle=':', alpha=0.7)
    
    save_path = os.path.join(output_dir, "sample_size_convergence.png")
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.close()
    print(f"[저장 완료] 표본 크기 수렴 그래프: {save_path}")
    
    csv_save_path = os.path.join(output_dir, "sample_size_convergence_results.csv")
    res_df.to_csv(csv_save_path, index=False)
    print(f"[저장 완료] 표본 크기 수렴 데이터표: {csv_save_path}")
    
    return res_df


# ==============================================================================
# 6. 은하 유형별(Subtype) 상관관계 비교 분석 엔진
# ==============================================================================
def run_galaxy_type_analysis(df: pd.DataFrame, output_dir: str = "output_plots") -> pd.DataFrame:
    """은하 유형별(Star-forming, AGN, Composite 등) 하위 집단 상관관계 비교"""
    if 'galaxy_type_clean' not in df.columns or df['galaxy_type_clean'].nunique() <= 1:
        print("\n[*] 은하 유형 분류 컬럼이 없거나 단일 유형이므로 유형별 세부 분석을 건너뜁니다.")
        return None
        
    print("\n" + "="*70)
    print(" [Step 5] 은하 유형별(Subtype) 상관관계 비교 분석")
    print("="*70)
    
    types = df['galaxy_type_clean'].unique()
    type_results = []
    
    relations = [
        ('log_mass', 'log_sfr', 'Mass - SFR'),
        ('log_mass', 'metallicity_clean', 'Mass - Metallicity'),
        ('log_sfr', 'metallicity_clean', 'SFR - Metallicity')
    ]
    
    for gtype in types:
        sub = df[df['galaxy_type_clean'] == gtype]
        if len(sub) < 10:
            continue
        for x_col, y_col, rel_name in relations:
            st = calculate_statistics(sub[x_col].values, sub[y_col].values)
            type_results.append({
                'Galaxy_Type': gtype,
                'Relation': rel_name,
                'N': st['n'],
                'Pearson_r': st['pearson_r'],
                'Spearman_rho': st['spearman_rho'],
                'p_value': st['pearson_p'],
                'R_squared': st['r_squared']
            })
            
    type_df = pd.DataFrame(type_results)
    
    print("\n[은하 유형별 상관분석 요약표]")
    print("-" * 80)
    print(f"{'Galaxy Type':<16} | {'Relation':<20} | {'N':>5} | {'Pearson r':>9} | {'Spearman rho':>12} | {'R2':>6}")
    print("-" * 80)
    for _, row in type_df.iterrows():
        print(f"{str(row['Galaxy_Type']):<16} | {row['Relation']:<20} | {int(row['N']):5d} | {row['Pearson_r']:9.3f} | {row['Spearman_rho']:12.3f} | {row['R_squared']:6.3f}")
    print("-" * 80)
    
    type_csv_path = os.path.join(output_dir, "galaxy_type_correlation_summary.csv")
    type_df.to_csv(type_csv_path, index=False)
    print(f"[저장 완료] 은하 유형별 분석 결과표: {type_csv_path}")
    
    return type_df


# ==============================================================================
# 7. 메인 파이프라인 및 최종 결과 출력
# ==============================================================================
def run_galaxy_analysis_pipeline(csv_path: str = None, output_dir: str = "galaxy_analysis_output"):
    """전체 은하 상관관계 분석 종합 실행 파이프라인"""
    os.makedirs(output_dir, exist_ok=True)
    
    print("="*70)
    print("  은하 물리량 및 화학적 조성 상관관계 자동 분석 파이프라인")
    print("="*70)
    
    # 1. 데이터 로드 및 전처리
    processor = GalaxyDataProcessor(filepath=csv_path)
    processor.inspect_and_map_columns()
    clean_df = processor.clean_and_transform()
    
    # 2. 시각화 및 상관분석 객체 생성
    visualizer = GalaxyVisualizer(output_dir=output_dir)
    
    # 3. 3대 핵심 관계 단일 산점도 생성
    print("\n" + "="*70)
    print(" [Step 3] 핵심 3대 관계 상관분석 및 산점도 시각화")
    print("="*70)
    
    core_results = {}
    
    # (1) 항성질량 - 별 생성률 (SFMS)
    core_results['Mass - SFR'] = visualizer.plot_single_relation(
        clean_df, 'log_mass', 'log_sfr',
        r"$\log_{10}(M_* / M_\odot)$ [Stellar Mass]",
        r"$\log_{10}(\mathrm{SFR} / [M_\odot\,\mathrm{yr}^{-1}])$ [Star Formation Rate]",
        "Mass vs SFR", "scatter_mass_vs_sfr.png",
        hue_col='galaxy_type_clean' if clean_df['galaxy_type_clean'].nunique() > 1 else None
    )
    
    # (2) 항성질량 - 금속함량 (MZR)
    core_results['Mass - Metallicity'] = visualizer.plot_single_relation(
        clean_df, 'log_mass', 'metallicity_clean',
        r"$\log_{10}(M_* / M_\odot)$ [Stellar Mass]",
        r"$12 + \log(\mathrm{O/H})$ [Gas-phase Metallicity]",
        "Mass vs Metallicity", "scatter_mass_vs_metallicity.png",
        hue_col='galaxy_type_clean' if clean_df['galaxy_type_clean'].nunique() > 1 else None
    )
    
    # (3) 별 생성률 - 금속함량 (FMR)
    core_results['SFR - Metallicity'] = visualizer.plot_single_relation(
        clean_df, 'log_sfr', 'metallicity_clean',
        r"$\log_{10}(\mathrm{SFR} / [M_\odot\,\mathrm{yr}^{-1}])$ [Star Formation Rate]",
        r"$12 + \log(\mathrm{O/H})$ [Gas-phase Metallicity]",
        "SFR vs Metallicity", "scatter_sfr_vs_metallicity.png",
        hue_col='galaxy_type_clean' if clean_df['galaxy_type_clean'].nunique() > 1 else None
    )
    
    # 3대 종합 플롯 생성
    visualizer.plot_three_core_relations(clean_df, "three_core_relations_summary.png")
    
    # 4. 표본 크기 검증 (Sample Size Test)
    sample_sizes = [100, 300, 500, 1000]
    run_sample_size_test(clean_df, relation=('log_mass', 'log_sfr'),
                         sample_sizes=sample_sizes, n_trials=15, output_dir=output_dir)
    
    # 5. 은하 유형별 세부 분석
    run_galaxy_type_analysis(clean_df, output_dir=output_dir)
    
    # 6. 상관관계 요약 CSV 저장
    summary_rows = []
    for rel_name, st in core_results.items():
        summary_rows.append({
            'Relation': rel_name,
            'N': st['n'],
            'Pearson_r': st['pearson_r'],
            'Pearson_p': st['pearson_p'],
            'Spearman_rho': st['spearman_rho'],
            'Spearman_p': st['spearman_p'],
            'Slope': st['slope'],
            'Intercept': st['intercept'],
            'R_squared': st['r_squared']
        })
    summary_df = pd.DataFrame(summary_rows)
    summary_csv_path = os.path.join(output_dir, "galaxy_correlation_summary.csv")
    summary_df.to_csv(summary_csv_path, index=False)
    print(f"[저장 완료] 종합 상관계수 요약표: {summary_csv_path}")
    
    # 7. 콘솔 최종 형식화 요약 출력
    print("\n" + "="*70)
    print("--------------------------------")
    print("Galaxy Correlation Analysis")
    print("--------------------------------")
    for rel_name, st in core_results.items():
        print(f"\n{rel_name}")
        print(f"N = {st['n']}")
        print(f"Pearson r = {st['pearson_r']:.3f}")
        print(f"Spearman rho = {st['spearman_rho']:.3f}")
        print(f"p-value = {format_p_value(st['pearson_p'])}")
        print(f"R^2 = {st['r_squared']:.3f}")
    print("--------------------------------")
    
    # 8. 학술적 주의사항 및 경고 출력
    print("\n" + "#"*70)
    print(" [학술적 주의사항 (Important Scientific Notice)]")
    print(" 1. 상관관계 != 인과관계:")
    print("    두 물리량 간의 높은 통계적 상관계수(r)가 직접적인 인과관계를 입증하지는 않습니다.")
    print("    예를 들어 은하 질량과 금속함량의 강한 상관관계(MZR)는 은하의 중력 퍼텐셜 우물(암흑물질 헤일로 질량),")
    print("    성간물질 유입(inflow) 및 항성풍 유출(outflow) 등 복합적인 진화 메커니즘이 함께 작용한 결과입니다.")
    if processor.is_synthetic:
        print("\n [!] [가상 데이터 경고 (Mock Data Warning)]:")
        print("    현재 분석에 사용된 데이터는 프로그램 기능 검증을 위해 생성된 '가상 은하 데이터'입니다.")
        print("    가상 데이터의 수치와 결과로 실제 천문학적 결론이나 학술 논문의 주장을 작성해서는 안 되며,")
        print("    실제 탐구를 수행할 때는 SDSS 관측 카탈로그 CSV 파일을 입력해야 합니다.")
    else:
        print("\n [관측 데이터 확인]: 실제 관측 데이터셋을 기반으로 정상 분석되었습니다.")
    print("#"*70 + "\n")
    
    return clean_df, summary_df

if __name__ == "__main__":
    target_file = "galaxy_master_complete_all.csv" if os.path.exists("galaxy_master_complete_all.csv") else None
    run_galaxy_analysis_pipeline(csv_path=target_file)
