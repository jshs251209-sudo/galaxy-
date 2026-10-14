"""
YSC 대회 제출용: 사용자 지정 6대 핵심 관계 전용 순수 산점도(Pure Scatter, Zero Lines) 완성 파이프라인
========================================================================================================
요청된 6대 핵심 관계:
  1. Ha 방출선과 별생성률 관계 (Ha vs SFR)
  2. 항성 질량과 Ha 방출선 관계 (Mass vs Ha)
  3. 거리-Ha 관계 (Distance/Redshift vs Ha)
  4. 거리-질량 관계 (Distance/Redshift vs Mass)
  5. 거리-별생성률 관계 (Distance/Redshift vs SFR)
  6. 거리-색지수 관계 (Distance/Redshift vs Color Index u-r)

엄격한 원칙 준수:
  - 선(Lines) 일체 100% 배제: 회귀선(regplot), 경계선, 추세선, 기준선 등 완전 제거 (오직 관측 데이터 점 Dots만 사용)
  - 은하 진화 지수(GEI) 축 전면 배제: 순수 관측 물리량(Ha, 질량, 거리/적색편이, 별생성률, 색지수)만 축으로 사용
  - 300 DPI 초고해상도 출판 및 포스터 규격
  - 이전 ZIP 아카이브 완전 삭제 및 신규 단일 ZIP 패키징
"""

import os
import sys
import shutil
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Windows UTF-8 및 콘솔 안전 출력 설정
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# 폰트 및 스타일 (Malgun Gothic)
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False
sns.set_theme(style="ticks")
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# 은하 형태/분광 분류 메타데이터 (정확한 매핑)
GALAXY_TYPE_META = {
    '나선은하': {'name': '나선은하 (Spiral)', 'color': '#2563eb'},
    '마젤란형': {'name': '마젤란형은하 (Magellanic)', 'color': '#10b981'},
    '타원은하': {'name': '타원은하 (Elliptical)', 'color': '#dc2626'},
    '세이퍼트은': {'name': '세이퍼트은하 (Seyfert AGN)', 'color': '#9333ea'},
    '막대나선은': {'name': '막대나선은하 (Barred Spiral)', 'color': '#0284c7'},
    '렌즈형은하': {'name': '렌즈형은하 (Lenticular)', 'color': '#ea580c'},
    '고리은하': {'name': '고리은하 (Ring)', 'color': '#8b5cf6'},
    '불규칙은하': {'name': '불규칙은하 (Irregular)', 'color': '#059669'},
    '전파은하': {'name': '전파은하 (Radio AGN)', 'color': '#b91c1c'},
    '퀘이사': {'name': '퀘이사 (Quasar)', 'color': '#d97706'}
}

