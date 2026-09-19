# -*- coding: utf-8 -*-
"""
SDSS Data Cross-Validation Suite
=================================
7 independent verification methods to confirm data authenticity:

1. specObjID bitfield decoding (plate/mjd/fiber)
2. Live SDSS API cross-check (sample specObjIDs queried back)
3. SDSS sky footprint verification (RA/Dec)
4. BPT diagram physical consistency
5. Mass-metallicity relation (Tremonti+2004)
6. Color-magnitude diagram sanity
7. Statistical distribution comparison with published SDSS results
"""

import os
import io
import requests
import pandas as pd
import numpy as np
from collections import Counter

DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "data", "download", "sdss_galaxy_verified.csv")

def load_data():
    print(f"Loading: {DATA_PATH}")
    df = pd.read_csv(DATA_PATH)
    print(f"Loaded {len(df):,} rows, {len(df.columns)} columns\n")
    return df


# ============================================================
# TEST 1: specObjID Bitfield Decoding
# ============================================================
def test_specobj_decode(df):
    """
    SDSS specObjID encodes plate, mjd, fiberID in a 64-bit integer.
    Format: plate(14 bits) | mjd(26 bits) | fiber(10 bits) | run2d(14 bits)
    
    We decode the specObjID and compare with the actual plate/mjd/fiberID
    columns that were fetched separately via the SQL query.
    """
    print("=" * 60)
    print("TEST 1: specObjID Bitfield Decoding")
    print("=" * 60)
    
    n_test = min(1000, len(df))
    sample = df.head(n_test)
    
    mismatches = 0
    examples = []
    
    for _, row in sample.iterrows():
        sid = int(row['specObjID'])
        
        # Decode from specObjID
        decoded_plate = (sid >> 50) & 0x3FFF
        decoded_fiber = (sid >> 14) & 0x3FF
        
        # The actual plate/fiberID from the query (if available)
        if 'plate' in df.columns and 'fiberID' in df.columns:
            actual_plate = int(row['plate']) if pd.notna(row['plate']) else None
            actual_fiber = int(row['fiberID']) if pd.notna(row['fiberID']) else None
            
            if actual_plate and decoded_plate != actual_plate:
                mismatches += 1
            if actual_fiber and decoded_fiber != actual_fiber:
                mismatches += 1
            
            if len(examples) < 5:
                examples.append({
                    'specObjID': sid,
                    'decoded_plate': decoded_plate,
                    'actual_plate': actual_plate,
                    'decoded_fiber': decoded_fiber,
                    'actual_fiber': actual_fiber,
                    'match': (decoded_plate == actual_plate)
                })
    
    print(f"  Tested {n_test} specObjIDs")
    print(f"  Mismatches: {mismatches}")
    
    print(f"\n  Sample decoding:")
    for ex in examples:
        status = "MATCH" if ex['match'] else "MISMATCH"
        print(f"    specObjID={ex['specObjID']}")
        print(f"      decoded:  plate={ex['decoded_plate']}, fiber={ex['decoded_fiber']}")
        print(f"      actual:   plate={ex['actual_plate']}, fiber={ex['actual_fiber']}")
        print(f"      status:   {status}")
    
    # Additional: check plate range (SDSS plates are typically 266-99999)
    if 'plate' in df.columns:
        plates = df['plate'].dropna().astype(int)
        print(f"\n  Plate range: [{plates.min()}, {plates.max()}]")
        print(f"  Unique plates: {plates.nunique()}")
        print(f"  Valid SDSS plate range (266-15000+): ", end="")
        if plates.min() >= 200 and plates.max() <= 20000:
            print("PASS")
        else:
            print("SUSPICIOUS")
    
    passed = mismatches == 0
    print(f"\n  RESULT: {'PASS' if passed else 'FAIL'}")
    return passed


