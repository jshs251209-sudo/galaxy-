# -*- coding: utf-8 -*-
"""GalaxyEvolution Studio 통합 테스트 — 모든 모듈과 앱이 사용하는 코드 경로를 검증

실행: python test_integration.py   (실패가 있으면 종료 코드 1)
"""
import sys, os, traceback

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
MASTER_CSV = os.path.join(ROOT, 'galaxy_master_complete_all.csv')
MODEL_DIR = os.path.join(ROOT, 'output', 'models')

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
print('=== 1. Spectrum Engine ===')
# ============================================
from modules.spectrum_engine import (SpectrumROIExtractor, WavelengthCalibrator, EmissionLineFitter,
                                     MockSpectrumGenerator, LINE_LIST)

fitter = EmissionLineFitter()
mock = MockSpectrumGenerator()


def test_fitter_complete():
    """방출선 피팅 결과 구조 + 유형별 기대 결과"""
    for gtype in ['star_forming', 'agn_seyfert', 'elliptical']:
        df = mock.generate(gtype)
        result = fitter.fit_all_lines(df['wavelength'].values, df['flux'].values, z=0.0)
        for k in ('fits', 'continuum', 'line_table', 'd4000'):
            assert k in result, '%s: missing %s' % (gtype, k)
        lines = fitter.extract_line_fluxes(result)
        print('    %s: %d lines %s' % (gtype, len(lines), sorted(lines)))
        if gtype != 'elliptical':
            for n in ('H_alpha', 'H_beta', 'NII_6584', 'OIII_5007'):
                assert n in lines, '%s: %s not detected' % (gtype, n)
        else:
            assert len(lines) <= 3, 'elliptical: too many spurious lines (%d)' % len(lines)


test('fitter_complete', test_fitter_complete)


def test_line_ratios():
    """블렌드 분리 후 BPT 비가 유형과 일치"""
    from modules.physics_calculator import PhysicsCalculator
    c = PhysicsCalculator()
    out = {}
    for gtype in ['star_forming', 'agn_seyfert']:
        df = mock.generate(gtype)
        r = fitter.fit_all_lines(df['wavelength'].values, df['flux'].values, z=0.0)
        p = c.compute_all(fitter.extract_line_fluxes(r), z=0.05)
        out[gtype] = p
        print('    %s: N2=%.2f O3=%.2f -> %s' % (gtype, p['log_nii_ha'], p['log_oiii_hb'], p['bpt_class']))
    assert out['star_forming']['log_nii_ha'] < -0.4
    assert out['agn_seyfert']['log_nii_ha'] > -0.1 and out['agn_seyfert']['log_oiii_hb'] > 0.3


test('line_ratios_bpt', test_line_ratios)


def test_redshift_estimate():
    for z_true in (0.03, 0.1, 0.2):
        df = mock.generate('star_forming', z=z_true)
        est = fitter.estimate_redshift(df['wavelength'].values, df['flux'].values, 0.0, 0.4)
        assert est is not None, 'z=%.2f: no estimate' % z_true
        assert abs(est['z'] - z_true) < 0.003, 'z=%.2f: got %.4f' % (z_true, est['z'])
        print('    z_true=%.2f -> z_est=%.4f' % (z_true, est['z']))


test('redshift_estimate', test_redshift_estimate)


def test_continuum():
    df = mock.generate('star_forming')
    for m in ('median', 'poly'):
        cont = fitter.fit_continuum(df['wavelength'].values, df['flux'].values, method=m)
        assert cont is not None and len(cont) == len(df), '%s continuum wrong length' % m


test('continuum_fitting', test_continuum)


def test_d4000_and_smooth():
    df = mock.generate('elliptical')
    d_e = fitter.d4000(df['wavelength'].values, df['flux'].values)
    df2 = mock.generate('star_forming')
    d_s = fitter.d4000(df2['wavelength'].values, df2['flux'].values)
    print('    D4000 elliptical=%s star_forming=%s' % (d_e, d_s))
    s = fitter.smooth(df['flux'].values, 7)
    assert len(s) == len(df)


test('d4000_smooth', test_d4000_and_smooth)


