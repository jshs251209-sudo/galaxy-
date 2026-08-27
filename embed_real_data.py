"""
실제 시뮬레이션 결과를 자체 완결형 HTML 대시보드에 임베딩하는 스크립트.
서버 없이 브라우저에서 바로 열 수 있는 단일 HTML 파일을 생성합니다.
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

    # ── 통계 요약 ──
    print("[2/4] 통계 요약 계산 중...")
    stats = {}
    for col in ['log_stellar_mass', 'log_sfr', 'metallicity_oh', 'g_r', 'u_g',
                'veldisp', 'z', 'concentration_index', 'dust_ebv',
                'dark_matter_fraction', 'log_dyn_mass']:
        if col in df.columns:
            s = df[col].dropna()
            stats[col] = {
                'mean': round(float(s.mean()), 4),
                'median': round(float(s.median()), 4),
                'std': round(float(s.std()), 4),
                'min': round(float(s.min()), 4),
                'max': round(float(s.max()), 4),
                'count': int(s.count()),
            }

    # 은하 유형 분포
    type_dist = {}
    if 'galaxy_type' in df.columns:
        type_dist = df['galaxy_type'].value_counts().to_dict()

    # ML 군집 분포
    cluster_dist = {}
    if 'cluster_name' in df.columns:
        cluster_dist = df['cluster_name'].value_counts().to_dict()

    # ── 플롯용 샘플 데이터 (5000개) ──
    print("[3/4] 플롯용 데이터 샘플링 (5,000개)...")
    sample_size = min(5000, total)
    sample = df.sample(n=sample_size, random_state=42)

    # 필요한 컬럼만 추출 & NaN을 null로
    plot_cols = [
        'log_stellar_mass', 'log_sfr', 'metallicity_oh',
        'g_r', 'u_g', 'veldisp', 'z',
        'log_nii_ha', 'log_oiii_hb',
        'concentration_index', 'dust_ebv',
        'dark_matter_fraction', 'log_dyn_mass',
        'galaxy_type'
    ]
    if 'cluster_name' in sample.columns:
        plot_cols.append('cluster_name')

    available_cols = [c for c in plot_cols if c in sample.columns]
    sample_df = sample[available_cols].copy()
    # NaN -> None for JSON
    sample_json = json.loads(sample_df.to_json(orient='records'))

    # ── HTML 생성 ──
    print("[4/4] 자체 완결형 HTML 생성 중...")

    median_z = stats.get('z', {}).get('median', 'N/A')

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>YSC 은하 진화 대시보드 (실제 데이터)</title>
<script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>
<style>
:root {{
    --bg: #080c1a; --card: rgba(14,20,48,.7); --border: rgba(80,140,220,.2);
    --text: #dce3ed; --muted: #7e8faa; --blue: #60b3f7; --purple: #b388ff;
    --gold: #ffd54f; --green: #66d9a0; --red: #ff7043;
}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:var(--bg);color:var(--text);font-family:'Segoe UI','Malgun Gothic',sans-serif;line-height:1.6}}
.hdr{{text-align:center;padding:2.5rem 1rem 1.5rem;background:rgba(0,0,0,.3)}}
.hdr h1{{font-size:2.2rem;font-weight:800;background:linear-gradient(135deg,#60b3f7,#a873e8);-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
.hdr p{{color:var(--muted);margin-top:.4rem}}
.badge{{display:inline-block;background:rgba(102,217,160,.12);border:1px solid rgba(102,217,160,.3);padding:.2rem .7rem;border-radius:14px;font-size:.82rem;color:var(--green);margin-top:.6rem}}
.container{{max-width:1300px;margin:0 auto;padding:1.5rem}}
.tabs{{display:flex;gap:.6rem;flex-wrap:wrap;justify-content:center;margin-bottom:1.5rem}}
.tab-btn{{background:rgba(255,255,255,.04);border:1px solid var(--border);color:var(--text);padding:.55rem 1.4rem;border-radius:24px;font-weight:600;cursor:pointer;transition:.25s;font-family:inherit;font-size:.92rem}}
.tab-btn:hover{{background:rgba(96,179,247,.15)}}
.tab-btn.active{{background:var(--blue);color:#000;box-shadow:0 0 14px rgba(96,179,247,.4)}}
.tab{{display:none;animation:fadeIn .35s}}.tab.active{{display:block}}
@keyframes fadeIn{{from{{opacity:0;transform:translateY(8px)}}to{{opacity:1;transform:translateY(0)}}}}
.glass{{background:var(--card);border:1px solid var(--border);border-radius:14px;padding:1.4rem;margin-bottom:1.2rem}}
.row{{display:grid;gap:1.2rem}}.row-4{{grid-template-columns:repeat(auto-fit,minmax(200px,1fr))}}
.stat-card{{text-align:center;padding:1.2rem}}.stat-card .val{{font-size:2rem;font-weight:800;color:var(--blue)}}.stat-card .lbl{{color:var(--muted);font-size:.88rem;margin-top:.3rem}}
.ctrls{{display:flex;gap:1rem;flex-wrap:wrap;margin-bottom:1rem}}
.ctrl{{flex:1;min-width:180px}}
.ctrl label{{display:block;color:var(--blue);font-weight:600;font-size:.85rem;margin-bottom:.3rem}}
select{{width:100%;padding:.55rem;border-radius:8px;border:1px solid var(--border);background:rgba(0,0,0,.3);color:#fff;font-family:inherit}}
.presets{{display:flex;gap:.7rem;flex-wrap:wrap;margin-bottom:1rem}}
.preset{{background:transparent;border:1px solid var(--purple);color:var(--purple);padding:.4rem 1.1rem;border-radius:18px;cursor:pointer;transition:.2s;font-family:inherit;font-size:.88rem}}
.preset:hover{{background:var(--purple);color:#000}}
#plot{{height:62vh;min-height:480px}}
table{{width:100%;border-collapse:collapse}}
th,td{{text-align:left;padding:.6rem .8rem;border-bottom:1px solid rgba(255,255,255,.05);font-size:.9rem}}
th{{color:var(--blue);font-weight:600;white-space:nowrap}}
td{{color:var(--muted)}}
.type-badge{{display:inline-block;padding:.15rem .6rem;border-radius:10px;font-size:.8rem;font-weight:600}}
.type-e{{background:rgba(255,112,67,.15);color:var(--red)}}
.type-s{{background:rgba(96,179,247,.15);color:var(--blue)}}
footer{{text-align:center;padding:2rem 1rem;color:#334;font-size:.82rem;border-top:1px solid rgba(255,255,255,.04)}}
</style>
</head>
<body>

<div class="hdr">
<h1>YSC 은하 진화 대시보드</h1>
<p>SDSS DR18 실제 관측 데이터 기반 &mdash; 총 {total:,}개 은하 분석 결과</p>
<span class="badge">실제 데이터 임베딩 완료 (샘플 {sample_size:,}개 시각화)</span>
</div>

<div class="container">
<div class="tabs">
<button class="tab-btn active" onclick="openTab('overview')">개요</button>
<button class="tab-btn" onclick="openTab('explore')">탐색</button>
<button class="tab-btn" onclick="openTab('stats')">통계</button>
<button class="tab-btn" onclick="openTab('validate')">판독기</button>
</div>

<!-- ══ TAB: 개요 ══ -->
<div id="overview" class="tab active">
<div class="row row-4">
<div class="glass stat-card"><div class="val">{total:,}</div><div class="lbl">분석된 은하 수</div></div>
<div class="glass stat-card"><div class="val">{len(type_dist)}</div><div class="lbl">은하 유형 분류</div></div>
<div class="glass stat-card"><div class="val">{len(cluster_dist)}</div><div class="lbl">ML 군집 수</div></div>
<div class="glass stat-card"><div class="val">{median_z}</div><div class="lbl">중앙 적색편이</div></div>
</div>

<div class="glass">
<h3 style="color:#fff;margin-bottom:.8rem">은하 유형 분포</h3>
<div class="row row-4">
"""
    for gtype, cnt in type_dist.items():
        pct = cnt / total * 100
        badge_cls = 'type-e' if '타원' in gtype else 'type-s'
        html += f'<div class="glass stat-card"><div class="val">{cnt:,}</div><div class="lbl"><span class="type-badge {badge_cls}">{gtype}</span><br>{pct:.1f}%</div></div>\n'

    html += """</div></div>

<div class="glass">
<h3 style="color:#fff;margin-bottom:.8rem">ML 군집 분포</h3>
<div class="row row-4">
"""
    colors_ml = ['var(--blue)', 'var(--green)', 'var(--gold)', 'var(--red)', 'var(--purple)']
    for i, (cname, cnt) in enumerate(cluster_dist.items()):
        pct = cnt / total * 100
        c = colors_ml[i % len(colors_ml)]
        html += f'<div class="glass stat-card"><div class="val" style="color:{c}">{cnt:,}</div><div class="lbl">{cname}<br>{pct:.1f}%</div></div>\n'

    html += """</div></div>
</div>

<!-- ══ TAB: 탐색 ══ -->
<div id="explore" class="tab">
<div class="glass">
<div class="ctrls">
<div class="ctrl"><label>X축</label><select id="x-var"></select></div>
<div class="ctrl"><label>Y축</label><select id="y-var"></select></div>
<div class="ctrl"><label>색상</label><select id="c-var"></select></div>
</div>
<div class="presets">
<button class="preset" onclick="setPreset('ms')">주계열</button>
<button class="preset" onclick="setPreset('bpt')">BPT</button>
<button class="preset" onclick="setPreset('cm')">색-질량</button>
<button class="preset" onclick="setPreset('mzr')">질량-금속성</button>
<button class="preset" onclick="setPreset('dm')">암흑물질</button>
</div>
<div id="plot"></div>
</div>
</div>

<!-- ══ TAB: 통계 ══ -->
<div id="stats" class="tab">
<div class="glass">
<h3 style="color:#fff;margin-bottom:.8rem">주요 변수 기술통계</h3>
<div style="overflow-x:auto">
<table>
<tr><th>변수</th><th>평균</th><th>중앙값</th><th>표준편차</th><th>최소</th><th>최대</th><th>유효 수</th></tr>
"""
    col_labels = {
        'log_stellar_mass': '항성 질량 (log M/M_sun)',
        'log_sfr': '별 생성률 (log SFR)',
        'metallicity_oh': '금속성 (12+log(O/H))',
        'g_r': 'g-r 색지수',
        'u_g': 'u-g 색지수',
        'veldisp': '속도 분산 (km/s)',
        'z': '적색편이',
        'concentration_index': '집중도 지수',
        'dust_ebv': '먼지 소광 E(B-V)',
        'dark_matter_fraction': '암흑물질 비율',
        'log_dyn_mass': '동역학적 질량 (log)',
    }
    for col, s in stats.items():
        label = col_labels.get(col, col)
        html += f"<tr><td>{label}</td><td>{s['mean']}</td><td>{s['median']}</td><td>{s['std']}</td><td>{s['min']}</td><td>{s['max']}</td><td>{s['count']:,}</td></tr>\n"

    html += """</table></div></div></div>

<!-- ══ TAB: 판독기 ══ -->
<div id="validate" class="tab">
<div class="glass">
<h3 style="color:#fff;margin-bottom:.6rem">은하 관측값 판독기</h3>
<p style="color:var(--muted);margin-bottom:1rem">방출선 플럭스를 입력하면 BPT 분류, 금속성, 먼지 소광을 자동 계산합니다.</p>
<div class="ctrls">
<div class="ctrl"><label>H-alpha Flux</label><input type="number" id="ha" step="any" placeholder="120.5"></div>
<div class="ctrl"><label>H-beta Flux</label><input type="number" id="hb" step="any" placeholder="42.1"></div>
<div class="ctrl"><label>[OIII] 5007 Flux</label><input type="number" id="oiii" step="any" placeholder="35.8"></div>
<div class="ctrl"><label>[NII] 6584 Flux</label><input type="number" id="nii" step="any" placeholder="45.2"></div>
</div>
<button class="preset" style="border-color:var(--gold);color:var(--gold);font-size:1rem;padding:.6rem 2rem" onclick="doValidate()">분석하기</button>
<div id="val-result" style="display:none;margin-top:1.2rem">
<div class="row row-4">
<div class="glass stat-card"><div class="val" id="r-bpt">-</div><div class="lbl">BPT 분류</div></div>
<div class="glass stat-card"><div class="val" id="r-oh">-</div><div class="lbl">금속성 (12+log O/H)</div></div>
<div class="glass stat-card"><div class="val" id="r-ebv">-</div><div class="lbl">먼지 소광 E(B-V)</div></div>
<div class="glass stat-card"><div class="val" id="r-type">-</div><div class="lbl">예측 유형</div></div>
</div>
<div id="val-plot" style="height:350px;margin-top:1rem"></div>
</div>
</div>
</div>

</div>

<footer>
YSC 2026 과학탐구 대회 &mdash; 은하 진화 다차원 분석 프로젝트<br>
이 파일은 실제 SDSS DR18 데이터가 임베딩되어 있어 서버 없이 오프라인에서 열 수 있습니다.
</footer>

<script>
// ═══ Embedded real data ═══
const DATA = PLACEHOLDER_DATA;

// ═══ Variable definitions ═══
const VARS = {
    log_stellar_mass: '항성 질량 (log M/M_sun)',
    log_sfr: '별 생성률 (log SFR)',
    metallicity_oh: '금속성 (12+log O/H)',
    g_r: 'g-r 색지수',
    u_g: 'u-g 색지수',
    veldisp: '속도 분산 (km/s)',
    z: '적색편이',
    log_nii_ha: 'log([NII]/Ha)',
    log_oiii_hb: 'log([OIII]/Hb)',
    concentration_index: '집중도 지수',
    dust_ebv: '먼지 소광 E(B-V)',
    dark_matter_fraction: '암흑물질 비율',
    log_dyn_mass: '동역학적 질량 (log)'
};
const CATS = { galaxy_type: '은하 유형', cluster_name: 'ML 군집' };

// ═══ Init selects ═══
const xs = document.getElementById('x-var'), ys = document.getElementById('y-var'), cs = document.getElementById('c-var');
Object.entries(VARS).forEach(([k,v]) => { xs.add(new Option(v,k)); ys.add(new Option(v,k)); cs.add(new Option(v,k)); });
Object.entries(CATS).forEach(([k,v]) => cs.add(new Option(v,k)));
xs.value='log_stellar_mass'; ys.value='log_sfr'; cs.value='galaxy_type';

// ═══ Draw plot ═══
function draw() {
    const xk=xs.value, yk=ys.value, ck=cs.value;
    const xd=DATA.map(d=>d[xk]), yd=DATA.map(d=>d[yk]);
    let traces;
    if(CATS[ck]) {
        const groups=[...new Set(DATA.map(d=>d[ck]).filter(v=>v!=null))];
        const palette=['#60b3f7','#ff7043','#66d9a0','#ffd54f','#b388ff','#ff80ab'];
        traces=groups.map((g,i)=>{
            const idx=DATA.map((d,j)=>d[ck]===g?j:-1).filter(j=>j>=0);
            return {x:idx.map(j=>xd[j]),y:idx.map(j=>yd[j]),mode:'markers',name:g,
                marker:{size:4,opacity:.7,color:palette[i%palette.length]},type:'scatter'};
        });
    } else {
        traces=[{x:xd,y:yd,mode:'markers',type:'scatter',
            marker:{size:4,opacity:.7,color:DATA.map(d=>d[ck]),colorscale:'Viridis',showscale:true,
                colorbar:{title:{text:VARS[ck]||ck,font:{color:'#aaa'}},tickfont:{color:'#888'}}}}];
    }
    const layout={
        xaxis:{title:VARS[xk]||xk,gridcolor:'#1a2040',color:'#8aa'},
        yaxis:{title:VARS[yk]||yk,gridcolor:'#1a2040',color:'#8aa'},
        paper_bgcolor:'rgba(0,0,0,0)',plot_bgcolor:'rgba(0,0,0,0)',
        font:{color:'#c0c8d8'},margin:{t:30,b:50,l:60,r:20},
        hovermode:'closest',legend:{font:{color:'#aab'}}
    };
    Plotly.newPlot('plot',traces,layout,{responsive:true});
}
xs.onchange=ys.onchange=cs.onchange=draw;

function setPreset(p){
    if(p==='ms'){xs.value='log_stellar_mass';ys.value='log_sfr';cs.value='cluster_name';}
    if(p==='bpt'){xs.value='log_nii_ha';ys.value='log_oiii_hb';cs.value='galaxy_type';}
    if(p==='cm'){xs.value='log_stellar_mass';ys.value='g_r';cs.value='galaxy_type';}
    if(p==='mzr'){xs.value='log_stellar_mass';ys.value='metallicity_oh';cs.value='log_sfr';}
    if(p==='dm'){xs.value='log_stellar_mass';ys.value='dark_matter_fraction';cs.value='galaxy_type';}
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
    if(!ha||!hb||!oiii||!nii){alert('모든 값을 입력해 주세요.');return;}
    const lnha=Math.log10(nii/ha), lohb=Math.log10(oiii/hb);
    let bpt='Unknown';
    if(lnha>=0.05) bpt=lohb>0.5?'AGN (Seyfert)':'LINER';
    else { const k=0.61/(lnha-0.05)+1.3; bpt=lohb<k?'Star-forming':'AGN/Composite'; }
    const bd=ha/hb, ebv=bd>2.86?(1.086*Math.log(bd/2.86)/1.16).toFixed(3):'0.000';
    const oh=(8.90+0.57*lnha).toFixed(2);
    document.getElementById('r-bpt').textContent=bpt;
    document.getElementById('r-oh').textContent=oh;
    document.getElementById('r-ebv').textContent=ebv;
    document.getElementById('r-type').textContent=bpt.includes('Star')?'Active SF':'Quenched/AGN';
    document.getElementById('val-result').style.display='block';
    // BPT overlay
    const bgx=DATA.map(d=>d.log_nii_ha).filter(v=>v!=null);
    const bgy=DATA.map((d,i)=>d.log_nii_ha!=null?d.log_oiii_hb:null).filter(v=>v!=null);
    const kx=[];for(let x=-2;x<=0.4;x+=0.02)kx.push(x);
    const ky1=kx.map(x=>x<0.05?0.61/(x-0.05)+1.3:null);
    Plotly.newPlot('val-plot',[
        {x:bgx,y:bgy,mode:'markers',marker:{size:2,color:'#334',opacity:.3},name:'Background',type:'scatter'},
        {x:kx,y:ky1,mode:'lines',line:{color:'#fff',dash:'dash',width:1.5},name:'Kauffmann 2003'},
        {x:[lnha],y:[lohb],mode:'markers',marker:{size:14,color:'#ff7043',symbol:'star'},name:'Target'}
    ],{xaxis:{title:'log([NII]/Ha)',range:[-2,1],gridcolor:'#1a2040',color:'#8aa'},
       yaxis:{title:'log([OIII]/Hb)',range:[-1.5,1.5],gridcolor:'#1a2040',color:'#8aa'},
       paper_bgcolor:'rgba(0,0,0,0)',plot_bgcolor:'rgba(0,0,0,0)',font:{color:'#c0c8d8'},
       margin:{t:20,b:40,l:50,r:20},showlegend:false},{responsive:true});
}

// Initial draw
draw();
</script>
</body>
</html>"""

    # JSON 데이터를 placeholder에 삽입
    data_json = json.dumps(sample_json, ensure_ascii=False)
    html = html.replace('PLACEHOLDER_DATA', data_json)

    # 저장
    output_path = os.path.join(config.PROJECT_ROOT, 'dashboard_real_data.html')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"\n=== 완료! ===")
    print(f"파일: {output_path}")
    print(f"크기: {size_mb:.1f} MB")
    print(f"임베딩된 은하 수: {sample_size:,}개 (전체 {total:,}개 중 샘플)")
    print(f"서버 없이 이 파일을 더블클릭하여 브라우저에서 열 수 있습니다.")

if __name__ == '__main__':
    main()