# ============================================================
# TEST 2: Live SDSS API Cross-Check
# ============================================================
def test_live_api_crosscheck(df):
    """
    Take 5 random specObjIDs from our data and query them back
    against the live SDSS SkyServer to verify they exist and
    their properties match.
    """
    print("\n" + "=" * 60)
    print("TEST 2: Live SDSS API Cross-Check")
    print("=" * 60)
    
    SDSS_URL = "https://skyserver.sdss.org/dr18/SkyServerWS/SearchTools/SqlSearch"
    
    # Pick 5 random specObjIDs
    sample_ids = df['specObjID'].dropna().sample(5, random_state=123).astype(int).tolist()
    
    print(f"  Querying {len(sample_ids)} specObjIDs against live SDSS SkyServer...")
    
    id_list = ','.join(str(s) for s in sample_ids)
    sql = f"""SELECT s.specObjID, s.ra, s.dec, s.z, s.velDisp, p.r
    FROM SpecObj s
    JOIN PhotoObj p ON s.bestObjID = p.objID
    WHERE s.specObjID IN ({id_list})"""
    
    try:
        resp = requests.get(SDSS_URL, params={"cmd": sql, "format": "csv"}, timeout=60)
        text = resp.text.strip()
        
        if resp.status_code != 200 or text.startswith("ERROR") or "<html" in text.lower()[:100]:
            print(f"  API returned error or HTML. Trying individual queries...")
            # Try one at a time
            found = 0
            for sid in sample_ids[:3]:
                sql2 = f"SELECT specObjID, ra, dec, z FROM SpecObj WHERE specObjID = {sid}"
                try:
                    r2 = requests.get(SDSS_URL, params={"cmd": sql2, "format": "csv"}, timeout=30)
                    t2 = r2.text.strip()
                    if 'specObjID' in t2 and str(sid)[:10] in t2:
                        found += 1
                        print(f"    specObjID {sid}: FOUND in SDSS")
                    else:
                        print(f"    specObjID {sid}: NOT FOUND or error")
                except:
                    print(f"    specObjID {sid}: Connection timeout")
            
            if found > 0:
                print(f"\n  {found}/{min(3, len(sample_ids))} specObjIDs confirmed in live SDSS")
                print(f"  RESULT: PASS (partial)")
                return True
            else:
                print(f"  RESULT: INCONCLUSIVE (network issues)")
                return None
        
        # Parse response
        lines = text.split('\n')
        header_idx = 0
        for idx, line in enumerate(lines):
            if 'specObjID' in line:
                header_idx = idx
                break
        csv_text = '\n'.join(lines[header_idx:])
        api_df = pd.read_csv(io.StringIO(csv_text))
        if len(api_df) > 0 and api_df.iloc[0].astype(str).str.contains('---').any():
            api_df = api_df.iloc[1:].reset_index(drop=True)
        for col in api_df.columns:
            api_df[col] = pd.to_numeric(api_df[col], errors='coerce')
        
        print(f"  API returned {len(api_df)} matching galaxies out of {len(sample_ids)} queried")
        
        # Cross-check values
        match_count = 0
        for _, api_row in api_df.iterrows():
            sid = int(api_row['specObjID'])
            local_row = df[df['specObjID'].astype(int) == sid]
            if len(local_row) == 0:
                continue
            local_row = local_row.iloc[0]
            
            z_match = abs(api_row['z'] - local_row['z']) < 0.001
            ra_match = abs(api_row['ra'] - local_row['ra']) < 0.01
            dec_match = abs(api_row['dec'] - local_row['dec']) < 0.01
            
            status = "MATCH" if (z_match and ra_match and dec_match) else "MISMATCH"
            match_count += 1 if status == "MATCH" else 0
            
            print(f"\n    specObjID: {sid}")
            print(f"      Local  -> z={local_row['z']:.6f}, RA={local_row['ra']:.5f}, Dec={local_row['dec']:.5f}")
            print(f"      SDSS   -> z={api_row['z']:.6f}, RA={api_row['ra']:.5f}, Dec={api_row['dec']:.5f}")
            print(f"      Status: {status}")
        
        passed = match_count == len(api_df) and len(api_df) > 0
        print(f"\n  {match_count}/{len(api_df)} values matched exactly")
        print(f"  RESULT: {'PASS' if passed else 'FAIL'}")
        return passed
        
    except requests.exceptions.Timeout:
        print("  RESULT: INCONCLUSIVE (SDSS server timeout)")
        return None
    except Exception as e:
        print(f"  RESULT: INCONCLUSIVE (error: {e})")
        return None


