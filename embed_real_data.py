"""
은하 대시보드 빌더
1. clean template (dashboard_template.html) 기반으로 안전하게 빌드 (syntax error 0%)
2. 3대 신규 분류 체계 및 암흑물질/회전곡선/광도/원소비 통계 생성
3. 10,000개 표본 데이터 임베딩
4. 55,000개 전체 마스터 파일(xlsx, json, zip, csv) 다운로드 센터 연결
"""
import os
import json
import pandas as pd
import numpy as np
import config

def build():
    print("[1/4] 마스터 데이터셋 로드 중...")
    df = pd.read_csv(config.MASTER_DATASET_FILE)
    total = len(df)
    print(f"  => 총 {total:,}개 은하 표본 로드 완료")

    # 핵심 물리량 딕셔너리 (35종)
    PARAM_DICT = {
        'log_luminosity_r': 'log_luminosity_r - r밴드 광도 log(L_r / L_sun)',
        'abs_mag_r': 'abs_mag_r - 거리를 보정한 은하의 r밴드 절대 등급 [mag]',
        'lgm_tot_p50': 'lgm_tot_p50 - 은하의 총 항성 질량 log(M* / M_sun)',
        'log_dyn_mass': 'log_dyn_mass - 회전속도와 반경으로 유도된 은하 동역학 총 질량 log(M_dyn / M_sun)',
        'v_rot': 'v_rot - 은하 회전곡선의 평탄 회전속도 [km/s]',
        'log_v_rot': 'log_v_rot - 은하 회전속도의 로그값 log(V_rot [km/s])',
        'velDisp': 'velDisp - 은하 중심부 별들의 무작위 운동 속도 분산 [km/s]',
        'log_dark_matter_mass': 'log_dark_matter_mass - 유도된 암흑물질 총 질량 log(M_DM / M_sun)',
        'dark_matter_fraction': 'dark_matter_fraction - 은하 전체 동역학 질량 대비 암흑물질 분율 f_DM (0~1)',
        'oh_p50': 'oh_p50 - 기체 산소 원소비 (산소 풍부도 12 + log(O/H))',
        'log_n_o': 'log_n_o - 질소-산소 원소비 log(N/O)',
        'log_oii_oiii': 'log_oii_oiii - 산소 원소 이온화 상태비 log([O II] / [O III])',
        'log_s_o': 'log_s_o - 황-산소 방출선 비율 log([S II] / [O III])',
        'log_nii_ha': 'log_nii_ha - BPT x축 비율 log([N II] 6584 / H-alpha)',
        'log_oiii_hb': 'log_oiii_hb - BPT y축 비율 log([O III] 5007 / H-beta)',
        'h_alpha_flux': 'h_alpha_flux - 젊은 별 생성 활동을 나타내는 수소 H-alpha (6563Å) 플럭스',
        'h_beta_flux': 'h_beta_flux - 성간 소광 및 별 생성 분석용 수소 H-beta (4861Å) 플럭스',
        'h_gamma_flux': 'h_gamma_flux - 발머 계열 수소 H-gamma (4340Å) 플럭스',
        'oiii_5007_flux': 'oiii_5007_flux - 고에너지 이온화 환경을 나타내는 산소 [O III] 5007Å 플럭스',
        'nii_6584_flux': 'nii_6584_flux - 가스 금속 함량을 지시하는 질소 [N II] 6584Å 플럭스',
        'sii_6717_flux': 'sii_6717_flux - 성간 가스 전자밀도를 추정하는 황 [S II] 6717Å 플럭스',
        'oii_3726_flux': 'oii_3726_flux - 은하 별 생성률을 대변하는 산소 [O II] 3726Å 플럭스',
        'u': 'u - 자외선 파장 대역 겉보기 등급 [mag]',
        'g': 'g - 녹색 파장 대역 겉보기 등급 [mag]',
        'r': 'r - 붉은색 파장 대역 겉보기 등급 [mag]',
        'i': 'i - 근적외선 파장 대역 겉보기 등급 [mag]',
        'color_u_r': 'color_u_r - 은하의 색 분포를 나타내는 (u - r) 색지수 [mag]',
        'petroRad_r': 'petroRad_r - r밴드 페트로시안 반지름 [arcsec]',
        'petroR50_r': 'petroR50_r - 은하 빛의 50%를 포함하는 유효 반광반경 [arcsec]',
        'petroR90_r': 'petroR90_r - 은하 빛의 90%를 포함하는 영역의 반지름 [arcsec]',
        'r_e_kpc': 'r_e_kpc - 물리적 유효 반경 [kpc]',
        'z': 'z - 스펙트럼 흡수/방출선으로 측정한 분광 적색편이',
        'phot_z': 'phot_z - 필터 밝기 비율로 추정한 측광 적색편이',
        'sfr_tot_p50': 'sfr_tot_p50 - 1년 동안 생성되는 별의 총 질량 log(SFR [M_sun/yr])',
        'd4000_n': 'd4000_n - 4000Å 불연속 감쇄폭 Dn(4000) (늙은 별 비율과 은하 나이)'
    }

    print(f"[2/4] 기술 통계 연산 중... ({len(PARAM_DICT)}개 물리량)")
    stats_rows = []
    median_z = "N/A"
    for col, desc in PARAM_DICT.items():
        if col in df.columns:
            s = pd.to_numeric(df[col], errors='coerce').dropna()
            if len(s) > 0:
                mean_val = round(float(s.mean()), 4)
                med_val = round(float(s.median()), 4)
                std_val = round(float(s.std()), 4)
                min_val = round(float(s.min()), 4)
                max_val = round(float(s.max()), 4)
                cnt_val = int(s.count())
                if col == 'z':
                    median_z = str(med_val)
                desc_text = desc.split(' - ', 1)[1] if ' - ' in desc else desc
                stats_rows.append(f"<tr><td><strong style='color:#ffff00'>{col}</strong></td><td><span style='color:#fff'>{desc_text}</span></td><td>{mean_val}</td><td>{med_val}</td><td>{std_val}</td><td>{min_val}</td><td>{max_val}</td><td>{cnt_val:,}</td></tr>")

    # 3대 분류 카드 HTML 생성
    morph_dist = df['class_morphology'].value_counts().to_dict()
    m_colors = {"타원은하": "#dc2626", "나선은하": "#2563eb", "렌즈형은하": "#ea580c", "불규칙은하": "#059669"}
    m_cards = []
    for gtype, cnt in morph_dist.items():
        pct = cnt / total * 100
        color = m_colors.get(gtype, "#fff")
        m_cards.append(f'<div class="glass stat-card"><div class="val" style="color:{color}">{cnt:,}</div><div class="lbl"><span class="type-badge" style="border-color:{color};color:{color}">{gtype}</span><br>{pct:.1f}%</div></div>')

    activity_dist = df['class_activity'].value_counts().to_dict()
    a_colors = {"전파은하": "#b91c1c", "세이퍼트 은하": "#9333ea", "퀘이사": "#d97706", "일반 은하": "#0284c7"}
    a_cards = []
    for gtype, cnt in activity_dist.items():
        pct = cnt / total * 100
        color = a_colors.get(gtype, "#fff")
        a_cards.append(f'<div class="glass stat-card"><div class="val" style="color:{color}">{cnt:,}</div><div class="lbl"><span class="type-badge" style="border-color:{color};color:{color}">{gtype}</span><br>{pct:.1f}%</div></div>')

    detail_dist = df['class_detail'].value_counts().to_dict()
    d_colors = {"마젤란형 은하": "#10b981", "나선은하": "#2563eb", "막대나선은하": "#0284c7", "고리은하": "#8b5cf6", "불규칙 은하": "#059669", "기타 은하": "#777"}
    d_cards = []
    for gtype, cnt in detail_dist.items():
        pct = cnt / total * 100
        color = d_colors.get(gtype, "#fff")
        d_cards.append(f'<div class="glass stat-card"><div class="val" style="color:{color}">{cnt:,}</div><div class="lbl"><span class="type-badge" style="border-color:{color};color:{color}">{gtype}</span><br>{pct:.1f}%</div></div>')

    print("[3/4] 10,000개 대표 표본 추출 및 JSON 직렬화...")
    sample_size = min(10000, total)
    sample = df.sample(n=sample_size, random_state=42)

    cat_cols = ['class_morphology', 'class_activity', 'class_detail', 'galaxy_type', 'bptclass']
    sample_cols = cat_cols + list(PARAM_DICT.keys())
    sample_cols = [c for c in sample_cols if c in sample.columns]
    sample_cols = list(dict.fromkeys(sample_cols))

    sample_df = sample[sample_cols].copy()
    for col in sample_df.select_dtypes(include=['float64', 'float32']).columns:
        sample_df[col] = sample_df[col].round(4)
    sample_json = json.loads(sample_df.to_json(orient='records'))

    CATS = {
        'class_morphology': '[기본 형태 4분류] 타원은하, 나선은하, 불규칙은하, 렌즈형은하',
        'class_activity': '[활동성 은하 3분류] 전파은하, 세이퍼트 은하, 퀘이사, 일반 은하',
        'class_detail': '[세부 구조 5분류] 마젤란형 은하, 나선은하, 막대나선은하, 고리은하, 불규칙 은하',
        'galaxy_type': '[11대 통합 분류] 전체 은하 분류 체계'
    }

    print("[4/4] 템플릿 로드 및 대시보드 HTML 조립...")
    template_path = os.path.join(config.PROJECT_ROOT, 'dashboard_template.html')
    with open(template_path, 'r', encoding='utf-8') as f:
        html = f.read()

    html = html.replace('__TOTAL_COUNT__', f"{total:,}")
    html = html.replace('__PARAM_COUNT__', str(len(PARAM_DICT)))
    html = html.replace('__MEDIAN_Z__', median_z)
    html = html.replace('__MORPH_CARDS__', "\n".join(m_cards))
    html = html.replace('__ACT_CARDS__', "\n".join(a_cards))
    html = html.replace('__DETAIL_CARDS__', "\n".join(d_cards))
    html = html.replace('__STATS_ROWS__', "\n".join(stats_rows))

    html = html.replace('__DATA__', json.dumps(sample_json, ensure_ascii=False))
    html = html.replace('__VARS__', json.dumps(PARAM_DICT, ensure_ascii=False))
    html = html.replace('__CATS__', json.dumps(CATS, ensure_ascii=False))

    output_path = os.path.join(config.PROJECT_ROOT, 'dashboard_real_data.html')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"\n=== 대시보드 빌드 성공! ===")
    print(f"파일: {output_path}")
    print(f"크기: {size_mb:.2f} MB")
    print(f"표본 수: {sample_size:,}개 / 물리량 수: {len(PARAM_DICT)}개")

if __name__ == '__main__':
    build()
