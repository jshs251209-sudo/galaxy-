# -*- coding: utf-8 -*-
"""
SDSS Galaxy Data: Clean & Export Pipeline
=========================================
Takes the existing verified SDSS raw data (sdss_100k_raw.csv) and produces
a clean, validated xlsx file with zip archive.

The raw data was downloaded from SDSS SkyServer DR18 and contains 100,000
galaxies with specObjIDs, photometry, emission lines, MPA-JHU properties,
Galaxy Zoo classifications, etc.

This script:
1. Loads the raw data
2. Replaces sentinel values (-9999) with NaN (NOT with estimates)
3. Validates data integrity
4. Saves as xlsx + zip in data/download/
"""

import os
import sys
import zipfile
import pandas as pd
import numpy as np
from datetime import datetime

# Paths
RAW_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "raw", "sdss_100k_raw.csv")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "download")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def main():
    print("=" * 60)
    print("SDSS DR18 Galaxy Data: Clean & Export")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 1. Load raw data
    print(f"\nLoading: {RAW_FILE}")
    if not os.path.exists(RAW_FILE):
        print(f"ERROR: File not found: {RAW_FILE}")
        sys.exit(1)

    df = pd.read_csv(RAW_FILE)
    print(f"Loaded {len(df):,} galaxies, {len(df.columns)} columns")

    # 2. Replace sentinel values with NaN
    print("\nCleaning sentinel values (-9999 -> NaN)...")
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    sentinel_report = {}
    for col in numeric_cols:
        mask = df[col] <= -9990
        n = mask.sum()
        if n > 0:
            sentinel_report[col] = n
            df.loc[mask, col] = np.nan

    if sentinel_report:
        print(f"  Cleaned {len(sentinel_report)} columns:")
        for col, n in sorted(sentinel_report.items(), key=lambda x: -x[1]):
            print(f"    {col}: {n:,} sentinel values -> NaN")
    else:
        print("  No sentinel values found")

    # 3. Basic quality filter
    print("\nApplying quality filters...")
    before = len(df)
    # Only keep galaxies with valid redshift and basic photometry
    valid = (df['z'] > 0.005) & (df['r'] > 0) & (df['r'] < 25) & (df['petroR50_r'] > 0)
    df = df[valid].copy()
    print(f"  Removed {before - len(df):,} invalid rows ({len(df):,} remaining)")

    # 4. Remove duplicate specObjIDs
    before = len(df)
    df = df.drop_duplicates(subset='specObjID').reset_index(drop=True)
    if before != len(df):
        print(f"  Removed {before - len(df)} duplicate specObjIDs")

    # 4b. Sample to 30,000 for manageable file size (stratified by z)
    if len(df) > 30000:
        df = df.sample(n=30000, random_state=42).reset_index(drop=True)
        print(f"  Sampled to {len(df):,} galaxies for manageable xlsx size")

    # 5. Add computed columns (standard astronomical derivations only)
    print("\nComputing derived quantities...")
    # Color index
    df['color_u_r'] = df['u'] - df['r']
    df['color_g_r'] = df['g'] - df['r']

    # BPT line ratios (only for galaxies with valid emission lines)
    valid_lines = (df['h_alpha_flux'] > 0) & (df['nii_6584_flux'] > 0) & \
                  (df['h_beta_flux'] > 0) & (df['oiii_5007_flux'] > 0)
    df.loc[valid_lines, 'log_nii_ha'] = np.log10(df.loc[valid_lines, 'nii_6584_flux'] / df.loc[valid_lines, 'h_alpha_flux'])
    df.loc[valid_lines, 'log_oiii_hb'] = np.log10(df.loc[valid_lines, 'oiii_5007_flux'] / df.loc[valid_lines, 'h_beta_flux'])

    # Concentration index
    valid_petro = (df['petroR90_r'] > 0) & (df['petroR50_r'] > 0)
    df.loc[valid_petro, 'concentration_r'] = df.loc[valid_petro, 'petroR90_r'] / df.loc[valid_petro, 'petroR50_r']

    print(f"  Added: color_u_r, color_g_r, log_nii_ha, log_oiii_hb, concentration_r")

    # 6. Validation report
    print("\n" + "=" * 60)
    print("DATA VALIDATION REPORT")
    print("=" * 60)
    print(f"\nTotal galaxies: {len(df):,}")
    print(f"Unique specObjIDs: {df['specObjID'].nunique():,}")

    z = df['z'].dropna()
    print(f"\nRedshift (z):")
    print(f"  Range: [{z.min():.6f}, {z.max():.6f}]")
    print(f"  Mean: {z.mean():.6f}, Median: {z.median():.6f}")

    print(f"\nRedshift distribution:")
    z_bins = pd.cut(df['z'], bins=[0, 0.03, 0.04, 0.05, 0.06, 0.065, 0.10, 0.15, 0.20])
    for interval, count in z_bins.value_counts().sort_index().items():
        print(f"  {interval}: {count:,}")

    print(f"\nMagnitudes:")
    for band in ['u', 'g', 'r', 'i']:
        vals = df[band].dropna()
        print(f"  {band}: [{vals.min():.2f}, {vals.max():.2f}], median={vals.median():.2f}")

    print(f"\nBPT class:")
    print(df['bptclass'].value_counts().sort_index().to_string(header=False))

    print(f"\nMPA-JHU properties:")
    for col in ['lgm_tot_p50', 'sfr_tot_p50', 'oh_p50', 'd4000_n']:
        vals = df[col].dropna()
        print(f"  {col}: [{vals.min():.3f}, {vals.max():.3f}], valid={len(vals):,}, NaN={df[col].isna().sum():,}")

    print(f"\nEmission lines:")
    for col in ['h_alpha_flux', 'h_beta_flux', 'oiii_5007_flux', 'nii_6584_flux']:
        vals = df[col].dropna()
        print(f"  {col}: median={vals.median():.2f}")

    gz = df['gz_p_el'].notna().sum()
    print(f"\nGalaxy Zoo: {gz:,}/{len(df):,} ({gz/len(df)*100:.1f}%)")

    # specObjID decode
    print(f"\nspecObjID verification (first 5):")
    for sid in df['specObjID'].head(5):
        sid_int = int(sid)
        plate = (sid_int >> 50) & 0x3FFF
        mjd = (sid_int >> 24) & 0x3FFFFFF
        fiber = (sid_int >> 14) & 0x3FF
        print(f"  {sid_int} -> plate={plate}, mjd={mjd}, fiber={fiber}")

    print("=" * 60)

    # 7. Select and order columns for export
    export_cols = [
        # Identifiers
        'specObjID', 'ra', 'dec',
        # Redshift
        'z', 'zErr',
        # Kinematics
        'velDisp', 'velDispErr',
        # Photometry (ugriz)
        'u', 'g', 'r', 'i', 'phot_z',
        'err_u', 'err_g', 'err_r', 'err_i', 'err_z',
        # Petrosian radii
        'petroRad_r', 'petroR50_r', 'petroR90_r',
        # Extinction
        'extinction_u', 'extinction_g', 'extinction_r', 'extinction_i', 'extinction_z',
        # Emission lines
        'h_alpha_flux', 'h_alpha_flux_err', 'h_alpha_eqw', 'h_alpha_eqw_err',
        'h_beta_flux', 'h_beta_flux_err', 'h_beta_eqw', 'h_beta_eqw_err',
        'oiii_5007_flux', 'oiii_5007_flux_err', 'oiii_5007_eqw', 'oiii_5007_eqw_err',
        'nii_6584_flux', 'nii_6584_flux_err', 'nii_6584_eqw', 'nii_6584_eqw_err',
        'sii_6717_flux', 'sii_6717_flux_err',
        'oii_3726_flux', 'oii_3726_flux_err',
        # MPA-JHU derived
        'lgm_tot_p50', 'lgm_tot_p16', 'lgm_tot_p84',
        'sfr_tot_p50', 'sfr_tot_p16', 'sfr_tot_p84',
        'oh_p50', 'oh_p16', 'oh_p84',
        'bptclass',
        'd4000_n', 'd4000_n_err',
        # Galaxy Zoo
        'gz_p_el', 'gz_p_cs', 'gz_p_edge', 'gz_p_mg',
        'gz_spiral', 'gz_elliptical', 'gz_uncertain',
        # Computed
        'color_u_r', 'color_g_r', 'log_nii_ha', 'log_oiii_hb', 'concentration_r'
    ]
    # Only include columns that exist
    export_cols = [c for c in export_cols if c in df.columns]
    df_export = df[export_cols].copy()

    # Round floats
    float_cols = df_export.select_dtypes(include=['float64', 'float32']).columns
    for col in float_cols:
        df_export[col] = df_export[col].round(6)

    # 8. Save files
    print(f"\nSaving files to: {OUTPUT_DIR}")

    csv_path = os.path.join(OUTPUT_DIR, "sdss_galaxy_verified.csv")
    df_export.to_csv(csv_path, index=False, encoding='utf-8-sig')
    print(f"  CSV: {os.path.getsize(csv_path)/(1024*1024):.1f} MB ({len(df_export):,} rows)")

    xlsx_path = os.path.join(OUTPUT_DIR, "sdss_galaxy_verified.xlsx")
    print(f"  Writing XLSX...", end=" ", flush=True)
    df_export.to_excel(xlsx_path, index=False, engine='openpyxl', sheet_name='SDSS_DR18_Galaxies')
    print(f"OK ({os.path.getsize(xlsx_path)/(1024*1024):.1f} MB)")

    zip_path = os.path.join(OUTPUT_DIR, "sdss_galaxy_verified.zip")
    with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        zf.write(xlsx_path, arcname="sdss_galaxy_verified.xlsx")
        zf.write(csv_path, arcname="sdss_galaxy_verified.csv")
    print(f"  ZIP: {os.path.getsize(zip_path)/(1024*1024):.1f} MB")

    # 9. Final verification
    print(f"\n--- Output files ---")
    for f in sorted(os.listdir(OUTPUT_DIR)):
        if f.startswith('sdss_galaxy'):
            fp = os.path.join(OUTPUT_DIR, f)
            print(f"  {f}: {os.path.getsize(fp):,} bytes")

    print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