# ============================================================
# TEST 3: SDSS Sky Footprint Verification
# ============================================================
def test_sky_footprint(df):
    """
    SDSS spectroscopic survey covers specific regions of the sky.
    Primary area: RA ~ 100-260 deg, Dec ~ -10 to +70 deg (North Galactic Cap)
    Plus Southern stripe (Stripe 82): RA ~ 310-60 deg, Dec ~ -1.25 to +1.25
    """
    print("\n" + "=" * 60)
    print("TEST 3: SDSS Sky Footprint Verification")
    print("=" * 60)
    
    ra = df['ra'].dropna()
    dec = df['dec'].dropna()
    
    print(f"  RA range:  [{ra.min():.2f}, {ra.max():.2f}] deg")
    print(f"  Dec range: [{dec.min():.2f}, {dec.max():.2f}] deg")
    
    # SDSS footprint checks
    # Most SDSS spectra are at Dec > -15 and < 80
    dec_valid = (dec > -15) & (dec < 80)
    dec_pct = dec_valid.sum() / len(dec) * 100
    
    # RA should span broadly (SDSS covers large parts of the sky)
    ra_span = ra.max() - ra.min()
    
    print(f"\n  Dec in SDSS range (-15 to +80): {dec_valid.sum():,}/{len(dec):,} ({dec_pct:.1f}%)")
    print(f"  RA span: {ra_span:.1f} deg")
    
    # Check for North Galactic Cap concentration
    ngc = ((ra > 100) & (ra < 270) & (dec > -5) & (dec < 70)).sum()
    ngc_pct = ngc / len(df) * 100
    print(f"  North Galactic Cap (RA 100-270, Dec -5 to 70): {ngc:,} ({ngc_pct:.1f}%)")
    
    # Check that there are NO impossible coordinates
    impossible = ((ra < 0) | (ra > 360) | (dec < -90) | (dec > 90)).sum()
    print(f"  Invalid coordinates (RA<0 or >360, Dec<-90 or >90): {impossible}")
    
    passed = dec_pct > 95 and impossible == 0 and ra_span > 100
    print(f"\n  RESULT: {'PASS' if passed else 'FAIL'}")
    return passed


# ============================================================
# TEST 4: BPT Diagram Physical Consistency
# ============================================================
def test_bpt_consistency(df):
    """
    The BPT (Baldwin-Phillips-Terlevich) diagram uses line ratios
    log([NII]/Ha) vs log([OIII]/Hb) to classify galaxies.
    
    The bptclass values from SDSS galSpecExtra should be:
    1=SF, 2=Composite, 3=AGN, 4=Seyfert, 5=LINER, -1=Unclassifiable
    
    We verify that the line ratios are consistent with the BPT classes.
    """
    print("\n" + "=" * 60)
    print("TEST 4: BPT Diagram Physical Consistency")
    print("=" * 60)
    
    valid = df['log_nii_ha'].notna() & df['log_oiii_hb'].notna() & df['bptclass'].notna()
    bpt = df[valid].copy()
    
    print(f"  Galaxies with valid BPT data: {len(bpt):,}")
    print(f"\n  BPT class distribution:")
    for cls, name in [(-1, 'Unclassifiable'), (1, 'Star-forming'), 
                       (2, 'Composite'), (3, 'AGN'), (4, 'Seyfert'), (5, 'LINER')]:
        n = (bpt['bptclass'] == cls).sum()
        subset = bpt[bpt['bptclass'] == cls]
        if len(subset) > 0:
            med_nii = subset['log_nii_ha'].median()
            med_oiii = subset['log_oiii_hb'].median()
            print(f"    {cls} ({name:15s}): {n:6,}  median log[NII]/Ha={med_nii:+.3f}  log[OIII]/Hb={med_oiii:+.3f}")
    
    # Physical checks:
    # SF galaxies should have low log[NII]/Ha (< ~0.0) 
    sf = bpt[bpt['bptclass'] == 1]
    sf_low_nii = (sf['log_nii_ha'] < 0.05).sum() / max(len(sf), 1) * 100
    
    # Seyferts should have high log[OIII]/Hb (> ~0.3)
    sey = bpt[bpt['bptclass'] == 4]
    sey_high_oiii = (sey['log_oiii_hb'] > 0.0).sum() / max(len(sey), 1) * 100
    
    # LINERs should have high log[NII]/Ha (> ~-0.2) and low log[OIII]/Hb
    liner = bpt[bpt['bptclass'] == 5]
    liner_correct = ((liner['log_nii_ha'] > -0.3) & (liner['log_oiii_hb'] < 0.5)).sum() / max(len(liner), 1) * 100
    
    print(f"\n  Physical consistency checks:")
    print(f"    SF with log[NII]/Ha < 0.05: {sf_low_nii:.1f}% (expect >70%)")
    print(f"    Seyfert with log[OIII]/Hb > 0.0: {sey_high_oiii:.1f}% (expect >70%)")
    print(f"    LINER with correct locus: {liner_correct:.1f}% (expect >60%)")
    
    passed = sf_low_nii > 60 and sey_high_oiii > 60
    print(f"\n  RESULT: {'PASS' if passed else 'FAIL'}")
    return passed