def test_spectrum_image_roundtrip():
    """분광 사진 생성 → 감마 보정 → 띠 추출 → 파장 교정 → 선 세기 비 복원"""
    from modules.physics_calculator import PhysicsCalculator
    img, w0, w1 = mock.generate_spectrum_image('agn_seyfert')
    lin = ((np.asarray(img, dtype=float) / 255.0) ** 2.2 * 255.0).mean(axis=2)   # app.spectral_gray 와 동일
    H, W = lin.shape
    mask = np.zeros_like(lin, bool)
    mask[int(H * 0.4):int(H * 0.6), :] = True
    _, flux = SpectrumROIExtractor().extract_from_mask(lin, mask, 'horizontal')
    wave = w0 + np.arange(len(flux)) / (W - 1) * (w1 - w0)
    lines = fitter.extract_line_fluxes(fitter.fit_all_lines(wave, flux, z=0.0))
    p = PhysicsCalculator().compute_all(lines, z=0.05)
    print('    image spectrum: N2=%.2f O3=%.2f -> %s' % (p['log_nii_ha'], p['log_oiii_hb'], p['bpt_class_en']))
    assert abs(p['log_oiii_hb'] - 1.0) < 0.1 and abs(p['log_nii_ha'] - 0.03) < 0.1
    assert p['bpt_class_en'] == 'Seyfert'


test('spectrum_image_roundtrip', test_spectrum_image_roundtrip)


def test_calibration():
    cal = WavelengthCalibrator()
    w, rms, coeffs = cal.calibrate_poly([100, 500, 900], [4861.3, 6562.8, 8000.0], 1000)
    assert len(w) == 1000 and w[0] < w[-1]
    hdr = {'CRVAL1': 3.5798, 'CD1_1': 0.0001, 'CRPIX1': 1, 'NAXIS1': 100}
    w2 = cal.calibrate_from_fits_header(hdr, 100)
    assert w2 is not None and abs(w2[0] - 10 ** 3.5798) < 1, 'log-linear SDSS header not handled'


test('wavelength_calibration', test_calibration)

# ============================================
print()
print('=== 2. Physics Calculator ===')
# ============================================
from modules.physics_calculator import PhysicsCalculator

calc = PhysicsCalculator()


def test_compute_all_full():
    r = calc.compute_all({'H_alpha': 100, 'H_beta': 30, 'OIII_5007': 50, 'NII_6584': 40}, z=0.05,
                         log_mass=10.5, color_ur=2.0)
    for k in ['ebv', 'log_sfr', 'metallicity', 'metallicity_oh', 'log_nii_ha', 'log_oiii_hb', 'bpt_class']:
        assert k in r and r[k] is not None, 'missing key: %s' % k
    for k in ['gei', 'evolution_stage', 'log_ssfr', 'balmer_decrement']:
        assert k in r, 'missing key: %s' % k


test('compute_all_full', test_compute_all_full)


def test_compute_all_spectrum_only():
    r = calc.compute_all({'H_alpha': 100, 'H_beta': 30, 'OIII_5007': 50, 'NII_6584': 40}, z=0.05)
    assert 'metallicity' in r
    print('    spectrum-only gei: %s' % r.get('gei'))


test('compute_all_spectrum_only', test_compute_all_spectrum_only)


def test_sii_diagnostics():
    r = calc.classify_sii_bpt(-0.5, 0.0)
    assert 'class' in r
    ne_low = calc.electron_density_sii(1.4, 1.0)
    ne_high = calc.electron_density_sii(0.6, 1.0)
    print('    SII-BPT=%s  n_e(1.4)=%s  n_e(0.6)=%s' % (r['class'], ne_low, ne_high))
    assert ne_high is None or ne_low is None or ne_high > ne_low


test('sii_diagnostics', test_sii_diagnostics)

# ============================================
print()
print('=== 3. Image Analyzer (영역 측광 · 형태) ===')
# ============================================
from modules.image_analyzer import GalaxyImageAnalyzer, RegionGeometry, synthetic_galaxy_image


