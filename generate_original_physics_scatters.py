"""
YSC 대회 제출용: 은하 진화 지수(GEI) 축을 전면 배제하고
기존 관측 물리량만으로 선(Line) 없이 점으로만 렌더링한 순수 산점도 생성 스크립트
================================================================================
규칙:
  1. 은하 진화 지수(GEI) 축/변수 전면 제거.
  2. 오직 기존 관측 데이터의 고유 물리량(질량, SFR, sSFR, 금속량, 색지수, 회전속도, 속도분산, Dn4000, 반경, 암흑물질 등)만 사용.
  3. 회귀선, 경계선, 기준선 등 일체의 선(Line)을 배제하고 오직 점(Scatter Dots)만으로 렌더링.
  4. 300 DPI 고해상도 출판 규격.
  5. 이전 생성된 zip 파일들을 삭제하고, 새로운 단일 zip 파일로 다운로드 폴더에 압축 저장.
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

# 폰트 및 스타일
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
    pkg_name = "YSC_은하관측_물리량_순수산점도"
    target_dir = os.path.join(downloads_dir, pkg_name)

    print("=" * 80)
    print("은하 진화 지수(GEI) 축 제외 & 기존 물리량만 사용한 순수 산점도(No Lines) 생성")
    print("=" * 80)

    # 1. 이전 생성된 zip 파일들 및 구버전 산점도 폴더 삭제
    print("\n[1/4] 이전 ZIP 파일들 정리 중...")
    for item in os.listdir(downloads_dir):
        full_path = os.path.join(downloads_dir, item)
        if item.endswith('.zip') and 'YSC' in item:
            os.remove(full_path)
            print(f"  -> 이전 ZIP 삭제: {item}")
        elif os.path.isdir(full_path) and item.startswith('YSC_') and item != pkg_name:
            shutil.rmtree(full_path, ignore_errors=True)
            print(f"  -> 이전 구버전 폴더 삭제: {item}")

    if os.path.exists(target_dir):
        shutil.rmtree(target_dir, ignore_errors=True)
    os.makedirs(target_dir, exist_ok=True)
    print(f"  -> 신규 저장 폴더 생성: {target_dir}")

    # 2. 데이터 로드
    print("\n[2/4] 마스터 데이터셋 로드...")
    csv_path = 'galaxy_master_complete_all.csv'
    df = pd.read_csv(csv_path)
    print(f"  -> 총 표본 수: {len(df):,}개")

    # 선명한 산점도를 위한 20,000개 표본 샘플링 (밀도와 투명도 최적화)
    sample_df = df.sample(min(len(df), 20000), random_state=42).copy()

    # 광학 색지수 극단적 이상치 클리핑 (-1 ~ 5 mag)
    sample_df['color_u_r_clean'] = sample_df['color_u_r'].clip(-0.5, 4.5)
    sample_df['r_e_kpc_clean'] = sample_df['r_e_kpc'].clip(0.1, 30.0)

    def save_scatter(fig, filename):
        out_path = os.path.join(target_dir, filename)
        fig.savefig(out_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
        print(f"  -> 산점도 저장: {filename}")

    print("\n[3/4] 순수 산점도(Line 일체 없음) 16종 생성 중...")

    # -------------------------------------------------------------
    # 01. BPT 화학 이온화 방출선비 산점도
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(10, 8))
    for gtype, color in CLASS_COLORS.items():
        sub = sample_df[sample_df['galaxy_type'] == gtype]
        if len(sub) > 0:
            ax.scatter(sub['log_nii_ha'], sub['log_oiii_hb'], s=12, alpha=0.45, color=color, 
                       label=gtype.split(" (")[0], edgecolors='none')
    ax.set_xlim(-1.8, 0.8); ax.set_ylim(-1.5, 1.6)
    ax.set_xlabel(r'$\log([\mathrm{N\,II}]\lambda6584 / \mathrm{H}\alpha)$', fontsize=13)
    ax.set_ylabel(r'$\log([\mathrm{O\,III}]\lambda5007 / \mathrm{H}\beta)$', fontsize=13)
    ax.set_title('BPT 화학 이온화 방출선비 관측 산점도 (선 없음)', fontsize=15, pad=12)
    ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", markerscale=2.5, fontsize=10)
    ax.grid(True, linestyle=':', alpha=0.5)
    save_scatter(fig, "산점도01_BPT_화학이온화_방출선비.png")

    # -------------------------------------------------------------
    # 02. 은하 주계열 (SFMS) : 항성 질량 vs 별 생성률
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(10, 8))
    for gtype, color in CLASS_COLORS.items():
        sub = sample_df[sample_df['galaxy_type'] == gtype]
        if len(sub) > 0:
            ax.scatter(sub['lgm_tot_p50'], sub['sfr_tot_p50'], s=12, alpha=0.45, color=color, 
                       label=gtype.split(" (")[0], edgecolors='none')
    ax.set_xlabel(r'항성 질량 $\log(M_* / M_\odot)$', fontsize=13)
    ax.set_ylabel(r'별 생성률 $\log(\mathrm{SFR}\,[M_\odot/\mathrm{yr}])$', fontsize=13)
    ax.set_title('은하 주계열(SFMS): 항성 질량 vs 별 생성률 관측 산점도 (선 없음)', fontsize=15, pad=12)
    ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", markerscale=2.5, fontsize=10)
    ax.grid(True, linestyle=':', alpha=0.5)
    save_scatter(fig, "산점도02_은하주계열_SFMS_항성질량_별생성률.png")

    # -------------------------------------------------------------
    # 03. 질량-금속량 관계 (MZR) : 항성 질량 vs 산소 금속량
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(10, 8))
    for gtype, color in CLASS_COLORS.items():
        sub = sample_df[sample_df['galaxy_type'] == gtype]
        if len(sub) > 0:
            ax.scatter(sub['lgm_tot_p50'], sub['oh_p50'], s=12, alpha=0.45, color=color, 
                       label=gtype.split(" (")[0], edgecolors='none')
    ax.set_xlabel(r'항성 질량 $\log(M_* / M_\odot)$', fontsize=13)
    ax.set_ylabel(r'기체 산소 풍부도 $12 + \log(\mathrm{O/H})$', fontsize=13)
    ax.set_title('질량-금속량 관계(MZR): 항성 질량 vs 산소 풍부도 관측 산점도 (선 없음)', fontsize=15, pad=12)
    ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", markerscale=2.5, fontsize=10)
    ax.grid(True, linestyle=':', alpha=0.5)
    save_scatter(fig, "산점도03_질량_금속량_MZR_항성질량_산소금속량.png")

    # -------------------------------------------------------------
    # 04. 기본 금속량 관계 (FMR) : 별 생성률 vs 산소 금속량
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(10, 8))
    sc = ax.scatter(sample_df['sfr_tot_p50'], sample_df['oh_p50'], c=sample_df['lgm_tot_p50'], 
                    cmap='viridis', s=12, alpha=0.5, edgecolors='none')
    cbar = plt.colorbar(sc, ax=ax)
    cbar.set_label(r'항성 질량 $\log(M_* / M_\odot)$', fontsize=12)
    ax.set_xlabel(r'별 생성률 $\log(\mathrm{SFR}\,[M_\odot/\mathrm{yr}])$', fontsize=13)
    ax.set_ylabel(r'기체 산소 풍부도 $12 + \log(\mathrm{O/H})$', fontsize=13)
    ax.set_title('별 생성률 vs 기체 산소 풍부도 관측 산점도 (질량 컬러맵, 선 없음)', fontsize=15, pad=12)
    ax.grid(True, linestyle=':', alpha=0.5)
    save_scatter(fig, "산점도04_기본금속량_FMR_별생성률_산소금속량.png")

    # -------------------------------------------------------------
    # 05. 색-질량 도표 (Color-Mass) : 항성 질량 vs 광학 색지수
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(10, 8))
    for gtype, color in CLASS_COLORS.items():
        sub = sample_df[sample_df['galaxy_type'] == gtype]
        if len(sub) > 0:
            ax.scatter(sub['lgm_tot_p50'], sub['color_u_r_clean'], s=12, alpha=0.45, color=color, 
                       label=gtype.split(" (")[0], edgecolors='none')
    ax.set_xlabel(r'항성 질량 $\log(M_* / M_\odot)$', fontsize=13)
    ax.set_ylabel(r'광학 색지수 $(u - r)\,\mathrm{[mag]}$', fontsize=13)
    ax.set_title('색-질량 도표(Color-Mass): 항성 질량 vs 광학 색지수 관측 산점도 (선 없음)', fontsize=15, pad=12)
    ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", markerscale=2.5, fontsize=10)
    ax.grid(True, linestyle=':', alpha=0.5)
    save_scatter(fig, "산점도05_색_질량_ColorMass_항성질량_광학색지수.png")

    # -------------------------------------------------------------
    # 06. 비별생성률 (sSFR) 퀜칭 도표 : 항성 질량 vs sSFR
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(10, 8))
    sc = ax.scatter(sample_df['lgm_tot_p50'], sample_df['log_ssfr'], c=sample_df['color_u_r_clean'], 
                    cmap='coolwarm', s=12, alpha=0.5, edgecolors='none')
    cbar = plt.colorbar(sc, ax=ax)
    cbar.set_label(r'광학 색지수 $(u - r)\,\mathrm{[mag]}$', fontsize=12)
    ax.set_xlabel(r'항성 질량 $\log(M_* / M_\odot)$', fontsize=13)
    ax.set_ylabel(r'비별생성률 $\log(\mathrm{sSFR}\,[\mathrm{yr}^{-1}])$', fontsize=13)
    ax.set_title('항성 질량 vs 비별생성률(sSFR) 관측 산점도 (색지수 컬러맵, 선 없음)', fontsize=15, pad=12)
    ax.grid(True, linestyle=':', alpha=0.5)
    save_scatter(fig, "산점도06_비별생성률_sSFR_항성질량_퀜칭.png")

    # -------------------------------------------------------------
    # 07. 바리온 툴리-피셔 : 항성 질량 vs 원반 회전속도
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(10, 8))
    for gtype, color in CLASS_COLORS.items():
        sub = sample_df[sample_df['galaxy_type'] == gtype]
        if len(sub) > 0:
            ax.scatter(sub['lgm_tot_p50'], sub['v_rot'], s=12, alpha=0.45, color=color, 
                       label=gtype.split(" (")[0], edgecolors='none')
    ax.set_xlabel(r'항성 질량 $\log(M_* / M_\odot)$', fontsize=13)
    ax.set_ylabel(r'은하 원반 회전속도 $V_{\mathrm{rot}}\,[\mathrm{km/s}]$', fontsize=13)
    ax.set_title('바리온 툴리-피셔: 항성 질량 vs 원반 회전속도 관측 산점도 (선 없음)', fontsize=15, pad=12)
    ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", markerscale=2.5, fontsize=10)
    ax.grid(True, linestyle=':', alpha=0.5)
    save_scatter(fig, "산점도07_바리온_툴리피셔_항성질량_원반회전속도.png")

    # -------------------------------------------------------------
    # 08. 파버-잭슨 동역학 : 항성 질량 vs 속도 분산
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(10, 8))
    for gtype, color in CLASS_COLORS.items():
        sub = sample_df[sample_df['galaxy_type'] == gtype]
        if len(sub) > 0:
            ax.scatter(sub['lgm_tot_p50'], sub['velDisp'], s=12, alpha=0.45, color=color, 
                       label=gtype.split(" (")[0], edgecolors='none')
    ax.set_xlabel(r'항성 질량 $\log(M_* / M_\odot)$', fontsize=13)
    ax.set_ylabel(r'중심부 속도 분산 $\sigma_v\,[\mathrm{km/s}]$', fontsize=13)
    ax.set_title('파버-잭슨 관계: 항성 질량 vs 중심부 속도 분산 관측 산점도 (선 없음)', fontsize=15, pad=12)
    ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", markerscale=2.5, fontsize=10)
    ax.grid(True, linestyle=':', alpha=0.5)
    save_scatter(fig, "산점도08_파버잭슨_항성질량_속도분산.png")

    # -------------------------------------------------------------
    # 09. 질량-크기 관계 (Mass-Size) : 항성 질량 vs 유효 반경
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(10, 8))
    for gtype, color in CLASS_COLORS.items():
        sub = sample_df[sample_df['galaxy_type'] == gtype]
        if len(sub) > 0:
            ax.scatter(sub['lgm_tot_p50'], sub['r_e_kpc_clean'], s=12, alpha=0.45, color=color, 
                       label=gtype.split(" (")[0], edgecolors='none')
    ax.set_xlabel(r'항성 질량 $\log(M_* / M_\odot)$', fontsize=13)
    ax.set_ylabel(r'유효 반경 $R_e\,[\mathrm{kpc}]$', fontsize=13)
    ax.set_title('질량-크기 관계(Mass-Size): 항성 질량 vs 유효 반경 관측 산점도 (선 없음)', fontsize=15, pad=12)
    ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", markerscale=2.5, fontsize=10)
    ax.grid(True, linestyle=':', alpha=0.5)
    save_scatter(fig, "산점도09_질량크기관계_항성질량_유효반경.png")

    # -------------------------------------------------------------
    # 10. 동역학 질량 vs 항성 질량
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(10, 8))
    for gtype, color in CLASS_COLORS.items():
        sub = sample_df[sample_df['galaxy_type'] == gtype]
        if len(sub) > 0:
            ax.scatter(sub['lgm_tot_p50'], sub['log_dyn_mass'], s=12, alpha=0.45, color=color, 
                       label=gtype.split(" (")[0], edgecolors='none')
    ax.set_xlabel(r'항성 질량 $\log(M_* / M_\odot)$', fontsize=13)
    ax.set_ylabel(r'동역학 질량 $\log(M_{\mathrm{dyn}} / M_\odot)$', fontsize=13)
    ax.set_title('항성 질량 vs 동역학 질량(M_dyn) 관측 산점도 (선 없음)', fontsize=15, pad=12)
    ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", markerscale=2.5, fontsize=10)
    ax.grid(True, linestyle=':', alpha=0.5)
    save_scatter(fig, "산점도10_동역학질량_항성질량.png")

    # -------------------------------------------------------------
    # 11. 항성 질량 vs 암흑물질 분율
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(10, 8))
    for gtype, color in CLASS_COLORS.items():
        sub = sample_df[sample_df['galaxy_type'] == gtype]
        if len(sub) > 0:
            ax.scatter(sub['lgm_tot_p50'], sub['dark_matter_fraction'] * 100, s=12, alpha=0.45, color=color, 
                       label=gtype.split(" (")[0], edgecolors='none')
    ax.set_xlabel(r'항성 질량 $\log(M_* / M_\odot)$', fontsize=13)
    ax.set_ylabel(r'암흑물질 분율 $f_{\mathrm{DM}}\,\,[\%]$', fontsize=13)
    ax.set_title('항성 질량 vs 암흑물질 분율 관측 산점도 (선 없음)', fontsize=15, pad=12)
    ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", markerscale=2.5, fontsize=10)
    ax.grid(True, linestyle=':', alpha=0.5)
    save_scatter(fig, "산점도11_항성질량_암흑물질분율.png")

    # -------------------------------------------------------------
    # 12. 항성 연령 지표 Dn(4000) vs 광학 색지수
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(10, 8))
    sc = ax.scatter(sample_df['color_u_r_clean'], sample_df['d4000_n'], c=sample_df['lgm_tot_p50'], 
                    cmap='viridis', s=12, alpha=0.5, edgecolors='none')
    cbar = plt.colorbar(sc, ax=ax)
    cbar.set_label(r'항성 질량 $\log(M_* / M_\odot)$', fontsize=12)
    ax.set_xlabel(r'광학 색지수 $(u - r)\,\mathrm{[mag]}$', fontsize=13)
    ax.set_ylabel(r'4000Å 불연속도 ($D_n(4000)$ - 항성 연령)', fontsize=13)
    ax.set_title('광학 색지수 vs 4000Å 불연속도(Dn4000) 관측 산점도 (질량 컬러맵, 선 없음)', fontsize=15, pad=12)
    ax.grid(True, linestyle=':', alpha=0.5)
    save_scatter(fig, "산점도12_항성연령_Dn4000_광학색지수.png")

    # -------------------------------------------------------------
    # 13. 항성 연령 지표 Dn(4000) vs 항성 질량
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(10, 8))
    sc = ax.scatter(sample_df['lgm_tot_p50'], sample_df['d4000_n'], c=sample_df['sfr_tot_p50'], 
                    cmap='plasma', s=12, alpha=0.5, edgecolors='none')
    cbar = plt.colorbar(sc, ax=ax)
    cbar.set_label(r'별 생성률 $\log(\mathrm{SFR})$', fontsize=12)
    ax.set_xlabel(r'항성 질량 $\log(M_* / M_\odot)$', fontsize=13)
    ax.set_ylabel(r'4000Å 불연속도 ($D_n(4000)$ - 항성 연령)', fontsize=13)
    ax.set_title('항성 질량 vs 4000Å 불연속도(Dn4000) 관측 산점도 (SFR 컬러맵, 선 없음)', fontsize=15, pad=12)
    ax.grid(True, linestyle=':', alpha=0.5)
    save_scatter(fig, "산점도13_항성연령_Dn4000_항성질량.png")

    # -------------------------------------------------------------
    # 14. 3차원 기본 금속량 관계 (FMR 3D) 순수 산점도 (선/곡면 전혀 없음!)
    # -------------------------------------------------------------
    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, projection='3d')
    sub_3d = sample_df.sample(min(len(sample_df), 5000), random_state=42)
    p = ax.scatter(sub_3d['lgm_tot_p50'], sub_3d['sfr_tot_p50'], sub_3d['oh_p50'], 
                   c=sub_3d['color_u_r_clean'], cmap='coolwarm', s=14, alpha=0.6, edgecolors='none')
    cbar = fig.colorbar(p, ax=ax, pad=0.1, shrink=0.7)
    cbar.set_label(r'색지수 $(u - r)\,\mathrm{[mag]}$', fontsize=12)
    ax.set_xlabel(r'항성 질량 $\log(M_*/M_\odot)$', fontsize=11, labelpad=10)
    ax.set_ylabel(r'별 생성률 $\log(\mathrm{SFR})$', fontsize=11, labelpad=10)
    ax.set_zlabel(r'산소 금속량 $12+\log(\mathrm{O/H})$', fontsize=11, labelpad=10)
    ax.set_title('3차원 기본 금속량 관계(FMR): 질량-SFR-금속량 순수 3D 관측 산점도 (선 없음)', fontsize=14, pad=15)
    ax.view_init(elev=24, azim=-55)
    save_scatter(fig, "산점도14_3차원_FMR_질량_별생성률_금속량_순수산점도.png")

    # -------------------------------------------------------------
    # 15. 3차원 은하 동역학 관계 (질량-회전속도-유효반경) 순수 3D 산점도
    # -------------------------------------------------------------
    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, projection='3d')
    p2 = ax.scatter(sub_3d['lgm_tot_p50'], sub_3d['v_rot'], sub_3d['r_e_kpc_clean'], 
                    c=sub_3d['velDisp'], cmap='viridis', s=14, alpha=0.6, edgecolors='none')
    cbar2 = fig.colorbar(p2, ax=ax, pad=0.1, shrink=0.7)
    cbar2.set_label(r'속도 분산 $\sigma_v\,[\mathrm{km/s}]$', fontsize=12)
    ax.set_xlabel(r'항성 질량 $\log(M_*/M_\odot)$', fontsize=11, labelpad=10)
    ax.set_ylabel(r'회전속도 $V_{\mathrm{rot}}\,[\mathrm{km/s}]$', fontsize=11, labelpad=10)
    ax.set_zlabel(r'유효 반경 $R_e\,[\mathrm{kpc}]$', fontsize=11, labelpad=10)
    ax.set_title('3차원 은하 동역학: 질량-회전속도-유효반경 순수 3D 관측 산점도 (선 없음)', fontsize=14, pad=15)
    ax.view_init(elev=26, azim=-60)
    save_scatter(fig, "산점도15_3차원_은하동역학_질량_회전속도_유효반경_순수산점도.png")

    # -------------------------------------------------------------
    # 16. 4대 핵심 관측 물리량 순수 산점도 4분할 패널
    # -------------------------------------------------------------
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
        if len(sub) > 0: ax.scatter(sub['lgm_tot_p50'], sub['color_u_r_clean'], s=8, alpha=0.4, color=color, edgecolors='none')
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

    plt.suptitle('SDSS DR18 은하 4대 핵심 고유 물리량 관측 순수 산점도 패널 (선 없음)', fontsize=17, y=1.01)
    save_scatter(fig, "산점도16_4대_핵심물리량_순수산점도_4분할종합패널.png")

    # -------------------------------------------------------------
    # 안내서 작성
    # -------------------------------------------------------------
    readme_text = """================================================================================
