"""
신현승 및 사용자 최신 요구사항 반영 자체 완결형 HTML 대시보드 생성 스크립트.
1. 색상 기준 3대 신규 분류 체계 추가:
   - 기본 형태 4분류: 타원은하, 나선은하, 불규칙은하, 렌즈형은하
   - 활동성 은하 3분류: 전파은하, 세이퍼트 은하, 퀘이사 (+ 일반 은하)
   - 세부 구조 5분류: 마젤란형 은하, 나선은하, 막대나선은하, 고리은하, 불규칙 은하 (+ 기타)
   - 11대 통합 은하 분류
2. 물리량 오차값(err) 전면 제외
3. 필수 물리량 신규 산출 및 탑재:
   - 광도 (abs_mag_r, log_luminosity_r, luminosity_solar)
   - 은하 질량 (항성질량 lgm_tot_p50, 동역학 총질량 log_dyn_mass)
   - 은하 회전곡선 (회전속도 v_rot [km/s], log_v_rot)
   - 회전곡선과 질량을 통해 유도된 암흑물질 양 (log_dark_matter_mass, dark_matter_fraction)
   - 은하의 원소비 (oh_p50, log_n_o, log_oii_oiii, log_s_o)
   - 플럭스 (h_alpha_flux, h_beta_flux, h_gamma_flux, oiii_5007_flux, nii_6584_flux, sii_6717_flux, oii_3726_flux)
4. 모든 은하계 데이터를 받을 수 있는 '다운로드 탭' 추가 (클라이언트측 원클릭 CSV 다운로드 및 파일 링크)
5. 90년대 아날로그 호러 테마 완벽 유지
"""
import os
import json
import pandas as pd
import numpy as np
import config

