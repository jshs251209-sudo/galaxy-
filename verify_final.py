# -*- coding: utf-8 -*-
"""Final verification of all output files."""
import os
import pandas as pd
import zipfile

d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "download")
print(f"Directory: {d}")
print(f"Exists: {os.path.exists(d)}")
print()

print("=== FILES ===")
for f in sorted(os.listdir(d)):
    fp = os.path.join(d, f)
    sz = os.path.getsize(fp)
    print(f"  {f}: {sz:,} bytes ({sz/(1024*1024):.1f} MB)")

print()

# Check CSV
csv_path = os.path.join(d, "sdss_galaxy_verified.csv")
if os.path.exists(csv_path) and os.path.getsize(csv_path) > 0:
    df = pd.read_csv(csv_path, nrows=5)
    total = sum(1 for _ in open(csv_path, encoding='utf-8-sig')) - 1
    print(f"=== CSV ===")
    print(f"Total rows: {total:,}")
    print(f"Columns: {len(df.columns)}")
    print(f"Column list: {list(df.columns)}")
    print()

# Check XLSX
xlsx_path = os.path.join(d, "sdss_galaxy_verified.xlsx")
if os.path.exists(xlsx_path) and os.path.getsize(xlsx_path) > 1000:
    try:
        dfx = pd.read_excel(xlsx_path, nrows=5)
        print(f"=== XLSX ===")
        print(f"Columns: {len(dfx.columns)}")
        print(f"First 3 specObjIDs: {dfx['specObjID'].head(3).tolist()}")
        print(f"z values: {dfx['z'].head(3).tolist()}")
        print("XLSX is valid and readable!")
    except Exception as e:
        print(f"XLSX error: {e}")
    print()

# Check ZIP
zip_path = os.path.join(d, "sdss_galaxy_verified.zip")
if os.path.exists(zip_path) and os.path.getsize(zip_path) > 1000:
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            print("=== ZIP ===")
            for info in zf.infolist():
                print(f"  {info.filename}: {info.file_size:,} bytes (compressed: {info.compress_size:,})")
            print("ZIP is valid!")
    except Exception as e:
        print(f"ZIP error: {e}")

print()
print("DONE!")
