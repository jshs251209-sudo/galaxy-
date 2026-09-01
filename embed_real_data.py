"""
실제 SDSS 200개 물리량 & 11대 은하 분류 데이터를 자체 완결형 HTML 대시보드에 임베딩하는 스크립트.
- 신현승 요구사항 100% 반영:
  1. Teams에 올린 200개 물리량 중 적경(ra), 적위(dec), 오차값(*err*, *p16*, *p84*)을 제외한 핵심 물리량 전체(130+개) 반영
  2. 11대 은하 분류 체계 (나선, 막대나선, 타원, 렌즈형, 마젤란형, 고리, 전파, 퀘이사, 세이퍼트, 불규칙, 병합) 완벽 반영
  3. 결측치는 NaN/null로 안전하게 처리
  4. 다차원 분석 프리셋 10종 지원
  5. 90년대 아날로그 호러 / 긴급 연구소 테마 완벽 유지
"""
import os
import json
import pandas as pd
import numpy as np
import config

def main():
    print("[1/4] 마스터 데이터셋(200 parameters, 55,000개 표본) 로드 중...")
    df = pd.read_csv(config.MASTER_DATASET_FILE)
    total = len(df)
    print(f"  => 총 {total:,}개 은하 로드 완료")

    # ── 제외할 컬럼 (적경, 적위, 식별자, 오차 컬럼) ──
    exclude_cols = {'ra', 'dec', 'objID', 'specObjID', 'run', 'rerun', 'camcol', 'field', 'plate', 'mjd', 'fiberID', 'zWarning'}

    # 133개 클린 물리량/화학량 변수 정의 및 한국어 라벨링
    PARAM_LABELS = {
        # 분광 및 기본 물리량
        'z': '적색편이 (Redshift z)',
        'velDisp': '속도 분산 (Velocity Dispersion σ_v [km/s])',
        'vdispChi2': '속도분산 피팅 카이자승 (vdisp Chi^2)',
        'snMedian_u': 'u밴드 중앙 S/N 비 (snMedian_u)',
        'snMedian_g': 'g밴드 중앙 S/N 비 (snMedian_g)',
        'snMedian_r': 'r밴드 중앙 S/N 비 (snMedian_r)',
        'snMedian_i': 'i밴드 중앙 S/N 비 (snMedian_i)',
        'snMedian_z': 'z밴드 중앙 S/N 비 (snMedian_z)',

        # 측광 등급 (Photometry Magnitudes)
        'psfMag_u': 'u밴드 점광원 등급 (psfMag_u [mag])',
        'psfMag_g': 'g밴드 점광원 등급 (psfMag_g [mag])',
        'psfMag_r': 'r밴드 점광원 등급 (psfMag_r [mag])',
        'psfMag_i': 'i밴드 점광원 등급 (psfMag_i [mag])',
        'psfMag_z': 'z밴드 점광원 등급 (psfMag_z [mag])',
        'fiberMag_u': 'u밴드 광섬유 내부 등급 (fiberMag_u [mag])',
        'fiberMag_g': 'g밴드 광섬유 내부 등급 (fiberMag_g [mag])',
        'fiberMag_r': 'r밴드 광섬유 내부 등급 (fiberMag_r [mag])',
        'fiberMag_i': 'i밴드 광섬유 내부 등급 (fiberMag_i [mag])',
        'fiberMag_z': 'z밴드 광섬유 내부 등급 (fiberMag_z [mag])',
        'petroMag_u': 'u밴드 페트로시안 등급 (petroMag_u [mag])',
        'petroMag_g': 'g밴드 페트로시안 등급 (petroMag_g [mag])',
        'petroMag_r': 'r밴드 페트로시안 등급 (petroMag_r [mag])',
        'petroMag_i': 'i밴드 페트로시안 등급 (petroMag_i [mag])',
        'petroMag_z': 'z밴드 페트로시안 등급 (petroMag_z [mag])',
        'modelMag_u': 'u밴드 모델 등급 (modelMag_u [mag])',
        'modelMag_g': 'g밴드 모델 등급 (modelMag_g [mag])',
        'modelMag_r': 'r밴드 모델 등급 (modelMag_r [mag])',
        'modelMag_i': 'i밴드 모델 등급 (modelMag_i [mag])',
        'modelMag_z': 'z밴드 모델 등급 (modelMag_z [mag])',
        'cModelMag_u': 'u밴드 복합 모델 등급 (cModelMag_u [mag])',
        'cModelMag_g': 'g밴드 복합 모델 등급 (cModelMag_g [mag])',
        'cModelMag_r': 'r밴드 복합 모델 등급 (cModelMag_r [mag])',
        'cModelMag_i': 'i밴드 복합 모델 등급 (cModelMag_i [mag])',
        'cModelMag_z': 'z밴드 복합 모델 등급 (cModelMag_z [mag])',

        # 성간 소광 (Galactic Extinction)
        'extinction_u': 'u밴드 성간 소광량 (extinction_u [mag])',
        'extinction_g': 'g밴드 성간 소광량 (extinction_g [mag])',
        'extinction_r': 'r밴드 성간 소광량 (extinction_r [mag])',
        'extinction_i': 'i밴드 성간 소광량 (extinction_i [mag])',
        'extinction_z': 'z밴드 성간 소광량 (extinction_z [mag])',

        # 은하 유효반경 및 크기 (Radii & Sizes)
        'petroRad_u': 'u밴드 페트로시안 반경 (petroRad_u [arcsec])',
        'petroRad_g': 'g밴드 페트로시안 반경 (petroRad_g [arcsec])',
        'petroRad_r': 'r밴드 페트로시안 반경 (petroRad_r [arcsec])',
        'petroRad_i': 'i밴드 페트로시안 반경 (petroRad_i [arcsec])',
        'petroRad_z': 'z밴드 페트로시안 반경 (petroRad_z [arcsec])',
        'petroR50_u': 'u밴드 50% 반광반경 (petroR50_u [arcsec])',
        'petroR50_g': 'g밴드 50% 반광반경 (petroR50_g [arcsec])',
        'petroR50_r': 'r밴드 50% 반광반경 (petroR50_r [arcsec])',
        'petroR50_i': 'i밴드 50% 반광반경 (petroR50_i [arcsec])',
        'petroR50_z': 'z밴드 50% 반광반경 (petroR50_z [arcsec])',
        'petroR90_u': 'u밴드 90% 광도반경 (petroR90_u [arcsec])',
        'petroR90_g': 'g밴드 90% 광도반경 (petroR90_g [arcsec])',
        'petroR90_r': 'r밴드 90% 광도반경 (petroR90_r [arcsec])',
        'petroR90_i': 'i밴드 90% 광도반경 (petroR90_i [arcsec])',
        'petroR90_z': 'z밴드 90% 광도반경 (petroR90_z [arcsec])',
        'deVRad_u': 'u밴드 드보클뢰르 유효반경 (deVRad_u [arcsec])',
        'deVRad_g': 'g밴드 드보클뢰르 유효반경 (deVRad_g [arcsec])',
        'deVRad_r': 'r밴드 드보클뢰르 유효반경 (deVRad_r [arcsec])',
        'deVRad_i': 'i밴드 드보클뢰르 유효반경 (deVRad_i [arcsec])',
        'deVRad_z': 'z밴드 드보클뢰르 유효반경 (deVRad_z [arcsec])',
        'expRad_u': 'u밴드 지수형 원반반경 (expRad_u [arcsec])',
        'expRad_g': 'g밴드 지수형 원반반경 (expRad_g [arcsec])',
        'expRad_r': 'r밴드 지수형 원반반경 (expRad_r [arcsec])',
        'expRad_i': 'i밴드 지수형 원반반경 (expRad_i [arcsec])',
        'expRad_z': 'z밴드 지수형 원반반경 (expRad_z [arcsec])',

        # 은하 형상 프로파일 및 축비 (Morphology Profiles)
        'deVAB_u': 'u밴드 드보클뢰르 축비 (deVAB_u b/a)',
        'deVAB_g': 'g밴드 드보클뢰르 축비 (deVAB_g b/a)',
        'deVAB_r': 'r밴드 드보클뢰르 축비 (deVAB_r b/a)',
        'deVAB_i': 'i밴드 드보클뢰르 축비 (deVAB_i b/a)',
        'deVAB_z': 'z밴드 드보클뢰르 축비 (deVAB_z b/a)',
        'expAB_u': 'u밴드 지수원반 축비 (expAB_u b/a)',
        'expAB_g': 'g밴드 지수원반 축비 (expAB_g b/a)',
        'expAB_r': 'r밴드 지수원반 축비 (expAB_r b/a)',
        'expAB_i': 'i밴드 지수원반 축비 (expAB_i b/a)',
        'expAB_z': 'z밴드 지수원반 축비 (expAB_z b/a)',
        'fracDeV_u': 'u밴드 드보클뢰르 기여분율 (fracDeV_u)',
        'fracDeV_g': 'g밴드 드보클뢰르 기여분율 (fracDeV_g)',
        'fracDeV_r': 'r밴드 드보클뢰르 기여분율 (fracDeV_r)',
        'fracDeV_i': 'i밴드 드보클뢰르 기여분율 (fracDeV_i)',
        'fracDeV_z': 'z밴드 드보클뢰르 기여분율 (fracDeV_z)',

        # 스펙트럼 방출선 플럭스 (Emission Line Fluxes)
        'h_alpha_flux': 'Hα 방출선 플럭스 (h_alpha_flux [10^-17])',
        'h_beta_flux': 'Hβ 방출선 플럭스 (h_beta_flux [10^-17])',
        'h_gamma_flux': 'Hγ 방출선 플럭스 (h_gamma_flux [10^-17])',
        'h_delta_flux': 'Hδ 방출선 플럭스 (h_delta_flux [10^-17])',
        'oiii_5007_flux': '[OIII] 5007Å 플럭스 (oiii_5007_flux)',
        'oiii_4959_flux': '[OIII] 4959Å 플럭스 (oiii_4959_flux)',
        'nii_6584_flux': '[NII] 6584Å 플럭스 (nii_6584_flux)',
        'nii_6548_flux': '[NII] 6548Å 플럭스 (nii_6548_flux)',
        'sii_6717_flux': '[SII] 6717Å 플럭스 (sii_6717_flux)',
        'sii_6731_flux': '[SII] 6731Å 플럭스 (sii_6731_flux)',
        'oii_3726_flux': '[OII] 3726Å 플럭스 (oii_3726_flux)',
        'oii_3729_flux': '[OII] 3729Å 플럭스 (oii_3729_flux)',
        'oi_6300_flux': '[OI] 6300Å 플럭스 (oi_6300_flux)',
        'hei_5876_flux': 'HeI 5876Å 플럭스 (hei_5876_flux)',
        'heii_4686_flux': 'HeII 4686Å 플럭스 (heii_4686_flux)',

        # 방출선 등가폭 (Equivalent Widths)
        'h_alpha_eqw': 'Hα 등가폭 (h_alpha_eqw [Å])',
        'h_beta_eqw': 'Hβ 등가폭 (h_beta_eqw [Å])',
        'oiii_5007_eqw': '[OIII] 5007Å 등가폭 (oiii_5007_eqw [Å])',
        'nii_6584_eqw': '[NII] 6584Å 등가폭 (nii_6584_eqw [Å])',
        'sii_6717_eqw': '[SII] 6717Å 등가폭 (sii_6717_eqw [Å])',
        'oii_3726_eqw': '[OII] 3726Å 등가폭 (oii_3726_eqw [Å])',

        # 천체물리/화학 진화 파생량 (MPA-JHU)
        'log_stellar_mass': '항성 질량 log(M*/M_sun)',
        'lgm_fib_p50': '광섬유 내부 항성질량 log(M_fib/M_sun)',
        'log_sfr': '별 생성률 log(SFR [M_sun/yr])',
        'sfr_fib_p50': '광섬유 내부 SFR log(SFR_fib)',
        'log_ssfr': '비별생성률 log(sSFR = SFR/M* [yr^-1])',
        'metallicity_oh': '기체 산소 풍부도 12 + log(O/H)',
        'd4000_n': '4000Å 불연속 지표 (D_n(4000) 항성 연령)',
        'dust_ebv': '먼지 소광 색초과 E(B-V) [mag]',

        # Galaxy Zoo 형태학적 확률
        'gz_p_el': '타원은하 확률 (gz_p_el)',
        'gz_p_cs': '나선/원반은하 확률 (gz_p_cs)',
        'gz_p_edge': '측면나선 확률 (gz_p_edge)',
        'gz_p_mg': '병합은하 확률 (gz_p_mg)',
        'gz_spiral': '나선은하 확정 플래그 (gz_spiral)',
        'gz_elliptical': '타원은하 확정 플래그 (gz_elliptical)',
        'gz_uncertain': '불확실/특이은하 플래그 (gz_uncertain)',
        'gz2_bar_prob': '은하 중심 막대 구조 확률 (gz2_bar_prob)',
        'gz2_ring_prob': '고리 구조 확률 (gz2_ring_prob)',
        'gz2_merger_prob': '병합/상호작용 징후 확률 (gz2_merger_prob)',
        'gz2_irregular_prob': '불규칙 구조 확률 (gz2_irregular_prob)',
        'gz2_bulge_prominence': '팽대부 돌출도 (gz2_bulge_prominence)',

        # 다파장 서베이 (2MASS, WISE, FIRST)
        'mag_j_2mass': '2MASS J밴드 1.25µm 적외선 등급 [mag]',
        'mag_h_2mass': '2MASS H밴드 1.65µm 적외선 등급 [mag]',
        'mag_k_2mass': '2MASS Ks밴드 2.17µm 적외선 등급 [mag]',
        'mag_w1_wise': 'WISE W1밴드 3.4µm 중적외선 등급 [mag]',
        'mag_w2_wise': 'WISE W2밴드 4.6µm 중적외선 등급 [mag]',
        'first_radio_flux': 'FIRST 1.4 GHz 전파 플럭스 [mJy]',

        # 파생 진단 지수 및 색지수
        'log_nii_ha': 'BPT x축 log([NII]6584 / Hα)',
        'log_oiii_hb': 'BPT y축 log([OIII]5007 / Hβ)',
        'log_sii_ha': '충격파 진단 log([SII]6717 / Hα)',
        'color_u_r': '색지수 (u - r) [mag]',
        'concentration_index_r': '빛 집중도 지수 (C = R_90 / R_50)'
    }

    # 존재하는 컬럼만 필터링
    valid_params = {}
    for col in df.columns:
        if col in exclude_cols:
            continue
        if 'err' in col.lower() or col.endswith('_p16') or col.endswith('_p84'):
            continue
        if col in PARAM_LABELS:
            valid_params[col] = PARAM_LABELS[col]
        else:
            valid_params[col] = col

    print(f"[2/4] 통계 요약 계산 중... ({len(valid_params)}개 물리량)")
    stats = {}
    for col in valid_params.keys():
        s = pd.to_numeric(df[col], errors='coerce').dropna()
        if len(s) > 0:
            stats[col] = {
                'mean': round(float(s.mean()), 4),
                'median': round(float(s.median()), 4),
                'std': round(float(s.std()), 4),
                'min': round(float(s.min()), 4),
                'max': round(float(s.max()), 4),
                'count': int(s.count()),
            }

    # 11대 은하 유형 분포
    type_dist = df['galaxy_type'].value_counts().to_dict()

    print("[3/4] 플롯용 데이터 샘플링 (10,000개)...")
    sample_size = min(10000, total)
    sample = df.sample(n=sample_size, random_state=42)

    # 플롯 및 테이블에 필요한 컬럼 추출
    sample_cols = ['galaxy_type', 'specClass', 'bptclass'] + list(valid_params.keys())
    sample_cols = [c for c in sample_cols if c in sample.columns]
    # 중복 제거
    sample_cols = list(dict.fromkeys(sample_cols))

    sample_df = sample[sample_cols].copy()
    # NaN -> None for JSON
    sample_json = json.loads(sample_df.to_json(orient='records'))

    print("[4/4] 자체 완결형 HTML 생성 중...")
    median_z = stats.get('z', {}).get('median', 'N/A')

    # HTML 템플릿 작성
    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>YSC 은하 진화 다차원 통계 대시보드</title>
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
.ctrl {{ flex: 1; min-width: 260px; }}
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
<h1>YSC 은하 진화 다차원 통계 대시보드</h1>
<p>SDSS DR18 &middot; 200개 핵심 물리량 &middot; 11대 은하 분류 체계 ({total:,}개 표본)</p>
<span class="badge">Teams 물리량 전체 탑재 &middot; 적경/적위 및 오차 제외 완료</span>
</div>

