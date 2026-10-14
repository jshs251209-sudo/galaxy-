"""
YSC 대회 제출용 은하 진화 전체 도표 고해상도 생성 및 다운로드 폴더 저장 스크립트
================================================================================
생성 도표 목록 (총 11종, 300 DPI):
  1. 도표1_전처리_파이프라인_흐름도.png
  2. 도표2_BPT_화학_이온화_진단도.png
  3. 도표3_은하_주계열_SFMS.png
  4. 도표4_질량_금속량_관계_MZR.png
  5. 도표5_색_질량_이분성_도표.png
  6. 도표6_바리온_툴리피셔_회전곡선.png
  7. 도표7_은하진화지수_GEI_다차원검증_4패널.png
  8. 도표8_3차원_기본금속량관계_FMR_3D.png
  9. 도표9_3대_핵심_상관관계_종합.png
 10. 도표10_표본크기_통계수렴도.png
 11. 도표11_통합진화_4분할_종합패널.png
"""

import os
import sys
import shutil
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from mpl_toolkits.mplot3d import Axes3D
import seaborn as sns
from scipy import stats

# 폰트 및 스타일 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False
sns.set_theme(style="ticks")
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

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

def create_all_charts():
    # 저장 경로 설정
    user_downloads = os.path.join(os.path.expanduser('~'), 'Downloads', 'YSC_은하진화_도표')
    proj_downloads = r'c:\Users\neato\Desktop\정현\03_과학탐구_대회\YSC_대회\data\download\YSC_은하진화_도표'
    out_plots = r'c:\Users\neato\Desktop\정현\03_과학탐구_대회\YSC_대회\output\plots'

    for d in [user_downloads, proj_downloads, out_plots]:
        os.makedirs(d, exist_ok=True)

    print(f"다운로드 저장 경로 1: {user_downloads}")
    print(f"다운로드 저장 경로 2: {proj_downloads}")

    def save_fig(fig, filename):
        path1 = os.path.join(user_downloads, filename)
        path2 = os.path.join(proj_downloads, filename)
        path3 = os.path.join(out_plots, filename)
        fig.savefig(path1, dpi=300, bbox_inches='tight')
        fig.savefig(path2, dpi=300, bbox_inches='tight')
        fig.savefig(path3, dpi=300, bbox_inches='tight')
        plt.close(fig)
        print(f"  -> 저장 완료: {filename}")

    # 데이터 로드
    csv_file = 'galaxy_master_complete_all.csv'
    if not os.path.exists(csv_file):
        print(f"데이터 파일 없음: {csv_file}")
        return
    print(f"데이터 로드 중: {csv_file} ...")
    df = pd.read_csv(csv_file)
    sample_df = df.sample(min(len(df), 15000), random_state=42)

    # -------------------------------------------------------------
    # [도표 1] 전처리 파이프라인 흐름도
    # -------------------------------------------------------------
    print("\n[1/11] 도표 1: 전처리 파이프라인 흐름도 생성...")
    fig, ax = plt.subplots(figsize=(14, 9), facecolor='white')
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    steps = [
        ("Step 1: 원시 데이터 수집 (Data Fetching)", 
         "• SDSS DR18 분광 관측 카탈로그\n• MPA-JHU 파생 파라미터 (SFR, Mass)\n• Galaxy Zoo 2 형태 분류 (총 10만 건)", "#1e3a8a"),
        ("Step 2: 관측 선택 효과 통제 (Quality Cuts)", 
         "• 적색편이 범위 한정 (0.02 < z < 0.1)\n• 주요 방출선 SNR >= 3.0 필터링\n• 겉보기 등급 완전성 (14.0 < r < 17.77)", "#0369a1"),
        ("Step 3: 성간 소광(Dust Extinction) 보정", 
         "• 이론적 발머 감소율 (Ha/Hb = 2.86) 적용\n• Cardelli et al. (1989) 소광곡선 복원\n• 본질적 방출선 플럭스 및 광도 산출", "#0f766e"),
        ("Step 4: 핵심 물리·화학량 정밀 계산", 
         "• Kennicutt (1998) Ha 광도 기반 SFR 변환\n• Tremonti (2004) N2 인덱스 산소 금속량 계산\n• 속도분산(velDisp) 기반 동역학 질량/암흑물질", "#b45309"),
        ("Step 5: 결측치 0% 정제 & 진화지수(GEI) 산출", 
         "• 비물리적 이상치 및 음수 플럭스 100% 제거\n• 결측치 완전 보정 (Null = 0건, Inf = 0건)\n• 은하 진화 지수(GEI) 표준화 산출 (N = 50,000)", "#15803d")
    ]

    y_positions = [82, 63, 44, 25, 6]
    for i, ((title, desc, color), y) in enumerate(zip(steps, y_positions)):
        # 상자
        bbox = patches.FancyBboxPatch((15, y), 70, 14, boxstyle="round,pad=1.2,rounding_size=2.0",
                                      facecolor=color, edgecolor='none', alpha=0.9, zorder=2)
        ax.add_patch(bbox)
        ax.text(18, y + 9.5, title, fontsize=13, fontweight='bold', color='white', zorder=3)
        ax.text(18, y + 2.5, desc, fontsize=10.5, color='#f1f5f9', zorder=3, linespacing=1.4)
        
        # 화살표
        if i < len(steps) - 1:
            ax.annotate('', xy=(50, y - 1), xytext=(50, y + 0.5),
                        arrowprops=dict(facecolor='#475569', edgecolor='none', width=3, headwidth=10, headlength=8),
                        zorder=4)

    ax.set_title("SDSS DR18 은하 분광 데이터 정제 및 파생 물리량 산출 전처리 파이프라인", fontsize=16, fontweight='bold', pad=20)
    save_fig(fig, "도표1_전처리_파이프라인_흐름도.png")

    # -------------------------------------------------------------
    # [도표 2] BPT 화학 이온화 진단도
    # -------------------------------------------------------------
    print("[2/11] 도표 2: BPT 화학 이온화 진단도 생성...")
    fig, ax = plt.subplots(figsize=(10, 8))
    x_kauff = np.linspace(-2.0, 0.0, 200)
    y_kauff = 0.61 / (x_kauff - 0.05) + 1.3
    x_kewley = np.linspace(-2.0, 0.4, 200)
    y_kewley = 0.61 / (x_kewley - 0.47) + 1.19
    
    ax.plot(x_kauff, y_kauff, 'k--', lw=2.2, label='Kauffmann et al. (2003) SF 경계')
    ax.plot(x_kewley, y_kewley, 'r-', lw=2.2, label='Kewley et al. (2001) 극대 광이온화')
    
    for gtype, color in CLASS_COLORS.items():
        sub = sample_df[sample_df['galaxy_type'] == gtype]
        if len(sub) > 0:
            short_name = gtype.split(" (")[0]
            ax.scatter(sub['log_nii_ha'], sub['log_oiii_hb'], s=14, alpha=0.5, color=color, label=short_name)
            
    ax.text(-1.2, -0.7, '별 생성 은하 영역\n(Star-forming)', fontsize=12, fontweight='bold', color='#1e3a8a')
    ax.text(0.1, 0.8, '활동은하핵 (AGN)\n& 충격파 영역', fontsize=12, fontweight='bold', color='#991b1b')
    ax.set_xlim(-1.8, 0.8)
    ax.set_ylim(-1.5, 1.6)
    ax.set_xlabel(r'$\log([\mathrm{N\,II}]\lambda6584 / \mathrm{H}\alpha)$', fontsize=13)
    ax.set_ylabel(r'$\log([\mathrm{O\,III}]\lambda5007 / \mathrm{H}\beta)$', fontsize=13)
    ax.set_title('SDSS 5만 개 은하 BPT 화학 이온화 진단도 (BPT Diagram)', fontsize=15, pad=12)
    ax.legend(bbox_to_anchor=(1.03, 1), loc="upper left", markerscale=2.5, fontsize=10)
    ax.grid(True, linestyle=':', alpha=0.6)
    save_fig(fig, "도표2_BPT_화학_이온화_진단도.png")

    # -------------------------------------------------------------
    # [도표 3] 은하 주계열 (SFMS)
    # -------------------------------------------------------------
    print("[3/11] 도표 3: 은하 주계열 (SFMS) 생성...")
    fig, ax = plt.subplots(figsize=(10, 8))
    for gtype, color in CLASS_COLORS.items():
        sub = sample_df[sample_df['galaxy_type'] == gtype]
        if len(sub) > 0:
            ax.scatter(sub['lgm_tot_p50'], sub['sfr_tot_p50'], s=14, alpha=0.5, color=color, label=gtype.split(" (")[0])
            
    # SFMS 기준선
    x_ms = np.linspace(8.0, 11.5, 100)
    ax.plot(x_ms, 0.72 * (x_ms - 10.0) + 0.15, 'k-', lw=2.5, label='은하 주계열 기준선 (SFMS Track)')
    ax.axhline(y=-1.5, color='crimson', linestyle='--', lw=2, label='별 생성 중단 (Quenched Threshold)')
    ax.set_xlabel(r'항성 질량 $\log(M_* / M_\odot)$', fontsize=13)
    ax.set_ylabel(r'별 생성률 $\log(\mathrm{SFR}\,[M_\odot/\mathrm{yr}])$', fontsize=13)
    ax.set_title('SDSS 은하 주계열과 퀜칭(Quenching) 진화 관계 (SFMS)', fontsize=15, pad=12)
    ax.legend(bbox_to_anchor=(1.03, 1), loc="upper left", markerscale=2.5, fontsize=10)
    ax.grid(True, linestyle=':', alpha=0.6)
    save_fig(fig, "도표3_은하_주계열_SFMS.png")

    # -------------------------------------------------------------
    # [도표 4] 질량-금속량 관계 (MZR)
    # -------------------------------------------------------------
    print("[4/11] 도표 4: 질량-금속량 관계 (MZR) 생성...")
    fig, ax = plt.subplots(figsize=(10, 8))
    for gtype, color in CLASS_COLORS.items():
        sub = sample_df[sample_df['galaxy_type'] == gtype]
        if len(sub) > 0:
            ax.scatter(sub['lgm_tot_p50'], sub['oh_p50'], s=14, alpha=0.5, color=color, label=gtype.split(" (")[0])
            
    ax.axhline(y=9.1, color='darkred', linestyle='--', lw=2, label='태양계 이상 금속량 포화한계 (~9.1)')
    ax.set_xlabel(r'항성 질량 $\log(M_* / M_\odot)$', fontsize=13)
    ax.set_ylabel(r'기체 산소 풍부도 $12 + \log(\mathrm{O/H})$', fontsize=13)
    ax.set_title('SDSS 질량-금속량 관계 및 중원소 축적 포화 (MZR, r = 0.572)', fontsize=15, pad=12)
    ax.legend(bbox_to_anchor=(1.03, 1), loc="upper left", markerscale=2.5, fontsize=10)
    ax.grid(True, linestyle=':', alpha=0.6)
    save_fig(fig, "도표4_질량_금속량_관계_MZR.png")

    # -------------------------------------------------------------
    # [도표 5] 색-질량 이분성 (Color-Mass Diagram)
    # -------------------------------------------------------------
    print("[5/11] 도표 5: 색-질량 이분성 도표 생성...")
    fig, ax = plt.subplots(figsize=(10, 8))
    for gtype, color in CLASS_COLORS.items():
        sub = sample_df[sample_df['galaxy_type'] == gtype]
        if len(sub) > 0:
            ax.scatter(sub['lgm_tot_p50'], sub['color_u_r'], s=14, alpha=0.5, color=color, label=gtype.split(" (")[0])
            
    ax.axhline(y=2.2, color='red', linestyle='--', lw=2, label='Red Sequence 하한선 (붉은 계열)')
    ax.axhline(y=1.8, color='blue', linestyle='--', lw=2, label='Blue Cloud 상한선 (푸른 구름)')
    ax.text(8.3, 2.0, 'Green Valley (전이 과도기 영역)', fontsize=12, fontweight='bold', color='darkgreen')
    ax.set_xlabel(r'항성 질량 $\log(M_* / M_\odot)$', fontsize=13)
    ax.set_ylabel(r'광학 색지수 $(u - r)\,\mathrm{[mag]}$', fontsize=13)
    ax.set_title('SDSS 색-질량 도표와 은하 진화 이분성 (Color-Mass Bimodality)', fontsize=15, pad=12)
    ax.legend(bbox_to_anchor=(1.03, 1), loc="upper left", markerscale=2.5, fontsize=10)
    ax.grid(True, linestyle=':', alpha=0.6)
    save_fig(fig, "도표5_색_질량_이분성_도표.png")

    # -------------------------------------------------------------
    # [도표 6] 바리온 툴리-피셔 및 회전속도
    # -------------------------------------------------------------
    print("[6/11] 도표 6: 바리온 툴리-피셔 회전곡선 생성...")
    fig, ax = plt.subplots(figsize=(10, 8))
    for gtype, color in CLASS_COLORS.items():
        sub = sample_df[sample_df['galaxy_type'] == gtype]
        if len(sub) > 0:
            ax.scatter(sub['lgm_tot_p50'], sub['v_rot'], s=14, alpha=0.5, color=color, label=gtype.split(" (")[0])
            
    ax.set_xlabel(r'항성 질량 $\log(M_* / M_\odot)$', fontsize=13)
    ax.set_ylabel(r'은하 원반 회전속도 $V_{\mathrm{rot}}\,[\mathrm{km/s}]$', fontsize=13)
    ax.set_title('SDSS 바리온 툴리-피셔 회전속도-항성 질량 관계 (Tully-Fisher)', fontsize=15, pad=12)
    ax.legend(bbox_to_anchor=(1.03, 1), loc="upper left", markerscale=2.5, fontsize=10)
    ax.grid(True, linestyle=':', alpha=0.6)
    save_fig(fig, "도표6_바리온_툴리피셔_회전곡선.png")

    # -------------------------------------------------------------
    # [도표 7] 은하 진화 지수(GEI) 다차원 검증 4패널
    # -------------------------------------------------------------
    print("[7/11] 도표 7: 은하 진화 지수(GEI) 다차원 검증 4패널 생성...")
    fig, axes = plt.subplots(2, 2, figsize=(15, 13))

    # Panel A: GEI vs Dn4000
    ax = axes[0, 0]
    sc = ax.scatter(sample_df['GEI'], sample_df['d4000_n'], c=sample_df['color_u_r'], cmap='coolwarm', s=12, alpha=0.5)
    cbar = plt.colorbar(sc, ax=ax)
    cbar.set_label('색지수 (u - r) [mag]', fontsize=11)
    
    valid = sample_df[['GEI', 'd4000_n']].dropna()
    slope, intercept, r_val, p_val, _ = stats.linregress(valid['GEI'], valid['d4000_n'])
    x_v = np.linspace(0, 1, 100)
    ax.plot(x_v, slope * x_v + intercept, 'k--', lw=2.5, label=f'선형 회귀선 (r = {r_val:.3f}, p < 1e-300)')
    ax.set_xlabel('은하 진화 지수 (GEI, Galaxy Evolution Index)', fontsize=12)
    ax.set_ylabel(r'4000Å 불연속도 ($D_n(4000)$ - 항성 종족 연령)', fontsize=12)
    ax.set_title('(A) GEI와 독립 항성 연령($D_n(4000)$) 상관성 검증', fontsize=13, pad=10)
    ax.legend(loc='upper left', fontsize=11)
    ax.grid(True, linestyle=':', alpha=0.6)

    # Panel B: GEI Distribution by Morphology
    ax = axes[0, 1]
    morph_order = ['불규칙은하', '나선은하', '렌즈형은하', '타원은하']
    c_list = ['#10b981', '#2563eb', '#ea580c', '#dc2626']
    for m, c in zip(morph_order, c_list):
        sub = df[df['class_morphology'] == m]['GEI'].dropna()
        if len(sub) > 0:
            sns.kdeplot(sub, ax=ax, label=f'{m} (평균 {sub.mean():.2f})', color=c, lw=2.2, fill=True, alpha=0.15)
    ax.axvline(x=0.42, color='gray', linestyle=':', lw=1.5, label='Green Valley 전이대')
    ax.axvline(x=0.62, color='red', linestyle=':', lw=1.5, label='Quenching 완료대')
    ax.set_xlabel('은하 진화 지수 (GEI)', fontsize=12)
    ax.set_ylabel('확률 밀도 (Density)', fontsize=12)
    ax.set_title('(B) 은하 형태별 GEI 진화 시퀀스 분포 (KDE)', fontsize=13, pad=10)
    ax.legend(loc='upper left', fontsize=10)
    ax.grid(True, linestyle=':', alpha=0.6)

    # Panel C: Color-Mass with GEI
    ax = axes[1, 0]
    sc2 = ax.scatter(sample_df['lgm_tot_p50'], sample_df['color_u_r'], c=sample_df['GEI'], cmap='viridis', s=12, alpha=0.6)
    cbar2 = plt.colorbar(sc2, ax=ax)
    cbar2.set_label('은하 진화 지수 (GEI)', fontsize=11)
    ax.axhline(y=2.2, color='red', linestyle='--', alpha=0.7, label='Red Sequence')
    ax.axhline(y=1.8, color='blue', linestyle='--', alpha=0.7, label='Blue Cloud')
    ax.set_xlabel(r'항성 질량 $\log(M_* / M_\odot)$', fontsize=12)
    ax.set_ylabel(r'색지수 $(u - r)\,\mathrm{[mag]}$', fontsize=12)
    ax.set_title('(C) 색-질량 도표 상의 GEI 궤적 (Blue Cloud → Green Valley → Red Sequence)', fontsize=13, pad=10)
    ax.legend(loc='lower right', fontsize=10)
    ax.grid(True, linestyle=':', alpha=0.6)

    # Panel D: sSFR Quenching
    ax = axes[1, 1]
    sc3 = ax.scatter(sample_df['lgm_tot_p50'], sample_df['log_ssfr'], c=sample_df['GEI'], cmap='inferno', s=12, alpha=0.6)
    cbar3 = plt.colorbar(sc3, ax=ax)
    cbar3.set_label('은하 진화 지수 (GEI)', fontsize=11)
    ax.axhline(y=-11.0, color='crimson', linestyle='--', lw=2, label=r'퀜칭 임계선 ($\log\mathrm{sSFR} = -11\,\mathrm{yr}^{-1}$)')
    ax.set_xlabel(r'항성 질량 $\log(M_* / M_\odot)$', fontsize=12)
    ax.set_ylabel(r'비별생성률 $\log(\mathrm{sSFR}\,[\mathrm{yr}^{-1}])$', fontsize=12)
    ax.set_title(r'(D) 비별생성률(sSFR) 감쇠 및 퀜칭(Quenching) 진화', fontsize=13, pad=10)
    ax.legend(loc='lower left', fontsize=10)
    ax.grid(True, linestyle=':', alpha=0.6)

    plt.suptitle('SDSS DR18 은하 진화 지수(GEI) 다차원 타당성 검증 및 진화 척도 분석', fontsize=16, y=0.995)
    save_fig(fig, "도표7_은하진화지수_GEI_다차원검증_4패널.png")

    # -------------------------------------------------------------
    # [도표 8] 3차원 기본 금속량 관계 (FMR 3D)
    # -------------------------------------------------------------
    print("[8/11] 도표 8: 3차원 기본 금속량 관계 (FMR 3D) 생성...")
    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, projection='3d')
    sub_3d = sample_df.dropna(subset=['lgm_tot_p50', 'sfr_tot_p50', 'oh_p50', 'GEI']).sample(min(len(sample_df), 4000), random_state=42)
    p = ax.scatter(sub_3d['lgm_tot_p50'], sub_3d['sfr_tot_p50'], sub_3d['oh_p50'], 
                   c=sub_3d['GEI'], cmap='plasma', s=16, alpha=0.7, edgecolors='none')
    cbar = fig.colorbar(p, ax=ax, pad=0.1, shrink=0.7)
    cbar.set_label('은하 진화 지수 (GEI)', fontsize=12)

    from sklearn.linear_model import LinearRegression
    X = sub_3d[['lgm_tot_p50', 'sfr_tot_p50']].values
    y = sub_3d['oh_p50'].values
    reg = LinearRegression().fit(X, y)
    x_s = np.linspace(sub_3d['lgm_tot_p50'].min(), sub_3d['lgm_tot_p50'].max(), 20)
    y_s = np.linspace(sub_3d['sfr_tot_p50'].min(), sub_3d['sfr_tot_p50'].max(), 20)
    x_m, y_m = np.meshgrid(x_s, y_s)
    z_m = reg.predict(np.c_[x_m.ravel(), y_m.ravel()]).reshape(x_m.shape)
    ax.plot_surface(x_m, y_m, z_m, color='cyan', alpha=0.25, edgecolor='none')
    ax.set_xlabel(r'항성 질량 $\log(M_*/M_\odot)$', fontsize=11, labelpad=10)
    ax.set_ylabel(r'별 생성률 $\log(\mathrm{SFR})$', fontsize=11, labelpad=10)
    ax.set_zlabel(r'산소 금속량 $12+\log(\mathrm{O/H})$', fontsize=11, labelpad=10)
    ax.set_title('3차원 기본 금속량 관계 (FMR: Mass-SFR-Metallicity) 및 은하 진화 궤적', fontsize=14, pad=15)
    ax.view_init(elev=24, azim=-55)
    save_fig(fig, "도표8_3차원_기본금속량관계_FMR_3D.png")

    # -------------------------------------------------------------
    # [도표 9] 3대 핵심 상관관계 요약 패널
    # -------------------------------------------------------------
    print("[9/11] 도표 9: 3대 핵심 상관관계 요약 패널 생성...")
    fig, axes = plt.subplots(1, 3, figsize=(18, 5.5))
    
    # 1. Mass vs SFR
    ax = axes[0]
    ax.scatter(sample_df['lgm_tot_p50'], sample_df['sfr_tot_p50'], s=8, alpha=0.35, color='#2563eb')
    sns.regplot(data=sample_df, x='lgm_tot_p50', y='sfr_tot_p50', ax=ax, scatter=False, color='red',
                line_kws={'lw': 2, 'label': '전체 선형 회귀선'})
    ax.set_xlabel(r'항성 질량 $\log(M_* / M_\odot)$', fontsize=12)
    ax.set_ylabel(r'별 생성률 $\log(\mathrm{SFR})$', fontsize=12)
    ax.set_title('(A) 항성 질량 - 별 생성률 관계 (SFMS)', fontsize=13)
    ax.grid(True, linestyle=':', alpha=0.6)

    # 2. Mass vs Metallicity
    ax = axes[1]
    ax.scatter(sample_df['lgm_tot_p50'], sample_df['oh_p50'], s=8, alpha=0.35, color='#059669')
    sns.regplot(data=sample_df, x='lgm_tot_p50', y='oh_p50', ax=ax, scatter=False, color='red',
                line_kws={'lw': 2, 'label': 'r = 0.572, ρ = 0.575'})
    ax.set_xlabel(r'항성 질량 $\log(M_* / M_\odot)$', fontsize=12)
    ax.set_ylabel(r'기체 산소 금속량 $12+\log(\mathrm{O/H})$', fontsize=12)
    ax.set_title('(B) 질량 - 금속량 관계 (MZR)', fontsize=13)
    ax.legend(loc='lower right', fontsize=11)
    ax.grid(True, linestyle=':', alpha=0.6)

    # 3. SFR vs Metallicity
    ax = axes[2]
    ax.scatter(sample_df['sfr_tot_p50'], sample_df['oh_p50'], s=8, alpha=0.35, color='#d97706')
    sns.regplot(data=sample_df, x='sfr_tot_p50', y='oh_p50', ax=ax, scatter=False, color='red',
                line_kws={'lw': 2, 'label': 'r = 0.267, ρ = 0.278'})
    ax.set_xlabel(r'별 생성률 $\log(\mathrm{SFR})$', fontsize=12)
    ax.set_ylabel(r'기체 산소 금속량 $12+\log(\mathrm{O/H})$', fontsize=12)
    ax.set_title('(C) 별 생성률 - 금속량 관계 (FMR)', fontsize=13)
    ax.legend(loc='lower right', fontsize=11)
    ax.grid(True, linestyle=':', alpha=0.6)

    plt.suptitle('SDSS 5만 개 은하 3대 핵심 물리·화학적 상관관계 종합 비교', fontsize=16, y=1.03)
    save_fig(fig, "도표9_3대_핵심_상관관계_종합.png")

    # -------------------------------------------------------------
    # [도표 10] 표본 크기 통계 수렴도
    # -------------------------------------------------------------
    print("[10/11] 도표 10: 표본 크기 통계 수렴도 생성...")
    fig, ax = plt.subplots(figsize=(10, 6))
    sample_sizes = [100, 300, 500, 1000, 3000, 5000, 10000, 20000, 50000]
    r_means = []
    r_stds = []
    for sz in sample_sizes:
        r_trials = []
        for _ in range(25):
            sub = df.sample(sz)
            r, _ = stats.pearsonr(sub['lgm_tot_p50'], sub['oh_p50'])
            r_trials.append(r)
        r_means.append(np.mean(r_trials))
        r_stds.append(np.std(r_trials))
        
    ax.errorbar(sample_sizes, r_means, yerr=r_stds, fmt='o-', color='#2563eb', lw=2.2, capsize=5, 
                label='MZR 상관계수 (r) 평균 및 1σ 오차')
    ax.axhline(y=0.572, color='crimson', linestyle='--', lw=1.8, label='전체 표본(N=50,000) 참값 (r = 0.572)')
    ax.set_xscale('log')
    ax.set_xlabel('표본 크기 N (Log Scale)', fontsize=12)
    ax.set_ylabel('상관계수 r (Mass vs Metallicity)', fontsize=12)
    ax.set_title('표본 크기 증가에 따른 질량-금속량 상관계수(r) 안정성 수렴 검증 (Bootstrap)', fontsize=14, pad=12)
    ax.legend(loc='lower right', fontsize=11)
    ax.grid(True, linestyle=':', alpha=0.6)
    save_fig(fig, "도표10_표본크기_통계수렴도.png")

    # -------------------------------------------------------------
    # [도표 11] 통합진화 4분할 종합 패널
    # -------------------------------------------------------------
    print("[11/11] 도표 11: 통합진화 4분할 종합 패널 생성...")
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
    ax.set_title('(A) BPT 이온화 화학 진단', fontsize=13)
    ax.grid(True, linestyle=':', alpha=0.5)

    # Panel 2: MS
    ax = axes[0, 1]
    for gtype, color in CLASS_COLORS.items():
        sub = sample_df[sample_df['galaxy_type'] == gtype]
        if len(sub) > 0: ax.scatter(sub['lgm_tot_p50'], sub['sfr_tot_p50'], s=8, alpha=0.4, color=color)
    ax.set_xlabel(r'$\log(M_* / M_\odot)$')
    ax.set_ylabel(r'$\log(\mathrm{SFR})$')
    ax.set_title('(B) 은하 주계열 및 퀜칭 진화 (SFMS)', fontsize=13)
    ax.grid(True, linestyle=':', alpha=0.5)

    # Panel 3: Color-Mass
    ax = axes[1, 0]
    for gtype, color in CLASS_COLORS.items():
        sub = sample_df[sample_df['galaxy_type'] == gtype]
        if len(sub) > 0: ax.scatter(sub['lgm_tot_p50'], sub['color_u_r'], s=8, alpha=0.4, color=color)
    ax.set_xlabel(r'$\log(M_* / M_\odot)$')
    ax.set_ylabel(r'$(u - r)\,\mathrm{[mag]}$')
    ax.set_title('(C) 색-질량 이분성 (Color-Mass Bimodality)', fontsize=13)
    ax.grid(True, linestyle=':', alpha=0.5)

    # Panel 4: Dark Matter Fraction vs Mass
    ax = axes[1, 1]
    for gtype, color in CLASS_COLORS.items():
        sub = sample_df[sample_df['galaxy_type'] == gtype]
        if len(sub) > 0: ax.scatter(sub['lgm_tot_p50'], sub['dark_matter_fraction'] * 100, s=8, alpha=0.4, color=color, label=gtype.split(" (")[0])
    ax.set_xlabel(r'$\log(M_* / M_\odot)$')
    ax.set_ylabel(r'암흑물질 분율 $f_{\mathrm{DM}}\,\,[\%]$')
    ax.set_title('(D) 회전곡선 유도 암흑물질 분율-항성 질량 진화', fontsize=13)
    ax.legend(bbox_to_anchor=(1.03, 1), loc="upper left", markerscale=2.5, fontsize=10)
    ax.grid(True, linestyle=':', alpha=0.5)

    plt.suptitle('SDSS DR18 11대 은하 다차원 물리/화학/암흑물질 진화 종합 패널', fontsize=17, y=1.01)
    save_fig(fig, "도표11_통합진화_4분할_종합패널.png")

    print("\n=================================================================")
    print(f"🎉 모든 11개 도표 고해상도(300 DPI) 생성 및 다운로드 폴더 저장 완료!")
    print(f"1. 사용자 다운로드 폴더: {user_downloads}")
    print(f"2. 프로젝트 다운로드 폴더: {proj_downloads}")
    print("=================================================================")

if __name__ == '__main__':
    create_all_charts()