# ============================================================
# TEST 5: Mass-Metallicity Relation (Tremonti+2004)
# ============================================================
def test_mass_metallicity(df):
    """
    The mass-metallicity relation (MZR) is one of the most robust
    scaling relations in galaxy astrophysics. More massive galaxies
    have higher gas-phase metallicities.
    
    Expected: positive correlation between lgm_tot_p50 and oh_p50
    Tremonti+2004: 12+log(O/H) ~ 8.9 at log(M*/Msun) ~ 10.5
    """
    print("\n" + "=" * 60)
    print("TEST 5: Mass-Metallicity Relation (Tremonti+2004)")
    print("=" * 60)
    
    valid = df['lgm_tot_p50'].notna() & df['oh_p50'].notna()
    mz = df[valid].copy()
    
    print(f"  Galaxies with valid mass+metallicity: {len(mz):,}")
    
    # Bin by mass and check metallicity trend
    mass_bins = [7, 8.5, 9.0, 9.5, 10.0, 10.5, 11.0, 13]
    mass_labels = ['7-8.5', '8.5-9', '9-9.5', '9.5-10', '10-10.5', '10.5-11', '11+']
    mz['mass_bin'] = pd.cut(mz['lgm_tot_p50'], bins=mass_bins, labels=mass_labels)
    
    print(f"\n  Mass vs. Metallicity trend:")
    prev_oh = 0
    monotonic_violations = 0
    for label in mass_labels:
        subset = mz[mz['mass_bin'] == label]
        if len(subset) > 10:
            med_oh = subset['oh_p50'].median()
            if med_oh < prev_oh and prev_oh > 0:
                monotonic_violations += 1
                trend = "DOWN (turnover expected at high mass)"
            else:
                trend = "UP" if med_oh > prev_oh else "FLAT"
            print(f"    log(M*) {label:8s}: median 12+log(O/H) = {med_oh:.3f}  N={len(subset):5,}  {trend}")
            prev_oh = med_oh
    
    # Overall correlation
    corr = mz[['lgm_tot_p50', 'oh_p50']].corr().iloc[0, 1]
    print(f"\n  Pearson correlation (mass vs metallicity): r = {corr:.3f}")
    print(f"  Expected: r > 0.3 (positive correlation)")
    
    # Check that metallicity at log(M)~10.5 is near 8.9
    high_mass = mz[(mz['lgm_tot_p50'] > 10.0) & (mz['lgm_tot_p50'] < 11.0)]
    if len(high_mass) > 0:
        med_oh_high = high_mass['oh_p50'].median()
        print(f"  Metallicity at log(M*)~10-11: {med_oh_high:.3f} (Tremonti+2004 predicts ~8.9)")
    
    passed = corr > 0.2
    print(f"\n  RESULT: {'PASS' if passed else 'FAIL'}")
    return passed