<div class="container">
<div class="tabs">
<button class="tab-btn active" onclick="openTab('overview')">1. 개요 & 11대 분류</button>
<button class="tab-btn" onclick="openTab('explore')">2. 다차원 상관관계 탐색</button>
<button class="tab-btn" onclick="openTab('stats')">3. 물리량 기술통계 ({len(valid_params)}개)</button>
<button class="tab-btn" onclick="openTab('data_table')">4. 표본 데이터 테이블</button>
<button class="tab-btn" onclick="openTab('validate')">5. 분광 관측 판독기</button>
</div>

<!-- ══ TAB: 개요 ══ -->
<div id="overview" class="tab active">
<div class="row row-4">
<div class="glass stat-card"><div class="val">{total:,}</div><div class="lbl">분석 표본 은하 수</div></div>
<div class="glass stat-card"><div class="val">{len(type_dist)}</div><div class="lbl">은하 분류 클래스</div></div>
<div class="glass stat-card"><div class="val">{len(valid_params)}</div><div class="lbl">탑재된 핵심 물리량</div></div>
<div class="glass stat-card"><div class="val">{median_z}</div><div class="lbl">중앙 적색편이 (z)</div></div>
</div>

<div class="glass">
<h3 style="color:#fff;margin-bottom:.8rem">&#127756; 11대 은하 형태 및 분광 분류 분포 (클래스별 5,000개 균등 표본)</h3>
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
<h3 style="color:#ffff00;margin-bottom:.6rem">&#9881;&#65039; 분석 데이터셋 스키마 정보</h3>
<p style="color:#aaa;font-size:1.1rem">
&bull; <strong>탑재 파라미터</strong>: 측광 등급 5종(u, g, r, i, z), 성간 소광량, 유효 반경(R50, R90, deVRad, expRad), 축비(b/a), 방출선 플럭스(Hα, Hβ, [OIII], [NII], [SII], [OII] 등), 등가폭(EQW), 항성 질량, 별 생성률(SFR), 비별생성률(sSFR), 기체 산소 풍부도(O/H), 항성 연령 D_n(4000), Galaxy Zoo 형태 확률, 2MASS/WISE 적외선 등급, FIRST 전파 플럭스 등 총 <strong>{len(valid_params)}개</strong><br>
&bull; <strong>제외 항목</strong>: 신현승 요구사항에 따라 천구 좌표(적경 ra, 적위 dec) 및 모든 오차값(err, p16, p84)을 통계/탐색 목록에서 제외하였습니다.
</p>
</div>
</div>