def test_morphology_classes():
    an = GalaxyImageAnalyzer()
    expect = {'elliptical': 'Early', 'spiral': 'Late', 'irregular': 'Irregular', 'merger': 'Merger'}
    for kind, exp in expect.items():
        img = np.asarray(synthetic_galaxy_image(kind).convert('RGB'))
        H, W = img.shape[:2]
        yy, xx = np.mgrid[:H, :W]
        mask = (xx - W / 2) ** 2 + (yy - H / 2) ** 2 < (0.45 * min(H, W)) ** 2
        res = an.analyze(img, mask)
        assert not res.get('error'), res.get('error')
        cls = res['morphology']['class_en']
        m = res['metrics']
        print('    %-10s -> %-18s C=%.2f A=%.2f G=%.2f M20=%.2f n=%s' % (
            kind, cls, m['C_sdss'], m['asymmetry'], m['gini'], m['m20'], m.get('sersic_n')))
        assert cls.startswith(exp), '%s classified as %s' % (kind, cls)
        for k in ('stats', 'metrics', 'profile', 'segmentation', 'cutout', 'ml_features'):
            assert k in res


test('morphology_classes', test_morphology_classes)


def test_region_geometry():
    """fabric.js 객체 → 원본 해상도 마스크 (스케일/회전 반영)"""
    shape = (400, 600)
    scale = 0.5    # 캔버스는 원본의 절반 크기
    rect = {'type': 'rect', 'left': 50, 'top': 40, 'width': 100, 'height': 60, 'originX': 'left',
            'originY': 'top', 'strokeWidth': 0, 'scaleX': 1, 'scaleY': 1, 'angle': 0}
    m, k = RegionGeometry.object_to_mask(rect, shape, scale)
    ys, xs = np.nonzero(m)
    assert k == 'rect' and abs(xs.min() - 100) <= 2 and abs(xs.max() - 300) <= 2 and abs(ys.min() - 80) <= 2
    circ = {'type': 'circle', 'left': 100, 'top': 100, 'radius': 20, 'originX': 'left', 'originY': 'top',
            'strokeWidth': 0, 'scaleX': 1, 'scaleY': 1, 'angle': 0}
    m, _ = RegionGeometry.object_to_mask(circ, shape, scale)
    area = m.sum()
    assert abs(area - np.pi * 40 ** 2) / (np.pi * 40 ** 2) < 0.05, 'circle area %d' % area
    rot_base = dict(rect, left=200, top=60)          # fabric 은 originX/Y(좌상단) 기준으로 회전
    rot = dict(rot_base, angle=90)
    m1, _ = RegionGeometry.object_to_mask(rot_base, shape, scale)
    m2, _ = RegionGeometry.object_to_mask(rot, shape, scale)
    ys2, xs2 = np.nonzero(m2)
    assert abs(int(m2.sum()) - int(m1.sum())) < 0.03 * m1.sum(), 'rotated area changed'
    assert xs2.max() <= 402 and xs2.min() >= 278 and ys2.max() >= 315, 'rotation about origin corner wrong'
    path = {'type': 'path', 'path': [['M', 10, 10], ['L', 60, 10], ['L', 60, 60], ['L', 10, 60]],
            'left': 10, 'top': 10, 'width': 50, 'height': 50, 'originX': 'left', 'originY': 'top',
            'strokeWidth': 0, 'scaleX': 1, 'scaleY': 1, 'angle': 0, 'pathOffset': {'x': 35, 'y': 35}}
    ma, _ = RegionGeometry.object_to_mask(path, shape, scale, 'area')
    ms, _ = RegionGeometry.object_to_mask(path, shape, scale, 'stroke')
    assert ma.sum() > ms.sum() > 0


test('region_geometry', test_region_geometry)


def test_line_cut_and_color():
    img = np.asarray(synthetic_galaxy_image('spiral').convert('RGB'))
    d, v = GalaxyImageAnalyzer.line_cut(img, 0, 0, img.shape[1] - 1, img.shape[0] - 1)
    assert len(d) == len(v) > 10
    ur = GalaxyImageAnalyzer.estimate_ur_from_rgb(0.1)
    assert 0.5 < ur < 4.0


test('line_cut_color', test_line_cut_and_color)