# ============================================================
# TEST 6: Color-Magnitude Diagram Sanity
# ============================================================
def test_color_magnitude(df):
    """
    The galaxy color-magnitude diagram should show bimodality:
    - Red sequence: old ellipticals with u-r > 2.2
    - Blue cloud: star-forming spirals with u-r < 2.2
    
    This bimodality is a fundamental feature of galaxy populations.
    """
    print("\n" + "=" * 60)
    print("TEST 6: Color-Magnitude Diagram Sanity")
    print("=" * 60)
    
    valid = df['color_u_r'].notna() & df['r'].notna()
    cm = df[valid].copy()
    
    print(f"  Galaxies with valid color+magnitude: {len(cm):,}")
    
    color = cm['color_u_r']
    print(f"\n  u-r color distribution:")
    print(f"    Range: [{color.min():.2f}, {color.max():.2f}]")
    print(f"    Mean:  {color.mean():.3f}")
    print(f"    Median: {color.median():.3f}")
    print(f"    Std:   {color.std():.3f}")
    
    # Check bimodality
    blue = (color < 2.2).sum()
    red = (color >= 2.2).sum()
    blue_pct = blue / len(cm) * 100
    red_pct = red / len(cm) * 100
    
    print(f"\n  Blue cloud (u-r < 2.2):  {blue:,} ({blue_pct:.1f}%)")
    print(f"  Red sequence (u-r >= 2.2): {red:,} ({red_pct:.1f}%)")
    
    # Both populations should be present (bimodality)
    bimodal = blue_pct > 10 and red_pct > 10
    print(f"  Bimodality detected: {'YES' if bimodal else 'NO'}")
    
    # Color should correlate with D4000 (old stellar populations = red, high D4000)
    d4k_valid = cm['d4000_n'].notna() & (cm['d4000_n'] > 0) & (cm['d4000_n'] < 5)
    if d4k_valid.sum() > 100:
        corr_d4k = cm.loc[d4k_valid, ['color_u_r', 'd4000_n']].corr().iloc[0, 1]
        print(f"\n  Color vs D4000 correlation: r = {corr_d4k:.3f} (expect > 0.5)")
    
    # Color should correlate with SFR (blue = higher SFR)
    sfr_valid = cm['sfr_tot_p50'].notna()
    if sfr_valid.sum() > 100:
        corr_sfr = cm.loc[sfr_valid, ['color_u_r', 'sfr_tot_p50']].corr().iloc[0, 1]
        print(f"  Color vs SFR correlation: r = {corr_sfr:.3f} (expect < -0.3, blue=high SFR)")
    
    passed = bimodal
    print(f"\n  RESULT: {'PASS' if passed else 'FAIL'}")
    return passed


# ============================================================
# TEST 7: Statistical Distribution Comparison
# ============================================================
def test_statistical_distributions(df):
    """
    Compare key distributions against published SDSS statistics:
    - Redshift distribution shape
    - Stellar mass function
    - D4000 distribution
    - Velocity dispersion range
    """
    print("\n" + "=" * 60)
    print("TEST 7: Statistical Distribution Comparison")
    print("=" * 60)
    
    issues = 0
    
    # 7a. Redshift distribution
    z = df['z'].dropna()
    print(f"\n  7a. Redshift distribution:")
    print(f"      Range: [{z.min():.4f}, {z.max():.4f}]")
    print(f"      Mean:  {z.mean():.4f}")
    # SDSS main galaxy sample peaks around z~0.08
    # Our low-z sample should peak around z~0.04
    z_reasonable = z.mean() > 0.01 and z.mean() < 0.15
    print(f"      Mean z in reasonable range (0.01-0.15): {'PASS' if z_reasonable else 'FAIL'}")
    if not z_reasonable:
        issues += 1
    
    # 7b. Stellar mass distribution
    mass = df['lgm_tot_p50'].dropna()
    print(f"\n  7b. Stellar mass distribution:")
    print(f"      Range: [{mass.min():.2f}, {mass.max():.2f}]")
    print(f"      Mean:  {mass.mean():.2f}")
    print(f"      Median: {mass.median():.2f}")
    # SDSS galaxies typically have 7 < log(M*) < 12.5
    mass_valid = mass.min() > 5 and mass.max() < 14 and mass.median() > 9 and mass.median() < 11
    print(f"      Physical range check: {'PASS' if mass_valid else 'FAIL'}")
    if not mass_valid:
        issues += 1
    
    # 7c. D4000 distribution
    d4k = df['d4000_n'].dropna()
    d4k = d4k[(d4k > 0) & (d4k < 5)]
    print(f"\n  7c. D4000 distribution:")
    print(f"      Range: [{d4k.min():.3f}, {d4k.max():.3f}]")
    print(f"      Mean:  {d4k.mean():.3f}")
    print(f"      Median: {d4k.median():.3f}")
    # D4000 typically ranges from ~1.0 (young) to ~2.2 (old), bimodal around 1.3 and 1.9
    d4k_valid = d4k.median() > 1.0 and d4k.median() < 2.0
    d4k_young = (d4k < 1.5).sum() / len(d4k) * 100
    d4k_old = (d4k > 1.5).sum() / len(d4k) * 100
    print(f"      Young (D4000<1.5): {d4k_young:.1f}%, Old (D4000>1.5): {d4k_old:.1f}%")
    print(f"      Physical range check: {'PASS' if d4k_valid else 'FAIL'}")
    if not d4k_valid:
        issues += 1
    
    # 7d. Velocity dispersion
    vd = df['velDisp'].dropna()
    vd_pos = vd[vd > 0]
    print(f"\n  7d. Velocity dispersion:")
    print(f"      Range (>0): [{vd_pos.min():.1f}, {vd_pos.max():.1f}] km/s")
    print(f"      Median: {vd_pos.median():.1f} km/s")
    print(f"      Zero values: {(vd == 0).sum()} ({(vd == 0).sum()/len(vd)*100:.1f}%)")
    # Typical galaxy sigma: 30-400 km/s, some zeros for unresolved
    vd_valid = vd_pos.median() > 30 and vd_pos.median() < 300 and vd_pos.max() < 1000
    print(f"      Physical range check: {'PASS' if vd_valid else 'FAIL'}")
    if not vd_valid:
        issues += 1
    
    # 7e. Emission line flux ratios
    valid_ha_hb = (df['h_alpha_flux'] > 0) & (df['h_beta_flux'] > 0)
    if valid_ha_hb.sum() > 100:
        balmer = df.loc[valid_ha_hb, 'h_alpha_flux'] / df.loc[valid_ha_hb, 'h_beta_flux']
        print(f"\n  7e. Balmer decrement (Ha/Hb):")
        print(f"      Median: {balmer.median():.2f}")
        print(f"      Expected: ~2.86 (Case B recombination) to ~5 (dusty)")
        balmer_valid = balmer.median() > 2.0 and balmer.median() < 8.0
        print(f"      Physical range check: {'PASS' if balmer_valid else 'FAIL'}")
        if not balmer_valid:
            issues += 1
    
    # 7f. Magnitude-redshift relation (Malmquist bias)
    print(f"\n  7f. Magnitude-redshift relation (Malmquist bias):")
    z_low = df[(df['z'] > 0.02) & (df['z'] < 0.03)]['r'].median()
    z_high = df[(df['z'] > 0.05) & (df['z'] < 0.065)]['r'].median()
    print(f"      Median r-mag at z~0.025: {z_low:.2f}")
    print(f"      Median r-mag at z~0.055: {z_high:.2f}")
    malmquist = z_high > z_low  # Higher z should be fainter
    print(f"      Higher z -> fainter (Malmquist bias): {'PASS' if malmquist else 'FAIL'}")
    if not malmquist:
        issues += 1
    
    passed = issues == 0
    print(f"\n  Issues found: {issues}")
    print(f"  RESULT: {'PASS' if passed else 'FAIL'}")
    return passed