<!-- ══ TAB: 탐색 ══ -->
<div id="explore" class="tab">
<div class="glass">
<div class="ctrls">
<div class="ctrl"><label>X축 물리량 선택</label><select id="x-var"></select></div>
<div class="ctrl"><label>Y축 물리량 선택</label><select id="y-var"></select></div>
<div class="ctrl"><label>색상(Color) 기준</label><select id="c-var"></select></div>
</div>
<div class="presets">
<strong style="color:#ffff00;align-self:center;margin-right:4px;">프리셋:</strong>
<button class="preset" onclick="setPreset('ms')">1. 은하 주계열 (MS)</button>
<button class="preset" onclick="setPreset('bpt')">2. BPT 이온화 진단</button>
<button class="preset" onclick="setPreset('cm')">3. 색-질량 (u-r vs Mass)</button>
<button class="preset" onclick="setPreset('mzr')">4. 질량-금속량 (MZR)</button>
<button class="preset" onclick="setPreset('d4000')">5. 항성연령-질량 (D4000)</button>
<button class="preset" onclick="setPreset('dyn')">6. 동역학 속도분산 (Faber-Jackson)</button>
<button class="preset" onclick="setPreset('c_index')">7. 빛 집중도-질량</button>
<button class="preset" onclick="setPreset('dust')">8. 먼지소광-SFR</button>
<button class="preset" onclick="setPreset('wise')">9. 중적외선-질량 (WISE)</button>
<button class="preset" onclick="setPreset('radio')">10. 전파플럭스-속도분산 (FIRST)</button>
</div>
<div id="plot"></div>
</div>
</div>

