"""
YSC 대회 제출용: 사용자 지정 4대 핵심 물리량 전용 순수 산점도(No Lines) 생성 및 ZIP 패키징
========================================================================================
지정 물리량 4종:
  1. 스펙트럼 분석 (Ha 영역): H-alpha 관측 플럭스 log(F_Ha), H-alpha 광도 log(L_Ha), [NII]/Ha 선비
  2. 항성 질량 (Mass): log(M* / M_sun)
  3. 거리 / 적색편이 (Distance / Redshift): 적색편이 z, 광도거리 D_L [Mpc]
  4. 별 생성률 (SFR): log(SFR [M_sun/yr]), 비별생성률 log(sSFR [yr^-1])

엄격한 작성 규칙:
  - 은하 진화 지수(GEI) 축 전면 배제 (일체 사용 안 함)
  - 회귀선, 경계선, 분할선 등 임의의 선(Line) 100% 제거 (오직 관측 데이터 점(Dots)만 사용)
  - 300 DPI 고해상도 출판 규격
  - 이전 ZIP 파일들 삭제 및 단일 ZIP 압축 아카이브 생성
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
    pkg_name = "YSC_은하관측_4대핵심물리량_순수산점도"
    target_dir = os.path.join(downloads_dir, pkg_name)

    print("=" * 80)
    print("4대 핵심 물리량(스펙트럼 Ha, 질량, 거리/적색편이, 별생성률) 순수 산점도 생성")
    print("=" * 80)

    # 1. 이전 ZIP 파일들 및 구버전 폴더 삭제
    print("\n[1/4] 이전 ZIP 파일들 정리 중...")
    for item in os.listdir(downloads_dir):
        full_path = os.path.join(downloads_dir, item)
        if item.endswith('.zip') and 'YSC' in item:
            os.remove(full_path)
            print(f"  -> 이전 ZIP 삭제: {item}")
        elif os.path.isdir(full_path) and item.startswith('YSC_') and item != pkg_name:
            shutil.rmtree(full_path, ignore_errors=True)
            print(f"  -> 이전 폴더 삭제: {item}")

    if os.path.exists(target_dir):
        shutil.rmtree(target_dir, ignore_errors=True)
    os.makedirs(target_dir, exist_ok=True)
    print(f"  -> 신규 저장 폴더: {target_dir}")

    # 2. 데이터 로드 및 4대 물리량 파생 변수 계산
    print("\n[2/4] 마스터 데이터셋 로드 및 물리량 계산...")
    df = pd.read_csv('galaxy_master_complete_all.csv')
    print(f"  -> 총 관측 표본: {len(df):,}개")

    # 광도거리 D_L (Mpc) 및 cm 단위 변환
    c = 299792.458 # km/s
    H0 = 70.0      # km/s/Mpc
    df['dist_lum_mpc'] = (c * df['z'] / H0) * (1 + df['z']/2)
    d_l_cm = df['dist_lum_mpc'] * 3.0857e24

    # H-alpha 관측 플럭스 log(F_Ha [10^-17 erg/s/cm^2]) 및 광도 log(L_Ha [erg/s])
    df['log_ha_flux'] = np.log10(np.maximum(0.1, df['h_alpha_flux'])).clip(-1.0, 5.0)
    df['log_ha_lum'] = (df['log_ha_flux'] + 2 * np.log10(d_l_cm) + np.log10(4 * np.pi) - 17).clip(36.5, 43.5)

    # 20,000개 표본 샘플링 (산점도 가독성 및 밀도 최적화)
    sample_df = df.sample(min(len(df), 20000), random_state=42).copy()

    def save_scatter(fig, filename):
        out_path = os.path.join(target_dir, filename)
        fig.savefig(out_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
        print(f"  -> 산점도 저장 완료: {filename}")

    print("\n[3/4] 4대 물리량 순수 산점도 16종 생성 중...")

    # -------------------------------------------------------------
    # 01. 스펙트럼 Ha 광도 vs 별 생성률 (Kennicutt 1998 실측 검증)
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(10, 8))
    for gtype, color in CLASS_COLORS.items():
        sub = sample_df[sample_df['galaxy_type'] == gtype]
        if len(sub) > 0:
            ax.scatter(sub['log_ha_lum'], sub['sfr_tot_p50'], s=12, alpha=0.45, color=color, 
                       label=gtype.split(" (")[0], edgecolors='none')
    ax.set_xlabel(r'$\mathrm{H}\alpha$ 방출선 광도 $\log(L_{\mathrm{H}\alpha}\,[\mathrm{erg/s}])$', fontsize=13)
    ax.set_ylabel(r'별 생성률 $\log(\mathrm{SFR}\,[M_\odot/\mathrm{yr}])$', fontsize=13)
    ax.set_title(r'스펙트럼 분석: $\mathrm{H}\alpha$ 광도 vs 별 생성률 관측 산점도 (선 없음)', fontsize=15, pad=12)
    ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", markerscale=2.5, fontsize=10)
    ax.grid(True, linestyle=':', alpha=0.5)
    save_scatter(fig, "산점도01_스펙트럼_Ha광도_vs_별생성률.png")

    # -------------------------------------------------------------
    # 02. 스펙트럼 Ha 플럭스 vs 별 생성률
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(10, 8))
    for gtype, color in CLASS_COLORS.items():
        sub = sample_df[sample_df['galaxy_type'] == gtype]
        if len(sub) > 0:
            ax.scatter(sub['log_ha_flux'], sub['sfr_tot_p50'], s=12, alpha=0.45, color=color, 
                       label=gtype.split(" (")[0], edgecolors='none')
    ax.set_xlabel(r'$\mathrm{H}\alpha$ 관측 플럭스 $\log(F_{\mathrm{H}\alpha}\,[10^{-17}\,\mathrm{erg/s/cm^2}])$', fontsize=13)
    ax.set_ylabel(r'별 생성률 $\log(\mathrm{SFR}\,[M_\odot/\mathrm{yr}])$', fontsize=13)
    ax.set_title(r'스펙트럼 분석: $\mathrm{H}\alpha$ 플럭스 vs 별 생성률 관측 산점도 (선 없음)', fontsize=15, pad=12)
    ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", markerscale=2.5, fontsize=10)
    ax.grid(True, linestyle=':', alpha=0.5)
    save_scatter(fig, "산점도02_스펙트럼_Ha플럭스_vs_별생성률.png")

    # -------------------------------------------------------------
    # 03. 항성 질량 vs 별 생성률 (은하 주계열 SFMS)
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
    save_scatter(fig, "산점도03_항성질량_vs_별생성률_SFMS.png")

    # -------------------------------------------------------------
    # 04. 항성 질량 vs 비별생성률 (sSFR)
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(10, 8))
    sc = ax.scatter(sample_df['lgm_tot_p50'], sample_df['log_ssfr'], c=sample_df['log_ha_lum'], 
                    cmap='viridis', s=12, alpha=0.5, edgecolors='none')
    cbar = plt.colorbar(sc, ax=ax)
    cbar.set_label(r'$\mathrm{H}\alpha$ 광도 $\log(L_{\mathrm{H}\alpha})$', fontsize=12)
    ax.set_xlabel(r'항성 질량 $\log(M_* / M_\odot)$', fontsize=13)
    ax.set_ylabel(r'비별생성률 $\log(\mathrm{sSFR}\,[\mathrm{yr}^{-1}])$', fontsize=13)
    ax.set_title(r'항성 질량 vs 비별생성률(sSFR) 관측 산점도 ($\mathrm{H}\alpha$ 광도 컬러맵, 선 없음)', fontsize=15, pad=12)
    ax.grid(True, linestyle=':', alpha=0.5)
    save_scatter(fig, "산점도04_항성질량_vs_비별생성률_sSFR.png")

    # -------------------------------------------------------------
    # 05. 항성 질량 vs 스펙트럼 Ha 광도
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(10, 8))
    for gtype, color in CLASS_COLORS.items():
        sub = sample_df[sample_df['galaxy_type'] == gtype]
        if len(sub) > 0:
            ax.scatter(sub['lgm_tot_p50'], sub['log_ha_lum'], s=12, alpha=0.45, color=color, 
                       label=gtype.split(" (")[0], edgecolors='none')
    ax.set_xlabel(r'항성 질량 $\log(M_* / M_\odot)$', fontsize=13)
    ax.set_ylabel(r'$\mathrm{H}\alpha$ 방출선 광도 $\log(L_{\mathrm{H}\alpha}\,[\mathrm{erg/s}])$', fontsize=13)
    ax.set_title(r'항성 질량 vs $\mathrm{H}\alpha$ 방출선 광도 관측 산점도 (선 없음)', fontsize=15, pad=12)
    ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", markerscale=2.5, fontsize=10)
    ax.grid(True, linestyle=':', alpha=0.5)
    save_scatter(fig, "산점도05_항성질량_vs_스펙트럼_Ha광도.png")

    # -------------------------------------------------------------
    # 06. 항성 질량 vs 스펙트럼 Ha 관측 플럭스
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(10, 8))
    for gtype, color in CLASS_COLORS.items():
        sub = sample_df[sample_df['galaxy_type'] == gtype]
        if len(sub) > 0:
            ax.scatter(sub['lgm_tot_p50'], sub['log_ha_flux'], s=12, alpha=0.45, color=color, 
                       label=gtype.split(" (")[0], edgecolors='none')
    ax.set_xlabel(r'항성 질량 $\log(M_* / M_\odot)$', fontsize=13)
    ax.set_ylabel(r'$\mathrm{H}\alpha$ 관측 플럭스 $\log(F_{\mathrm{H}\alpha}\,[10^{-17}\,\mathrm{erg/s/cm^2}])$', fontsize=13)
    ax.set_title(r'항성 질량 vs $\mathrm{H}\alpha$ 플럭스 관측 산점도 (선 없음)', fontsize=15, pad=12)
    ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", markerscale=2.5, fontsize=10)
    ax.grid(True, linestyle=':', alpha=0.5)
    save_scatter(fig, "산점도06_항성질량_vs_스펙트럼_Ha플럭스.png")

    # -------------------------------------------------------------
    # 07. 스펙트럼 [NII]/Ha 선비 vs 항성 질량
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(10, 8))
    for gtype, color in CLASS_COLORS.items():
        sub = sample_df[sample_df['galaxy_type'] == gtype]
        if len(sub) > 0:
            ax.scatter(sub['lgm_tot_p50'], sub['log_nii_ha'], s=12, alpha=0.45, color=color, 
                       label=gtype.split(" (")[0], edgecolors='none')
    ax.set_xlabel(r'항성 질량 $\log(M_* / M_\odot)$', fontsize=13)
    ax.set_ylabel(r'질소-수소 분광 선비 $\log([\mathrm{N\,II}]/\mathrm{H}\alpha)$', fontsize=13)
    ax.set_title(r'항성 질량 vs 스펙트럼 $[\mathrm{N\,II}]/\mathrm{H}\alpha$ 선비 관측 산점도 (선 없음)', fontsize=15, pad=12)
    ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", markerscale=2.5, fontsize=10)
    ax.grid(True, linestyle=':', alpha=0.5)
    save_scatter(fig, "산점도07_스펙트럼_NII_Ha선비_vs_항성질량.png")

    # -------------------------------------------------------------
    # 08. 거리(적색편이 z) vs 항성 질량
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(10, 8))
    sc = ax.scatter(sample_df['z'], sample_df['lgm_tot_p50'], c=sample_df['sfr_tot_p50'], 
                    cmap='plasma', s=12, alpha=0.5, edgecolors='none')
    cbar = plt.colorbar(sc, ax=ax)
    cbar.set_label(r'별 생성률 $\log(\mathrm{SFR})$', fontsize=12)
    ax.set_xlabel('거리 (적색편이 z)', fontsize=13)
    ax.set_ylabel(r'항성 질량 $\log(M_* / M_\odot)$', fontsize=13)
    ax.set_title('거리(적색편이 z) vs 항성 질량 관측 산점도 (SFR 컬러맵, 선 없음)', fontsize=15, pad=12)
    ax.grid(True, linestyle=':', alpha=0.5)
    save_scatter(fig, "산점도08_거리_적색편이_vs_항성질량.png")

    # -------------------------------------------------------------
    # 09. 거리(적색편이 z) vs 별 생성률
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(10, 8))
    sc = ax.scatter(sample_df['z'], sample_df['sfr_tot_p50'], c=sample_df['lgm_tot_p50'], 
                    cmap='viridis', s=12, alpha=0.5, edgecolors='none')
    cbar = plt.colorbar(sc, ax=ax)
    cbar.set_label(r'항성 질량 $\log(M_* / M_\odot)$', fontsize=12)
    ax.set_xlabel('거리 (적색편이 z)', fontsize=13)
    ax.set_ylabel(r'별 생성률 $\log(\mathrm{SFR}\,[M_\odot/\mathrm{yr}])$', fontsize=13)
    ax.set_title('거리(적색편이 z) vs 별 생성률 관측 산점도 (질량 컬러맵, 선 없음)', fontsize=15, pad=12)
    ax.grid(True, linestyle=':', alpha=0.5)
    save_scatter(fig, "산점도09_거리_적색편이_vs_별생성률.png")

    # -------------------------------------------------------------
    # 10. 거리(적색편이 z) vs 스펙트럼 Ha 플럭스 (거리 제곱 감쇄 효과)
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(10, 8))
    for gtype, color in CLASS_COLORS.items():
        sub = sample_df[sample_df['galaxy_type'] == gtype]
        if len(sub) > 0:
            ax.scatter(sub['z'], sub['log_ha_flux'], s=12, alpha=0.45, color=color, 
                       label=gtype.split(" (")[0], edgecolors='none')
    ax.set_xlabel('거리 (적색편이 z)', fontsize=13)
    ax.set_ylabel(r'$\mathrm{H}\alpha$ 관측 플럭스 $\log(F_{\mathrm{H}\alpha}\,[10^{-17}\,\mathrm{erg/s/cm^2}])$', fontsize=13)
    ax.set_title(r'거리(적색편이 z) vs $\mathrm{H}\alpha$ 관측 플럭스 산점도 (선 없음)', fontsize=15, pad=12)
    ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", markerscale=2.5, fontsize=10)
    ax.grid(True, linestyle=':', alpha=0.5)
    save_scatter(fig, "산점도10_거리_적색편이_vs_스펙트럼_Ha플럭스.png")

    # -------------------------------------------------------------
    # 11. 거리(적색편이 z) vs 스펙트럼 Ha 광도
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(10, 8))
    sc = ax.scatter(sample_df['z'], sample_df['log_ha_lum'], c=sample_df['sfr_tot_p50'], 
                    cmap='coolwarm', s=12, alpha=0.5, edgecolors='none')
    cbar = plt.colorbar(sc, ax=ax)
    cbar.set_label(r'별 생성률 $\log(\mathrm{SFR})$', fontsize=12)
    ax.set_xlabel('거리 (적색편이 z)', fontsize=13)
    ax.set_ylabel(r'$\mathrm{H}\alpha$ 방출선 광도 $\log(L_{\mathrm{H}\alpha}\,[\mathrm{erg/s}])$', fontsize=13)
    ax.set_title(r'거리(적색편이 z) vs $\mathrm{H}\alpha$ 광도 관측 산점도 (SFR 컬러맵, 선 없음)', fontsize=15, pad=12)
    ax.grid(True, linestyle=':', alpha=0.5)
    save_scatter(fig, "산점도11_거리_적색편이_vs_스펙트럼_Ha광도.png")

    # -------------------------------------------------------------
    # 12. 광도거리 D_L (Mpc) vs 항성 질량
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(10, 8))
    sc = ax.scatter(sample_df['dist_lum_mpc'], sample_df['lgm_tot_p50'], c=sample_df['log_ha_lum'], 
                    cmap='plasma', s=12, alpha=0.5, edgecolors='none')
    cbar = plt.colorbar(sc, ax=ax)
    cbar.set_label(r'$\mathrm{H}\alpha$ 광도 $\log(L_{\mathrm{H}\alpha})$', fontsize=12)
    ax.set_xlabel('광도 거리 $D_L\,[\mathrm{Mpc}]$', fontsize=13)
    ax.set_ylabel(r'항성 질량 $\log(M_* / M_\odot)$', fontsize=13)
    ax.set_title(r'광도 거리 $D_L$ vs 항성 질량 관측 산점도 ($\mathrm{H}\alpha$ 광도 컬러맵, 선 없음)', fontsize=15, pad=12)
    ax.grid(True, linestyle=':', alpha=0.5)
    save_scatter(fig, "산점도12_광도거리_vs_항성질량.png")

    # -------------------------------------------------------------
    # 13. 3차원 순수 산점도: 항성질량 - 별생성률 - Ha광도 (선/곡면 전혀 없음!)
    # -------------------------------------------------------------
    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, projection='3d')
    sub_3d = sample_df.sample(min(len(sample_df), 5000), random_state=42)
    p = ax.scatter(sub_3d['lgm_tot_p50'], sub_3d['sfr_tot_p50'], sub_3d['log_ha_lum'], 
                   c=sub_3d['z'], cmap='viridis', s=14, alpha=0.6, edgecolors='none')
    cbar = fig.colorbar(p, ax=ax, pad=0.1, shrink=0.7)
    cbar.set_label('적색편이 z (거리)', fontsize=12)
    ax.set_xlabel(r'항성 질량 $\log(M_*/M_\odot)$', fontsize=11, labelpad=10)
    ax.set_ylabel(r'별 생성률 $\log(\mathrm{SFR})$', fontsize=11, labelpad=10)
    ax.set_zlabel(r'$\mathrm{H}\alpha$ 광도 $\log(L_{\mathrm{H}\alpha})$', fontsize=11, labelpad=10)
    ax.set_title(r'3차원 관측 산점도: 항성질량 - 별생성률 - $\mathrm{H}\alpha$ 광도 (선 없음)', fontsize=14, pad=15)
    ax.view_init(elev=24, azim=-55)
    save_scatter(fig, "산점도13_3차원_항성질량_별생성률_Ha광도_순수산점도.png")

    # -------------------------------------------------------------
    # 14. 3차원 순수 산점도: 거리(z) - 항성질량 - 별생성률 (선/곡면 전혀 없음!)
    # -------------------------------------------------------------
    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, projection='3d')
    p2 = ax.scatter(sub_3d['z'], sub_3d['lgm_tot_p50'], sub_3d['sfr_tot_p50'], 
                    c=sub_3d['log_ha_flux'], cmap='plasma', s=14, alpha=0.6, edgecolors='none')
    cbar2 = fig.colorbar(p2, ax=ax, pad=0.1, shrink=0.7)
    cbar2.set_label(r'$\mathrm{H}\alpha$ 플럭스 $\log(F_{\mathrm{H}\alpha})$', fontsize=12)
    ax.set_xlabel('적색편이 z (거리)', fontsize=11, labelpad=10)
    ax.set_ylabel(r'항성 질량 $\log(M_*/M_\odot)$', fontsize=11, labelpad=10)
    ax.set_zlabel(r'별 생성률 $\log(\mathrm{SFR})$', fontsize=11, labelpad=10)
    ax.set_title('3차원 관측 산점도: 거리(z) - 항성질량 - 별생성률 (선 없음)', fontsize=14, pad=15)
    ax.view_init(elev=26, azim=-60)
    save_scatter(fig, "산점도14_3차원_거리_항성질량_별생성률_순수산점도.png")

    # -------------------------------------------------------------
    # 15. 3차원 순수 산점도: 거리(z) - 항성질량 - Ha광도 (선/곡면 전혀 없음!)
    # -------------------------------------------------------------
    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, projection='3d')
    p3 = ax.scatter(sub_3d['z'], sub_3d['lgm_tot_p50'], sub_3d['log_ha_lum'], 
                    c=sub_3d['sfr_tot_p50'], cmap='coolwarm', s=14, alpha=0.6, edgecolors='none')
    cbar3 = fig.colorbar(p3, ax=ax, pad=0.1, shrink=0.7)
    cbar3.set_label(r'별 생성률 $\log(\mathrm{SFR})$', fontsize=12)
    ax.set_xlabel('적색편이 z (거리)', fontsize=11, labelpad=10)
    ax.set_ylabel(r'항성 질량 $\log(M_*/M_\odot)$', fontsize=11, labelpad=10)
    ax.set_zlabel(r'$\mathrm{H}\alpha$ 광도 $\log(L_{\mathrm{H}\alpha})$', fontsize=11, labelpad=10)
    ax.set_title(r'3차원 관측 산점도: 거리(z) - 항성질량 - $\mathrm{H}\alpha$ 광도 (선 없음)', fontsize=14, pad=15)
    ax.view_init(elev=25, azim=-50)
    save_scatter(fig, "산점도15_3차원_거리_항성질량_Ha광도_순수산점도.png")

    # -------------------------------------------------------------
    # 16. 4대 핵심 물리량 4분할 종합 순수 산점도 패널
    # -------------------------------------------------------------
    fig, axes = plt.subplots(2, 2, figsize=(16, 14))

    # Panel 1: 질량 vs 별생성률
    ax = axes[0, 0]
    for gtype, color in CLASS_COLORS.items():
        sub = sample_df[sample_df['galaxy_type'] == gtype]
        if len(sub) > 0: ax.scatter(sub['lgm_tot_p50'], sub['sfr_tot_p50'], s=8, alpha=0.4, color=color, edgecolors='none')
    ax.set_xlabel(r'항성 질량 $\log(M_* / M_\odot)$', fontsize=12)
    ax.set_ylabel(r'별 생성률 $\log(\mathrm{SFR})$', fontsize=12)
    ax.set_title('(A) 항성 질량 vs 별 생성률 산점도 (SFMS)', fontsize=13)
    ax.grid(True, linestyle=':', alpha=0.5)

    # Panel 2: Ha 광도 vs 별생성률
    ax = axes[0, 1]
    for gtype, color in CLASS_COLORS.items():
        sub = sample_df[sample_df['galaxy_type'] == gtype]
        if len(sub) > 0: ax.scatter(sub['log_ha_lum'], sub['sfr_tot_p50'], s=8, alpha=0.4, color=color, edgecolors='none')
    ax.set_xlabel(r'$\mathrm{H}\alpha$ 광도 $\log(L_{\mathrm{H}\alpha}\,[\mathrm{erg/s}])$', fontsize=12)
    ax.set_ylabel(r'별 생성률 $\log(\mathrm{SFR})$', fontsize=12)
    ax.set_title(r'(B) $\mathrm{H}\alpha$ 스펙트럼 광도 vs 별 생성률 산점도', fontsize=13)
    ax.grid(True, linestyle=':', alpha=0.5)

    # Panel 3: 거리 vs 질량
    ax = axes[1, 0]
    for gtype, color in CLASS_COLORS.items():
        sub = sample_df[sample_df['galaxy_type'] == gtype]
        if len(sub) > 0: ax.scatter(sub['z'], sub['lgm_tot_p50'], s=8, alpha=0.4, color=color, edgecolors='none')
    ax.set_xlabel('거리 (적색편이 z)', fontsize=12)
    ax.set_ylabel(r'항성 질량 $\log(M_* / M_\odot)$', fontsize=12)
    ax.set_title('(C) 거리(적색편이 z) vs 항성 질량 산점도', fontsize=13)
    ax.grid(True, linestyle=':', alpha=0.5)

    # Panel 4: 거리 vs 별생성률
    ax = axes[1, 1]
    for gtype, color in CLASS_COLORS.items():
        sub = sample_df[sample_df['galaxy_type'] == gtype]
        if len(sub) > 0: ax.scatter(sub['z'], sub['sfr_tot_p50'], s=8, alpha=0.4, color=color, 
                                     label=gtype.split(" (")[0], edgecolors='none')
    ax.set_xlabel('거리 (적색편이 z)', fontsize=12)
    ax.set_ylabel(r'별 생성률 $\log(\mathrm{SFR})$', fontsize=12)
    ax.set_title('(D) 거리(적색편이 z) vs 별 생성률 산점도', fontsize=13)
    ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", markerscale=2.5, fontsize=10)
    ax.grid(True, linestyle=':', alpha=0.5)

    plt.suptitle('SDSS DR18 4대 핵심 물리량(스펙트럼 Ha, 질량, 거리, 별생성률) 순수 산점도 패널 (선 없음)', fontsize=17, y=1.01)
    save_scatter(fig, "산점도16_4대_핵심물리량_순수산점도_4분할종합패널.png")

    # -------------------------------------------------------------
    # 안내서 작성
    # -------------------------------------------------------------
    readme_text = """================================================================================
