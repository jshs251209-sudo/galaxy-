# -*- coding: utf-8 -*-
"""
SDSS DR18 Verified Galaxy Data Download Pipeline (Robust Version)
=================================================================
Downloads authentic galaxy data from official SDSS SkyServer DR18 SQL API.
Uses smaller query chunks with robust retry logic.
"""

import os
import sys
import time
import io
import zipfile
import requests
import pandas as pd
import numpy as np
from datetime import datetime

# ============================================================
# Configuration
# ============================================================
SDSS_API_URL = "https://skyserver.sdss.org/dr18/SkyServerWS/SearchTools/SqlSearch"
OUTPUT_DIR = r"C:\Users\neato\sdss_download"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Redshift bins: 0.02 to 0.20, step=0.01 -> 18 bins (smaller chunks)
Z_MIN = 0.02
Z_MAX = 0.20
Z_STEP = 0.01
ROWS_PER_BIN = 1500  # Smaller per-bin limit to avoid timeouts
REQUEST_TIMEOUT = 90  # shorter timeout
RETRY_COUNT = 3
RETRY_DELAY = 5
INTER_QUERY_DELAY = 1  # 1 second between queries


def build_sql_query(z_lo, z_hi, limit):
    """Build the SDSS SQL query for a given redshift bin."""
    return f"""SELECT TOP {limit}
s.specObjID, s.plate, s.mjd, s.fiberID,
s.ra, s.dec, s.z, s.zErr, s.velDisp, s.velDispErr,
p.u, p.g, p.r, p.i, p.z as phot_z,
p.err_u, p.err_g, p.err_r, p.err_i, p.err_z as err_phot_z,
p.petroRad_r, p.petroR50_r, p.petroR90_r,
p.extinction_u, p.extinction_g, p.extinction_r, p.extinction_i,
p.extinction_z as extinction_phot_z,
l.h_alpha_flux, l.h_alpha_flux_err,
l.h_beta_flux, l.h_beta_flux_err,
l.oiii_5007_flux, l.oiii_5007_flux_err,
l.nii_6584_flux, l.nii_6584_flux_err,
l.sii_6717_flux, l.sii_6717_flux_err,
l.oii_3726_flux, l.oii_3726_flux_err,
l.h_alpha_eqw, l.h_beta_eqw,
l.oiii_5007_eqw, l.nii_6584_eqw,
e.lgm_tot_p50, e.lgm_tot_p16, e.lgm_tot_p84,
e.sfr_tot_p50, e.sfr_tot_p16, e.sfr_tot_p84,
e.oh_p50, e.oh_p16, e.oh_p84,
e.bptclass,
indx.d4000_n, indx.d4000_n_err,
zoo.p_el as gz_p_el, zoo.p_cs as gz_p_cs,
zoo.p_mg as gz_p_mg, zoo.spiral as gz_spiral,
zoo.elliptical as gz_elliptical
FROM SpecObj s
JOIN PhotoObj p ON s.bestObjID = p.objID
JOIN galSpecLine l ON s.specObjID = l.specObjID
JOIN galSpecExtra e ON s.specObjID = e.specObjID
JOIN galSpecIndx indx ON s.specObjID = indx.specObjID
LEFT JOIN zooSpec zoo ON s.specObjID = zoo.specObjID
WHERE s.class = 'GALAXY'
AND s.zWarning = 0
AND s.z >= {z_lo:.6f} AND s.z < {z_hi:.6f}
AND l.h_alpha_flux > 0 AND l.h_beta_flux > 0
AND l.oiii_5007_flux > 0 AND l.nii_6584_flux > 0
AND p.r > 0 AND p.r < 25
AND p.petroR50_r > 0
ORDER BY s.specObjID"""


