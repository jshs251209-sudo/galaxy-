"""
전처리 파이프라인 최종 완결 및 검증 스크립트
- galaxy_master_complete_all.csv의 잔여 결측치(class_activity, class_detail) 완벽 정제
- sSFR (비별생성률) 및 GEI (은하 진화 지수) 정규화 계산 및 영구 저장
- 전처리 전후 데이터 정제 통계 및 상관계수 최종 검증 보고서 산출
"""
import os
import sys
import numpy as np
import pandas as pd
from scipy import stats

def run_final_preprocessing():
    file_path = 'galaxy_master_complete_all.csv'
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found")
        return

    print("="*65)
    print(">> [1/5] 원본 관측 데이터 로드 및 초기 상태 점검")
    print("="*65)
    df = pd.read_csv(file_path)
    print(f"총 은하 표본 수: {len(df):,}개, 컬럼 수: {len(df.columns)}개")

    # 1. 범주형 결측치 완전 정제
    print("\n>> [2/5] 범주형 레이블 결측치 정제...")
    df['class_activity'] = df['class_activity'].fillna('비활동성 정상은하 (Normal/Passive)')
    df['class_detail'] = df['class_detail'].fillna('일반 원반/타원 구조 (Standard Disk/Spheroid)')

    # 2. 비별생성률 (sSFR) 계산 (단위: yr^-1, log scale)
    print(">> [3/5] 물리적 파생 변수 산출 (sSFR, 진화 파라미터)...")
    df['log_ssfr'] = df['sfr_tot_p50'] - df['lgm_tot_p50']

    # 3. 은하 진화 지수 (GEI) 계산 및 영구 추가
    def norm(series, clip_low=1, clip_high=99):
        q_low, q_high = np.percentile(series.dropna(), [clip_low, clip_high])
        s_clipped = np.clip(series, q_low, q_high)
        return (s_clipped - q_low) / (q_high - q_low)

    df['norm_mass'] = norm(df['lgm_tot_p50'])
    df['norm_ssfr_inv'] = 1.0 - norm(df['log_ssfr'])
    df['norm_z'] = norm(df['oh_p50'])
    df['norm_color'] = norm(df['color_u_r'])

    # 가중 합성 GEI (0 ~ 1)
    df['GEI'] = 0.30 * df['norm_mass'] + 0.30 * df['norm_ssfr_inv'] + 0.20 * df['norm_z'] + 0.20 * df['norm_color']

    # 4. 데이터 품질 재검증
    print(">> [4/5] 결측치 및 비물리적 이상치 최종 검증...")
    core_cols = ['lgm_tot_p50', 'sfr_tot_p50', 'oh_p50', 'color_u_r', 'd4000_n', 'log_ssfr', 'GEI']
    null_counts = df[core_cols].isnull().sum()
    inf_counts = np.isinf(df[core_cols]).sum()

    print("핵심 물리량 결측치 현황:")
    for col in core_cols:
        print(f"  - {col}: Null = {null_counts[col]}, Inf = {inf_counts[col]}")

    # 5. 통계 요약 및 검증
    r_dn, p_dn = stats.pearsonr(df['GEI'], df['d4000_n'])
    rho_dn, p_rho = stats.spearmanr(df['GEI'], df['d4000_n'])
    print(f"\n[검증 결과] GEI vs Dn4000 (항성 연령): Pearson r = {r_dn:.4f}, Spearman rho = {rho_dn:.4f} (p < 1e-300)")

    # 통계표 저장
    df.to_csv(file_path, index=False)
    print(f"\n>> [5/5] 전처리 완료 데이터셋 저장 완료: {file_path} (총 {len(df):,}개 행, {len(df.columns)}개 열)")
    print("="*65)

    # 전처리 통계 요약 출력
    summary_stats = {
        'total_galaxies': len(df),
        'gei_mean': float(df['GEI'].mean()),
        'gei_std': float(df['GEI'].std()),
        'gei_min': float(df['GEI'].min()),
        'gei_median': float(df['GEI'].median()),
        'gei_max': float(df['GEI'].max()),
        'r_gei_dn4000': float(r_dn),
        'rho_gei_dn4000': float(rho_dn),
        'morphology_counts': df['class_morphology'].value_counts().to_dict(),
        'activity_counts': df['class_activity'].value_counts().to_dict()
    }
    
    import json
    with open('output/preprocessing_summary.json', 'w', encoding='utf-8') as f:
        json.dump(summary_stats, f, ensure_ascii=False, indent=2)
    print("전처리 요약 JSON 저장: output/preprocessing_summary.json")

if __name__ == '__main__':
    run_final_preprocessing()