YSC 은하 관측 4대 핵심 물리량 순수 산점도(No Lines) 패키지 안내서
학교명: 전남과학고등학교 | 연구 동아리: AGN (Active Galactic Nuclei)
================================================================================

본 패키지는 사용자 지정 4대 핵심 물리량:
  1. 스펙트럼 분석 (Ha 영역: 플럭스, 광도, [NII]/Ha 선비)
  2. 질량 (항성 질량 log(M*))
  3. 거리 / 적색편이 (적색편이 z, 광도거리 D_L [Mpc])
  4. 별 생성률 (별 생성률 log(SFR), 비별생성률 log(sSFR))

만을 축으로 사용하여, 일체의 회귀선, 경계선, 기준선(Line)을 배제하고
오직 실제 SDSS 관측 데이터의 점(Scatter Dots)으로만 구성한 300 DPI 순수 산점도 16종 모음입니다.
* 은하 진화 지수(GEI) 축은 전면 배제되었습니다.

[수록된 순수 산점도 파일 목록 (총 16종, 300 DPI PNG)]
01. 산점도01_스펙트럼_Ha광도_vs_별생성률.png        : Ha 광도 vs SFR (Kennicutt 1998 실측 상관성)
02. 산점도02_스펙트럼_Ha플럭스_vs_별생성률.png      : Ha 관측 플럭스 vs SFR
03. 산점도03_항성질량_vs_별생성률_SFMS.png         : 항성 질량 vs 별생성률 (은하 주계열)
04. 산점도04_항성질량_vs_비별생성률_sSFR.png        : 항성 질량 vs 비별생성률 (Ha 광도 컬러맵)
05. 산점도05_항성질량_vs_스펙트럼_Ha광도.png        : 항성 질량 vs Ha 광도
06. 산점도06_항성질량_vs_스펙트럼_Ha플럭스.png      : 항성 질량 vs Ha 플럭스
07. 산점도07_스펙트럼_NII_Ha선비_vs_항성질량.png    : 항성 질량 vs [NII]/Ha 방출선비
08. 산점도08_거리_적색편이_vs_항성질량.png          : 거리(z) vs 항성 질량 (SFR 컬러맵)
09. 산점도09_거리_적색편이_vs_별생성률.png          : 거리(z) vs 별생성률 (질량 컬러맵)
10. 산점도10_거리_적색편이_vs_스펙트럼_Ha플럭스.png : 거리(z) vs Ha 플럭스 (거리제곱 감쇄 효과)
11. 산점도11_거리_적색편이_vs_스펙트럼_Ha광도.png   : 거리(z) vs Ha 광도 (SFR 컬러맵)
12. 산점도12_광도거리_vs_항성질량.png               : 광도거리 D_L (Mpc) vs 항성 질량
13. 산점도13_3차원_항성질량_별생성률_Ha광도_순수산점도.png : 3D 점 산점도 (질량-SFR-Ha광도)
14. 산점도14_3차원_거리_항성질량_별생성률_순수산점도.png : 3D 점 산점도 (거리-질량-SFR)
15. 산점도15_3차원_거리_항성질량_Ha광도_순수산점도.png   : 3D 점 산점도 (거리-질량-Ha광도)
16. 산점도16_4대_핵심물리량_순수산점도_4분할종합패널.png : 4대 핵심 물리량 4분할 종합 패널
================================================================================
"""
    with open(os.path.join(target_dir, "README_4대물리량_순수산점도_명세서.txt"), "w", encoding='utf-8') as f:
        f.write(readme_text)

    # 4. ZIP 압축 파일 생성
    print("\n[4/4] 단일 ZIP 아카이브 압축 중...")
    zip_dest = os.path.join(downloads_dir, pkg_name)
    shutil.make_archive(zip_dest, 'zip', target_dir)
    final_zip = zip_dest + ".zip"
    print("=" * 80)
    print(f"🎉 4대 핵심 물리량 순수 산점도 16종 생성 및 최종 ZIP 압축 완료!")
    print(f"• 최종 ZIP 파일 위치: {final_zip} ({os.path.getsize(final_zip)/(1024*1024):.2f} MB)")
    print(f"• 압축 해제 폴더: {target_dir}")
    print("=" * 80)

if __name__ == '__main__':
    main()