def query_sdss(sql):
    """Execute a SQL query against SDSS SkyServer and return a DataFrame."""
    params = {"cmd": sql, "format": "csv"}
    
    for attempt in range(1, RETRY_COUNT + 1):
        try:
            resp = requests.get(
                SDSS_API_URL, params=params, timeout=REQUEST_TIMEOUT
            )
            resp.raise_for_status()
            
            text = resp.text.strip()
            
            # Check for API error responses
            if text.startswith("ERROR") or "<html" in text.lower()[:100]:
                print(f"[API error, attempt {attempt}]", end=" ", flush=True)
                if attempt < RETRY_COUNT:
                    time.sleep(RETRY_DELAY)
                    continue
                return pd.DataFrame()
            
            # Parse CSV - SDSS adds a #Table1 header line
            lines = text.split('\n')
            header_idx = 0
            for idx, line in enumerate(lines):
                if 'specObjID' in line:
                    header_idx = idx
                    break
            
            csv_text = '\n'.join(lines[header_idx:])
            df = pd.read_csv(io.StringIO(csv_text))
            
            # Remove separator rows (SDSS adds a '---' row after header)
            if len(df) > 0:
                first_row = df.iloc[0].astype(str)
                if first_row.str.contains('---').any():
                    df = df.iloc[1:].reset_index(drop=True)
            
            # Convert numeric columns
            for col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            return df
            
        except requests.exceptions.Timeout:
            print(f"[timeout, attempt {attempt}]", end=" ", flush=True)
            if attempt < RETRY_COUNT:
                time.sleep(RETRY_DELAY * attempt)  # exponential backoff
        except requests.exceptions.ConnectionError:
            print(f"[conn error, attempt {attempt}]", end=" ", flush=True)
            if attempt < RETRY_COUNT:
                time.sleep(RETRY_DELAY * attempt * 2)
        except Exception as e:
            print(f"[error: {e}, attempt {attempt}]", end=" ", flush=True)
            if attempt < RETRY_COUNT:
                time.sleep(RETRY_DELAY)
    
    return pd.DataFrame()


def clean_sentinel_values(df):
    """Replace SDSS sentinel values (-9999, -9999.0) with NaN."""
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        df.loc[df[col] <= -9990, col] = np.nan
    return df


def validate_data(df):
    """Run validation checks on the downloaded data."""
    print("\n" + "=" * 60)
    print("DATA VALIDATION REPORT")
    print("=" * 60)
    
    print(f"\nTotal galaxies: {len(df):,}")
    print(f"Unique specObjIDs: {df['specObjID'].nunique():,}")
    
    z_valid = df['z'].dropna()
    print(f"\nRedshift (z):")
    print(f"  Range: [{z_valid.min():.6f}, {z_valid.max():.6f}]")
    print(f"  Mean:  {z_valid.mean():.6f}")
    print(f"  Median: {z_valid.median():.6f}")
    
    print(f"\nMagnitudes:")
    for band in ['u', 'g', 'r', 'i']:
        vals = df[band].dropna()
        print(f"  {band}: [{vals.min():.2f}, {vals.max():.2f}], median={vals.median():.2f}")
    
    print(f"\nBPT class distribution:")
    print(df['bptclass'].value_counts().sort_index().to_string(header=False))
    
    print(f"\nMPA-JHU properties (after sentinel removal):")
    for col in ['lgm_tot_p50', 'sfr_tot_p50', 'oh_p50', 'd4000_n']:
        vals = df[col].dropna()
        if len(vals) > 0:
            print(f"  {col}: [{vals.min():.3f}, {vals.max():.3f}], valid={len(vals)}, NaN={df[col].isna().sum()}")
    
    print(f"\nEmission line fluxes:")
    for col in ['h_alpha_flux', 'h_beta_flux', 'oiii_5007_flux', 'nii_6584_flux']:
        vals = df[col].dropna()
        if len(vals) > 0:
            print(f"  {col}: median={vals.median():.2f}, max={vals.max():.2f}")
    
    gz_valid = df['gz_p_el'].notna().sum()
    print(f"\nGalaxy Zoo coverage: {gz_valid}/{len(df)} ({gz_valid/len(df)*100:.1f}%)")
    
    print("=" * 60)