def main():
    print("[1/4] 마스터 데이터셋 로드 중...")
    df = pd.read_csv(config.MASTER_DATASET_FILE)
    total = len(df)
    print(f"  => 총 {total:,}개 은하 표본 로드 완료")

    # 신현승 및 사용자 지정 핵심 물리량 (오차값 완전 배제, 광도/회전곡선/암흑물질/원소비 반영)
    PARAM_DICT = {
        # 1. 광도 및 절대등급
        'log_luminosity_r': 'log_luminosity_r - r밴드 광도 log(L_r / L_sun)',
        'abs_mag_r': 'abs_mag_r - 거리를 보정한 은하의 r밴드 절대 등급 [mag]',
        
        # 2. 은하 질량
        'lgm_tot_p50': 'lgm_tot_p50 - 은하의 총 항성 질량 log(M* / M_sun)',
        'log_dyn_mass': 'log_dyn_mass - 회전속도와 반경으로 유도된 은하 동역학 총 질량 log(M_dyn / M_sun)',
        
        # 3. 은하 회전곡선
        'v_rot': 'v_rot - 은하 회전곡선의 평탄 회전속도 [km/s]',
        'log_v_rot': 'log_v_rot - 은하 회전속도의 로그값 log(V_rot [km/s])',
        'velDisp': 'velDisp - 은하 중심부 별들의 무작위 운동 속도 분산 [km/s]',
        
        # 4. 회전곡선과 질량으로 유도된 암흑물질 양
        'log_dark_matter_mass': 'log_dark_matter_mass - 유도된 암흑물질 총 질량 log(M_DM / M_sun)',
        'dark_matter_fraction': 'dark_matter_fraction - 은하 전체 동역학 질량 대비 암흑물질 분율 f_DM (0~1)',
        
        # 5. 은하 원소비 및 화학적 조성
        'oh_p50': 'oh_p50 - 기체 산소 원소비 (산소 풍부도 12 + log(O/H))',
        'log_n_o': 'log_n_o - 질소-산소 원소비 log(N/O)',
        'log_oii_oiii': 'log_oii_oiii - 산소 원소 이온화 상태비 log([O II] / [O III])',
        'log_s_o': 'log_s_o - 황-산소 방출선 비율 log([S II] / [O III])',
        'log_nii_ha': 'log_nii_ha - BPT x축 비율 log([N II] 6584 / H-alpha)',
        'log_oiii_hb': 'log_oiii_hb - BPT y축 비율 log([O III] 5007 / H-beta)',
        
        # 6. 순수 방출선 플럭스 (오차값 제외)
        'h_alpha_flux': 'h_alpha_flux - 젊은 별 생성 활동을 나타내는 수소 H-alpha (6563Å) 플럭스',
        'h_beta_flux': 'h_beta_flux - 성간 소광 및 별 생성 분석용 수소 H-beta (4861Å) 플럭스',
        'h_gamma_flux': 'h_gamma_flux - 발머 계열 수소 H-gamma (4340Å) 플럭스',
        'oiii_5007_flux': 'oiii_5007_flux - 고에너지 이온화 환경을 나타내는 산소 [O III] 5007Å 플럭스',
        'nii_6584_flux': 'nii_6584_flux - 가스 금속 함량을 지시하는 질소 [N II] 6584Å 플럭스',
        'sii_6717_flux': 'sii_6717_flux - 성간 가스 전자밀도를 추정하는 황 [S II] 6717Å 플럭스',
        'oii_3726_flux': 'oii_3726_flux - 은하 별 생성률을 대변하는 산소 [O II] 3726Å 플럭스',
        
        # 7. 측광 겉보기 등급 및 색지수
        'u': 'u - 자외선 파장 대역 겉보기 등급 [mag]',
        'g': 'g - 녹색 파장 대역 겉보기 등급 [mag]',
        'r': 'r - 붉은색 파장 대역 겉보기 등급 [mag]',
        'i': 'i - 근적외선 파장 대역 겉보기 등급 [mag]',
        'color_u_r': 'color_u_r - 은하의 색 분포를 나타내는 (u - r) 색지수 [mag]',
        
        # 8. 구조 및 크기, 연령, 적색편이
        'petroRad_r': 'petroRad_r - r밴드 페트로시안 반지름 [arcsec]',
        'petroR50_r': 'petroR50_r - 은하 빛의 50%를 포함하는 유효 반광반경 [arcsec]',
        'petroR90_r': 'petroR90_r - 은하 빛의 90%를 포함하는 영역의 반지름 [arcsec]',
        'r_e_kpc': 'r_e_kpc - 물리적 유효 반경 [kpc]',
        'z': 'z - 스펙트럼 흡수/방출선으로 측정한 분광 적색편이',
        'phot_z': 'phot_z - 필터 밝기 비율로 추정한 측광 적색편이',
        'sfr_tot_p50': 'sfr_tot_p50 - 1년 동안 생성되는 별의 총 질량 log(SFR [M_sun/yr])',
        'd4000_n': 'd4000_n - 4000Å 불연속 감쇄폭 Dn(4000) (늙은 별 비율과 은하 나이)'
    }

    print(f"[2/4] 통계 요약 계산 중... ({len(PARAM_DICT)}개 물리량)")
    stats = {}
    for col, desc in PARAM_DICT.items():
        if col in df.columns:
            s = pd.to_numeric(df[col], errors='coerce').dropna()
            if len(s) > 0:
                stats[col] = {
                    'name': col,
                    'desc': desc,
                    'mean': round(float(s.mean()), 4),
                    'median': round(float(s.median()), 4),
                    'std': round(float(s.std()), 4),
                    'min': round(float(s.min()), 4),
                    'max': round(float(s.max()), 4),
                    'count': int(s.count()),
                }

    # 분류별 표본 수 집계
    morph_dist = df['class_morphology'].value_counts().to_dict()
    activity_dist = df['class_activity'].value_counts().to_dict()
    detail_dist = df['class_detail'].value_counts().to_dict()
    type_dist = df['galaxy_type'].value_counts().to_dict()

    print("[3/4] 플롯 및 다운로드용 표본 데이터 샘플링 (10,000개)...")
    sample_size = min(10000, total)
    sample = df.sample(n=sample_size, random_state=42)

    cat_cols = ['class_morphology', 'class_activity', 'class_detail', 'galaxy_type', 'bptclass']
    sample_cols = cat_cols + list(PARAM_DICT.keys())
    sample_cols = [c for c in sample_cols if c in sample.columns]
    sample_cols = list(dict.fromkeys(sample_cols))

    sample_df = sample[sample_cols].copy()
    sample_json = json.loads(sample_df.to_json(orient='records'))

    print("[4/4] 자체 완결형 HTML 대시보드(다운로드 탭 포함) 생성 중...")
    median_z = stats.get('z', {}).get('median', 'N/A')

    # Color definitions for categories in JS
    CATS = {
        'class_morphology': '[형태 4분류] 타원은하, 나선은하, 불규칙은하, 렌즈형은하',
        'class_activity': '[활동성 3분류] 전파은하, 세이퍼트 은하, 퀘이사, 일반 은하',
        'class_detail': '[세부구조 5분류] 마젤란형 은하, 나선은하, 막대나선은하, 고리은하, 불규칙 은하',
        'galaxy_type': '[11대 통합분류] 전체 은하 분류 체계'
    }

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>YSC 은하 물리량 & 암흑물질 & 다차원 진화 대시보드</title>
<script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>
<style>
@import url('https://fonts.googleapis.com/css2?family=VT323&display=swap');
@font-face {{
    font-family: 'DungGeunMo';
    src: url('https://fastly.jsdelivr.net/gh/projectnoonnu/noonfonts_six@1.2/DungGeunMo.woff') format('woff');
    font-weight: normal; font-style: normal;
}}
:root {{ --bg: #000; --text: #d0d0d0; }}
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ background: var(--bg); color: var(--text); font-family: 'DungGeunMo', 'VT323', monospace; line-height: 1.6; overflow-x: hidden; position: relative; }}
body::before {{
    content: " "; display: block; position: fixed; top: 0; left: 0; bottom: 0; right: 0;
    background: linear-gradient(rgba(18,16,16,0) 50%, rgba(0,0,0,0.4) 50%),
                linear-gradient(90deg, rgba(255,0,0,0.08), rgba(0,255,0,0.03), rgba(0,0,255,0.08));
    z-index: 999; background-size: 100% 4px, 4px 100%; pointer-events: none;
}}
.hdr {{ text-align: center; padding: 2.5rem 1rem 1.5rem; border-bottom: 2px solid #f00; position: relative; z-index: 10; }}
.hdr h1 {{ font-size: 2.5rem; color: #fff; text-shadow: 2px 2px 0px #f00, -2px -2px 0px #00f; text-transform: uppercase; letter-spacing: 2px; }}
.hdr p {{ color: #aaa; margin-top: .4rem; font-size: 1.2rem; }}
.badge {{ display: inline-block; background: #f00; color: #000; padding: .2rem .7rem; border: 2px solid #fff; font-size: 1rem; margin-top: .6rem; animation: blink 2s infinite; font-weight: bold; text-transform: uppercase; }}
@keyframes blink {{ 0%, 49% {{ opacity: 1; }} 50%, 100% {{ opacity: 0; }} }}
.container {{ max-width: 1400px; margin: 0 auto; padding: 1.5rem; position: relative; z-index: 10; }}
.tabs {{ display: flex; gap: .6rem; flex-wrap: wrap; justify-content: center; margin-bottom: 1.5rem; }}
.tab-btn {{ background: #000; border: 2px solid #f00; color: #f00; padding: .55rem 1.4rem; font-size: 1.2rem; cursor: pointer; transition: .1s; font-family: inherit; text-transform: uppercase; }}
.tab-btn:hover {{ background: #f00; color: #000; }}
.tab-btn.active {{ background: #f00; color: #000; border-color: #fff; font-weight: bold; }}
.tab {{ display: none; }} .tab.active {{ display: block; animation: glitch 0.2s linear; }}
@keyframes glitch {{ 0% {{ transform: translate(2px, 2px); }} 20% {{ transform: translate(-2px, -2px); }} 40% {{ transform: translate(2px, -2px); }} 60% {{ transform: translate(-2px, 2px); }} 80% {{ transform: translate(2px, 2px); }} 100% {{ transform: translate(0, 0); }} }}
.glass {{ background: #000; border: 2px solid #f00; padding: 1.4rem; margin-bottom: 1.2rem; }}
.row {{ display: grid; gap: 1.2rem; }} 
.row-4 {{ grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); }}
.row-5 {{ grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); }}
.stat-card {{ text-align: center; padding: 1rem; border: 1px dashed #444; }}
.stat-card .val {{ font-size: 2.2rem; font-weight: bold; color: #fff; text-shadow: 2px 2px 0 #f00; }}
.stat-card .lbl {{ color: #ffff00; font-size: 1.05rem; margin-top: .3rem; text-transform: uppercase; }}
.ctrls {{ display: flex; gap: 1rem; flex-wrap: wrap; margin-bottom: 1rem; }}
.ctrl {{ flex: 1; min-width: 280px; }}
.ctrl label {{ display: block; color: #fff; font-weight: bold; font-size: 1.1rem; margin-bottom: .3rem; }}
select, input {{ width: 100%; padding: .55rem; border: 2px solid #f00; background: #000; color: #fff; font-family: inherit; font-size: 1.1rem; outline: none; }}
select:focus, input:focus {{ border-color: #fff; }}
.presets {{ display: flex; gap: .6rem; flex-wrap: wrap; margin-bottom: 1rem; }}
.preset {{ background: #000; border: 2px solid #fff; color: #fff; padding: .4rem 1rem; cursor: pointer; font-family: inherit; font-size: 1.05rem; text-transform: uppercase; }}
.preset:hover {{ background: #fff; color: #000; }}
#plot {{ height: 65vh; min-height: 520px; border: 2px solid #444; background: #000; }}
table {{ width: 100%; border-collapse: collapse; }}
th, td {{ text-align: left; padding: .6rem .8rem; border-bottom: 1px dashed #444; font-size: 1.05rem; }}
th {{ color: #ffff00; font-weight: bold; text-transform: uppercase; border-bottom: 2px solid #f00; position: sticky; top: 0; background: #111; }}
td {{ color: #ccc; }}
.type-badge {{ display: inline-block; padding: .15rem .5rem; border: 1px solid #fff; font-size: 0.95rem; text-transform: uppercase; }}
.btn-dl {{ display: inline-block; background: #f00; color: #000; font-weight: bold; font-size: 1.2rem; padding: .8rem 2rem; border: 2px solid #fff; cursor: pointer; text-decoration: none; text-transform: uppercase; font-family: inherit; margin: .5rem .5rem .5rem 0; transition: .2s; }}
.btn-dl:hover {{ background: #ffff00; color: #000; border-color: #f00; text-shadow: none; }}
footer {{ text-align: center; padding: 2rem 1rem; color: #555; font-size: 1rem; border-top: 2px solid #f00; }}
</style>
</head>
<body>

<div class="hdr">
<h1>YSC 은하 물리량 & 암흑물질 & 다차원 진화 대시보드</h1>
<p>SDSS DR18 &middot; 신현승 지정 핵심 물리량 &middot; 암흑물질/회전곡선/광도/원소비 &middot; 3대 신규 분류 체계</p>
<span class="badge">오차값 제외 &middot; 암흑물질 유도량 산출 &middot; 전표본 다운로드 탭 완비</span>
</div>

<div class="container">
<div class="tabs">
<button class="tab-btn active" onclick="openTab('overview')">1. 개요 & 3대 분류 체계</button>
<button class="tab-btn" onclick="openTab('explore')">2. 물리량 & 암흑물질 상관관계 탐색</button>
<button class="tab-btn" onclick="openTab('stats')">3. 물리량 기술통계 ({len(stats)}종)</button>
<button class="tab-btn" onclick="openTab('data_table')">4. 표본 데이터 테이블</button>
<button class="tab-btn" onclick="openTab('validate')">5. 분광 관측 판독기</button>
<button class="tab-btn" onclick="openTab('download')" style="border-color:#ffff00;color:#ffff00;">6. 📥 데이터 다운로드</button>
</div>

<!-- ══ TAB: 개요 ══ -->
<div id="overview" class="tab active">
<div class="row row-4">
<div class="glass stat-card"><div class="val">{total:,}</div><div class="lbl">분석 표본 은하 수</div></div>
<div class="glass stat-card"><div class="val">3대 체계</div><div class="lbl">형태/활동성/세부구조 분류</div></div>
<div class="glass stat-card"><div class="val">{len(stats)}</div><div class="lbl">탑재된 물리량/원소비</div></div>
<div class="glass stat-card"><div class="val">{median_z}</div><div class="lbl">중앙 적색편이 (z)</div></div>
</div>

<!-- 1. 기본 형태 4분류 -->
<div class="glass">
<h3 style="color:#ffff00;margin-bottom:.8rem">&#127756; [신규 1] 기본 형태 4분류 (타원은하, 나선은하, 불규칙은하, 렌즈형은하)</h3>
<div class="row row-4">
"""
    m_colors = {"타원은하": "#dc2626", "나선은하": "#2563eb", "렌즈형은하": "#ea580c", "불규칙은하": "#059669"}
    for gtype, cnt in morph_dist.items():
        pct = cnt / total * 100
        color = m_colors.get(gtype, "#fff")
        html += f'<div class="glass stat-card"><div class="val" style="color:{color}">{cnt:,}</div><div class="lbl"><span class="type-badge" style="border-color:{color};color:{color}">{gtype}</span><br>{pct:.1f}%</div></div>\n'

    html += """</div></div>

<!-- 2. 활동성 은하 3분류 -->
<div class="glass">
<h3 style="color:#ffff00;margin-bottom:.8rem">&#9889; [신규 2] 활동성 은하 3분류 (전파은하, 세이퍼트 은하, 퀘이사, 일반 은하)</h3>
<div class="row row-4">
"""
    a_colors = {"전파은하": "#b91c1c", "세이퍼트 은하": "#9333ea", "퀘이사": "#d97706", "일반 은하": "#0284c7"}
    for gtype, cnt in activity_dist.items():
        pct = cnt / total * 100
        color = a_colors.get(gtype, "#fff")
        html += f'<div class="glass stat-card"><div class="val" style="color:{color}">{cnt:,}</div><div class="lbl"><span class="type-badge" style="border-color:{color};color:{color}">{gtype}</span><br>{pct:.1f}%</div></div>\n'

    html += """</div></div>

<!-- 3. 세부 구조 5분류 -->
<div class="glass">
<h3 style="color:#ffff00;margin-bottom:.8rem">&#128302; [신규 3] 세부 구조 5분류 (마젤란형 은하, 나선은하, 막대나선은하, 고리은하, 불규칙 은하)</h3>
<div class="row row-5">
"""
    d_colors = {"마젤란형 은하": "#10b981", "나선은하": "#2563eb", "막대나선은하": "#0284c7", "고리은하": "#8b5cf6", "불규칙 은하": "#059669", "기타 은하": "#777"}
    for gtype, cnt in detail_dist.items():
        pct = cnt / total * 100
        color = d_colors.get(gtype, "#fff")
        html += f'<div class="glass stat-card"><div class="val" style="color:{color}">{cnt:,}</div><div class="lbl"><span class="type-badge" style="border-color:{color};color:{color}">{gtype}</span><br>{pct:.1f}%</div></div>\n'

    html += """</div></div>

<div class="glass">
<h3 style="color:#fff;margin-bottom:.6rem">&#9881;&#65039; 물리량 산출 및 암흑물질 유도 모델 안내</h3>
<p style="color:#aaa;font-size:1.1rem">
&bull; <strong>광도 (Luminosity)</strong>: 광도거리(D_L)와 겉보기 r등급을 바탕으로 r밴드 절대 등급(M_r)을 도출하고, 태양 광도 단위의 복사 광도 log(L_r / L_sun)를 산출하였습니다.<br>
&bull; <strong>은하 회전곡선 (Rotation Curve)</strong>: 중심부 속도분산(velDisp)과 비리얼 정리 평탄 회전속도 관계식 V_rot = sqrt(2) * velDisp 로 은하의 회전곡선 원형속도를 유도하였습니다.<br>
&bull; <strong>암흑물질 양 (Dark Matter Mass & Fraction)</strong>: 은하 유효반경 R_e와 회전속도 V_rot를 이용해 총 동역학적 질량 M_dyn = 5 * V_rot^2 * R_e / (2G) 을 도출한 뒤, 항성 질량 M*을 감산하여 암흑물질 질량 M_DM = M_dyn - M* 및 분율 f_DM = M_DM / M_dyn 을 과학적으로 유도하였습니다.<br>
&bull; <strong>은하 원소비 (Elemental Abundances)</strong>: 기체 산소 풍부도(12 + log(O/H)), 질소-산소 원소비 log(N/O), 산소 이온화 상태비 log([O II]/[O III]), 황-산소비 log([S II]/[O III])를 방출선 적분을 통해 산출하였습니다.
</p>
</div>
</div>

<!-- ══ TAB: 탐색 ══ -->
<div id="explore" class="tab">
<div class="glass">
<div class="ctrls">
<div class="ctrl"><label>X축 물리량</label><select id="x-var"></select></div>
<div class="ctrl"><label>Y축 물리량</label><select id="y-var"></select></div>
<div class="ctrl"><label>색상(Color) 기준 (3대 신규 분류 또는 물리량)</label><select id="c-var"></select></div>
</div>
<div class="presets">
<strong style="color:#ffff00;align-self:center;margin-right:4px;">탐색 프리셋:</strong>
<button class="preset" onclick="setPreset('ms')">1. 은하 주계열 (질량 vs SFR)</button>
<button class="preset" onclick="setPreset('bpt')">2. BPT 진단도 (NII/Ha vs OIII/Hb)</button>
<button class="preset" onclick="setPreset('dm')">3. 암흑물질 분율 vs 항성 질량</button>
<button class="preset" onclick="setPreset('rot')">4. 은하 회전속도 vs 질량 (Tully-Fisher)</button>
<button class="preset" onclick="setPreset('lum')">5. 질량-광도 관계 (Mass vs Luminosity)</button>
<button class="preset" onclick="setPreset('no')">6. 질소-산소 원소비 (log(N/O) vs O/H)</button>
<button class="preset" onclick="setPreset('cm')">7. 색-질량 도표 (u-r vs Mass)</button>
<button class="preset" onclick="setPreset('dyn')">8. 동역학 질량 vs 항성 질량</button>
<button class="preset" onclick="setPreset('d4000')">9. D4000 별나이 vs 금속성</button>
<button class="preset" onclick="setPreset('flux')">10. Hα vs [OIII] 방출선 플럭스</button>
</div>
<div id="plot"></div>
</div>
</div>

<!-- ══ TAB: 통계 ══ -->
<div id="stats" class="tab">
<div class="glass">
<h3 style="color:#fff;margin-bottom:.8rem">전체 {len(stats)}개 핵심 물리량 기술통계 명세표 (오차값 제외 완료)</h3>
<div style="overflow-x:auto; max-height: 650px; overflow-y: auto;">
<table>
<thead>
<tr><th>물리량 변수명</th><th>천문학적 설명</th><th>평균 (Mean)</th><th>중앙값 (Median)</th><th>표준편차 (Std)</th><th>최소 (Min)</th><th>최대 (Max)</th><th>표본 수</th></tr>
</thead>
<tbody>
"""
    for col, s in stats.items():
        desc_text = s['desc'].split(' - ', 1)[1] if ' - ' in s['desc'] else s['desc']
        html += f"<tr><td><strong style='color:#ffff00'>{col}</strong></td><td><span style='color:#fff'>{desc_text}</span></td><td>{s['mean']}</td><td>{s['median']}</td><td>{s['std']}</td><td>{s['min']}</td><td>{s['max']}</td><td>{s['count']:,}</td></tr>\n"

    html += """</tbody>
</table></div></div></div>

<!-- ══ TAB: 데이터 표 ══ -->
<div id="data_table" class="tab">
<div class="glass">
<h3 style="color:#fff;margin-bottom:1rem">대표 표본 데이터 목록 (Sample Data Viewer)</h3>
<div style="overflow-x:auto; max-height: 600px; overflow-y: auto;">
<table id="galaxy_table">
<thead>
<tr>
<th>기본 형태</th>
<th>활동성</th>
<th>세부 구조</th>
<th>적색편이 (z)</th>
<th>항성질량 (log M*)</th>
<th>동역학질량 (log M_dyn)</th>
<th>회전속도 (V_rot)</th>
<th>암흑물질분율 (f_DM)</th>
<th>광도 (log L)</th>
<th>산소원소비 (O/H)</th>
<th>N/O 원소비</th>
</tr>
</thead>
<tbody id="galaxy_table_body">
</tbody>
</table>
</div>
</div>
</div>

<!-- ══ TAB: 판독기 ══ -->
<div id="validate" class="tab">
<div class="glass">
<h3 style="color:#fff;margin-bottom:.6rem">은하 분광 관측값 판독기</h3>
<p style="color:#aaa;margin-bottom:1rem">방출선 플럭스를 입력하면 BPT 분류, 산소 금속성, Balmer Decrement 먼지 소광을 자동 연산합니다.</p>
<div class="ctrls">
<div class="ctrl"><label>H-alpha Flux (6563Å)</label><input type="number" id="ha" step="any" placeholder="예: 125.4"></div>
<div class="ctrl"><label>H-beta Flux (4861Å)</label><input type="number" id="hb" step="any" placeholder="예: 38.2"></div>
<div class="ctrl"><label>[OIII] 5007Å Flux</label><input type="number" id="oiii" step="any" placeholder="예: 42.1"></div>
<div class="ctrl"><label>[NII] 6584Å Flux</label><input type="number" id="nii" step="any" placeholder="예: 48.7"></div>
</div>
<button class="preset" style="border-color:#ffff00;color:#ffff00;font-size:1.1rem;padding:.6rem 2rem" onclick="doValidate()">판독 가동</button>
<div id="val-result" style="display:none;margin-top:1.2rem">
<div class="row row-4">
<div class="glass stat-card"><div class="val" id="r-bpt">-</div><div class="lbl">BPT 이온화 분류</div></div>
<div class="glass stat-card"><div class="val" id="r-oh">-</div><div class="lbl">금속성 (12+log O/H)</div></div>
<div class="glass stat-card"><div class="val" id="r-ebv">-</div><div class="lbl">먼지 소광 E(B-V)</div></div>
<div class="glass stat-card"><div class="val" id="r-type">-</div><div class="lbl">에너지원 기원</div></div>
</div>
<div id="val-plot" style="height:380px;margin-top:1rem;border:2px solid #444;background:#000"></div>
</div>
</div>
</div>

<!-- ══ TAB: 다운로드 ══ -->
<div id="download" class="tab">
<div class="glass">
<h2 style="color:#ffff00;margin-bottom:1rem">&#128229; 은하계 데이터 파일 다운로드 센터</h2>
<p style="color:#ccc;font-size:1.15rem;margin-bottom:1.5rem">
연구에 활용된 전체 은하 데이터셋 및 물리량/화학 원소비 데이터를 아래 버튼을 통해 즉시 다운로드하실 수 있습니다.<br>
서버 없이 브라우저에서 바로 추출되는 원클릭 CSV 다운로드 및 로컬 원본 데이터 링크를 제공합니다.
</p>

<div style="display:grid; gap:1.5rem; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));">
    <div class="glass stat-card" style="text-align:left; padding:1.5rem;">
        <h3 style="color:#fff; margin-bottom:.5rem;">1. 대시보드 표본 데이터셋 (10,000개)</h3>
        <p style="color:#aaa; font-size:1rem; margin-bottom:1rem;">
            현재 대시보드에 임베딩된 10,000개 표본의 모든 물리량(광도, 회전곡선, 암흑물질, 원소비 등 35개 변수)과 3대 분류 체계가 포함된 완전한 CSV 파일입니다.
        </p>
        <button class="btn-dl" onclick="downloadSampleCSV()">📥 표본 10,000개 CSV 즉시 받기</button>
    </div>

    <div class="glass stat-card" style="text-align:left; padding:1.5rem;">
        <h3 style="color:#fff; margin-bottom:.5rem;">2. 마스터 데이터셋 전체 (55,000개)</h3>
        <p style="color:#aaa; font-size:1rem; margin-bottom:1rem;">
            SDSS 11대 은하 분류 체계(각 5,000개 균등 표본) 및 200개 파라미터가 모두 수록된 종합 마스터 CSV 파일입니다.
        </p>
        <a class="btn-dl" href="data/processed/galaxy_master_200params.csv" download="galaxy_master_200params.csv">📁 마스터 CSV 다운로드</a>
    </div>

    <div class="glass stat-card" style="text-align:left; padding:1.5rem;">
        <h3 style="color:#fff; margin-bottom:.5rem;">3. 물리량 특화 데이터셋 (Physical 100k)</h3>
        <p style="color:#aaa; font-size:1rem; margin-bottom:1rem;">
            측광 등급, 반경, 축비, 질량, 암흑물질, 회전속도 등 은하의 물리적 특성 파라미터가 정리된 데이터셋입니다.
        </p>
        <a class="btn-dl" href="data/excel_exports/physical_100k.csv" download="physical_100k.csv">📁 물리 데이터 CSV 받기</a>
    </div>

    <div class="glass stat-card" style="text-align:left; padding:1.5rem;">
        <h3 style="color:#fff; margin-bottom:.5rem;">4. 분광 & 원소비 데이터셋 (Chemical 100k)</h3>
        <p style="color:#aaa; font-size:1rem; margin-bottom:1rem;">
            방출선 플럭스, 등가폭(EQW), 산소/질소/황 원소비, BPT 진단 코드, D4000 등이 정리된 분광 특화 데이터셋입니다.
        </p>
        <a class="btn-dl" href="data/excel_exports/chemical_100k.csv" download="chemical_100k.csv">📁 화학/원소비 CSV 받기</a>
    </div>
</div>

<div style="margin-top:2rem; padding:1.2rem; border:1px dashed #f00;">
    <h4 style="color:#ffff00; margin-bottom:.5rem;">💡 다운로드 데이터 포맷 안내</h4>
    <p style="color:#aaa; font-size:1rem;">
    &bull; 모든 CSV 파일은 UTF-8 인코딩으로 저장되어 Excel 및 Python(Pandas), R 등에서 바로 로드할 수 있습니다.<br>
    &bull; 웹 브라우저 환경에서도 '표본 10,000개 CSV 즉시 받기' 버튼을 누르면 브라우저 메모리에서 실시간으로 CSV가 조합되어 즉시 다운로드됩니다.
    </p>
</div>
</div>
</div>

</div>

<footer>
YSC 2026 청소년과학탐구반 &mdash; 은하의 물리량 및 화학조성 분석을 통한 은하 진화 경향 및 메커니즘 분석 도표 탐구<br>
SDSS DR18 &middot; 암흑물질 &middot; 회전곡선 &middot; 광도 &middot; 원소비 &middot; 3대 신규 분류 체계 탑재 완결형 대시보드
</footer>

<script>
// ═══ Embedded real data ═══
const DATA = PLACEHOLDER_DATA;

// ═══ Variable definitions ═══
const VARS = PLACEHOLDER_VARS;
const CATS = PLACEHOLDER_CATS;

// ═══ Init selects ═══
const xs = document.getElementById('x-var'), ys = document.getElementById('y-var'), cs = document.getElementById('c-var');
Object.entries(VARS).forEach(([k,v]) => {{ xs.add(new Option(v,k)); ys.add(new Option(v,k)); }});
// Color dropdown: Add categorical classifications first, then continuous variables
const optGroupCat = document.createElement('optgroup');
optGroupCat.label = "── 은하 분류 체계 (색상 그룹) ──";
Object.entries(CATS).forEach(([k,v]) => {{ optGroupCat.appendChild(new Option(v,k)); }});
cs.appendChild(optGroupCat);

const optGroupNum = document.createElement('optgroup');
optGroupNum.label = "── 연속 물리량 (컬러바 스케일) ──";
Object.entries(VARS).forEach(([k,v]) => {{ optGroupNum.appendChild(new Option(v,k)); }});
cs.appendChild(optGroupNum);

xs.value='lgm_tot_p50'; ys.value='sfr_tot_p50'; cs.value='class_morphology';

// ═══ Populate Table ═══
const tbody = document.getElementById('galaxy_table_body');
DATA.slice(0, 100).forEach(d => {{
    const tr = document.createElement('tr');
    tr.innerHTML = `
        <td><span style="color:#2563eb">${{d.class_morphology || '-'}}</span></td>
        <td><span style="color:#9333ea">${{d.class_activity || '-'}}</span></td>
        <td><span style="color:#10b981">${{d.class_detail || '-'}}</span></td>
        <td>${{d.z !== null && d.z !== undefined ? d.z.toFixed(4) : '-'}}</td>
        <td>${{d.lgm_tot_p50 !== null && d.lgm_tot_p50 !== undefined ? d.lgm_tot_p50.toFixed(2) : '-'}}</td>
        <td>${{d.log_dyn_mass !== null && d.log_dyn_mass !== undefined ? d.log_dyn_mass.toFixed(2) : '-'}}</td>
        <td>${{d.v_rot !== null && d.v_rot !== undefined ? d.v_rot.toFixed(1) : '-'}}</td>
        <td>${{d.dark_matter_fraction !== null && d.dark_matter_fraction !== undefined ? (d.dark_matter_fraction * 100).toFixed(1) + '%' : '-'}}</td>
        <td>${{d.log_luminosity_r !== null && d.log_luminosity_r !== undefined ? d.log_luminosity_r.toFixed(2) : '-'}}</td>
        <td>${{d.oh_p50 !== null && d.oh_p50 !== undefined ? d.oh_p50.toFixed(2) : '-'}}</td>
        <td>${{d.log_n_o !== null && d.log_n_o !== undefined ? d.log_n_o.toFixed(2) : '-'}}</td>
    `;
    tbody.appendChild(tr);
}});

// ═══ Draw plot ═══
function draw() {{
    const xk=xs.value, yk=ys.value, ck=cs.value;
    const xd=DATA.map(d=>d[xk]), yd=DATA.map(d=>d[yk]);
    let traces;
    if(CATS[ck]) {{
        const groups=[...new Set(DATA.map(d=>d[ck]).filter(v=>v!=null))];
        const palette=['#2563eb', '#dc2626', '#059669', '#ea580c', '#9333ea', '#d97706', '#b91c1c', '#0284c7', '#8b5cf6', '#10b981', '#777777'];
        traces=groups.map((g,i)=>{{
            const idx=DATA.map((d,j)=>d[ck]===g?j:-1).filter(j=>j>=0);
            return {{x:idx.map(j=>xd[j]),y:idx.map(j=>yd[j]),mode:'markers',name:g.split(' (')[0],
                marker:{{size:4.5,opacity:0.65,color:palette[i%palette.length]}},type:'scatter'}};
        }});
    }} else {{
        traces=[{{x:xd,y:yd,mode:'markers',type:'scatter',
            marker:{{size:4.5,opacity:0.65,color:DATA.map(d=>d[ck]),colorscale:'Viridis',showscale:true,
                colorbar:{{title:{{text:VARS[ck]||ck,font:{{color:'#aaa'}}}},tickfont:{{color:'#888'}}}}}}];
    }}
    const layout={{
        xaxis:{{title:VARS[xk]||xk,gridcolor:'#333',color:'#fff'}},
        yaxis:{{title:VARS[yk]||yk,gridcolor:'#333',color:'#fff'}},
        paper_bgcolor:'#000',plot_bgcolor:'#000',
        font:{{color:'#f00', family: 'VT323, DungGeunMo, monospace', size: 14}},
        margin:{{t:30,b:50,l:60,r:20}},
        hovermode:'closest',legend:{{font:{{color:'#fff'}}}}
    }};
    Plotly.newPlot('plot',traces,layout,{{responsive:true}});
}}
xs.onchange=ys.onchange=cs.onchange=draw;

function setPreset(p){{
    if(p==='ms'){{xs.value='lgm_tot_p50';ys.value='sfr_tot_p50';cs.value='class_morphology';}}
    if(p==='bpt'){{xs.value='log_nii_ha';ys.value='log_oiii_hb';cs.value='class_activity';}}
    if(p==='dm'){{xs.value='lgm_tot_p50';ys.value='dark_matter_fraction';cs.value='class_morphology';}}
    if(p==='rot'){{xs.value='lgm_tot_p50';ys.value='v_rot';cs.value='class_detail';}}
    if(p==='lum'){{xs.value='lgm_tot_p50';ys.value='log_luminosity_r';cs.value='class_morphology';}}
    if(p==='no'){{xs.value='oh_p50';ys.value='log_n_o';cs.value='class_activity';}}
    if(p==='cm'){{xs.value='lgm_tot_p50';ys.value='color_u_r';cs.value='class_morphology';}}
    if(p==='dyn'){{xs.value='lgm_tot_p50';ys.value='log_dyn_mass';cs.value='class_morphology';}}
    if(p==='d4000'){{xs.value='oh_p50';ys.value='d4000_n';cs.value='class_morphology';}}
    if(p==='flux'){{xs.value='h_alpha_flux';ys.value='oiii_5007_flux';cs.value='class_activity';}}
    draw();
}}

// ═══ Tabs ═══
function openTab(id){{
    document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(b=>b.classList.remove('active'));
    document.getElementById(id).classList.add('active');
    event.target.classList.add('active');
    if(id==='explore') setTimeout(draw,100);
}}

// ═══ Validate ═══
function doValidate(){{
    const ha=+document.getElementById('ha').value, hb=+document.getElementById('hb').value;
    const oiii=+document.getElementById('oiii').value, nii=+document.getElementById('nii').value;
    if(!ha||!hb||!oiii||!nii){{alert('모든 방출선 플럭스 값을 입력해 주세요.');return;}}
    const lnha=Math.log10(nii/ha), lohb=Math.log10(oiii/hb);
    let bpt='Unknown';
    if(lnha>=0.05) bpt=lohb>0.5?'세이퍼트 (Seyfert AGN)':'라이너 (LINER/Shock)';
    else {{ const k=0.61/(lnha-0.05)+1.3; bpt=lohb<k?'정상 별생성 은하 (Star-forming)':'복합형/활동은하핵 (Composite/AGN)'; }}
    const bd=ha/hb, ebv=bd>2.86?(1.086*Math.log(bd/2.86)/1.16).toFixed(3):'0.000';
    const oh=(8.90+0.57*lnha).toFixed(2);
    document.getElementById('r-bpt').textContent=bpt;
    document.getElementById('r-oh').textContent=oh;
    document.getElementById('r-ebv').textContent=ebv;
    document.getElementById('r-type').textContent=bpt.includes('Star')?'광이온화 (HII 영역)':'중심 블랙홀 강착/충격파';
    document.getElementById('val-result').style.display='block';

    const bgx=DATA.map(d=>d.log_nii_ha).filter(v=>v!=null);
    const bgy=DATA.map((d,i)=>d.log_nii_ha!=null?d.log_oiii_hb:null).filter(v=>v!=null);
    const kx=[];for(let x=-2;x<=0.04;x+=0.02)kx.push(x);
    const ky1=kx.map(x=>x<0.05?0.61/(x-0.05)+1.3:null);
    Plotly.newPlot('val-plot',[
        {{x:bgx,y:bgy,mode:'markers',marker:{{size:3,color:'#444',opacity:0.3}},name:'SDSS 표본',type:'scatter'}},
        {{x:kx,y:ky1,mode:'lines',line:{{color:'#ffff00',dash:'dash',width:2}},name:'Kauffmann (2003)'}},
        {{x:[lnha],y:[lohb],mode:'markers',marker:{{size:16,color:'#ff0000',symbol:'star',line:{{color:'#fff',width:2}}}},name:'입력 타겟'}}
    ],{{xaxis:{{title:'log([NII] / Hα)',range:[-1.8,0.8],gridcolor:'#333',color:'#fff'}},
       yaxis:{{title:'log([OIII] / Hβ)',range:[-1.5,1.6],gridcolor:'#333',color:'#fff'}},
       paper_bgcolor:'#000',plot_bgcolor:'#000',font:{{color:'#f00',family:'VT323, DungGeunMo, monospace',size:13}},
       margin:{{t:20,b:40,l:50,r:20}},showlegend:true}},{{responsive:true}});
}}

// ═══ Client-side CSV Download ═══
function downloadSampleCSV() {{
    if (!DATA || DATA.length === 0) {{
        alert('데이터가 준비되지 않았습니다.');
        return;
    }}
    const headers = Object.keys(DATA[0]);
    let csvContent = "\uFEFF" + headers.join(",") + "\\n";
    DATA.forEach(row => {{
        const line = headers.map(h => {{
            let val = row[h];
            if (val === null || val === undefined) return "";
            if (typeof val === 'string' && val.includes(',')) return `"${{val}}"`;
            return val;
        }}).join(",");
        csvContent += line + "\\n";
    }});
    const blob = new Blob([csvContent], {{ type: 'text/csv;charset=utf-8;' }});
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "galaxy_dashboard_sample_10000.csv";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}}

// Initial draw
draw();
</script>
</body>
</html>"""

    data_json = json.dumps(sample_json, ensure_ascii=False)
    vars_json = json.dumps(PARAM_DICT, ensure_ascii=False)
    cats_json = json.dumps(CATS, ensure_ascii=False)

    html = html.replace('PLACEHOLDER_DATA', data_json)
    html = html.replace('PLACEHOLDER_VARS', vars_json)
    html = html.replace('PLACEHOLDER_CATS', cats_json)

    output_path = os.path.join(config.PROJECT_ROOT, 'dashboard_real_data.html')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"\n=== 완료! ===")
    print(f"파일: {output_path}")
    print(f"크기: {size_mb:.1f} MB")
    print(f"임베딩된 은하 수: {sample_size:,}개")
    print(f"임베딩된 물리량 수: {len(PARAM_DICT)}개")
    print(f"신규 분류 체계 3종 + 통합 분류 반영 완료")

if __name__ == '__main__':
    main()
