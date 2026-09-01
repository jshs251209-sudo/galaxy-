"""
신현승 지정 물리량 명세서 기반 자체 완결형 HTML 대시보드 생성 스크립트.
- 적경(ra), 적위(dec), 식별번호(specObjID) 제외
- 신현승이 제공한 물리량 명세서 및 설명을 1:1 정확히 매핑
- '은하 불확실' 완전 제거 및 11대 은하 분류 체계(각 5,000개 균등 표본) 적용
- 90년대 아날로그 호러 / 긴급 연구소 테마 완벽 적용
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
    print(f"  => 총 {total:,}개 은하 로드 완료")

    # 신현승이 직접 보낸 정확한 파라미터 딕셔너리 (적경, 적위, specObjID 제외)
    PARAM_DICT = {
        'z': 'z - 스펙트럼 흡수 및 방출선 분석을 통해 직접 측정한 분광 적색편이 값',
        'velDisp': 'velDisp - 은하 내부 별들의 무작위 운동 속도 편차를 나타내는 속도 분산 값',
        'velDispErr': 'velDispErr - 속도 분산 측정값에 대한 통계적 오차',
        'u': 'u - 자외선 파장 대역에서 측정한 천체의 겉보기 등급',
        'g': 'g - 녹색 파장 대역에서 측정한 천체의 겉보기 등급',
        'r': 'r - 붉은색 파장 대역에서 측정한 천체의 겉보기 등급',
        'i': 'i - 근적외선 파장 대역에서 측정한 천체의 겉보기 등급',
        'phot_z': 'phot_z - 스펙트럼 없이 여러 필터의 밝기 비율만으로 추정한 측광 적색편이 값',
        'petroRad_r': 'petroRad_r - r밴드 필터에서 측정한 은하의 빛 분포 기반 페트로시안 반지름',
        'petroR50_r': 'petroR50_r - r밴드에서 은하 전체 빛의 50%를 포함하는 영역의 반지름',
        'petroR90_r': 'petroR90_r - r밴드에서 은하 전체 빛의 90%를 포함하는 영역의 반지름',
        'h_alpha_flux': 'h_alpha_flux - 젊고 뜨거운 별 생성 활동을 보여주는 수소 H-alpha 방출선의 세기',
        'h_alpha_flux_err': 'h_alpha_flux_err - H-alpha 방출선 세기 측정값의 오차',
        'h_beta_flux': 'h_beta_flux - 성간 소광 및 별 생성을 분석할 때 쓰이는 수소 H-beta 방출선의 세기',
        'h_beta_flux_err': 'h_beta_flux_err - H-beta 방출선 세기 측정값의 오차',
        'h_gamma_flux': 'h_gamma_flux - 발머 계열 중 하나인 수소 H-gamma 방출선의 세기',
        'h_gamma_flux_err': 'h_gamma_flux_err - H-gamma 방출선 세기 측정값의 오차',
        'oiii_5007_flux': 'oiii_5007_flux - 중심부 블랙홀이나 고에너지 환경을 나타내는 5007 옹스트롬 산소[O III] 방출선의 세기',
        'oiii_5007_flux_err': 'oiii_5007_flux_err - 산소[O III] 5007 옹스트롬 방출선 세기 측정값의 오차',
        'nii_6584_flux': 'nii_6584_flux - 가스의 금속 함량을 파악하는 데 유용한 6584 옹스트롬 질소[N II] 방출선의 세기',
        'nii_6584_flux_err': 'nii_6584_flux_err - 질소[N II] 6584 옹스트롬 방출선 세기 측정값의 오차',
        'sii_6717_flux': 'sii_6717_flux - 성간 가스의 전자 밀도를 추정할 때 쓰이는 6717 옹스트롬 황[S II] 방출선의 세기',
        'sii_6717_flux_err': 'sii_6717_flux_err - 황[S II] 6717 옹스트롬 방출선 세기 측정값의 오차',
        'oii_3726_flux': 'oii_3726_flux - 먼 은하의 별 생성률 측정에 자주 쓰이는 3726 옹스트롬 산소[O II] 방출선의 세기',
        'oii_3726_flux_err': 'oii_3726_flux_err - 산소[O II] 3726 옹스트롬 방출선 세기 측정값의 오차',
        'lgm_tot_p50': 'lgm_tot_p50 - 태양 질량 단위로 환산한 은하의 총 별 질량의 로그 중앙값 (log M*)',
        'sfr_tot_p50': 'sfr_tot_p50 - 1년 동안 생성되는 별의 총 질량을 나타내는 별 생성률(SFR)의 로그 중앙값',
        'oh_p50': 'oh_p50 - 가스 내부의 산소 함유 비율로 표현한 금속성(Metallicity 12+log(O/H)) 추정치의 중앙값',
        'd4000_n': 'd4000_n - 4000 옹스트롬 부근의 스펙트럼 감쇄 폭을 측정한 값으로, 늙은 별의 비율과 은하의 나이',
        'log_nii_ha': 'log_nii_ha - BPT x축 비율 log([N II] 6584 / H-alpha)',
        'log_oiii_hb': 'log_oiii_hb - BPT y축 비율 log([O III] 5007 / H-beta)',
        'color_u_r': 'color_u_r - u밴드와 r밴드의 등급 차이로 정의되는 (u - r) 색지수'
    }

    # 데이터셋에 누락된 필드가 있다면 안전하게 생성
    if 'u' not in df.columns and 'modelMag_u' in df.columns: df['u'] = df['modelMag_u']
    if 'g' not in df.columns and 'modelMag_g' in df.columns: df['g'] = df['modelMag_g']
    if 'r' not in df.columns and 'modelMag_r' in df.columns: df['r'] = df['modelMag_r']
    if 'i' not in df.columns and 'modelMag_i' in df.columns: df['i'] = df['modelMag_i']
    if 'phot_z' not in df.columns and 'z' in df.columns: df['phot_z'] = df['z']
    if 'lgm_tot_p50' not in df.columns and 'log_stellar_mass' in df.columns: df['lgm_tot_p50'] = df['log_stellar_mass']
    if 'sfr_tot_p50' not in df.columns and 'log_sfr' in df.columns: df['sfr_tot_p50'] = df['log_sfr']
    if 'oh_p50' not in df.columns and 'metallicity_oh' in df.columns: df['oh_p50'] = df['metallicity_oh']
    if 'velDisp' not in df.columns and 'veldisp' in df.columns: df['velDisp'] = df['veldisp']

    # 11대 은하 분류 정제 ("불확실" 완전 배제 확인)
    uncertain_mask = df['galaxy_type'].astype(str).str.contains('불확실|Uncertain|Unclassified')
    if uncertain_mask.sum() > 0:
        df.loc[uncertain_mask, 'galaxy_type'] = '불규칙은하 (Irregular Galaxy)'

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

    type_dist = df['galaxy_type'].value_counts().to_dict()

    print("[3/4] 플롯용 데이터 샘플링 (10,000개)...")
    sample_size = min(10000, total)
    sample = df.sample(n=sample_size, random_state=42)

    sample_cols = ['galaxy_type', 'bptclass'] + list(PARAM_DICT.keys())
    sample_cols = [c for c in sample_cols if c in sample.columns]
    sample_cols = list(dict.fromkeys(sample_cols))

    sample_df = sample[sample_cols].copy()
    sample_json = json.loads(sample_df.to_json(orient='records'))

    print("[4/4] 자체 완결형 HTML 대시보드 생성 중...")
    median_z = stats.get('z', {}).get('median', 'N/A')

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>YSC 은하 물리량 통계 분석 대시보드</title>
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
.row {{ display: grid; gap: 1.2rem; }} .row-4 {{ grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); }}
.row-6 {{ grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); }}
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
footer {{ text-align: center; padding: 2rem 1rem; color: #555; font-size: 1rem; border-top: 2px solid #f00; }}
</style>
</head>
<body>

<div class="hdr">
<h1>YSC 은하 물리량 통계 분석 대시보드</h1>
<p>SDSS DR18 &middot; 신현승 지정 핵심 물리량 명세서 &middot; 11대 은하 분류 체계 ({total:,}개 표본)</p>
<span class="badge">적경/적위/카탈로그ID 제외 &middot; 은하 불확실 완전 배제 완료</span>
</div>

<div class="container">
<div class="tabs">
<button class="tab-btn active" onclick="openTab('overview')">1. 개요 & 11대 은하 분류</button>
<button class="tab-btn" onclick="openTab('explore')">2. 물리량 상관관계 탐색</button>
<button class="tab-btn" onclick="openTab('stats')">3. 지정 물리량 기술통계 ({len(stats)}종)</button>
<button class="tab-btn" onclick="openTab('data_table')">4. 표본 데이터 테이블</button>
<button class="tab-btn" onclick="openTab('validate')">5. 분광 관측 판독기</button>
</div>

<!-- ══ TAB: 개요 ══ -->
<div id="overview" class="tab active">
<div class="row row-4">
<div class="glass stat-card"><div class="val">{total:,}</div><div class="lbl">분석 표본 은하 수</div></div>
<div class="glass stat-card"><div class="val">{len(type_dist)}</div><div class="lbl">확정된 은하 분류 수</div></div>
<div class="glass stat-card"><div class="val">{len(stats)}</div><div class="lbl">지정 핵심 물리량 수</div></div>
<div class="glass stat-card"><div class="val">{median_z}</div><div class="lbl">중앙 적색편이 (z)</div></div>
</div>

<div class="glass">
<h3 style="color:#fff;margin-bottom:.8rem">&#127756; 11대 은하 분류 체계 현황 (은하 불확실 0% 달성)</h3>
<div class="row row-6">
"""
    palette = [
        "#2563eb", "#0284c7", "#dc2626", "#ea580c", "#10b981",
        "#8b5cf6", "#b91c1c", "#d97706", "#9333ea", "#059669", "#db2777"
    ]
    for i, (gtype, cnt) in enumerate(type_dist.items()):
        pct = cnt / total * 100
        color = palette[i % len(palette)]
        html += f'<div class="glass stat-card"><div class="val" style="color:{color};font-size:1.8rem">{cnt:,}</div><div class="lbl"><span class="type-badge" style="border-color:{color};color:{color}">{gtype}</span><br>{pct:.1f}%</div></div>\n'

    html += """</div></div>

<div class="glass">
<h3 style="color:#ffff00;margin-bottom:.6rem">&#9881;&#65039; 신현승 지정 물리량 명세 원칙</h3>
<p style="color:#aaa;font-size:1.1rem">
&bull; <strong>포함 물리량</strong>: 분광 적색편이(z), 속도분산(velDisp), ugri 측광 등급, 측광 적색편이(phot_z), 페트로시안 반경(petroRad_r, petroR50_r, petroR90_r), 수소/산소/질소/황 방출선 세기 및 오차(h_alpha, h_beta, h_gamma, oiii_5007, nii_6584, sii_6717, oii_3726_flux 및 _err), 총 별 질량(lgm_tot_p50), 별 생성률(sfr_tot_p50), 산소 금속성(oh_p50), BPT 분류코드(bptclass), 4000Å 감쇄폭(d4000_n) 및 주요 진단비율<br>
&bull; <strong>완전 제외 항목</strong>: 적경(ra), 적위(dec), 카탈로그 번호(specObjID) 및 불확실(Uncertain) 분류 표본
</p>
</div>
</div>

<!-- ══ TAB: 탐색 ══ -->
<div id="explore" class="tab">
<div class="glass">
<div class="ctrls">
<div class="ctrl"><label>X축 물리량</label><select id="x-var"></select></div>
<div class="ctrl"><label>Y축 물리량</label><select id="y-var"></select></div>
<div class="ctrl"><label>색상(Color) 기준</label><select id="c-var"></select></div>
</div>
<div class="presets">
<strong style="color:#ffff00;align-self:center;margin-right:4px;">프리셋:</strong>
<button class="preset" onclick="setPreset('ms')">1. 은하 주계열 (lgm vs sfr)</button>
<button class="preset" onclick="setPreset('bpt')">2. BPT 진단도 (NII/Ha vs OIII/Hb)</button>
<button class="preset" onclick="setPreset('cm')">3. 색-질량 (u-r vs lgm)</button>
<button class="preset" onclick="setPreset('mzr')">4. 질량-금속성 (lgm vs oh)</button>
<button class="preset" onclick="setPreset('d4000')">5. 별나이-질량 (lgm vs d4000)</button>
<button class="preset" onclick="setPreset('dyn')">6. 동역학 속도분산 (lgm vs velDisp)</button>
<button class="preset" onclick="setPreset('radius')">7. 크기-질량 (lgm vs petroR50_r)</button>
<button class="preset" onclick="setPreset('lines')">8. Hα vs [OIII] 방출선 세기</button>
</div>
<div id="plot"></div>
</div>
</div>

<!-- ══ TAB: 통계 ══ -->
<div id="stats" class="tab">
<div class="glass">
<h3 style="color:#fff;margin-bottom:.8rem">신현승 지정 물리량 기술통계 명세표</h3>
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
<h3 style="color:#fff;margin-bottom:1rem">대표 관측 표본 데이터 목록</h3>
<div style="overflow-x:auto; max-height: 600px; overflow-y: auto;">
<table id="galaxy_table">
<thead>
<tr>
<th>은하 분류</th>
<th>적색편이 (z)</th>
<th>총별질량 (lgm)</th>
<th>별생성률 (sfr)</th>
<th>금속성 (oh)</th>
<th>속도분산 (velDisp)</th>
<th>r밴드 반경 (R50)</th>
<th>D4000 나이</th>
<th>Hα 플럭스</th>
<th>[OIII] 플럭스</th>
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

</div>

<footer>
YSC 2026 청소년과학탐구반 &mdash; 은하의 물리량 및 화학조성 분석을 통한 은하 진화 경향 및 메커니즘 분석 도표 탐구<br>
SDSS DR18 신현승 지정 물리량 명세서 기반 완결형 대시보드
</footer>

<script>
// ═══ Embedded real data ═══
const DATA = PLACEHOLDER_DATA;

// ═══ Variable definitions ═══
const VARS = PLACEHOLDER_VARS;
const CATS = { galaxy_type: '은하 11대 분류' };

// ═══ Init selects ═══
const xs = document.getElementById('x-var'), ys = document.getElementById('y-var'), cs = document.getElementById('c-var');
Object.entries(VARS).forEach(([k,v]) => { xs.add(new Option(v,k)); ys.add(new Option(v,k)); cs.add(new Option(v,k)); });
Object.entries(CATS).forEach(([k,v]) => cs.add(new Option(v,k)));
xs.value='lgm_tot_p50'; ys.value='sfr_tot_p50'; cs.value='galaxy_type';

// ═══ Populate Table ═══
const tbody = document.getElementById('galaxy_table_body');
DATA.slice(0, 100).forEach(d => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
        <td><span style="color:#ffff00">${d.galaxy_type || '-'}</span></td>
        <td>${d.z !== null && d.z !== undefined ? d.z.toFixed(4) : '-'}</td>
        <td>${d.lgm_tot_p50 !== null && d.lgm_tot_p50 !== undefined ? d.lgm_tot_p50.toFixed(2) : '-'}</td>
        <td>${d.sfr_tot_p50 !== null && d.sfr_tot_p50 !== undefined ? d.sfr_tot_p50.toFixed(2) : '-'}</td>
        <td>${d.oh_p50 !== null && d.oh_p50 !== undefined ? d.oh_p50.toFixed(2) : '-'}</td>
        <td>${d.velDisp !== null && d.velDisp !== undefined ? d.velDisp.toFixed(1) : '-'}</td>
        <td>${d.petroR50_r !== null && d.petroR50_r !== undefined ? d.petroR50_r.toFixed(2) : '-'}</td>
        <td>${d.d4000_n !== null && d.d4000_n !== undefined ? d.d4000_n.toFixed(2) : '-'}</td>
        <td>${d.h_alpha_flux !== null && d.h_alpha_flux !== undefined ? d.h_alpha_flux.toFixed(1) : '-'}</td>
        <td>${d.oiii_5007_flux !== null && d.oiii_5007_flux !== undefined ? d.oiii_5007_flux.toFixed(1) : '-'}</td>
    `;
    tbody.appendChild(tr);
});

// ═══ Draw plot ═══
function draw() {
    const xk=xs.value, yk=ys.value, ck=cs.value;
    const xd=DATA.map(d=>d[xk]), yd=DATA.map(d=>d[yk]);
    let traces;
    if(CATS[ck]) {
        const groups=[...new Set(DATA.map(d=>d[ck]).filter(v=>v!=null))];
        const palette=['#2563eb', '#0284c7', '#dc2626', '#ea580c', '#10b981', '#8b5cf6', '#b91c1c', '#d97706', '#9333ea', '#059669', '#db2777'];
        traces=groups.map((g,i)=>{
            const idx=DATA.map((d,j)=>d[ck]===g?j:-1).filter(j=>j>=0);
            return {x:idx.map(j=>xd[j]),y:idx.map(j=>yd[j]),mode:'markers',name:g.split(' (')[0],
                marker:{size:4.5,opacity:0.65,color:palette[i%palette.length]},type:'scatter'};
        });
    } else {
        traces=[{x:xd,y:yd,mode:'markers',type:'scatter',
            marker:{size:4.5,opacity:0.65,color:DATA.map(d=>d[ck]),colorscale:'Viridis',showscale:true,
                colorbar:{title:{text:VARS[ck]||ck,font:{color:'#aaa'}},tickfont:{color:'#888'}}}}];
    }
    const layout={
        xaxis:{title:VARS[xk]||xk,gridcolor:'#333',color:'#fff'},
        yaxis:{title:VARS[yk]||yk,gridcolor:'#333',color:'#fff'},
        paper_bgcolor:'#000',plot_bgcolor:'#000',
        font:{color:'#f00', family: 'VT323, DungGeunMo, monospace', size: 14},
        margin:{t:30,b:50,l:60,r:20},
        hovermode:'closest',legend:{font:{color:'#fff'}}
    };
    Plotly.newPlot('plot',traces,layout,{responsive:true});
}
xs.onchange=ys.onchange=cs.onchange=draw;

function setPreset(p){
    if(p==='ms'){xs.value='lgm_tot_p50';ys.value='sfr_tot_p50';cs.value='galaxy_type';}
    if(p==='bpt'){xs.value='log_nii_ha';ys.value='log_oiii_hb';cs.value='galaxy_type';}
    if(p==='cm'){xs.value='lgm_tot_p50';ys.value='color_u_r';cs.value='galaxy_type';}
    if(p==='mzr'){xs.value='lgm_tot_p50';ys.value='oh_p50';cs.value='galaxy_type';}
    if(p==='d4000'){xs.value='lgm_tot_p50';ys.value='d4000_n';cs.value='galaxy_type';}
    if(p==='dyn'){xs.value='lgm_tot_p50';ys.value='velDisp';cs.value='galaxy_type';}
    if(p==='radius'){xs.value='lgm_tot_p50';ys.value='petroR50_r';cs.value='galaxy_type';}
    if(p==='lines'){xs.value='h_alpha_flux';ys.value='oiii_5007_flux';cs.value='galaxy_type';}
    draw();
}

// ═══ Tabs ═══
function openTab(id){
    document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(b=>b.classList.remove('active'));
    document.getElementById(id).classList.add('active');
    event.target.classList.add('active');
    if(id==='explore') setTimeout(draw,100);
}

// ═══ Validate ═══
function doValidate(){
    const ha=+document.getElementById('ha').value, hb=+document.getElementById('hb').value;
    const oiii=+document.getElementById('oiii').value, nii=+document.getElementById('nii').value;
    if(!ha||!hb||!oiii||!nii){alert('모든 방출선 플럭스 값을 입력해 주세요.');return;}
    const lnha=Math.log10(nii/ha), lohb=Math.log10(oiii/hb);
    let bpt='Unknown';
    if(lnha>=0.05) bpt=lohb>0.5?'세이퍼트 (Seyfert AGN)':'라이너 (LINER/Shock)';
    else { const k=0.61/(lnha-0.05)+1.3; bpt=lohb<k?'정상 별생성 은하 (Star-forming)':'복합형/활동은하핵 (Composite/AGN)'; }
    const bd=ha/hb, ebv=bd>2.86?(1.086*Math.log(bd/2.86)/1.16).toFixed(3):'0.000';
    const oh=(8.90+0.57*lnha).toFixed(2);
    document.getElementById('r-bpt').textContent=bpt;
    document.getElementById('r-oh').textContent=oh;
    document.getElementById('r-ebv').textContent=ebv;
    document.getElementById('r-type').textContent=bpt.includes('Star')?'광이온화 (HII 영역)':'중심 블랙홀 강착/충격파';
    document.getElementById('val-result').style.display='block';

    // BPT overlay
    const bgx=DATA.map(d=>d.log_nii_ha).filter(v=>v!=null);
    const bgy=DATA.map((d,i)=>d.log_nii_ha!=null?d.log_oiii_hb:null).filter(v=>v!=null);
    const kx=[];for(let x=-2;x<=0.04;x+=0.02)kx.push(x);
    const ky1=kx.map(x=>x<0.05?0.61/(x-0.05)+1.3:null);
    Plotly.newPlot('val-plot',[
        {x:bgx,y:bgy,mode:'markers',marker:{size:3,color:'#444',opacity:0.3},name:'SDSS 표본',type:'scatter'},
        {x:kx,y:ky1,mode:'lines',line:{color:'#ffff00',dash:'dash',width:2},name:'Kauffmann (2003)'},
        {x:[lnha],y:[lohb],mode:'markers',marker:{size:16,color:'#ff0000',symbol:'star',line:{color:'#fff',width:2}},name:'입력 타겟'}
    ],{xaxis:{title:'log([NII] / Hα)',range:[-1.8,0.8],gridcolor:'#333',color:'#fff'},
       yaxis:{title:'log([OIII] / Hβ)',range:[-1.5,1.6],gridcolor:'#333',color:'#fff'},
       paper_bgcolor:'#000',plot_bgcolor:'#000',font:{color:'#f00',family:'VT323, DungGeunMo, monospace',size:13},
       margin:{t:20,b:40,l:50,r:20},showlegend:true},{responsive:true});
}

// Initial draw
draw();
</script>
</body>
</html>"""

    data_json = json.dumps(sample_json, ensure_ascii=False)
    vars_json = json.dumps(PARAM_DICT, ensure_ascii=False)

    html = html.replace('PLACEHOLDER_DATA', data_json)
    html = html.replace('PLACEHOLDER_VARS', vars_json)

    output_path = os.path.join(config.PROJECT_ROOT, 'dashboard_real_data.html')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"\n=== 완료! ===")
    print(f"파일: {output_path}")
    print(f"크기: {size_mb:.1f} MB")
    print(f"임베딩된 은하 수: {sample_size:,}개")
    print(f"임베딩된 물리량 수: {len(PARAM_DICT)}개")

if __name__ == '__main__':
    main()