YSC 은하 관측 고유 물리량 순수 산점도(No Lines) 패키지 안내서
학교명: 전남과학고등학교 | 연구 동아리: AGN (Active Galactic Nuclei)
================================================================================

본 패키지는 '은하 진화 지수(GEI)' 축을 전면 배제하고,
기존 SDSS 관측 데이터에 존재하는 고유 천체물리량들만을 사용하여
모든 회귀선, 경계선, 기준선(Line)을 배제하고 오직 순수 데이터 점(Dots)으로만 구성한
300 DPI 고해상도 산점도 16종 모음입니다.

[사용된 고유 천체물리량 목록]
• 항성 질량 (lgm_tot_p50): log(M* / M_sun)
• 별 생성률 (sfr_tot_p50): log(SFR [M_sun/yr])
• 비별생성률 (log_ssfr): log(sSFR [yr^-1])
• 기체 산소 금속량 (oh_p50): 12 + log(O/H)
• 광학 색지수 (color_u_r): u - r [mag]
• 4000Å 불연속도 (d4000_n): 분광 항성 종족 연령 지표
• 은하 원반 회전속도 (v_rot): km/s
• 중심부 속도 분산 (velDisp): km/s
• 은하 유효 반경 (r_e_kpc): kpc
• 동역학 질량 (log_dyn_mass): log(M_dyn / M_sun)
• 암흑물질 분율 (dark_matter_fraction): %
• BPT 방출선비: log([NII]/Ha), log([OIII]/Hb)

