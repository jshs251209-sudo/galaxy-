# -*- coding: utf-8 -*-
"""앱 전체 파이프라인 시뮬레이션 테스트 — 모든 코드 경로를 검증"""
import sys, os, traceback
sys.path.insert(0, r'c:\Users\neato\Desktop\정현\03_과학탐구_대회\YSC_대회')

import numpy as np
import pandas as pd

errors = []

def test(name, fn):
    try:
        fn()
        print('  PASS: %s' % name)
    except Exception as e:
        errors.append((name, str(e), traceback.format_exc()))
        print('  FAIL: %s -> %s' % (name, str(e)))

# ============================================
print('=== 1. Spectrum Engine 심화 테스트 ===')
# ============================================
from modules.spectrum_engine import SpectrumROIExtractor, WavelengthCalibrator, EmissionLineFitter, MockSpectrumGenerator

def test_fitter_complete():
    """방출선 피터 전체 경로 + app.py에서 사용하는 결과 구조 확인"""
    mock = MockSpectrumGenerator()
    fitter = EmissionLineFitter()
    
    for gtype in ['star_forming', 'agn_seyfert', 'elliptical']:
        df = mock.generate(gtype)
        result = fitter.fit_all_lines(df['wavelength'].values, df['flux'].values, z=0.0)
        assert result is not None, '%s: result is None' % gtype
        
        # app.py expects result to have 'fits' and 'peaks' keys
        # Check what keys actually exist
        keys = list(result.keys())
        
        # Try extracting fluxes the way app.py does
        lines = {}
        fits = result.get('fits', {})
        peaks = result.get('peaks', {})
        
        for line_name in ['H_alpha', 'H_beta', 'OIII_5007', 'NII_6584']:
            if isinstance(fits, dict) and line_name in fits:
                fit_data = fits[line_name]
                if fit_data and isinstance(fit_data, dict) and 'integrated_flux' in fit_data:
                    lines[line_name] = fit_data['integrated_flux']
            elif isinstance(peaks, dict) and line_name in peaks:
                peak_data = peaks[line_name]
                if peak_data and isinstance(peak_data, dict) and 'flux' in peak_data:
                    lines[line_name] = peak_data['flux']
        
        print('    %s: result_keys=%s, extracted_lines=%s' % (gtype, keys, list(lines.keys())))

test('fitter_complete', test_fitter_complete)

def test_continuum():
    fitter = EmissionLineFitter()
    mock = MockSpectrumGenerator()
    df = mock.generate('star_forming')
    cont = fitter.fit_continuum(df['wavelength'].values, df['flux'].values, method='median')
    assert cont is not None and len(cont) == len(df), 'continuum wrong length'
    cont2 = fitter.fit_continuum(df['wavelength'].values, df['flux'].values, method='poly')
    assert cont2 is not None and len(cont2) == len(df), 'poly continuum wrong length'
test('continuum_fitting', test_continuum)

# ============================================
print()
print('=== 2. Physics Calculator 심화 테스트 ===')
# ============================================
from modules.physics_calculator import PhysicsCalculator
calc = PhysicsCalculator()

def test_compute_all_full():
    """compute_all이 app.py에서 필요한 모든 키를 반환하는지"""
    r = calc.compute_all({'H_alpha': 100, 'H_beta': 30, 'OIII_5007': 50, 'NII_6584': 40}, z=0.05, log_mass=10.5, color_ur=2.0)
    required_keys = ['ebv', 'log_sfr', 'metallicity', 'metallicity_oh', 'log_nii_ha', 'log_oiii_hb', 'bpt_class']
    for k in required_keys:
        assert k in r, 'missing key: %s' % k
        assert r[k] is not None, 'key %s is None' % k
    # GEI keys
    gei_keys = ['gei', 'evolution_stage', 'log_ssfr']
    for k in gei_keys:
        assert k in r, 'missing GEI key: %s' % k
test('compute_all_full', test_compute_all_full)

def test_compute_all_spectrum_only():
    """스펙트럼에서만 추출한 경우 (log_mass, color_ur 없음)"""
    r = calc.compute_all({'H_alpha': 100, 'H_beta': 30, 'OIII_5007': 50, 'NII_6584': 40}, z=0.05)
    assert r is not None
    assert 'metallicity' in r
    # GEI should NOT be present
    print('    spectrum-only gei: %s' % r.get('gei'))
test('compute_all_spectrum_only', test_compute_all_spectrum_only)

# ============================================
print()
print('=== 3. Phase Space Mapper 심화 테스트 ===')
# ============================================
from modules.phase_space_mapper import PhaseSpaceMapper