<!-- ══ TAB: 통계 ══ -->
<div id="stats" class="tab">
<div class="glass">
<h3 style="color:#fff;margin-bottom:.8rem">전체 {len(valid_params)}개 핵심 물리량 기술통계 명세표</h3>
<div style="overflow-x:auto; max-height: 650px; overflow-y: auto;">
<table>
<thead>
<tr><th>물리량 파라미터 (변수명 및 설명)</th><th>평균 (Mean)</th><th>중앙값 (Median)</th><th>표준편차 (Std)</th><th>최소 (Min)</th><th>최대 (Max)</th><th>유효 표본 수</th></tr>
</thead>
<tbody>
"""
    for col, s in stats.items():
        label = valid_params.get(col, col)
        html += f"<tr><td><strong style='color:#fff'>{label}</strong> <span style='color:#888'>({col})</span></td><td>{s['mean']}</td><td>{s['median']}</td><td>{s['std']}</td><td>{s['min']}</td><td>{s['max']}</td><td>{s['count']:,}</td></tr>\n"

    html += """</tbody>
</table></div></div></div>

<!-- ══ TAB: 데이터 표 ══ -->
<div id="data_table" class="tab">
<div class="glass">
<h3 style="color:#fff;margin-bottom:1rem">대표 관측 표본 목록 (Sample Data Viewer)</h3>
<div style="overflow-x:auto; max-height: 600px; overflow-y: auto;">
<table id="galaxy_table">
<thead>
<tr>
<th>은하 분류</th>
<th>적색편이 (z)</th>
<th>항성질량 (log M*)</th>
<th>별생성률 (log SFR)</th>
<th>금속성 (O/H)</th>
<th>속도분산 (σ_v)</th>
<th>색지수 (u-r)</th>
<th>D_n(4000)</th>
<th>[NII]/Hα</th>
<th>[OIII]/Hβ</th>
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
<h3 style="color:#fff;margin-bottom:.6rem">은하 분광 관측값 판독기 (Spectral Line Diagnostic Analyzer)</h3>
<p style="color:#aaa;margin-bottom:1rem">방출선 플럭스 값을 입력하면 BPT 분류, 기체 산소 금속성, Balmer Decrement 먼지 소광값을 실시간 연산합니다.</p>
<div class="ctrls">
<div class="ctrl"><label>H-alpha Flux (6563Å)</label><input type="number" id="ha" step="any" placeholder="예: 125.4"></div>
<div class="ctrl"><label>H-beta Flux (4861Å)</label><input type="number" id="hb" step="any" placeholder="예: 38.2"></div>
<div class="ctrl"><label>[OIII] 5007Å Flux</label><input type="number" id="oiii" step="any" placeholder="예: 42.1"></div>
<div class="ctrl"><label>[NII] 6584Å Flux</label><input type="number" id="nii" step="any" placeholder="예: 48.7"></div>
</div>
<button class="preset" style="border-color:#ffff00;color:#ffff00;font-size:1.1rem;padding:.6rem 2rem" onclick="doValidate()">판독 및 진단 가동</button>
<div id="val-result" style="display:none;margin-top:1.2rem">
<div class="row row-4">
<div class="glass stat-card"><div class="val" id="r-bpt">-</div><div class="lbl">BPT 이온화 분류</div></div>
<div class="glass stat-card"><div class="val" id="r-oh">-</div><div class="lbl">금속성 (12+log O/H)</div></div>
<div class="glass stat-card"><div class="val" id="r-ebv">-</div><div class="lbl">먼지 소광 E(B-V) [mag]</div></div>
<div class="glass stat-card"><div class="val" id="r-type">-</div><div class="lbl">주요 에너지원</div></div>
</div>
<div id="val-plot" style="height:380px;margin-top:1rem;border:2px solid #444;background:#000"></div>
</div>
</div>
</div>