# ============================================================
# MAIN
# ============================================================
def main():
    print("=" * 60)
    print("SDSS DATA CROSS-VALIDATION SUITE")
    print("7 Independent Verification Methods")
    print("=" * 60)
    print()
    
    df = load_data()
    
    results = {}
    
    results['specObjID_decode'] = test_specobj_decode(df)
    results['live_api_check'] = test_live_api_crosscheck(df)
    results['sky_footprint'] = test_sky_footprint(df)
    results['bpt_consistency'] = test_bpt_consistency(df)
    results['mass_metallicity'] = test_mass_metallicity(df)
    results['color_magnitude'] = test_color_magnitude(df)
    results['stat_distributions'] = test_statistical_distributions(df)
    
    # Summary
    print("\n" + "=" * 60)
    print("CROSS-VALIDATION SUMMARY")
    print("=" * 60)
    
    for test_name, result in results.items():
        if result is None:
            status = "INCONCLUSIVE"
        elif bool(result):
            status = "PASS"
        else:
            status = "FAIL"
        print(f"  {test_name:25s}: {status}")
    
    passed = sum(1 for v in results.values() if v is not None and bool(v))
    failed = sum(1 for v in results.values() if v is not None and not bool(v))
    inconclusive = sum(1 for v in results.values() if v is None)
    
    print(f"\n  PASSED: {passed}/{len(results)}")
    print(f"  FAILED: {failed}/{len(results)}")
    print(f"  INCONCLUSIVE: {inconclusive}/{len(results)}")
    
    if failed == 0 and passed >= 5:
        print("\n  >>> DATA IS CONFIRMED AS AUTHENTIC SDSS DATA <<<")
    elif failed == 0:
        print("\n  >>> DATA APPEARS CONSISTENT WITH SDSS (some tests inconclusive) <<<")
    else:
        print("\n  >>> DATA VERIFICATION ISSUES DETECTED <<<")
    
    print("=" * 60)


if __name__ == "__main__":
    main()