def test_mapper_all_plots():
    master_path = r'c:\Users\neato\Desktop\정현\03_과학탐구_대회\YSC_대회\galaxy_master_complete_all.csv'
    mapper = PhaseSpaceMapper(master_path)
    assert len(mapper.df) > 0, 'empty dataframe'
    
    # Test each plot function
    fig1 = mapper.plot_bpt(-0.3, 0.5)
    assert fig1 is not None, 'plot_bpt returned None'
    
    fig2 = mapper.plot_sfms(10.5, 0.5)
    assert fig2 is not None, 'plot_sfms returned None'
    
    fig3 = mapper.plot_mzr(10.5, 8.8)
    assert fig3 is not None, 'plot_mzr returned None'
    
    fig4 = mapper.plot_color_mass(10.5, 2.0)
    assert fig4 is not None, 'plot_color_mass returned None'
    
    fig5 = mapper.plot_3d_fmr(10.5, 0.5, 8.8)
    assert fig5 is not None, 'plot_3d_fmr returned None'
    
    fig6 = mapper.plot_summary_4panel({'log_nii_ha': -0.3, 'log_oiii_hb': 0.5, 'log_mass': 10.5, 'log_sfr': 0.5, 'metallicity': 8.8, 'color_ur': 2.0})
    assert fig6 is not None, 'plot_summary_4panel returned None'
    
    # Test with None targets (no overlay)
    fig_no = mapper.plot_bpt(None, None)
    assert fig_no is not None, 'plot_bpt None returned None'
    
test('mapper_all_plots', test_mapper_all_plots)

# ============================================
print()
print('=== 4. ML Predictor 심화 테스트 ===')
# ============================================
from modules.ml_predictor import GalaxyPredictor

def test_predictor_full():
    model_dir = r'c:\Users\neato\Desktop\정현\03_과학탐구_대회\YSC_대회\output\models'
    pred = GalaxyPredictor(model_dir)
    assert pred.is_loaded, 'models not loaded'
    
    # Full properties
    props = {'log_stellar_mass': 10.5, 'log_sfr': 0.5, 'log_ssfr': -10.0,
             'metallicity_oh': 8.8, 'color_u_r': 2.0, 'log_nii_ha': -0.3,
             'log_oiii_hb': 0.2, 'z': 0.05, 'velDisp': 150, 'd4000_n': 1.5}
    
    t = pred.predict_galaxy_type(props)
    assert t is not None, 'predict_galaxy_type None'
    assert 'predicted_class' in t, 'missing predicted_class'
    assert 'probabilities' in t, 'missing probabilities'
    assert 'top_3' in t, 'missing top_3'
    assert 'confidence' in t, 'missing confidence'
    print('    type: %s (%.1f%%)' % (t['predicted_class'], t['confidence']*100))
    
    c = pred.predict_evolution_cluster(props)
    assert c is not None, 'predict_evolution_cluster None'
    assert 'cluster_name' in c, 'missing cluster_name'
    print('    cluster: %s' % c['cluster_name'])
    
    imp = pred.get_feature_importance(props)
    assert imp is not None, 'get_feature_importance None'
    
    # Charts
    prob_fig = pred.create_probability_chart(t['probabilities'])
    assert prob_fig is not None, 'probability chart None'
    
    imp_fig = pred.create_feature_importance_chart(imp)
    assert imp_fig is not None, 'importance chart None'
    
    gauge = pred.create_evolution_gauge(54.3)
    assert gauge is not None, 'gauge None'

test('predictor_full', test_predictor_full)

def test_predictor_partial():
    """부분 입력 (스펙트럼만)"""
    model_dir = r'c:\Users\neato\Desktop\정현\03_과학탐구_대회\YSC_대회\output\models'
    pred = GalaxyPredictor(model_dir)
    
    # Minimal properties (from spectrum analysis only)
    props = {'log_nii_ha': -0.3, 'log_oiii_hb': 0.2}
    t = pred.predict_galaxy_type(props)
    assert t is not None, 'partial predict None'
    print('    partial type: %s' % t.get('predicted_class', '?'))
    
test('predictor_partial', test_predictor_partial)

# ============================================
print()
print('=== 5. SDSS Fetcher 테스트 ===')
# ============================================
from modules.sdss_fetcher import SDSSFetcher

def test_sdss_samples():
    sdss = SDSSFetcher()
    samples = sdss.get_sample_galaxies()
    assert len(samples) >= 3, 'too few samples'
    for s in samples:
        required = ['name', 'ra', 'dec', 'log_mass', 'log_sfr', 'metallicity', 'color_ur', 'log_nii_ha', 'log_oiii_hb']
        for k in required:
            assert k in s, 'sample missing key: %s in %s' % (k, s.get('name', '?'))
        print('    %s: OK' % s['name'])
test('sdss_samples', test_sdss_samples)

# ============================================
print()
print('=== 6. Report Generator 테스트 ===')
# ============================================
from modules.report_generator import ReportGenerator