# ============================================
print()
print('=== 4. Phase Space Mapper ===')
# ============================================
from modules.phase_space_mapper import PhaseSpaceMapper

mapper = PhaseSpaceMapper(MASTER_CSV)


def test_mapper_all_plots():
    assert len(mapper.df) > 0, 'empty dataframe'
    assert mapper.plot_bpt(-0.3, 0.5) is not None
    assert mapper.plot_sfms(10.5, 0.5) is not None
    assert mapper.plot_mzr(10.5, 8.8) is not None
    assert mapper.plot_color_mass(10.5, 2.0) is not None
    assert mapper.plot_3d_fmr(10.5, 0.5, 8.8) is not None
    assert mapper.plot_summary_4panel({'log_nii_ha': -0.3, 'log_oiii_hb': 0.5, 'log_mass': 10.5, 'log_sfr': 0.5,
                                       'metallicity': 8.8, 'color_ur': 2.0}) is not None
    assert mapper.plot_bpt(None, None) is not None


test('mapper_all_plots', test_mapper_all_plots)


def test_mapper_context():
    t = {'log_mass': 10.5, 'log_sfr': 0.3, 'metallicity': 8.9, 'color_ur': 2.2, 'log_nii_ha': -0.4,
         'log_oiii_hb': -0.3}
    pr = mapper.percentile_ranks(t)
    assert not pr.empty and pr['백분위(%)'].between(0, 100).all()
    ms = mapper.sfms_offset(10.5, 0.3)
    assert ms and 'delta_ms' in ms
    sim = mapper.find_similar(t, k=10)
    assert sim and len(sim['neighbors']) == 10
    print('    ΔMS=%+.2f (%s), kNN vote=%s' % (ms['delta_ms'], ms['state'],
                                            dict(sim['vote'].head(3)) if sim['vote'] is not None else None))


test('mapper_context', test_mapper_context)

# ============================================
print()
print('=== 5. ML Predictor ===')
# ============================================
from modules.ml_predictor import GalaxyPredictor

pred = GalaxyPredictor(MODEL_DIR, master_csv=MASTER_CSV)


def test_predictor_full():
    assert pred.is_loaded, 'models not loaded: %s' % pred.load_error
    props = {'log_stellar_mass': 10.5, 'log_sfr': 0.5, 'log_ssfr': -10.0, 'metallicity_oh': 8.8, 'color_u_r': 2.0,
             'log_nii_ha': -0.3, 'log_oiii_hb': 0.2, 'z': 0.05, 'velDisp': 150, 'd4000_n': 1.5}
    t = pred.predict_galaxy_type(props)
    for k in ('predicted_class', 'probabilities', 'top_3', 'confidence', 'coverage'):
        assert k in t, 'missing %s' % k
    print('    type: %s (%.1f%%) %s' % (t['predicted_class'], t['confidence'] * 100,
                                       '[fallback model]' if pred.is_fallback else ''))
    c = pred.predict_evolution_cluster(props)
    assert 'cluster_name' in c
    imp = pred.get_feature_importance(props)
    assert pred.create_probability_chart(t['probabilities']) is not None
    assert pred.create_feature_importance_chart(imp) is not None
    assert pred.create_evolution_gauge(54.3) is not None


test('predictor_full', test_predictor_full)


def test_predictor_partial_and_xai():
    props = {'log_nii_ha': -0.3, 'log_oiii_hb': 0.2}
    t = pred.predict_galaxy_type(props)
    cov = pred.feature_coverage(props)
    assert 0 <= cov['weighted'] < 0.5
    ex = pred.explain_local({'log_mass': 10.8, 'color_ur': 2.6, 'log_sfr': -0.5, 'metallicity': 9.0})
    assert isinstance(ex, list)
    assert pred.create_local_explanation_chart(ex, t['predicted_class']) is not None
    print('    partial type: %s, coverage=%.0f%%, xai rows=%d' % (t['predicted_class'], cov['weighted'] * 100, len(ex)))


test('predictor_partial_xai', test_predictor_partial_and_xai)

# ============================================
print()
print('=== 6. SDSS Fetcher ===')
# ============================================
from modules.sdss_fetcher import SDSSFetcher


