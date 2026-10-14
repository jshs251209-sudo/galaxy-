"""
YSC 대회 제출용: 선(Line)을 일체 배제한 순수 관측 데이터 산점도(Scatter Plot) 전용 도표 생성 및 ZIP 패키징
====================================================================================================
규칙:
  1. 회귀선, 경계선, 기준선, 격자선 외 임의의 선(Line)을 일체 넣지 않음.
  2. 오직 관측 데이터 포인트(점, Scatter Dots)로만 2차원 및 3차원 도표를 구성함.
  3. 모든 산점도는 300 DPI 고해상도로 렌더링.
  4. 생성된 순수 산점도 파일들만 모아서 다운로드 폴더에 ZIP 파일로 압축 생성.
"""

import os
import sys
import shutil
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import seaborn as sns

# Windows UTF-8 설정
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# 스타일 및 한글 폰트 설정
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

def main():
    downloads_dir = os.path.expanduser('~/Downloads')
    pkg_name = "YSC_은하관측_순수산점도_도표모음"
    target_dir = os.path.join(downloads_dir, pkg_name)
    if os.path.exists(target_dir):
        shutil.rmtree(target_dir, ignore_errors=True)
    os.makedirs(target_dir, exist_ok=True)

    print("=" * 80)
    print("선 없는 순수 데이터 산점도(Scatter Plot) 14종 고해상도 생성 및 패키징")
    print(f"저장 폴더: {target_dir}")
    print("=" * 80)

    csv_path = 'galaxy_master_complete_all.csv'
    if not os.path.exists(csv_path):
        print(f"오류: {csv_path} 파일을 찾을 수 없습니다.")
        return

    print("데이터 로드 중...")
    df = pd.read_csv(csv_path)
    print(f"총 데이터 수: {len(df):,}개")

    # 선명한 산점도를 위한 20,000개 표본 샘플링 (밀도와 가독성 최적화)
    sample_df = df.sample(min(len(df), 20000), random_state=42)

    def save_scatter(fig, filename):
        out_path = os.path.join(target_dir, filename)
        fig.savefig(out_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
        print(f"  -> 순수 산점도 저장 완료: {filename}")

    # -------------------------------------------------------------
    # 1. BPT 화학 이온화 진단 산점도 (선 전혀 없음)
    # -------------------------------------------------------------
    print("\n[1/14] BPT 화학 이온화 산점도 생성...")
    fig, ax = plt.subplots(figsize=(10, 8))
    for gtype, color in CLASS_COLORS.items():
        sub = sample_df[sample_df['galaxy_type'] == gtype]
        if len(sub) > 0:
            ax.scatter(sub['log_nii_ha'], sub['log_oiii_hb'], s=12, alpha=0.45, color=color, 
                       label=gtype.split(" (")[0], edgecolors='none')
    ax.set_xlim(-1.8, 0.8)
    ax.set_ylim(-1.5, 1.6)
    ax.set_xlabel(r'$\log([\mathrm{N\,II}]\lambda6584 / \mathrm{H}\alpha)$', fontsize=13)
    ax.set_ylabel(r'$\log([\mathrm{O\,III}]\lambda5007 / \mathrm{H}\beta)$', fontsize=13)
    ax.set_title('SDSS 은하 BPT 화학 이온화 방출선비 관측 산점도', fontsize=15, pad=12)
    ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", markerscale=2.5, fontsize=10)
    ax.grid(True, linestyle=':', alpha=0.5)
    save_scatter(fig, "산점도01_BPT_화학이온화_방출선비.png")

    # -------------------------------------------------------------
    # 2. 은하 주계열 (SFMS) 산점도 (선 전혀 없음)
    # -------------------------------------------------------------
    print("[2/14] 은하 주계열(SFMS) 산점도 생성...")
    fig, ax = plt.subplots(figsize=(10, 8))
    for gtype, color in CLASS_COLORS.items():
        sub = sample_df[sample_df['galaxy_type'] == gtype]
        if len(sub) > 0:
            ax.scatter(sub['lgm_tot_p50'], sub['sfr_tot_p50'], s=12, alpha=0.45, color=color, 
                       label=gtype.split(" (")[0], edgecolors='none')
    ax.set_xlabel(r'항성 질량 $\log(M_* / M_\odot)$', fontsize=13)
    ax.set_ylabel(r'별 생성률 $\log(\mathrm{SFR}\,[M_\odot/\mathrm{yr}])$', fontsize=13)
    ax.set_title('은하 주계열(SFMS): 항성 질량 vs 별 생성률 관측 산점도', fontsize=15, pad=12)
    ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", markerscale=2.5, fontsize=10)
    ax.grid(True, linestyle=':', alpha=0.5)
    save_scatter(fig, "산점도02_은하주계열_SFMS_항성질량_별생성률.png")

    # -------------------------------------------------------------
    # 3. 질량-금속량 관계 (MZR) 산점도 (선 전혀 없음)
    # -------------------------------------------------------------
    print("[3/14] 질량-금속량 관계(MZR) 산점도 생성...")
    fig, ax = plt.subplots(figsize=(10, 8))
    for gtype, color in CLASS_COLORS.items():
        sub = sample_df[sample_df['galaxy_type'] == gtype]
        if len(sub) > 0:
            ax.scatter(sub['lgm_tot_p50'], sub['oh_p50'], s=12, alpha=0.45, color=color, 
                       label=gtype.split(" (")[0], edgecolors='none')
    ax.set_xlabel(r'항성 질량 $\log(M_* / M_\odot)$', fontsize=13)
    ax.set_ylabel(r'기체 산소 풍부도 $12 + \log(\mathrm{O/H})$', fontsize=13)
    ax.set_title('질량-금속량 관계(MZR): 항성 질량 vs 기체 산소 금속량 관측 산점도', fontsize=15, pad=12)
    ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", markerscale=2.5, fontsize=10)
    ax.grid(True, linestyle=':', alpha=0.5)
    save_scatter(fig, "산점도03_질량_금속량_MZR_항성질량_산소풍부도.png")

    # -------------------------------------------------------------
    # 4. 별 생성률 - 금속량 관계 (FMR) 산점도 (선 전혀 없음)
    # -------------------------------------------------------------
    print("[4/14] 별 생성률-금속량 관계(FMR) 산점도 생성...")
    fig, ax = plt.subplots(figsize=(10, 8))
    sc = ax.scatter(sample_df['sfr_tot_p50'], sample_df['oh_p50'], c=sample_df['lgm_tot_p50'], 
                    cmap='viridis', s=12, alpha=0.5, edgecolors='none')
    cbar = plt.colorbar(sc, ax=ax)
    cbar.set_label(r'항성 질량 $\log(M_* / M_\odot)$', fontsize=12)
    ax.set_xlabel(r'별 생성률 $\log(\mathrm{SFR}\,[M_\odot/\mathrm{yr}])$', fontsize=13)
    ax.set_ylabel(r'기체 산소 풍부도 $12 + \log(\mathrm{O/H})$', fontsize=13)
    ax.set_title('별 생성률 vs 기체 산소 금속량 관측 산점도 (질량 컬러맵)', fontsize=15, pad=12)
    ax.grid(True, linestyle=':', alpha=0.5)
    save_scatter(fig, "산점도04_별생성률_금속량_FMR_산점도.png")

    # -------------------------------------------------------------
    # 5. 색-질량 도표 (Color-Mass) 산점도 (선 전혀 없음)
    # -------------------------------------------------------------
    print("[5/14] 색-질량 도표(Color-Mass) 산점도 생성...")
    fig, ax = plt.subplots(figsize=(10, 8))
    for gtype, color in CLASS_COLORS.items():
        sub = sample_df[sample_df['galaxy_type'] == gtype]
        if len(sub) > 0:
            ax.scatter(sub['lgm_tot_p50'], sub['color_u_r'], s=12, alpha=0.45, color=color, 
                       label=gtype.split(" (")[0], edgecolors='none')
    ax.set_xlabel(r'항성 질량 $\log(M_* / M_\odot)$', fontsize=13)
    ax.set_ylabel(r'광학 색지수 $(u - r)\,\mathrm{[mag]}$', fontsize=13)
    ax.set_title('색-질량 이분성(Color-Mass): 항성 질량 vs 광학 색지수 관측 산점도', fontsize=15, pad=12)
    ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", markerscale=2.5, fontsize=10)
    ax.grid(True, linestyle=':', alpha=0.5)
    save_scatter(fig, "산점도05_색_질량_ColorMass_항성질량_색지수.png")

    # -------------------------------------------------------------
    # 6. 바리온 툴리-피셔 회전속도 산점도 (선 전혀 없음)
    # -------------------------------------------------------------
    print("[6/14] 바리온 툴리-피셔 회전속도 산점도 생성...")
    fig, ax = plt.subplots(figsize=(10, 8))
    for gtype, color in CLASS_COLORS.items():
        sub = sample_df[sample_df['galaxy_type'] == gtype]
        if len(sub) > 0:
            ax.scatter(sub['lgm_tot_p50'], sub['v_rot'], s=12, alpha=0.45, color=color, 
                       label=gtype.split(" (")[0], edgecolors='none')
    ax.set_xlabel(r'항성 질량 $\log(M_* / M_\odot)$', fontsize=13)
    ax.set_ylabel(r'은하 원반 회전속도 $V_{\mathrm{rot}}\,[\mathrm{km/s}]$', fontsize=13)
    ax.set_title('바리온 툴리-피셔: 항성 질량 vs 원반 회전속도 관측 산점도', fontsize=15, pad=12)
    ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", markerscale=2.5, fontsize=10)
    ax.grid(True, linestyle=':', alpha=0.5)
    save_scatter(fig, "산점도06_바리온_툴리피셔_항성질량_원반회전속도.png")

    # -------------------------------------------------------------
    # 7. 항성 질량 vs 암흑물질 분율 산점도 (선 전혀 없음)
    # -------------------------------------------------------------
    print("[7/14] 항성 질량 vs 암흑물질 분율 산점도 생성...")
    fig, ax = plt.subplots(figsize=(10, 8))
    for gtype, color in CLASS_COLORS.items():
        sub = sample_df[sample_df['galaxy_type'] == gtype]
        if len(sub) > 0:
            ax.scatter(sub['lgm_tot_p50'], sub['dark_matter_fraction'] * 100, s=12, alpha=0.45, color=color, 
                       label=gtype.split(" (")[0], edgecolors='none')
    ax.set_xlabel(r'항성 질량 $\log(M_* / M_\odot)$', fontsize=13)
    ax.set_ylabel(r'암흑물질 분율 $f_{\mathrm{DM}}\,\,[\%]$', fontsize=13)
    ax.set_title('항성 질량 vs 회전곡선 유도 암흑물질 분율 관측 산점도', fontsize=15, pad=12)
    ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", markerscale=2.5, fontsize=10)
    ax.grid(True, linestyle=':', alpha=0.5)
    save_scatter(fig, "산점도07_항성질량_암흑물질분율.png")

    # -------------------------------------------------------------
    # 8. 비별생성률 (sSFR) 퀜칭 산점도 (선 전혀 없음)
    # -------------------------------------------------------------
    print("[8/14] 비별생성률(sSFR) 퀜칭 산점도 생성...")
    fig, ax = plt.subplots(figsize=(10, 8))
    sc = ax.scatter(sample_df['lgm_tot_p50'], sample_df['log_ssfr'], c=sample_df['GEI'], 
                    cmap='inferno', s=12, alpha=0.5, edgecolors='none')
    cbar = plt.colorbar(sc, ax=ax)
    cbar.set_label('은하 진화 지수 (GEI)', fontsize=12)
    ax.set_xlabel(r'항성 질량 $\log(M_* / M_\odot)$', fontsize=13)
    ax.set_ylabel(r'비별생성률 $\log(\mathrm{sSFR}\,[\mathrm{yr}^{-1}])$', fontsize=13)
    ax.set_title('비별생성률(sSFR) 감쇠 및 퀜칭 관측 산점도 (GEI 컬러맵)', fontsize=15, pad=12)
    ax.grid(True, linestyle=':', alpha=0.5)
    save_scatter(fig, "산점도08_비별생성률_sSFR_항성질량_퀜칭.png")

    # -------------------------------------------------------------
    # 9. 은하 진화 지수 (GEI) vs 항성 연령 (Dn4000) 산점도 (선 전혀 없음)
    # -------------------------------------------------------------
    print("[9/14] 은하 진화 지수(GEI) vs Dn(4000) 산점도 생성...")
    fig, ax = plt.subplots(figsize=(10, 8))
    sc = ax.scatter(sample_df['GEI'], sample_df['d4000_n'], c=sample_df['color_u_r'], 
                    cmap='coolwarm', s=14, alpha=0.5, edgecolors='none')
    cbar = plt.colorbar(sc, ax=ax)
    cbar.set_label('색지수 (u - r) [mag]', fontsize=12)
    ax.set_xlabel('은하 진화 지수 (GEI, Galaxy Evolution Index)', fontsize=13)
    ax.set_ylabel(r'4000Å 불연속도 ($D_n(4000)$ - 항성 종족 연령)', fontsize=13)
    ax.set_title('은하 진화 지수(GEI) vs 분광 항성 연령(Dn4000) 관측 산점도', fontsize=15, pad=12)
    ax.grid(True, linestyle=':', alpha=0.5)
    save_scatter(fig, "산점도09_은하진화지수_GEI_항성연령_Dn4000.png")

    # -------------------------------------------------------------
    # 10. 은하 진화 지수 (GEI) vs 광학 색지수 산점도 (선 전혀 없음)
    # -------------------------------------------------------------
    print("[10/14] 은하 진화 지수(GEI) vs 광학 색지수 산점도 생성...")
    fig, ax = plt.subplots(figsize=(10, 8))
    morph_colors = {'나선은하': '#2563eb', '불규칙은하': '#10b981', '타원은하': '#dc2626', '렌즈형은하': '#ea580c'}
    for m, col in morph_colors.items():
        sub = sample_df[sample_df['class_morphology'] == m]
        if len(sub) > 0:
            ax.scatter(sub['GEI'], sub['color_u_r'], s=12, alpha=0.45, color=col, label=m, edgecolors='none')
    ax.set_xlabel('은하 진화 지수 (GEI)', fontsize=13)
    ax.set_ylabel(r'광학 색지수 $(u - r)\,\mathrm{[mag]}$', fontsize=13)
    ax.set_title('은하 진화 지수(GEI) vs 광학 색지수 관측 산점도', fontsize=15, pad=12)
    ax.legend(loc='upper left', markerscale=2.5, fontsize=11)
    ax.grid(True, linestyle=':', alpha=0.5)
    save_scatter(fig, "산점도10_은하진화지수_GEI_광학색지수.png")

    # -------------------------------------------------------------
    # 11. 항성 질량 vs 은하 진화 지수 (GEI) 산점도 (선 전혀 없음)
    # -------------------------------------------------------------
    print("[11/14] 항성 질량 vs 은하 진화 지수(GEI) 산점도 생성...")
    fig, ax = plt.subplots(figsize=(10, 8))
    sc = ax.scatter(sample_df['lgm_tot_p50'], sample_df['GEI'], c=sample_df['sfr_tot_p50'], 
                    cmap='plasma', s=12, alpha=0.5, edgecolors='none')
    cbar = plt.colorbar(sc, ax=ax)
    cbar.set_label(r'별 생성률 $\log(\mathrm{SFR})$', fontsize=12)
    ax.set_xlabel(r'항성 질량 $\log(M_* / M_\odot)$', fontsize=13)
    ax.set_ylabel('은하 진화 지수 (GEI)', fontsize=13)
    ax.set_title('항성 질량 vs 은하 진화 지수(GEI) 관측 산점도 (SFR 컬러맵)', fontsize=15, pad=12)
    ax.grid(True, linestyle=':', alpha=0.5)
    save_scatter(fig, "산점도11_항성질량_은하진화지수_GEI.png")

    # -------------------------------------------------------------
    # 12. 3차원 FMR 순수 3D 점 산점도 (곡면/평면선 전혀 없음!)
    # -------------------------------------------------------------
    print("[12/14] 3차원 기본 금속량 관계(FMR 3D) 순수 산점도 생성...")
    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, projection='3d')
    sub_3d = sample_df.sample(min(len(sample_df), 5000), random_state=42)
    p = ax.scatter(sub_3d['lgm_tot_p50'], sub_3d['sfr_tot_p50'], sub_3d['oh_p50'], 
                   c=sub_3d['GEI'], cmap='plasma', s=14, alpha=0.6, edgecolors='none')
    cbar = fig.colorbar(p, ax=ax, pad=0.1, shrink=0.7)
    cbar.set_label('은하 진화 지수 (GEI)', fontsize=12)
    ax.set_xlabel(r'항성 질량 $\log(M_*/M_\odot)$', fontsize=11, labelpad=10)
    ax.set_ylabel(r'별 생성률 $\log(\mathrm{SFR})$', fontsize=11, labelpad=10)
    ax.set_zlabel(r'산소 금속량 $12+\log(\mathrm{O/H})$', fontsize=11, labelpad=10)
    ax.set_title('3차원 기본 금속량 관계 (FMR): 순수 3D 관측 데이터 산점도', fontsize=14, pad=15)
    ax.view_init(elev=24, azim=-55)
    save_scatter(fig, "산점도12_3차원_FMR_질량_별생성률_금속량_순수산점도.png")

    # -------------------------------------------------------------
    # 13. 3차원 물리 진화 궤적 순수 3D 산점도 (선 전혀 없음!)
    # -------------------------------------------------------------
    print("[13/14] 3차원 물리 진화 궤적 순수 산점도 생성...")
    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, projection='3d')
    p2 = ax.scatter(sub_3d['lgm_tot_p50'], sub_3d['color_u_r'], sub_3d['GEI'], 
                    c=sub_3d['log_ssfr'], cmap='coolwarm', s=14, alpha=0.6, edgecolors='none')
    cbar2 = fig.colorbar(p2, ax=ax, pad=0.1, shrink=0.7)
    cbar2.set_label(r'비별생성률 $\log(\mathrm{sSFR})$', fontsize=12)
    ax.set_xlabel(r'항성 질량 $\log(M_*/M_\odot)$', fontsize=11, labelpad=10)
    ax.set_ylabel(r'색지수 $(u - r)\,\mathrm{[mag]}$', fontsize=11, labelpad=10)
    ax.set_zlabel('은하 진화 지수 (GEI)', fontsize=11, labelpad=10)
    ax.set_title('3차원 은하 진화 궤적 (질량-색지수-GEI): 순수 3D 관측 산점도', fontsize=14, pad=15)
    ax.view_init(elev=26, azim=-60)
    save_scatter(fig, "산점도13_3차원_물리진화_질량_색지수_GEI_순수산점도.png")

    # -------------------------------------------------------------
    # 14. 4대 핵심 관계 순수 산점도 4분할 종합 패널 (선 전혀 없음!)
    # -------------------------------------------------------------
    print("[14/14] 4대 핵심 관계 순수 산점도 4분할 패널 생성...")
    fig, axes = plt.subplots(2, 2, figsize=(16, 14))

    # Panel 1: BPT
    ax = axes[0, 0]
    for gtype, color in CLASS_COLORS.items():
        sub = sample_df[sample_df['galaxy_type'] == gtype]
        if len(sub) > 0: ax.scatter(sub['log_nii_ha'], sub['log_oiii_hb'], s=8, alpha=0.4, color=color, edgecolors='none')
    ax.set_xlim(-1.8, 0.8); ax.set_ylim(-1.5, 1.6)
    ax.set_xlabel(r'$\log([\mathrm{N\,II}]/\mathrm{H}\alpha)$', fontsize=12)
    ax.set_ylabel(r'$\log([\mathrm{O\,III}]/\mathrm{H}\beta)$', fontsize=12)
    ax.set_title('(A) BPT 이온화 화학 방출선비 산점도', fontsize=13)
    ax.grid(True, linestyle=':', alpha=0.5)

    # Panel 2: MS
    ax = axes[0, 1]
    for gtype, color in CLASS_COLORS.items():
        sub = sample_df[sample_df['galaxy_type'] == gtype]
        if len(sub) > 0: ax.scatter(sub['lgm_tot_p50'], sub['sfr_tot_p50'], s=8, alpha=0.4, color=color, edgecolors='none')
    ax.set_xlabel(r'$\log(M_* / M_\odot)$', fontsize=12)
    ax.set_ylabel(r'$\log(\mathrm{SFR})$', fontsize=12)
    ax.set_title('(B) 은하 주계열 (SFMS) 질량 vs 별생성률 산점도', fontsize=13)
    ax.grid(True, linestyle=':', alpha=0.5)

    # Panel 3: Color-Mass
    ax = axes[1, 0]
    for gtype, color in CLASS_COLORS.items():
        sub = sample_df[sample_df['galaxy_type'] == gtype]
        if len(sub) > 0: ax.scatter(sub['lgm_tot_p50'], sub['color_u_r'], s=8, alpha=0.4, color=color, edgecolors='none')
    ax.set_xlabel(r'$\log(M_* / M_\odot)$', fontsize=12)
    ax.set_ylabel(r'$(u - r)\,\mathrm{[mag]}$', fontsize=12)
    ax.set_title('(C) 색-질량 이분성 (Color-Mass) 산점도', fontsize=13)
    ax.grid(True, linestyle=':', alpha=0.5)

    # Panel 4: MZR
    ax = axes[1, 1]
    for gtype, color in CLASS_COLORS.items():
        sub = sample_df[sample_df['galaxy_type'] == gtype]
        if len(sub) > 0: ax.scatter(sub['lgm_tot_p50'], sub['oh_p50'], s=8, alpha=0.4, color=color, 
                                     label=gtype.split(" (")[0], edgecolors='none')
    ax.set_xlabel(r'$\log(M_* / M_\odot)$', fontsize=12)
    ax.set_ylabel(r'$12 + \log(\mathrm{O/H})$', fontsize=12)
    ax.set_title('(D) 질량-금속량 관계 (MZR) 산점도', fontsize=13)
    ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", markerscale=2.5, fontsize=10)
    ax.grid(True, linestyle=':', alpha=0.5)

    plt.suptitle('SDSS DR18 은하 4대 핵심 관측 다이어그램 순수 산점도 종합 패널', fontsize=17, y=1.01)
    save_scatter(fig, "산점도14_4대_핵심관계_순수산점도_4분할종합패널.png")

    # -------------------------------------------------------------
    # 안내서 작성
    # -------------------------------------------------------------
    readme_text = """================================================================================
YSC 은하 관측 순수 산점도(Scatter Plot) 도표 패키지 안내서
학교명: 전남과학고등학교 | 연구 동아리: AGN (Active Galactic Nuclei)
================================================================================

본 패키지는 모든 회귀선, 경계선, 기준선(Line)을 일체 배제하고,
오직 실제 SDSS DR18 관측 데이터의 점(Scatter Points)만으로 렌더링한
고해상도(300 DPI) 순수 산점도 도표 14종 모음입니다.

[수록된 순수 산점도 파일 목록 (총 14종, 300 DPI PNG)]
1. 산점도01_BPT_화학이온화_방출선비.png       : Kauffmann/Kewley 선 없는 순수 방출선비 산점도
2. 산점도02_은하주계열_SFMS_항성질량_별생성률.png : 회귀선/퀜칭선 없는 순수 주계열 산점도
3. 산점도03_질량_금속량_MZR_항성질량_산소풍부도.png: 포화한계선 없는 순수 MZR 산점도
4. 산점도04_별생성률_금속량_FMR_산점도.png          : 질량 컬러맵 기반 순수 FMR 산점도
5. 산점도05_색_질량_ColorMass_항성질량_색지수.png   : Red/Blue 경계선 없는 순수 색-질량 산점도
6. 산점도06_바리온_툴리피셔_항성질량_원반회전속도.png: 순수 툴리-피셔 회전속도 산점도
7. 산점도07_항성질량_암흑물질분율.png              : 순수 암흑물질 분율 산점도
8. 산점도08_비별생성률_sSFR_항성질량_퀜칭.png       : 퀜칭 임계선 없는 순수 sSFR 산점도
9. 산점도09_은하진화지수_GEI_항성연령_Dn4000.png    : 회귀선 없는 순수 GEI vs Dn4000 산점도
10. 산점도10_은하진화지수_GEI_광학색지수.png        : 형태별 GEI vs 색지수 산점도
11. 산점도11_항성질량_은하진화지수_GEI.png          : SFR 컬러맵 기반 질량 vs GEI 산점도
12. 산점도12_3차원_FMR_질량_별생성률_금속량_순수산점도.png: 회귀 곡면(Surface) 없는 순수 3D 점 산점도
13. 산점도13_3차원_물리진화_질량_색지수_GEI_순수산점도.png: 순수 3D 질량-색지수-GEI 관측 산점도
14. 산점도14_4대_핵심관계_순수산점도_4분할종합패널.png : 선 없는 BPT, SFMS, Color-Mass, MZR 4분할 종합
================================================================================
"""
    with open(os.path.join(target_dir, "README_순수산점도_명세서.txt"), "w", encoding='utf-8') as f:
        f.write(readme_text)

    # -------------------------------------------------------------
    # ZIP 압축 파일 생성
    # -------------------------------------------------------------
    print("\nZIP 압축 파일 생성 중...")
    zip_dest = os.path.join(downloads_dir, pkg_name)
    shutil.make_archive(zip_dest, 'zip', target_dir)
    zip_full_path = zip_dest + ".zip"
    print("=" * 80)
    print(f"🎉 순수 산점도 14종 생성 및 ZIP 압축 완료!")
    print(f"• 압축 파일: {zip_full_path} ({os.path.getsize(zip_full_path)/(1024*1024):.2f} MB)")
    print(f"• 해제 폴더: {target_dir}")
    print("=" * 80)

if __name__ == '__main__':
    main()