def test_report_full():
    rg = ReportGenerator()
    analysis = {
        'target_name': 'M31',
        'analysis_datetime': '2026-10-01 22:00:00',
        'input_mode': 'test',
        'ebv': 0.15,
        'log_sfr': -0.5,
        'metallicity': 8.9,
        'metallicity_method': 'N2',
        'log_nii_ha': -0.4,
        'log_oiii_hb': -0.2,
        'bpt_class': 'Star-Forming',
        'predicted_type': 'Spiral',
        'confidence': 0.85,
        'top_3_types': [('Spiral', 0.85), ('Barred Spiral', 0.10), ('Irregular', 0.05)],
        'evolution_cluster': 'Growth',
        'gei_score': 35.0,
        'evolution_stage': 'Growth Phase',
        'log_mass': 10.8,
        'color_ur': 2.1,
        'z': 0.001,
    }
    md = rg.generate_markdown(analysis)
    assert len(md) > 100, 'report too short'
    print('    md length: %d chars' % len(md))
    
    html = rg.generate_html(md)
    assert len(html) > 100, 'html too short'
    assert '<html' in html.lower() or '<div' in html.lower(), 'not valid html'
    print('    html length: %d chars' % len(html))
    
    summary = rg.generate_summary_card(analysis)
    assert summary is not None, 'summary None'
    assert 'metrics' in summary, 'summary missing metrics'
    print('    summary metrics: %d' % len(summary['metrics']))
    
test('report_full', test_report_full)

def test_report_empty():
    rg = ReportGenerator()
    md = rg.generate_markdown({})
    assert md is not None, 'empty report None'
    print('    empty report length: %d' % len(md))
test('report_empty', test_report_empty)

# ============================================
print()
print('=== 7. App.py 함수 시뮬레이션 ===')
# ============================================

def test_app_sample_flow():
    """샘플 은하 로드 → 물리량 → 매핑 → AI분류 → 보고서 전체 흐름"""
    sdss = SDSSFetcher()
    samples = sdss.get_sample_galaxies()
    sample = samples[0]  # M31
    
    props = dict(sample)
    props['log_stellar_mass'] = props.get('log_mass')
    props['lgm_tot_p50'] = props.get('log_mass')
    props['sfr_tot_p50'] = props.get('log_sfr')
    props['metallicity_oh'] = props.get('metallicity')
    props['oh_p50'] = props.get('metallicity')
    props['color_u_r'] = props.get('color_ur')
    
    # PhysicsCalc
    calc_local = PhysicsCalculator()
    log_ssfr = calc_local.calculate_log_ssfr(props['log_sfr'], props['log_mass'])
    props['log_ssfr'] = log_ssfr if log_ssfr else -10.5
    bpt = calc_local.classify_bpt(props['log_nii_ha'], props['log_oiii_hb'])
    props['bpt_class'] = bpt['class']
    gei = calc_local.calculate_gei(props['log_mass'], props['log_ssfr'], props['metallicity'], props['color_ur'])
    props['gei_score'] = gei
    stage = calc_local.diagnose_evolution_stage(gei)
    props['evolution_stage'] = stage['stage']
    
    # Phase Space
    mapper_local = PhaseSpaceMapper(r'c:\Users\neato\Desktop\정현\03_과학탐구_대회\YSC_대회\galaxy_master_complete_all.csv')
    fig = mapper_local.plot_summary_4panel({
        'log_nii_ha': props['log_nii_ha'],
        'log_oiii_hb': props['log_oiii_hb'],
        'log_mass': props['log_mass'],
        'log_sfr': props['log_sfr'],
        'metallicity': props['metallicity'],
        'color_ur': props['color_ur'],
    })
    assert fig is not None
    
    # ML Predictor
    pred_local = GalaxyPredictor(r'c:\Users\neato\Desktop\정현\03_과학탐구_대회\YSC_대회\output\models')
    t = pred_local.predict_galaxy_type(props)
    c = pred_local.predict_evolution_cluster(props)
    
    # Report
    rg_local = ReportGenerator()
    analysis = {
        'target_name': sample['name'],
        'analysis_datetime': '2026-10-01',
        'input_mode': 'sample',
        'log_sfr': props['log_sfr'],
        'metallicity': props['metallicity'],
        'bpt_class': props['bpt_class'],
        'predicted_type': t.get('predicted_class', '?'),
        'confidence': t.get('confidence', 0),
        'top_3_types': t.get('top_3', []),
        'evolution_cluster': c.get('cluster_name', '?'),
        'gei_score': gei,
        'evolution_stage': stage['stage'],
        'log_mass': props['log_mass'],
        'color_ur': props['color_ur'],
        'z': props.get('z', 0),
    }
    md = rg_local.generate_markdown(analysis)
    assert len(md) > 100
    print('    Full pipeline for %s: OK' % sample['name'])
    
test('app_sample_flow', test_app_sample_flow)

# ============================================
print()
print('=' * 50)
print('RESULTS: %d errors found' % len(errors))
print('=' * 50)
for name, err, tb in errors:
    print()
    print('--- FAIL: %s ---' % name)
    print(tb)