def test_sdss_samples():
    samples = SDSSFetcher().get_sample_galaxies()
    assert len(samples) >= 3, 'too few samples'
    for s in samples:
        for k in ['name', 'ra', 'dec', 'log_mass', 'log_sfr', 'metallicity', 'color_ur', 'log_nii_ha', 'log_oiii_hb']:
            assert k in s, 'sample missing key: %s in %s' % (k, s.get('name', '?'))


test('sdss_samples', test_sdss_samples)

# ============================================
print()
print('=== 7. Report Generator ===')
# ============================================
from modules.report_generator import ReportGenerator


def test_report_full():
    rg = ReportGenerator()
    analysis = {
        'target_name': 'M31 <test>', 'analysis_datetime': '2026-10-01 22:00:00', 'input_mode': 'test',
        'ebv': 0.15, 'log_sfr': -0.5, 'metallicity': 8.9, 'metallicity_method': 'N2',
        'log_nii_ha': -0.4, 'log_oiii_hb': -0.2, 'bpt_class': 'Star-Forming', 'predicted_type': 'Spiral',
        'confidence': 0.85, 'top_3_types': [('Spiral', 0.85), ('Barred Spiral', 0.10), ('Irregular', 0.05)],
        'evolution_cluster': 'Growth', 'gei_score': 35.0, 'evolution_stage': 'Growth Phase',
        'log_mass': 10.8, 'color_ur': 2.1, 'z': 0.001, 'd4000': 1.4, 'electron_density': 120.0,
        'morphology': {'class': '만기형 (나선/원반)', 'reasons': ['C 낮음']},
        'photometry': {'집중도 C': '2.3'}, 'notes': ['테스트 메모'],
        'sfms': {'delta_ms': 0.1, 'state': '주계열'},
    }
    md = rg.generate_markdown(analysis)
    assert len(md) > 100
    html = rg.generate_html(md)
    assert '<html' in html.lower()
    assert '<test>' not in html, 'HTML not escaped'
    assert '85.0%' in md or '85%' in md, 'confidence formatting wrong'
    summary = rg.generate_summary_card(analysis)
    assert 'metrics' in summary
    print('    md=%d chars, html=%d chars, card=%d metrics' % (len(md), len(html), len(summary['metrics'])))


test('report_full', test_report_full)


def test_report_empty():
    md = ReportGenerator().generate_markdown({})
    assert md is not None


test('report_empty', test_report_empty)

# ============================================
print()
print('=== 8. 전체 파이프라인 (샘플 은하) ===')
# ============================================


def test_app_sample_flow():
    sample = SDSSFetcher().get_sample_galaxies()[0]
    props = dict(sample)
    props.update({'log_stellar_mass': props['log_mass'], 'metallicity_oh': props['metallicity'],
                  'color_u_r': props['color_ur']})
    props['log_ssfr'] = calc.calculate_log_ssfr(props['log_sfr'], props['log_mass']) or -10.5
    props['bpt_class'] = calc.classify_bpt(props['log_nii_ha'], props['log_oiii_hb'])['class']
    gei = calc.calculate_gei(props['log_mass'], props['log_ssfr'], props['metallicity'], props['color_ur'])
    stage = calc.diagnose_evolution_stage(gei)
    t = pred.predict_galaxy_type(props)
    c = pred.predict_evolution_cluster(props)
    md = ReportGenerator().generate_markdown({
        'target_name': sample['name'], 'input_mode': 'sample', 'log_sfr': props['log_sfr'],
        'metallicity': props['metallicity'], 'bpt_class': props['bpt_class'],
        'predicted_type': t['predicted_class'], 'confidence': t['confidence'], 'top_3_types': t['top_3'],
        'evolution_cluster': c['cluster_name'], 'gei_score': gei, 'evolution_stage': stage['stage'],
        'log_mass': props['log_mass'], 'color_ur': props['color_ur'], 'z': props.get('z', 0)})
    assert len(md) > 100
    print('    %s: GEI=%.1f (%s), AI=%s' % (sample['name'], gei, stage['stage'], t['predicted_class']))


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
sys.exit(1 if errors else 0)
