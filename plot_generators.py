import os
import sys
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# UTF-8 설정 및 한글 폰트 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False
sns.set_theme(style="ticks")
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

sys.path.append(r"c:\Users\neato\Desktop\정현\03_과학탐구_대회\YSC_대회")
import config

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

def generate_all_plots():
    print("="*60)
    print("--- 200개 물리량 & 암흑물질 & 회전곡선 시각화 생성 시작 ---")
    print("="*60)
    
    if not os.path.exists(config.MASTER_DATASET_FILE):
        print(f"데이터 파일이 없습니다: {config.MASTER_DATASET_FILE}")
        return
        
    df = pd.read_csv(config.MASTER_DATASET_FILE)
    os.makedirs(config.PLOT_DIR, exist_ok=True)

    sample_df = df.sample(min(len(df), 15000), random_state=42)

    # 1. BPT 다이어그램
    print("[1/6] BPT 다이어그램 생성 중...")
    plt.figure(figsize=(10, 8))
    x_kauff = np.linspace(-2.0, 0.0, 200)
    y_kauff = 0.61 / (x_kauff - 0.05) + 1.3
    x_kewley = np.linspace(-2.0, 0.4, 200)
    y_kewley = 0.61 / (x_kewley - 0.47) + 1.19
    
    plt.plot(x_kauff, y_kauff, 'k--', lw=2, label='Kauffmann et al. (2003) SF 경계')
    plt.plot(x_kewley, y_kewley, 'r-', lw=2, label='Kewley et al. (2001) 극대 광이온화')
    
    for gtype, color in CLASS_COLORS.items():
        sub = sample_df[sample_df['galaxy_type'] == gtype]
        if len(sub) > 0:
            short_name = gtype.split(" (")[0]
            plt.scatter(sub['log_nii_ha'], sub['log_oiii_hb'], s=12, alpha=0.5, color=color, label=short_name)
            
    plt.xlim(-1.8, 0.8)
    plt.ylim(-1.5, 1.6)
    plt.xlabel(r'$\log([\mathrm{N\,II}]\lambda6584 / \mathrm{H}\alpha)$', fontsize=13)
    plt.ylabel(r'$\log([\mathrm{O\,III}]\lambda5007 / \mathrm{H}\beta)$', fontsize=13)
    plt.title('SDSS 11대 은하 분류 BPT 이온화 진단도 (BPT Diagram)', fontsize=15, pad=12)
    plt.legend(bbox_to_anchor=(1.04, 1), loc="upper left", markerscale=2.5, fontsize=10)
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.tight_layout()
    plt.savefig(os.path.join(config.PLOT_DIR, "bpt_diagram.png"), dpi=300)
    plt.close()

    # 2. 은하 주계열 (Main Sequence)
    print("[2/6] 은하 주계열 (Main Sequence) 생성 중...")
    plt.figure(figsize=(10, 8))
    for gtype, color in CLASS_COLORS.items():
        sub = sample_df[sample_df['galaxy_type'] == gtype]
        if len(sub) > 0:
            short_name = gtype.split(" (")[0]
            plt.scatter(sub['lgm_tot_p50'], sub['sfr_tot_p50'], s=12, alpha=0.5, color=color, label=short_name)
            
    plt.xlabel(r'항성 질량 $\log(M_* / M_\odot)$', fontsize=13)
    plt.ylabel(r'별 생성률 $\log(\mathrm{SFR}\,[M_\odot/\mathrm{yr}])$', fontsize=13)
    plt.title('SDSS 11대 은하 주계열 (Galaxy Star-Forming Main Sequence)', fontsize=15, pad=12)
    plt.legend(bbox_to_anchor=(1.04, 1), loc="upper left", markerscale=2.5, fontsize=10)
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.tight_layout()
    plt.savefig(os.path.join(config.PLOT_DIR, "main_sequence.png"), dpi=300)
    plt.close()

    # 3. 질량-금속량 관계 (MZR)
    print("[3/6] 질량-금속량 관계 (MZR) 생성 중...")
    plt.figure(figsize=(10, 8))
    for gtype, color in CLASS_COLORS.items():
        sub = sample_df[sample_df['galaxy_type'] == gtype]
        if len(sub) > 0:
            short_name = gtype.split(" (")[0]
            plt.scatter(sub['lgm_tot_p50'], sub['oh_p50'], s=12, alpha=0.5, color=color, label=short_name)
            
    plt.xlabel(r'항성 질량 $\log(M_* / M_\odot)$', fontsize=13)
    plt.ylabel(r'기체 산소 풍부도 $12 + \log(\mathrm{O/H})$', fontsize=13)
    plt.title('SDSS 11대 은하 질량-금속량 관계 (Mass-Metallicity Relation)', fontsize=15, pad=12)
    plt.legend(bbox_to_anchor=(1.04, 1), loc="upper left", markerscale=2.5, fontsize=10)
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.tight_layout()
    plt.savefig(os.path.join(config.PLOT_DIR, "mass_metallicity.png"), dpi=300)
    plt.close()

    # 4. 색-질량 도표 (Color-Mass)
    print("[4/6] 색-질량 도표 (Color-Mass Diagram) 생성 중...")
    plt.figure(figsize=(10, 8))
    for gtype, color in CLASS_COLORS.items():
        sub = sample_df[sample_df['galaxy_type'] == gtype]
        if len(sub) > 0:
            short_name = gtype.split(" (")[0]
            plt.scatter(sub['lgm_tot_p50'], sub['color_u_r'], s=12, alpha=0.5, color=color, label=short_name)
            
    plt.axhline(y=2.2, color='red', linestyle='--', alpha=0.7, label='Red Sequence 하한')
    plt.axhline(y=1.8, color='blue', linestyle='--', alpha=0.7, label='Blue Cloud 상한')
    plt.xlabel(r'항성 질량 $\log(M_* / M_\odot)$', fontsize=13)
    plt.ylabel(r'색지수 $(u - r)\,\mathrm{[mag]}$', fontsize=13)
    plt.title('SDSS 11대 은하 색-질량 도표 (Color-Mass Diagram & Bimodality)', fontsize=15, pad=12)
    plt.legend(bbox_to_anchor=(1.04, 1), loc="upper left", markerscale=2.5, fontsize=10)
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.tight_layout()
    plt.savefig(os.path.join(config.PLOT_DIR, "color_mass_diagram.png"), dpi=300)
    plt.close()

    # 5. 은하 회전곡선 및 툴리-피셔 관계 (Tully-Fisher: Mass vs Rotation Velocity)
    print("[5/6] 은하 회전곡선/툴리-피셔 도표 생성 중...")
    plt.figure(figsize=(10, 8))
    for gtype, color in CLASS_COLORS.items():
        sub = sample_df[sample_df['galaxy_type'] == gtype]
        if len(sub) > 0:
            short_name = gtype.split(" (")[0]
            plt.scatter(sub['lgm_tot_p50'], sub['v_rot'], s=12, alpha=0.5, color=color, label=short_name)
            
    plt.xlabel(r'항성 질량 $\log(M_* / M_\odot)$', fontsize=13)
    plt.ylabel(r'은하 회전속도 $V_{\mathrm{rot}}\,[\mathrm{km/s}]$', fontsize=13)
    plt.title('SDSS 11대 은하 바리온 툴리-피셔 회전곡선 관계 (Tully-Fisher Relation)', fontsize=15, pad=12)
    plt.legend(bbox_to_anchor=(1.04, 1), loc="upper left", markerscale=2.5, fontsize=10)
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.tight_layout()
    plt.savefig(os.path.join(config.PLOT_DIR, "tully_fisher.png"), dpi=300)
    plt.close()

    # 6. 통합 4분할 진화 패널 (암흑물질 분율 포함)
    print("[6/6] 통합 진화 4분할 패널 생성 중...")
    fig, axes = plt.subplots(2, 2, figsize=(16, 14))
    
    # Panel 1: BPT
    ax = axes[0, 0]
    ax.plot(x_kauff, y_kauff, 'k--', lw=1.5)
    ax.plot(x_kewley, y_kewley, 'r-', lw=1.5)
    for gtype, color in CLASS_COLORS.items():
        sub = sample_df[sample_df['galaxy_type'] == gtype]
        if len(sub) > 0: ax.scatter(sub['log_nii_ha'], sub['log_oiii_hb'], s=8, alpha=0.4, color=color)
    ax.set_xlim(-1.8, 0.8); ax.set_ylim(-1.5, 1.6)
    ax.set_xlabel(r'$\log([\mathrm{N\,II}]/\mathrm{H}\alpha)$')
    ax.set_ylabel(r'$\log([\mathrm{O\,III}]/\mathrm{H}\beta)$')
    ax.set_title('(A) BPT 이온화 진단')
    ax.grid(True, linestyle=':', alpha=0.5)

    # Panel 2: MS
    ax = axes[0, 1]
    for gtype, color in CLASS_COLORS.items():
        sub = sample_df[sample_df['galaxy_type'] == gtype]
        if len(sub) > 0: ax.scatter(sub['lgm_tot_p50'], sub['sfr_tot_p50'], s=8, alpha=0.4, color=color)
    ax.set_xlabel(r'$\log(M_* / M_\odot)$')
    ax.set_ylabel(r'$\log(\mathrm{SFR})$')
    ax.set_title('(B) 은하 주계열 (Star-Formation Main Sequence)')
    ax.grid(True, linestyle=':', alpha=0.5)

    # Panel 3: Color-Mass
    ax = axes[1, 0]
    for gtype, color in CLASS_COLORS.items():
        sub = sample_df[sample_df['galaxy_type'] == gtype]
        if len(sub) > 0: ax.scatter(sub['lgm_tot_p50'], sub['color_u_r'], s=8, alpha=0.4, color=color)
    ax.set_xlabel(r'$\log(M_* / M_\odot)$')
    ax.set_ylabel(r'$(u - r)\,\mathrm{[mag]}$')
    ax.set_title('(C) 색-질량 이분성 (Color-Mass Bimodality)')
    ax.grid(True, linestyle=':', alpha=0.5)

    # Panel 4: Dark Matter Fraction vs Mass
    ax = axes[1, 1]
    for gtype, color in CLASS_COLORS.items():
        sub = sample_df[sample_df['galaxy_type'] == gtype]
        if len(sub) > 0: ax.scatter(sub['lgm_tot_p50'], sub['dark_matter_fraction'] * 100, s=8, alpha=0.4, color=color, label=gtype.split(" (")[0])
    ax.set_xlabel(r'$\log(M_* / M_\odot)$')
    ax.set_ylabel(r'암흑물질 분율 $f_{\mathrm{DM}}\,\,[\%]$')
    ax.set_title('(D) 회전곡선 유도 암흑물질 분율-항성 질량 진화 관계')
    ax.legend(bbox_to_anchor=(1.04, 1), loc="upper left", markerscale=2.5, fontsize=10)
    ax.grid(True, linestyle=':', alpha=0.5)

    plt.suptitle('SDSS DR18 11대 은하 다차원 물리/화학/암흑물질 진화 종합 패널', fontsize=18, y=1.02)
    plt.tight_layout()
    plt.savefig(os.path.join(config.PLOT_DIR, "integrated_evolution.png"), dpi=300, bbox_inches='tight')
    plt.close()

    print("[완료] 모든 다이어그램 생성 완료!")
    print("="*60)

if __name__ == "__main__":
    generate_all_plots()