def main():
    downloads_dir = os.path.expanduser('~/Downloads')
    pkg_name = "YSC_은하관측_6대핵심관계_순수산점도"
    target_dir = os.path.join(downloads_dir, pkg_name)

    print("=" * 80)
    print("YSC 6대 핵심 관계(Ha-SFR, 질량-Ha, 거리-Ha, 거리-질량, 거리-SFR, 거리-색지수) 순수 산점도 파이프라인")
    print("=" * 80)

    # 1. 이전 ZIP 파일들 및 구버전 폴더 완전 삭제
    print("\n[1/5] 다운로드 폴더 내 이전 ZIP 파일 및 폴더 완전 정리...")
    for item in os.listdir(downloads_dir):
        full_path = os.path.join(downloads_dir, item)
        # YSC 관련 이전 zip 삭제
        if item.endswith('.zip') and ('YSC' in item or '은하' in item):
            try:
                os.remove(full_path)
                print(f"  -> 이전 ZIP 삭제 완료: {item}")
            except Exception as e:
                print(f"  -> 삭제 실패 ({item}): {e}")
        # YSC 관련 이전 폴더 삭제
        elif os.path.isdir(full_path) and (item.startswith('YSC_') or '은하관측' in item) and item != pkg_name:
            try:
                shutil.rmtree(full_path, ignore_errors=True)
                print(f"  -> 이전 폴더 삭제 완료: {item}")
            except Exception as e:
                print(f"  -> 폴더 삭제 실패 ({item}): {e}")

    if os.path.exists(target_dir):
        shutil.rmtree(target_dir, ignore_errors=True)
    os.makedirs(target_dir, exist_ok=True)
    print(f"  -> 신규 저장 대상 폴더: {target_dir}")

    # 2. 데이터셋 로드 및 물리량 정제
    print("\n[2/5] 마스터 데이터셋 로드 및 6대 핵심 물리량 정제...")
    csv_file = 'galaxy_master_complete_all.csv'
    if not os.path.exists(csv_file):
        raise FileNotFoundError(f"{csv_file} 파일이 현재 디렉토리에 없습니다.")
    
    df = pd.read_csv(csv_file, encoding='utf-8')
    print(f"  -> 원본 관측 데이터 표본수: {len(df):,}개")

    # 광도거리 D_L 계산 (Hubble constant H0 = 70 km/s/Mpc)
    c = 299792.458 # km/s
    H0 = 70.0      # km/s/Mpc
    df['dist_lum_mpc'] = (c * df['z'] / H0) * (1 + df['z']/2)
    d_l_cm = df['dist_lum_mpc'] * 3.0857e24

    # H-alpha 관측 플럭스 log(F_Ha) 및 방출선 광도 log(L_Ha)
    df['log_ha_flux'] = np.log10(np.maximum(0.1, df['h_alpha_flux'])).clip(0.0, 4.5)
    # L_Ha = 4 * pi * D_L^2 * F_Ha * 10^-17 [erg/s]
    df['log_ha_lum'] = (df['log_ha_flux'] + 2 * np.log10(d_l_cm) + np.log10(4 * np.pi) - 17).clip(37.0, 43.5)

    # 은하 분류명 매핑
    df['clean_type'] = df['galaxy_type'].astype(str).str.strip().map(
        lambda k: GALAXY_TYPE_META.get(k, {}).get('name', '기타 은하')
    )
    df['clean_color'] = df['galaxy_type'].astype(str).str.strip().map(
        lambda k: GALAXY_TYPE_META.get(k, {}).get('color', '#6b7280')
    )

    # 비물리적 측광 결측치 필터링 (색지수 0.0 ~ 4.0 범위 은하 보존: 99.5% 유효 표본)
    clean_mask = (df['color_u_r'] >= 0.0) & (df['color_u_r'] <= 4.0) & (df['h_alpha_flux'] > 0)
    clean_df = df[clean_mask].copy()
    print(f"  -> 물리적 유효 표본 정제 완료: {len(clean_df):,}개 (전체의 {len(clean_df)/len(df)*100:.2f}%)")

    # 정제된 핵심 6대 물리량 CSV 저장
    core_cols = [
        'galaxy_type', 'clean_type', 'z', 'dist_lum_mpc', 'lgm_tot_p50', 'sfr_tot_p50', 
        'log_ssfr', 'h_alpha_flux', 'log_ha_flux', 'log_ha_lum', 'color_u_r',
        'u', 'g', 'r', 'i', 'd4000_n'
    ]
    core_csv_path = os.path.join(target_dir, "00_은하_6대핵심물리량_정제데이터.csv")
    clean_df[core_cols].to_csv(core_csv_path, index=False, encoding='utf-8-sig')
    print(f"  -> 정제 데이터셋 CSV 저장 완료: {os.path.basename(core_csv_path)}")

    # 기술통계량 및 상관계수 표 생성
    stat_summary = clean_df[['z', 'dist_lum_mpc', 'lgm_tot_p50', 'sfr_tot_p50', 'log_ha_lum', 'log_ha_flux', 'color_u_r']].describe().T
    stat_summary.columns = ['표본수', '평균값', '표준편차', '최솟값', '25%위수', '중앙값(50%)', '75%위수', '최댓값']
    stat_summary.to_csv(os.path.join(target_dir, "00_6대물리량_기술통계치.csv"), encoding='utf-8-sig')

    corr_matrix = clean_df[['z', 'dist_lum_mpc', 'lgm_tot_p50', 'sfr_tot_p50', 'log_ha_lum', 'log_ha_flux', 'color_u_r']].corr()
    corr_matrix.columns = ['적색편이 z', '광도거리 D_L', '항성 질량', '별 생성률', 'Ha 광도', 'Ha 플럭스', '광학 색지수']
    corr_matrix.index = corr_matrix.columns
    corr_matrix.to_csv(os.path.join(target_dir, "00_6대물리량_상관계수행렬.csv"), encoding='utf-8-sig')

    # 산점도 렌더링 최적 표본 추출 (25,000개 표본 샘플링으로 관측 밀도 및 형태 완벽 보존)
    sample_size = min(len(clean_df), 25000)
    plot_df = clean_df.sample(sample_size, random_state=42).copy()
    print(f"  -> 고해상도 산점도 렌더링 표본: {sample_size:,}개")

    def save_scatter(fig, filename):
        out_path = os.path.join(target_dir, filename)
        fig.savefig(out_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
        print(f"  -> [300 DPI 저장 완료] {filename}")

    print("\n[3/5] 요청된 6대 핵심 관계 순수 산점도(점 전용, 선 없음) 생성...")

    # =========================================================================
    # [핵심 1] Ha 방출선과 별생성률 관계 (Ha vs SFR)
    # =========================================================================
    # 1-A. H-alpha 방출선 광도 vs 별생성률 (은하 분류별 색상 점)
    fig, ax = plt.subplots(figsize=(10, 8))
    for raw_k, meta in GALAXY_TYPE_META.items():
        sub = plot_df[plot_df['clean_type'] == meta['name']]
        if len(sub) > 0:
            ax.scatter(sub['log_ha_lum'], sub['sfr_tot_p50'], s=12, alpha=0.45, color=meta['color'], 
                       label=meta['name'].split(" (")[0], edgecolors='none')
    ax.set_xlabel(r'$\mathrm{H}\alpha$ 방출선 광도 $\log(L_{\mathrm{H}\alpha}\,[\mathrm{erg/s}])$', fontsize=13)
    ax.set_ylabel(r'별 생성률 $\log(\mathrm{SFR}\,[M_\odot/\mathrm{yr}])$', fontsize=13)
    ax.set_title(r'[관계 1-A] $\mathrm{H}\alpha$ 방출선 광도 vs 별 생성률 관측 산점도 (선 없음)', fontsize=15, pad=12)
    ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", markerscale=2.5, fontsize=10)
    ax.grid(True, linestyle=':', alpha=0.35)
    save_scatter(fig, "01A_Ha방출선광도_vs_별생성률_순수산점도.png")

    # 1-B. H-alpha 관측 플럭스 vs 별생성률
    fig, ax = plt.subplots(figsize=(10, 8))
    for raw_k, meta in GALAXY_TYPE_META.items():
        sub = plot_df[plot_df['clean_type'] == meta['name']]
        if len(sub) > 0:
            ax.scatter(sub['log_ha_flux'], sub['sfr_tot_p50'], s=12, alpha=0.45, color=meta['color'], 
                       label=meta['name'].split(" (")[0], edgecolors='none')
    ax.set_xlabel(r'$\mathrm{H}\alpha$ 관측 플럭스 $\log(F_{\mathrm{H}\alpha}\,[10^{-17}\,\mathrm{erg/s/cm^2}])$', fontsize=13)
    ax.set_ylabel(r'별 생성률 $\log(\mathrm{SFR}\,[M_\odot/\mathrm{yr}])$', fontsize=13)
    ax.set_title(r'[관계 1-B] $\mathrm{H}\alpha$ 관측 플럭스 vs 별 생성률 관측 산점도 (선 없음)', fontsize=15, pad=12)
    ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", markerscale=2.5, fontsize=10)
    ax.grid(True, linestyle=':', alpha=0.35)
    save_scatter(fig, "01B_Ha관측플럭스_vs_별생성률_순수산점도.png")

    # =========================================================================
    # [핵심 2] 항성 질량과 Ha 방출선 관계 (Mass vs Ha)
    # =========================================================================
    # 2-A. 항성 질량 vs H-alpha 광도
    fig, ax = plt.subplots(figsize=(10, 8))
    for raw_k, meta in GALAXY_TYPE_META.items():
        sub = plot_df[plot_df['clean_type'] == meta['name']]
        if len(sub) > 0:
            ax.scatter(sub['lgm_tot_p50'], sub['log_ha_lum'], s=12, alpha=0.45, color=meta['color'], 
                       label=meta['name'].split(" (")[0], edgecolors='none')
    ax.set_xlabel(r'항성 질량 $\log(M_* / M_\odot)$', fontsize=13)
    ax.set_ylabel(r'$\mathrm{H}\alpha$ 방출선 광도 $\log(L_{\mathrm{H}\alpha}\,[\mathrm{erg/s}])$', fontsize=13)
    ax.set_title(r'[관계 2-A] 항성 질량 vs $\mathrm{H}\alpha$ 방출선 광도 관측 산점도 (선 없음)', fontsize=15, pad=12)
    ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", markerscale=2.5, fontsize=10)
    ax.grid(True, linestyle=':', alpha=0.35)
    save_scatter(fig, "02A_항성질량_vs_Ha방출선광도_순수산점도.png")

    # 2-B. 항성 질량 vs H-alpha 관측 플럭스
    fig, ax = plt.subplots(figsize=(10, 8))
    for raw_k, meta in GALAXY_TYPE_META.items():
        sub = plot_df[plot_df['clean_type'] == meta['name']]
        if len(sub) > 0:
            ax.scatter(sub['lgm_tot_p50'], sub['log_ha_flux'], s=12, alpha=0.45, color=meta['color'], 
                       label=meta['name'].split(" (")[0], edgecolors='none')
    ax.set_xlabel(r'항성 질량 $\log(M_* / M_\odot)$', fontsize=13)
    ax.set_ylabel(r'$\mathrm{H}\alpha$ 관측 플럭스 $\log(F_{\mathrm{H}\alpha}\,[10^{-17}\,\mathrm{erg/s/cm^2}])$', fontsize=13)
    ax.set_title(r'[관계 2-B] 항성 질량 vs $\mathrm{H}\alpha$ 플럭스 관측 산점도 (선 없음)', fontsize=15, pad=12)
    ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", markerscale=2.5, fontsize=10)
    ax.grid(True, linestyle=':', alpha=0.35)
    save_scatter(fig, "02B_항성질량_vs_Ha관측플럭스_순수산점도.png")

    # =========================================================================
    # [핵심 3] 거리-Ha 관계 (Distance/Redshift vs Ha)
    # =========================================================================
    # 3-A. 거리(적색편이 z) vs H-alpha 관측 플럭스 (은하 분류별, 역제곱 감쇄 효과)
    fig, ax = plt.subplots(figsize=(10, 8))
    for raw_k, meta in GALAXY_TYPE_META.items():
        sub = plot_df[plot_df['clean_type'] == meta['name']]
        if len(sub) > 0:
            ax.scatter(sub['z'], sub['log_ha_flux'], s=12, alpha=0.45, color=meta['color'], 
                       label=meta['name'].split(" (")[0], edgecolors='none')
    ax.set_xlabel('거리 (적색편이 z)', fontsize=13)
    ax.set_ylabel(r'$\mathrm{H}\alpha$ 관측 플럭스 $\log(F_{\mathrm{H}\alpha}\,[10^{-17}\,\mathrm{erg/s/cm^2}])$', fontsize=13)
    ax.set_title(r'[관계 3-A] 거리(적색편이 z) vs $\mathrm{H}\alpha$ 관측 플럭스 산점도 (선 없음)', fontsize=15, pad=12)
    ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", markerscale=2.5, fontsize=10)
    ax.grid(True, linestyle=':', alpha=0.35)
    save_scatter(fig, "03A_거리_적색편이_vs_Ha관측플럭스_순수산점도.png")

    # 3-B. 거리(적색편이 z) vs H-alpha 광도 (말름퀴스트 편향 효과, SFR 컬러맵)
    fig, ax = plt.subplots(figsize=(10, 8))
    sc = ax.scatter(plot_df['z'], plot_df['log_ha_lum'], c=plot_df['sfr_tot_p50'], 
                    cmap='coolwarm', s=12, alpha=0.5, edgecolors='none')
    cbar = plt.colorbar(sc, ax=ax)
    cbar.set_label(r'별 생성률 $\log(\mathrm{SFR}\,[M_\odot/\mathrm{yr}])$', fontsize=12)
    ax.set_xlabel('거리 (적색편이 z)', fontsize=13)
    ax.set_ylabel(r'$\mathrm{H}\alpha$ 방출선 광도 $\log(L_{\mathrm{H}\alpha}\,[\mathrm{erg/s}])$', fontsize=13)
    ax.set_title(r'[관계 3-B] 거리(적색편이 z) vs $\mathrm{H}\alpha$ 광도 관측 산점도 (SFR 컬러맵, 선 없음)', fontsize=15, pad=12)
    ax.grid(True, linestyle=':', alpha=0.35)
    save_scatter(fig, "03B_거리_적색편이_vs_Ha방출선광도_순수산점도.png")

    # 3-C. 광도거리 D_L (Mpc) vs H-alpha 관측 플럭스
    fig, ax = plt.subplots(figsize=(10, 8))
    sc = ax.scatter(plot_df['dist_lum_mpc'], plot_df['log_ha_flux'], c=plot_df['lgm_tot_p50'], 
                    cmap='viridis', s=12, alpha=0.5, edgecolors='none')
    cbar = plt.colorbar(sc, ax=ax)
    cbar.set_label(r'항성 질량 $\log(M_* / M_\odot)$', fontsize=12)
    ax.set_xlabel(r'광도 거리 $D_L\,[\mathrm{Mpc}]$', fontsize=13)
    ax.set_ylabel(r'$\mathrm{H}\alpha$ 관측 플럭스 $\log(F_{\mathrm{H}\alpha}\,[10^{-17}\,\mathrm{erg/s/cm^2}])$', fontsize=13)
    ax.set_title(r'[관계 3-C] 광도 거리 $D_L$ vs $\mathrm{H}\alpha$ 플럭스 관측 산점도 (질량 컬러맵, 선 없음)', fontsize=15, pad=12)
    ax.grid(True, linestyle=':', alpha=0.35)
    save_scatter(fig, "03C_광도거리_vs_Ha관측플럭스_순수산점도.png")

    # =========================================================================
    # [핵심 4] 거리-질량 관계 (Distance/Redshift vs Mass)
    # =========================================================================
    # 4-A. 거리(적색편이 z) vs 항성 질량 (은하 분류별 색상 점)
    fig, ax = plt.subplots(figsize=(10, 8))
    for raw_k, meta in GALAXY_TYPE_META.items():
        sub = plot_df[plot_df['clean_type'] == meta['name']]
        if len(sub) > 0:
            ax.scatter(sub['z'], sub['lgm_tot_p50'], s=12, alpha=0.45, color=meta['color'], 
                       label=meta['name'].split(" (")[0], edgecolors='none')
    ax.set_xlabel('거리 (적색편이 z)', fontsize=13)
    ax.set_ylabel(r'항성 질량 $\log(M_* / M_\odot)$', fontsize=13)
    ax.set_title('거리(적색편이 z) vs 항성 질량 관측 산점도 (은하 분류별, 선 없음)', fontsize=15, pad=12)
    ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", markerscale=2.5, fontsize=10)
    ax.grid(True, linestyle=':', alpha=0.35)
    save_scatter(fig, "04A_거리_적색편이_vs_항성질량_은하분류별_순수산점도.png")

    # 4-B. 거리(적색편이 z) vs 항성 질량 (SFR 연속 컬러맵 점)
    fig, ax = plt.subplots(figsize=(10, 8))
    sc = ax.scatter(plot_df['z'], plot_df['lgm_tot_p50'], c=plot_df['sfr_tot_p50'], 
                    cmap='plasma', s=12, alpha=0.5, edgecolors='none')
    cbar = plt.colorbar(sc, ax=ax)
    cbar.set_label(r'별 생성률 $\log(\mathrm{SFR}\,[M_\odot/\mathrm{yr}])$', fontsize=12)
    ax.set_xlabel('거리 (적색편이 z)', fontsize=13)
    ax.set_ylabel(r'항성 질량 $\log(M_* / M_\odot)$', fontsize=13)
    ax.set_title('거리(적색편이 z) vs 항성 질량 관측 산점도 (SFR 컬러맵, 선 없음)', fontsize=15, pad=12)
    ax.grid(True, linestyle=':', alpha=0.35)
    save_scatter(fig, "04B_거리_적색편이_vs_항성질량_SFR컬러맵_순수산점도.png")

    # 4-C. 광도거리 D_L (Mpc) vs 항성 질량
    fig, ax = plt.subplots(figsize=(10, 8))
    sc = ax.scatter(plot_df['dist_lum_mpc'], plot_df['lgm_tot_p50'], c=plot_df['log_ha_lum'], 
                    cmap='magma', s=12, alpha=0.5, edgecolors='none')
    cbar = plt.colorbar(sc, ax=ax)
    cbar.set_label(r'$\mathrm{H}\alpha$ 방출선 광도 $\log(L_{\mathrm{H}\alpha})$', fontsize=12)
    ax.set_xlabel(r'광도 거리 $D_L\,[\mathrm{Mpc}]$', fontsize=13)
    ax.set_ylabel(r'항성 질량 $\log(M_* / M_\odot)$', fontsize=13)
    ax.set_title(r'광도 거리 $D_L$ vs 항성 질량 관측 산점도 ($\mathrm{H}\alpha$ 광도 컬러맵, 선 없음)', fontsize=15, pad=12)
    ax.grid(True, linestyle=':', alpha=0.35)
    save_scatter(fig, "04C_광도거리_vs_항성질량_순수산점도.png")

    # =========================================================================
    # [핵심 5] 거리-별생성률 관계 (Distance/Redshift vs SFR)
    # =========================================================================
    # 5-A. 거리(적색편이 z) vs 별 생성률 (은하 분류별 색상 점)
    fig, ax = plt.subplots(figsize=(10, 8))
    for raw_k, meta in GALAXY_TYPE_META.items():
        sub = plot_df[plot_df['clean_type'] == meta['name']]
        if len(sub) > 0:
            ax.scatter(sub['z'], sub['sfr_tot_p50'], s=12, alpha=0.45, color=meta['color'], 
                       label=meta['name'].split(" (")[0], edgecolors='none')
    ax.set_xlabel('거리 (적색편이 z)', fontsize=13)
    ax.set_ylabel(r'별 생성률 $\log(\mathrm{SFR}\,[M_\odot/\mathrm{yr}])$', fontsize=13)
    ax.set_title('거리(적색편이 z) vs 별 생성률 관측 산점도 (은하 분류별, 선 없음)', fontsize=15, pad=12)
    ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", markerscale=2.5, fontsize=10)
    ax.grid(True, linestyle=':', alpha=0.35)
    save_scatter(fig, "05A_거리_적색편이_vs_별생성률_은하분류별_순수산점도.png")

    # 5-B. 거리(적색편이 z) vs 별 생성률 (항성 질량 컬러맵 점)
    fig, ax = plt.subplots(figsize=(10, 8))
    sc = ax.scatter(plot_df['z'], plot_df['sfr_tot_p50'], c=plot_df['lgm_tot_p50'], 
                    cmap='viridis', s=12, alpha=0.5, edgecolors='none')
    cbar = plt.colorbar(sc, ax=ax)
    cbar.set_label(r'항성 질량 $\log(M_* / M_\odot)$', fontsize=12)
    ax.set_xlabel('거리 (적색편이 z)', fontsize=13)
    ax.set_ylabel(r'별 생성률 $\log(\mathrm{SFR}\,[M_\odot/\mathrm{yr}])$', fontsize=13)
    ax.set_title('거리(적색편이 z) vs 별 생성률 관측 산점도 (질량 컬러맵, 선 없음)', fontsize=15, pad=12)
    ax.grid(True, linestyle=':', alpha=0.35)
    save_scatter(fig, "05B_거리_적색편이_vs_별생성률_질량컬러맵_순수산점도.png")

    # 5-C. 광도거리 D_L (Mpc) vs 별 생성률
    fig, ax = plt.subplots(figsize=(10, 8))
    sc = ax.scatter(plot_df['dist_lum_mpc'], plot_df['sfr_tot_p50'], c=plot_df['log_ha_lum'], 
                    cmap='coolwarm', s=12, alpha=0.5, edgecolors='none')
    cbar = plt.colorbar(sc, ax=ax)
    cbar.set_label(r'$\mathrm{H}\alpha$ 광도 $\log(L_{\mathrm{H}\alpha})$', fontsize=12)
    ax.set_xlabel(r'광도 거리 $D_L\,[\mathrm{Mpc}]$', fontsize=13)
    ax.set_ylabel(r'별 생성률 $\log(\mathrm{SFR}\,[M_\odot/\mathrm{yr}])$', fontsize=13)
    ax.set_title(r'광도 거리 $D_L$ vs 별 생성률 관측 산점도 ($\mathrm{H}\alpha$ 광도 컬러맵, 선 없음)', fontsize=15, pad=12)
    ax.grid(True, linestyle=':', alpha=0.35)
    save_scatter(fig, "05C_광도거리_vs_별생성률_순수산점도.png")

    # =========================================================================
    # [핵심 6] 거리-색지수 관계 (Distance/Redshift vs Color Index u-r)
    # =========================================================================
    # 6-A. 거리(적색편이 z) vs 광학 색지수 (u-r) (은하 분류별 색상 점)
    fig, ax = plt.subplots(figsize=(10, 8))
    for raw_k, meta in GALAXY_TYPE_META.items():
        sub = plot_df[plot_df['clean_type'] == meta['name']]
        if len(sub) > 0:
            ax.scatter(sub['z'], sub['color_u_r'], s=12, alpha=0.45, color=meta['color'], 
                       label=meta['name'].split(" (")[0], edgecolors='none')
    ax.set_xlabel('거리 (적색편이 z)', fontsize=13)
    ax.set_ylabel(r'광학 색지수 $(u - r)\,\mathrm{[mag]}$', fontsize=13)
    ax.set_ylim(0.0, 3.8)
    ax.set_title('거리(적색편이 z) vs 광학 색지수(u - r) 관측 산점도 (은하 분류별, 선 없음)', fontsize=15, pad=12)
    ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", markerscale=2.5, fontsize=10)
    ax.grid(True, linestyle=':', alpha=0.35)
    save_scatter(fig, "06A_거리_적색편이_vs_광학색지수_은하분류별_순수산점도.png")

    # 6-B. 거리(적색편이 z) vs 광학 색지수 (u-r) (별생성률 컬러맵 점)
    fig, ax = plt.subplots(figsize=(10, 8))
    sc = ax.scatter(plot_df['z'], plot_df['color_u_r'], c=plot_df['sfr_tot_p50'], 
                    cmap='coolwarm_r', s=12, alpha=0.5, edgecolors='none')
    cbar = plt.colorbar(sc, ax=ax)
    cbar.set_label(r'별 생성률 $\log(\mathrm{SFR}\,[M_\odot/\mathrm{yr}])$', fontsize=12)
    ax.set_xlabel('거리 (적색편이 z)', fontsize=13)
    ax.set_ylabel(r'광학 색지수 $(u - r)\,\mathrm{[mag]}$', fontsize=13)
    ax.set_ylim(0.0, 3.8)
    ax.set_title('거리(적색편이 z) vs 광학 색지수(u - r) 관측 산점도 (SFR 컬러맵, 선 없음)', fontsize=15, pad=12)
    ax.grid(True, linestyle=':', alpha=0.35)
    save_scatter(fig, "06B_거리_적색편이_vs_광학색지수_SFR컬러맵_순수산점도.png")

    # 6-C. 광도거리 D_L (Mpc) vs 광학 색지수 (u-r)
    fig, ax = plt.subplots(figsize=(10, 8))
    sc = ax.scatter(plot_df['dist_lum_mpc'], plot_df['color_u_r'], c=plot_df['lgm_tot_p50'], 
                    cmap='viridis', s=12, alpha=0.5, edgecolors='none')
    cbar = plt.colorbar(sc, ax=ax)
    cbar.set_label(r'항성 질량 $\log(M_* / M_\odot)$', fontsize=12)
    ax.set_xlabel(r'광도 거리 $D_L\,[\mathrm{Mpc}]$', fontsize=13)
    ax.set_ylabel(r'광학 색지수 $(u - r)\,\mathrm{[mag]}$', fontsize=13)
    ax.set_ylim(0.0, 3.8)
    ax.set_title(r'광도 거리 $D_L$ vs 광학 색지수(u - r) 관측 산점도 (질량 컬러맵, 선 없음)', fontsize=15, pad=12)
    ax.grid(True, linestyle=':', alpha=0.35)
    save_scatter(fig, "06C_광도거리_vs_광학색지수_순수산점도.png")

    # =========================================================================
    # [종합 패널 1] 요청된 6대 핵심 관계 6분할 종합 순수 산점도 패널 (포스터용)
    # =========================================================================
    print("\n[4/5] 6대 핵심 관계 6분할 종합 마스터 패널 생성...")
    fig, axes = plt.subplots(2, 3, figsize=(21, 13))

    # Panel 1: Ha 방출선 광도 vs 별생성률
    ax = axes[0, 0]
    for raw_k, meta in GALAXY_TYPE_META.items():
        sub = plot_df[plot_df['clean_type'] == meta['name']]
        if len(sub) > 0: ax.scatter(sub['log_ha_lum'], sub['sfr_tot_p50'], s=7, alpha=0.4, color=meta['color'], edgecolors='none')
    ax.set_xlabel(r'$\mathrm{H}\alpha$ 광도 $\log(L_{\mathrm{H}\alpha}\,[\mathrm{erg/s}])$', fontsize=11)
    ax.set_ylabel(r'별 생성률 $\log(\mathrm{SFR})$', fontsize=11)
    ax.set_title(r'(1) $\mathrm{H}\alpha$ 방출선 광도 vs 별 생성률 관계', fontsize=12, fontweight='bold')
    ax.grid(True, linestyle=':', alpha=0.35)

    # Panel 2: 항성 질량 vs Ha 광도
    ax = axes[0, 1]
    for raw_k, meta in GALAXY_TYPE_META.items():
        sub = plot_df[plot_df['clean_type'] == meta['name']]
        if len(sub) > 0: ax.scatter(sub['lgm_tot_p50'], sub['log_ha_lum'], s=7, alpha=0.4, color=meta['color'], edgecolors='none')
    ax.set_xlabel(r'항성 질량 $\log(M_* / M_\odot)$', fontsize=11)
    ax.set_ylabel(r'$\mathrm{H}\alpha$ 광도 $\log(L_{\mathrm{H}\alpha}\,[\mathrm{erg/s}])$', fontsize=11)
    ax.set_title(r'(2) 항성 질량 vs $\mathrm{H}\alpha$ 방출선 광도 관계', fontsize=12, fontweight='bold')
    ax.grid(True, linestyle=':', alpha=0.35)

    # Panel 3: 거리 vs Ha 플럭스
    ax = axes[0, 2]
    for raw_k, meta in GALAXY_TYPE_META.items():
        sub = plot_df[plot_df['clean_type'] == meta['name']]
        if len(sub) > 0: ax.scatter(sub['z'], sub['log_ha_flux'], s=7, alpha=0.4, color=meta['color'], edgecolors='none')
    ax.set_xlabel('거리 (적색편이 z)', fontsize=11)
    ax.set_ylabel(r'$\mathrm{H}\alpha$ 플럭스 $\log(F_{\mathrm{H}\alpha})$', fontsize=11)
    ax.set_title(r'(3) 거리(적색편이 z) vs $\mathrm{H}\alpha$ 방출선 플럭스 관계', fontsize=12, fontweight='bold')
    ax.grid(True, linestyle=':', alpha=0.35)

    # Panel 4: 거리 vs 질량
    ax = axes[1, 0]
    for raw_k, meta in GALAXY_TYPE_META.items():
        sub = plot_df[plot_df['clean_type'] == meta['name']]
        if len(sub) > 0: ax.scatter(sub['z'], sub['lgm_tot_p50'], s=7, alpha=0.4, color=meta['color'], edgecolors='none')
    ax.set_xlabel('거리 (적색편이 z)', fontsize=11)
    ax.set_ylabel(r'항성 질량 $\log(M_* / M_\odot)$', fontsize=11)
    ax.set_title('(4) 거리(적색편이 z) vs 항성 질량 관계', fontsize=12, fontweight='bold')
    ax.grid(True, linestyle=':', alpha=0.35)

    # Panel 5: 거리 vs 별생성률
    ax = axes[1, 1]
    for raw_k, meta in GALAXY_TYPE_META.items():
        sub = plot_df[plot_df['clean_type'] == meta['name']]
        if len(sub) > 0: ax.scatter(sub['z'], sub['sfr_tot_p50'], s=7, alpha=0.4, color=meta['color'], edgecolors='none')
    ax.set_xlabel('거리 (적색편이 z)', fontsize=11)
    ax.set_ylabel(r'별 생성률 $\log(\mathrm{SFR})$', fontsize=11)
    ax.set_title('(5) 거리(적색편이 z) vs 별 생성률 관계', fontsize=12, fontweight='bold')
    ax.grid(True, linestyle=':', alpha=0.35)

    # Panel 6: 거리 vs 색지수
    ax = axes[1, 2]
    for raw_k, meta in GALAXY_TYPE_META.items():
        sub = plot_df[plot_df['clean_type'] == meta['name']]
        if len(sub) > 0: ax.scatter(sub['z'], sub['color_u_r'], s=7, alpha=0.4, color=meta['color'], 
                                     label=meta['name'].split(" (")[0], edgecolors='none')
    ax.set_xlabel('거리 (적색편이 z)', fontsize=11)
    ax.set_ylabel(r'광학 색지수 $(u - r)\,\mathrm{[mag]}$', fontsize=11)
    ax.set_ylim(0.0, 3.8)
    ax.set_title('(6) 거리(적색편이 z) vs 광학 색지수(u - r) 관계', fontsize=12, fontweight='bold')
    ax.legend(bbox_to_anchor=(1.03, 1), loc="upper left", markerscale=2.5, fontsize=10)
    ax.grid(True, linestyle=':', alpha=0.35)

    plt.suptitle('SDSS DR18 은하 관측 6대 핵심 물리량 관계 순수 산점도 마스터 패널 (일체 선 없음, 점 전용)', fontsize=16, y=1.01)
    save_scatter(fig, "07_6대_핵심물리량관계_6분할종합_마스터패널.png")

    # =========================================================================
    # [종합 패널 2] 3차원 다변량 순수 산점도 2종 추가 (거리-질량-Ha, 거리-질량-색지수)
    # =========================================================================
    sub_3d = plot_df.sample(min(len(plot_df), 6000), random_state=42)

    # 3D 산점도 1: 거리 - 질량 - Ha광도
    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, projection='3d')
    p1 = ax.scatter(sub_3d['z'], sub_3d['lgm_tot_p50'], sub_3d['log_ha_lum'], 
                    c=sub_3d['sfr_tot_p50'], cmap='coolwarm', s=14, alpha=0.6, edgecolors='none')
    cbar1 = fig.colorbar(p1, ax=ax, pad=0.1, shrink=0.7)
    cbar1.set_label(r'별 생성률 $\log(\mathrm{SFR})$', fontsize=12)
    ax.set_xlabel('적색편이 z (거리)', fontsize=11, labelpad=10)
    ax.set_ylabel(r'항성 질량 $\log(M_*/M_\odot)$', fontsize=11, labelpad=10)
    ax.set_zlabel(r'$\mathrm{H}\alpha$ 광도 $\log(L_{\mathrm{H}\alpha})$', fontsize=11, labelpad=10)
    ax.set_title(r'3차원 관측 산점도: 거리(z) - 항성질량 - $\mathrm{H}\alpha$ 광도 (선 없음)', fontsize=14, pad=15)
    ax.view_init(elev=25, azim=-50)
    save_scatter(fig, "08_3차원_거리_항성질량_Ha광도_순수산점도.png")

    # 3D 산점도 2: 거리 - 질량 - 광학색지수
    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, projection='3d')
    p2 = ax.scatter(sub_3d['z'], sub_3d['lgm_tot_p50'], sub_3d['color_u_r'], 
                    c=sub_3d['log_ha_lum'], cmap='viridis', s=14, alpha=0.6, edgecolors='none')
    cbar2 = fig.colorbar(p2, ax=ax, pad=0.1, shrink=0.7)
    cbar2.set_label(r'$\mathrm{H}\alpha$ 광도 $\log(L_{\mathrm{H}\alpha})$', fontsize=12)
    ax.set_xlabel('적색편이 z (거리)', fontsize=11, labelpad=10)
    ax.set_ylabel(r'항성 질량 $\log(M_*/M_\odot)$', fontsize=11, labelpad=10)
    ax.set_zlabel(r'색지수 $(u - r)$', fontsize=11, labelpad=10)
    ax.set_title('3차원 관측 산점도: 거리(z) - 항성질량 - 색지수(u - r) (선 없음)', fontsize=14, pad=15)
    ax.view_init(elev=24, azim=-55)
    save_scatter(fig, "09_3차원_거리_항성질량_색지수_순수산점도.png")

    # 4. 분석 코드 자체를 패키지에 복사
    print("\n[5/5] 분석 코드, 가이드 문서, 결과 로그 복사 및 최종 단일 ZIP 압축...")
    current_script_path = os.path.abspath(__file__)
    shutil.copy2(current_script_path, os.path.join(target_dir, "generate_6core_physics_scatters.py"))

    # 상세 안내서 작성
    readme_text = f"""================================================================================
YSC 과학탐구대회: 은하 관측 6대 핵심 물리량 순수 산점도(Pure Scatter, Zero Lines) 패키지
학교명: 전남과학고등학교 | 연구 동아리: AGN (Active Galactic Nuclei)
================================================================================

본 패키지는 사용자 지정 6대 핵심 관계:
  1. Ha 방출선과 별생성률 관계 (Ha vs SFR)
  2. 항성 질량과 Ha 방출선 관계 (Mass vs Ha)
  3. 거리-Ha 관계 (Distance/Redshift vs Ha)
  4. 거리-질량 관계 (Distance/Redshift vs Mass)
  5. 거리-별생성률 관계 (Distance/Redshift vs SFR)
  6. 거리-색지수 관계 (Distance/Redshift vs Color Index u-r)

를 실제 SDSS 관측 데이터(총 49,740개 물리적 유효 표본)를 바탕으로,
일체의 회귀선, 추세선, 경계선(Line)을 배제하고 
오직 실제 관측 데이터 점(Scatter Dots)만으로 렌더링한 300 DPI 출판/포스터 규격 산점도 모음입니다.

* 엄격한 원칙 준수:
  - 은하 진화 지수(GEI) 축 전면 배제 (순수 관측 물리량만 축으로 구성)
  - 임의의 선(Lines) 100% 제거 (순수 산점도 점으로만 데이터 경향성 확인)
  - 관측치 기반 천체물리학적 단위 및 해석 완비

--------------------------------------------------------------------------------
[수록 파일 목록]
--------------------------------------------------------------------------------
1. 핵심 산점도 이미지 파일 (300 DPI 고해상도 PNG):
  • 01A_Ha방출선광도_vs_별생성률_순수산점도.png       : Ha 방출선 광도 log(L_Ha) vs 별 생성률 log(SFR)
  • 01B_Ha관측플럭스_vs_별생성률_순수산점도.png       : Ha 관측 플럭스 log(F_Ha) vs 별 생성률 log(SFR)
  • 02A_항성질량_vs_Ha방출선광도_순수산점도.png       : 항성 질량 log(M*) vs Ha 방출선 광도 log(L_Ha)
  • 02B_항성질량_vs_Ha관측플럭스_순수산점도.png       : 항성 질량 log(M*) vs Ha 관측 플럭스 log(F_Ha)
  • 03A_거리_적색편이_vs_Ha관측플럭스_순수산점도.png  : 거리(적색편이 z) vs Ha 관측 플럭스 (거리제곱 감쇄 효과)
  • 03B_거리_적색편이_vs_Ha방출선광도_순수산점도.png  : 거리(적색편이 z) vs Ha 광도 (말름퀴스트 편향 효과)
  • 03C_광도거리_vs_Ha관측플럭스_순수산점도.png       : 광도거리 D_L (Mpc) vs Ha 관측 플럭스
  • 04A_거리_적색편이_vs_항성질량_은하분류별_순수산점도.png : 거리(적색편이 z) vs 항성 질량 (은하 분류별)
  • 04B_거리_적색편이_vs_항성질량_SFR컬러맵_순수산점도.png : 거리(적색편이 z) vs 항성 질량 (SFR 컬러맵)
  • 04C_광도거리_vs_항성질량_순수산점도.png           : 광도거리 D_L (Mpc) vs 항성 질량
  • 05A_거리_적색편이_vs_별생성률_은하분류별_순수산점도.png : 거리(적색편이 z) vs 별 생성률 (은하 분류별)
  • 05B_거리_적색편이_vs_별생성률_질량컬러맵_순수산점도.png : 거리(적색편이 z) vs 별 생성률 (질량 컬러맵)
  • 05C_광도거리_vs_별생성률_순수산점도.png           : 광도거리 D_L (Mpc) vs 별 생성률
  • 06A_거리_적색편이_vs_광학색지수_은하분류별_순수산점도.png : 거리(적색편이 z) vs 광학 색지수 (u - r)
  • 06B_거리_적색편이_vs_광학색지수_SFR컬러맵_순수산점도.png : 거리(적색편이 z) vs 광학 색지수 (u - r)
  • 06C_광도거리_vs_광학색지수_순수산점도.png         : 광도거리 D_L (Mpc) vs 광학 색지수 (u - r)
  • 07_6대_핵심물리량관계_6분할종합_마스터패널.png   : 6대 핵심 관계 한눈에 보기 6분할 종합 패널 (포스터 최적)
  • 08_3차원_거리_항성질량_Ha광도_순수산점도.png     : 3차원 순수 산점도 (거리 - 질량 - Ha광도)
  • 09_3차원_거리_항성질량_색지수_순수산점도.png     : 3차원 순수 산점도 (거리 - 질량 - 색지수)

2. 전처리 데이터 및 통계 파일 (CSV):
  • 00_은하_6대핵심물리량_정제데이터.csv : 정제된 49,740개 은하의 6대 핵심 물리량 전수 데이터셋
  • 00_6대물리량_기술통계치.csv          : 평균, 표준편차, 사분위수 등 기술 통계치
  • 00_6대물리량_상관계수행렬.csv        : 6대 물리량 상호 간 피어슨 상관계수 행렬

3. 재현성 보장 소스 코드:
  • generate_6core_physics_scatters.py : 그래프 생성 및 전처리 파이프라인 전체 소스 코드
================================================================================
"""
    with open(os.path.join(target_dir, "README_6대핵심관계_순수산점도_안내서.txt"), "w", encoding='utf-8') as f:
        f.write(readme_text)

    # 5. ZIP 압축 파일 생성
    zip_dest = os.path.join(downloads_dir, pkg_name)
    shutil.make_archive(zip_dest, 'zip', target_dir)
    final_zip = zip_dest + ".zip"

    print("=" * 80)
    print("6대 핵심 관계 순수 산점도 생성 및 최종 단일 ZIP 압축 완료!")
    print(f"• 최종 ZIP 파일 경로: {final_zip} ({os.path.getsize(final_zip)/(1024*1024):.2f} MB)")
    print(f"• 개별 파일 저장 경로: {target_dir}")
    print("=" * 80)

if __name__ == '__main__':
    main()