def main():
    print("=" * 60)
    print("SDSS DR18 Verified Galaxy Data Download Pipeline")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # First test connectivity
    print("\nTesting SDSS API connectivity...", end=" ", flush=True)
    test_df = query_sdss("SELECT TOP 1 specObjID FROM SpecObj WHERE class='GALAXY'")
    if test_df.empty:
        print("FAILED - cannot connect to SDSS SkyServer")
        sys.exit(1)
    print("OK")
    
    # Build redshift bins
    z_bins = np.arange(Z_MIN, Z_MAX + Z_STEP/2, Z_STEP)
    n_bins = len(z_bins) - 1
    print(f"\nRedshift range: z = {Z_MIN} to {Z_MAX}")
    print(f"Number of bins: {n_bins} (step = {Z_STEP})")
    print(f"Max rows per bin: {ROWS_PER_BIN}")
    
    all_data = []
    total_fetched = 0
    failed_bins = []
    
    for i in range(n_bins):
        z_lo = round(z_bins[i], 6)
        z_hi = round(z_bins[i + 1], 6)
        
        print(f"\n[Bin {i+1}/{n_bins}] z={z_lo:.4f}~{z_hi:.4f} ", end="", flush=True)
        
        sql = build_sql_query(z_lo, z_hi, ROWS_PER_BIN)
        df_bin = query_sdss(sql)
        
        if df_bin.empty:
            print("-> FAILED (0 galaxies)")
            failed_bins.append((z_lo, z_hi))
        else:
            all_data.append(df_bin)
            total_fetched += len(df_bin)
            print(f"-> {len(df_bin)} galaxies (total: {total_fetched:,})")
        
        # Respectful delay
        if i < n_bins - 1:
            time.sleep(INTER_QUERY_DELAY)
    
    if not all_data:
        print("\n[ERROR] No data was collected. Exiting.")
        sys.exit(1)
    
    # Report failed bins
    if failed_bins:
        print(f"\n[WARNING] {len(failed_bins)} bins failed: {failed_bins}")
    
    # Combine all bins
    print(f"\nCombining {len(all_data)} successful bins...")
    df = pd.concat(all_data, ignore_index=True)
    
    # Remove duplicates
    before = len(df)
    df = df.drop_duplicates(subset='specObjID').reset_index(drop=True)
    after = len(df)
    if before != after:
        print(f"Removed {before - after} duplicate specObjIDs")
    
    print(f"Total unique galaxies: {len(df):,}")
    
    # Clean sentinel values
    print("Cleaning sentinel values (-9999 -> NaN)...")
    df = clean_sentinel_values(df)
    
    # Validate
    validate_data(df)
    
    # Save CSV
    csv_path = os.path.join(OUTPUT_DIR, "sdss_galaxy_verified.csv")
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    csv_size = os.path.getsize(csv_path)
    print(f"\nSaved CSV: {csv_path} ({csv_size/(1024*1024):.1f} MB)")
    
    # Save XLSX
    xlsx_path = os.path.join(OUTPUT_DIR, "sdss_galaxy_verified.xlsx")
    print(f"Saving XLSX...", end=" ", flush=True)
    df_export = df.copy()
    float_cols = df_export.select_dtypes(include=['float64', 'float32']).columns
    for col in float_cols:
        df_export[col] = df_export[col].round(6)
    df_export.to_excel(xlsx_path, index=False, engine='openpyxl', sheet_name='SDSS_DR18_Galaxies')
    xlsx_size = os.path.getsize(xlsx_path)
    print(f"OK ({xlsx_size/(1024*1024):.1f} MB)")
    
    # Create ZIP
    zip_path = os.path.join(OUTPUT_DIR, "sdss_galaxy_verified.zip")
    with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        zf.write(xlsx_path, arcname="sdss_galaxy_verified.xlsx")
        zf.write(csv_path, arcname="sdss_galaxy_verified.csv")
    zip_size = os.path.getsize(zip_path)
    print(f"Saved ZIP: {zip_path} ({zip_size/(1024*1024):.1f} MB)")
    
    # Final verification
    print(f"\n--- Final file verification ---")
    for f in os.listdir(OUTPUT_DIR):
        if f.startswith('sdss_galaxy'):
            fp = os.path.join(OUTPUT_DIR, f)
            print(f"  {f}: {os.path.getsize(fp):,} bytes")
    
    print(f"\nPipeline completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