[수록된 순수 산점도 파일 목록 (총 16종, 300 DPI PNG)]
01. 산점도01_BPT_화학이온화_방출선비.png
02. 산점도02_은하주계열_SFMS_항성질량_별생성률.png
03. 산점도03_질량_금속량_MZR_항성질량_산소금속량.png
04. 산점도04_기본금속량_FMR_별생성률_산소금속량.png
05. 산점도05_색_질량_ColorMass_항성질량_광학색지수.png
06. 산점도06_비별생성률_sSFR_항성질량_퀜칭.png
07. 산점도07_바리온_툴리피셔_항성질량_원반회전속도.png
08. 산점도08_파버잭슨_항성질량_속도분산.png
09. 산점도09_질량크기관계_항성질량_유효반경.png
10. 산점도10_동역학질량_항성질량.png
11. 산점도11_항성질량_암흑물질분율.png
12. 산점도12_항성연령_Dn4000_광학색지수.png
13. 산점도13_항성연령_Dn4000_항성질량.png
14. 산점도14_3차원_FMR_질량_별생성률_금속량_순수산점도.png (질량-SFR-금속량 3D 점)
15. 산점도15_3차원_은하동역학_질량_회전속도_유효반경_순수산점도.png (질량-회전속도-반경 3D 점)
16. 산점도16_4대_핵심물리량_순수산점도_4분할종합패널.png (BPT, SFMS, Color-Mass, MZR 종합)
================================================================================
"""
    with open(os.path.join(target_dir, "README_물리량_순수산점도_명세서.txt"), "w", encoding='utf-8') as f:
        f.write(readme_text)

    # 4. 단일 ZIP 압축 아카이브 생성
    print("\n[4/4] 단일 ZIP 아카이브 압축 중...")
    zip_dest = os.path.join(downloads_dir, pkg_name)
    shutil.make_archive(zip_dest, 'zip', target_dir)
    final_zip = zip_dest + ".zip"
    print("=" * 80)
    print(f"🎉 순수 물리량 산점도 16종 생성 및 최종 ZIP 압축 완료!")
    print(f"• 최종 ZIP 파일 위치: {final_zip} ({os.path.getsize(final_zip)/(1024*1024):.2f} MB)")
    print(f"• 압축 해제 폴더: {target_dir}")
    print("=" * 80)

if __name__ == '__main__':
    main()
