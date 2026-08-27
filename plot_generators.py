"""
은하 진화 다차원 분석 및 관측 소프트웨어 (버전 2.0)
plot_generators.py - 물리적/화학적 다이어그램 생성기

D4000(은하 진화 지표)을 기준으로 각 2D 산점도의 진화 설명 적합도를 계산하고
물리적/화학적 특성에 대한 방대한 플롯을 자동 생성합니다.
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import itertools
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
import config

# 한글 폰트 및 마이너스 기호 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

def calculate_evolution_metric(df, x_col, y_col, target_col='D4000'):
    """
    X, Y 변수가 D4000을 얼마나 잘 설명하는지 다중 선형 회귀의 R^2 점수로 평가합니다.
    결과값은 진화 설명 적합도로 사용됩니다.
    """
    if target_col not in df.columns:
        return 0.0

    valid_data = df[[x_col, y_col, target_col]].replace([np.inf, -np.inf], np.nan).dropna()
    if len(valid_data) < 10:
        return 0.0
    
    X = valid_data[[x_col, y_col]]
    y = valid_data[target_col]
    
    try:
        model = LinearRegression()
        model.fit(X, y)
        predictions = model.predict(X)
        score = r2_score(y, predictions)
        return max(0.0, score) # 음수 점수는 0으로 처리
    except Exception as e:
        return 0.0

def create_scatter_plot(df, x_col, y_col, x_label, y_label, output_dir, filename_prefix, target_col='D4000'):
    """
    주어진 X, Y 컬럼에 대한 산점도를 그리고 D4000을 기준으로 색상을 매핑합니다.
    진화 설명 적합도를 계산하여 제목에 포함합니다.
    """
    if target_col not in df.columns:
        target_col_use = None
        plot_df = df[[x_col, y_col]].replace([np.inf, -np.inf], np.nan).dropna()
        score = 0.0
    else:
        target_col_use = target_col
        plot_df = df[[x_col, y_col, target_col]].replace([np.inf, -np.inf], np.nan).dropna()
        score = calculate_evolution_metric(df, x_col, y_col, target_col)

    if len(plot_df) == 0:
        print(f"데이터가 부족하여 {x_col} vs {y_col} 플롯을 생성할 수 없습니다.")
        return
    
    plt.figure(figsize=(10, 8))
    
    if target_col_use:
        scatter = plt.scatter(plot_df[x_col], plot_df[y_col], c=plot_df[target_col_use], cmap='viridis', s=2, alpha=0.6)
        cbar = plt.colorbar(scatter)
        cbar.set_label('D4000 (은하 연령 지표)')
    else:
        plt.scatter(plot_df[x_col], plot_df[y_col], s=2, alpha=0.6, color='blue')
    
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    
    if target_col_use:
        plt.title(f"{x_label} vs {y_label}\n진화 설명 적합도: {score:.4f}")
    else:
        plt.title(f"{x_label} vs {y_label}")
        
    plt.grid(True, linestyle='--', alpha=0.5)
    
    # 이상치에 의해 축이 너무 넓어지는 것을 방지하기 위해 1% ~ 99% 백분위수로 제한
    x_min, x_max = np.percentile(plot_df[x_col], [1, 99])
    y_min, y_max = np.percentile(plot_df[y_col], [1, 99])
    
    if x_min < x_max: plt.xlim(x_min, x_max)
    if y_min < y_max: plt.ylim(y_min, y_max)
    
    plt.tight_layout()
    filename = f"{filename_prefix}_{x_col}_vs_{y_col}.png"
    filepath = os.path.join(output_dir, filename)
    plt.savefig(filepath, dpi=300)
    plt.close()
    
    print(f"생성 완료: {filename} (적합도: {score:.4f})")

def generate_physical_diagrams(df):
    """
    물리적 특성에 대한 다이어그램 생성 (약 30개 조합)
    """
    print("--- 물리적 다이어그램 생성 시작 ---")
    
    physical_features = {
        'Mass': '항성 질량 (log M/M_sun)',
        'petroRad_r': '크기 (Petrosian Radius r-band)',
        'Concentration': '집중도 (R90/R50)',
        'SurfaceBrightness': '표면 밝기',
        'velDisp': '속도 분산 (km/s)',
        'SFR': '별 생성률 (log SFR)',
        'u_r': 'u-r 색상',
        'g_r': 'g-r 색상',
        'z': '적색편이 (Redshift)'
    }
    
    available_features = {k: v for k, v in physical_features.items() if k in df.columns}
    combinations = list(itertools.combinations(available_features.keys(), 2))
    
    count = 0
    for x_col, y_col in combinations:
        if count >= 35:
            break
        create_scatter_plot(
            df, 
            x_col, 
            y_col, 
            available_features[x_col], 
            available_features[y_col], 
            config.PHYSICAL_PLOT_DIR,
            "phys"
        )
        count += 1
        
    print(f"물리적 다이어그램 {count}개 생성 완료.\n")

def generate_chemical_diagrams(df):
    """
    화학적 특성에 대한 다이어그램 생성 (약 20개 조합)
    """
    print("--- 화학적 다이어그램 생성 시작 ---")
    
    chemical_features = {
        'Mass': '항성 질량 (log M/M_sun)',
        'Metallicity': '금속함량 (12 + log(O/H))',
        'D4000': 'D4000 (4000Å Break)',
        'NII_Ha': 'BPT: log([NII]/Hα)',
        'OIII_Hb': 'BPT: log([OIII]/Hβ)',
        'SII_Ha': 'log([SII]/Hα)',
        'OII_OIII': 'log([OII]/[OIII])',
        'E_B_V': '먼지 소광 E(B-V)'
    }
    
    available_features = {k: v for k, v in chemical_features.items() if k in df.columns}
    combinations = list(itertools.combinations(available_features.keys(), 2))
    
    count = 0
    for x_col, y_col in combinations:
        if count >= 25:
            break
        create_scatter_plot(
            df, 
            x_col, 
            y_col, 
            available_features[x_col], 
            available_features[y_col], 
            config.CHEMICAL_PLOT_DIR,
            "chem"
        )
        count += 1
        
    print(f"화학적 다이어그램 {count}개 생성 완료.\n")

def generate_all_plots():
    """
    모든 물리적, 화학적 플롯을 일괄 생성합니다.
    """
    if not os.path.exists(config.MASTER_DATASET_FILE):
        print(f"데이터 파일이 존재하지 않습니다: {config.MASTER_DATASET_FILE}")
        print("먼저 데이터 수집/전처리 작업이 완료되어야 합니다.")
        return

    print(f"데이터 로딩 중... ({config.MASTER_DATASET_FILE})")
    df = pd.read_csv(config.MASTER_DATASET_FILE)
    
    # --- 유도 변수 계산 (만약 존재하지 않을 경우를 대비) ---
    if 'Concentration' not in df.columns and 'petroR90_r' in df.columns and 'petroR50_r' in df.columns:
        df['Concentration'] = df['petroR90_r'] / df['petroR50_r']
    if 'u_r' not in df.columns and 'u' in df.columns and 'r' in df.columns:
        df['u_r'] = df['u'] - df['r']
    if 'g_r' not in df.columns and 'g' in df.columns and 'r' in df.columns:
        df['g_r'] = df['g'] - df['r']
        
    # 방출선 기반 화학적 특성 방어 코드 (로그 비율)
    def calc_log_ratio(num_col, den_col):
        if num_col in df.columns and den_col in df.columns:
            # 0 또는 음수 값은 np.nan 처리하여 로그 연산 오류 방지
            num = np.where(df[num_col] > 0, df[num_col], np.nan)
            den = np.where(df[den_col] > 0, df[den_col], np.nan)
            return np.log10(num / den)
        return np.nan

    if 'NII_Ha' not in df.columns:
        df['NII_Ha'] = calc_log_ratio('nii_6584_flux', 'h_alpha_flux')
    if 'OIII_Hb' not in df.columns:
        df['OIII_Hb'] = calc_log_ratio('oiii_5007_flux', 'h_beta_flux')
    if 'SII_Ha' not in df.columns:
        df['SII_Ha'] = calc_log_ratio('sii_6717_flux', 'h_alpha_flux')
    if 'OII_OIII' not in df.columns:
        df['OII_OIII'] = calc_log_ratio('oii_3726_flux', 'oiii_5007_flux')

    generate_physical_diagrams(df)
    generate_chemical_diagrams(df)
    
    print("모든 다이어그램 생성이 완료되었습니다.")

if __name__ == "__main__":
    generate_all_plots()
