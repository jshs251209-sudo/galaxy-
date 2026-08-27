"""
은하 진화 데이터 대화형 시각화 모듈
================================================
Plotly를 사용하여 웹 대시보드에 임베딩할 수 있는 대화형 HTML 그래프를 생성합니다.
"""

import os
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import config

# 대화형 플롯 저장 디렉토리 생성
INTERACTIVE_PLOT_DIR = os.path.join(config.PLOT_DIR, 'interactive')
os.makedirs(INTERACTIVE_PLOT_DIR, exist_ok=True)

def generate_interactive_main_sequence(df):
    """
    대화형 주계열 다이어그램 생성
    """
    cols_to_check = ['log_stellar_mass', 'log_sfr']
    if 'bpt_class' in df.columns:
        cols_to_check.append('bpt_class')
    df_clean = df.dropna(subset=cols_to_check)
    
    hover_cols = []
    if 'specobjid' in df_clean.columns: hover_cols.append('specobjid')
    if 'z' in df_clean.columns: hover_cols.append('z')
    if 'metallicity_oh' in df_clean.columns: hover_cols.append('metallicity_oh')
    
    fig = px.scatter(
        df_clean,
        x='log_stellar_mass',
        y='log_sfr',
        color='bpt_class' if 'bpt_class' in df.columns else None,
        hover_data=hover_cols if hover_cols else None,
        title='Interactive Star-Forming Main Sequence',
        labels={
            'log_stellar_mass': 'Log Stellar Mass (M_sun)',
            'log_sfr': 'Log SFR (M_sun/yr)',
            'bpt_class': 'BPT Classification'
        },
        opacity=0.6,
        color_discrete_map={
            'Star-forming': 'blue',
            'Composite': 'green',
            'AGN': 'red',
            'LINER': 'orange'
        } if 'bpt_class' in df.columns else None
    )
    
    fig.update_layout(template="plotly_white")
    
    output_path = os.path.join(INTERACTIVE_PLOT_DIR, 'main_sequence_interactive.html')
    fig.write_html(output_path)
    print(f"[저장 완료] 대화형 주계열: {output_path}")

def generate_interactive_bpt(df):
    """
    대화형 BPT 다이어그램 생성
    """
    cols_to_check = ['log_nii_ha', 'log_oiii_hb']
    if 'bpt_class' in df.columns:
        cols_to_check.append('bpt_class')
    df_clean = df.dropna(subset=cols_to_check)
    
    hover_cols = []
    if 'specobjid' in df_clean.columns: hover_cols.append('specobjid')
    if 'log_stellar_mass' in df_clean.columns: hover_cols.append('log_stellar_mass')
    if 'log_sfr' in df_clean.columns: hover_cols.append('log_sfr')
    
    fig = px.scatter(
        df_clean,
        x='log_nii_ha',
        y='log_oiii_hb',
        color='bpt_class' if 'bpt_class' in df.columns else None,
        hover_data=hover_cols if hover_cols else None,
        title='Interactive BPT Diagnostic Diagram',
        labels={
            'log_nii_ha': 'Log([NII]/Hα)',
            'log_oiii_hb': 'Log([OIII]/Hβ)',
            'bpt_class': 'Classification'
        },
        opacity=0.7,
        color_discrete_map={
            'Star-forming': 'blue',
            'Composite': 'green',
            'AGN': 'red',
            'LINER': 'orange'
        } if 'bpt_class' in df.columns else None
    )
    
    # Kauffmann & Kewley 곡선 추가
    x_kauff = np.linspace(-2.0, 0.0, 100)
    y_kauff = config.BPT_KAUFFMANN_PARAMS[0] / (x_kauff - config.BPT_KAUFFMANN_PARAMS[1]) + config.BPT_KAUFFMANN_PARAMS[2]
    
    x_kewley = np.linspace(-2.0, 0.4, 100)
    y_kewley = config.BPT_KEWLEY_PARAMS[0] / (x_kewley - config.BPT_KEWLEY_PARAMS[1]) + config.BPT_KEWLEY_PARAMS[2]
    
    fig.add_trace(go.Scatter(x=x_kauff, y=y_kauff, mode='lines', name='Kauffmann+2003', line=dict(color='black', dash='dash')))
    fig.add_trace(go.Scatter(x=x_kewley, y=y_kewley, mode='lines', name='Kewley+2001', line=dict(color='black')))
    
    fig.update_layout(template="plotly_white", xaxis_range=[-1.5, 1.0], yaxis_range=[-1.5, 1.5])
    
    output_path = os.path.join(INTERACTIVE_PLOT_DIR, 'bpt_interactive.html')
    fig.write_html(output_path)
    print(f"[저장 완료] 대화형 BPT: {output_path}")

def generate_interactive_color_mass(df):
    """
    대화형 색-질량 다이어그램 생성
    """
    df_clean = df.dropna(subset=['log_stellar_mass', 'g_r'])
    
    hover_cols = []
    if 'specobjid' in df_clean.columns: hover_cols.append('specobjid')
    if 'bpt_class' in df_clean.columns: hover_cols.append('bpt_class')
    
    fig = px.scatter(
        df_clean,
        x='log_stellar_mass',
        y='g_r',
        color='g_r',
        color_continuous_scale='RdYlBu_r',
        hover_data=hover_cols if hover_cols else None,
        title='Interactive Color-Mass Diagram',
        labels={
            'log_stellar_mass': 'Log Stellar Mass (M_sun)',
            'g_r_color': 'g - r Color'
        },
        opacity=0.7
    )
    
    fig.update_layout(template="plotly_white")
    
    output_path = os.path.join(INTERACTIVE_PLOT_DIR, 'color_mass_interactive.html')
    fig.write_html(output_path)
    print(f"[저장 완료] 대화형 색-질량: {output_path}")

def generate_all_interactive_plots(df=None):
    """
    모든 대화형 시각화 생성 및 저장 메인 함수
    """
    if df is None:
        try:
            df = pd.read_csv(config.MASTER_DATASET_FILE)
            print(f"[데이터 로드 완료] {config.MASTER_DATASET_FILE}")
        except FileNotFoundError:
            print(f"[오류] 마스터 데이터셋 파일을 찾을 수 없습니다: {config.MASTER_DATASET_FILE}")
            return
            
    print("대화형 그래프 생성을 시작합니다...")
    generate_interactive_main_sequence(df)
    generate_interactive_bpt(df)
    generate_interactive_color_mass(df)
    print("모든 대화형 그래프 생성이 완료되었습니다.")

if __name__ == "__main__":
    generate_all_interactive_plots()