</div>

<footer>
YSC 2026 청소년과학탐구반 &mdash; 은하의 물리량 및 화학조성 분석을 통한 은하 진화 경향 및 메커니즘 분석 도표 탐구<br>
SDSS DR18 200개 핵심 물리량 & 11대 은하 분류 체계 탑재 완결형 대시보드
</footer>

<script>
// ═══ Embedded real data ═══
const DATA = PLACEHOLDER_DATA;

// ═══ Variable definitions ═══
const VARS = PLACEHOLDER_VARS;
const CATS = { galaxy_type: '은하 11대 분류', specClass: '분광 1차 분류' };

// ═══ Init selects ═══
const xs = document.getElementById('x-var'), ys = document.getElementById('y-var'), cs = document.getElementById('c-var');
Object.entries(VARS).forEach(([k,v]) => { xs.add(new Option(v,k)); ys.add(new Option(v,k)); cs.add(new Option(v,k)); });
Object.entries(CATS).forEach(([k,v]) => cs.add(new Option(v,k)));
xs.value='log_stellar_mass'; ys.value='log_sfr'; cs.value='galaxy_type';

// ═══ Populate Table ═══
const tbody = document.getElementById('galaxy_table_body');
DATA.slice(0, 100).forEach(d => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
        <td><span style="color:#ffff00">${d.galaxy_type || '-'}</span></td>
        <td>${d.z !== null && d.z !== undefined ? d.z.toFixed(4) : '-'}</td>
        <td>${d.log_stellar_mass !== null && d.log_stellar_mass !== undefined ? d.log_stellar_mass.toFixed(2) : '-'}</td>
        <td>${d.log_sfr !== null && d.log_sfr !== undefined ? d.log_sfr.toFixed(2) : '-'}</td>
        <td>${d.metallicity_oh !== null && d.metallicity_oh !== undefined ? d.metallicity_oh.toFixed(2) : '-'}</td>
        <td>${d.velDisp !== null && d.velDisp !== undefined ? d.velDisp.toFixed(1) : '-'}</td>
        <td>${d.color_u_r !== null && d.color_u_r !== undefined ? d.color_u_r.toFixed(2) : '-'}</td>
        <td>${d.d4000_n !== null && d.d4000_n !== undefined ? d.d4000_n.toFixed(2) : '-'}</td>
        <td>${d.log_nii_ha !== null && d.log_nii_ha !== undefined ? d.log_nii_ha.toFixed(2) : '-'}</td>
        <td>${d.log_oiii_hb !== null && d.log_oiii_hb !== undefined ? d.log_oiii_hb.toFixed(2) : '-'}</td>
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
    if(p==='ms'){xs.value='log_stellar_mass';ys.value='log_sfr';cs.value='galaxy_type';}
    if(p==='bpt'){xs.value='log_nii_ha';ys.value='log_oiii_hb';cs.value='galaxy_type';}
    if(p==='cm'){xs.value='log_stellar_mass';ys.value='color_u_r';cs.value='galaxy_type';}
    if(p==='mzr'){xs.value='log_stellar_mass';ys.value='metallicity_oh';cs.value='galaxy_type';}
    if(p==='d4000'){xs.value='log_stellar_mass';ys.value='d4000_n';cs.value='galaxy_type';}
    if(p==='dyn'){xs.value='log_stellar_mass';ys.value='velDisp';cs.value='galaxy_type';}
    if(p==='c_index'){xs.value='log_stellar_mass';ys.value='concentration_index_r';cs.value='galaxy_type';}
    if(p==='dust'){xs.value='log_sfr';ys.value='dust_ebv';cs.value='galaxy_type';}
    if(p==='wise'){xs.value='log_stellar_mass';ys.value='mag_w1_wise';cs.value='galaxy_type';}
    if(p==='radio'){xs.value='velDisp';ys.value='first_radio_flux';cs.value='galaxy_type';}
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

    # JSON 데이터 및 VARS 주입
    data_json = json.dumps(sample_json, ensure_ascii=False)
    vars_json = json.dumps(valid_params, ensure_ascii=False)

    html = html.replace('PLACEHOLDER_DATA', data_json)
    html = html.replace('PLACEHOLDER_VARS', vars_json)

    # 저장
    output_path = os.path.join(config.PROJECT_ROOT, 'dashboard_real_data.html')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"\n=== 완료! ===")
    print(f"파일: {output_path}")
    print(f"크기: {size_mb:.1f} MB")
    print(f"임베딩된 은하 수: {sample_size:,}개 (전체 {total:,}개 중 샘플)")
    print(f"임베딩된 물리량 수: {len(valid_params)}개")

if __name__ == '__main__':
    main()
