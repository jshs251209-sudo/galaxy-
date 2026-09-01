import os
import sys
import io
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# UTF-8 출력 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.append(r"c:\Users\neato\Desktop\정현\03_과학탐구_대회\YSC_대회")
import config

INTERACTIVE_PLOT_DIR = os.path.join(config.PLOT_DIR, 'interactive')
os.makedirs(INTERACTIVE_PLOT_DIR, exist_ok=True)

CLASS_COLORS = {
    "나선은하 (Spiral Galaxy)": "#2563eb",
    "막대나선은하 (Barred Spiral Galaxy)": "#0284c7",
    "타원은하 (Elliptical Galaxy)": "#dc2626",
    "렌즈형은하 (Lenticular Galaxy)": "#ea580c",
    "마젤란형 은하 (Magellanic Galaxy)": "#10b981",
    "고리은하 (Ring Galaxy)": "#8b5cf6",
    "전파은하 (Radio Galaxy)": "#b91c1c",
    "퀘이사 (Quasar)": "#d97706",
    "세이퍼트은하 (Seyfert Galaxy)": "#9333ea",
    "불규칙은하 (Irregular Galaxy)": "#059669",
    "병합은하 (Merger Galaxy)": "#db2777"
}

def generate_interactive_plots():
    if not os.path.exists(config.MASTER_DATASET_FILE):
        print(f"데이터 파일이 없습니다: {config.MASTER_DATASET_FILE}")
        return
        
    df = pd.read_csv(config.MASTER_DATASET_FILE)
    sample_df = df.sample(min(len(df), 10000), random_state=42)

    # 1. Interactive Main Sequence
    fig_ms = px.scatter(
        sample_df,
        x='log_stellar_mass',
        y='log_sfr',
        color='galaxy_type',
        color_discrete_map=CLASS_COLORS,
        hover_data=['specObjID', 'z', 'metallicity_oh', 'velDisp', 'color_u_r'],
        title='SDSS 11대 은하 분류 대화형 은하 주계열 (Star-Forming Main Sequence)',
        labels={'log_stellar_mass': '항성 질량 log(M*/M_sun)', 'log_sfr': '별 생성률 log(SFR [M_sun/yr])', 'galaxy_type': '은하 분류'},
        opacity=0.65
    )
    fig_ms.update_layout(template="plotly_white")
    out_ms = os.path.join(INTERACTIVE_PLOT_DIR, 'main_sequence_interactive.html')
    fig_ms.write_html(out_ms)
    print(f"[저장 완료] 대화형 주계열: {out_ms}")

    # 2. Interactive BPT Diagram
    fig_bpt = px.scatter(
        sample_df,
        x='log_nii_ha',
        y='log_oiii_hb',
        color='galaxy_type',
        color_discrete_map=CLASS_COLORS,
        hover_data=['specObjID', 'z', 'log_stellar_mass', 'log_sfr', 'd4000_n'],
        title='SDSS 11대 은하 분류 대화형 BPT 이온화 진단도',
        labels={'log_nii_ha': 'log([NII]/Hα)', 'log_oiii_hb': 'log([OIII]/Hβ)', 'galaxy_type': '은하 분류'},
        opacity=0.65
    )
    x_kauff = np.linspace(-2.0, 0.0, 100)
    y_kauff = 0.61 / (x_kauff - 0.05) + 1.3
    x_kewley = np.linspace(-2.0, 0.4, 100)
    y_kewley = 0.61 / (x_kewley - 0.47) + 1.19
    fig_bpt.add_trace(go.Scatter(x=x_kauff, y=y_kauff, mode='lines', name='Kauffmann (2003) SF', line=dict(color='black', dash='dash')))
    fig_bpt.add_trace(go.Scatter(x=x_kewley, y=y_kewley, mode='lines', name='Kewley (2001) AGN', line=dict(color='red')))
    fig_bpt.update_layout(template="plotly_white", xaxis_range=[-1.8, 0.8], yaxis_range=[-1.5, 1.6])
    out_bpt = os.path.join(INTERACTIVE_PLOT_DIR, 'bpt_interactive.html')
    fig_bpt.write_html(out_bpt)
    print(f"[저장 완료] 대화형 BPT: {out_bpt}")

    # 3. Interactive Color-Mass
    fig_cm = px.scatter(
        sample_df,
        x='log_stellar_mass',
        y='color_u_r',
        color='galaxy_type',
        color_discrete_map=CLASS_COLORS,
        hover_data=['specObjID', 'z', 'd4000_n', 'concentration_index_r'],
        title='SDSS 11대 은하 분류 대화형 색-질량 도표 (Color-Mass Diagram)',
        labels={'log_stellar_mass': '항성 질량 log(M*/M_sun)', 'color_u_r': '색지수 (u - r) [mag]', 'galaxy_type': '은하 분류'},
        opacity=0.65
    )
    fig_cm.update_layout(template="plotly_white")
    out_cm = os.path.join(INTERACTIVE_PLOT_DIR, 'color_mass_interactive.html')
    fig_cm.write_html(out_cm)
    print(f"[저장 완료] 대화형 색-질량: {out_cm}")

if __name__ == "__main__":
    generate_interactive_plots()
