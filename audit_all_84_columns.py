import os
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import numpy as np
import pandas as pd
from astropy.io import fits

fits_file = 'NEDLVS_20260424.fits'
hdul = fits.open(fits_file)
h1 = hdul[1].header
row_size = h1['NAXIS1']
offset = hdul[1]._data_offset
n_rows = (os.path.getsize(fits_file) - offset) // row_size
dtype = hdul[1].columns.dtype.newbyteorder('>')

with open(fits_file, 'rb') as f:
    f.seek(offset)
    raw = f.read(n_rows * row_size)
    data = np.frombuffer(raw, dtype=dtype, count=n_rows)

print(f"Total Rows: {n_rows:,}")
print(f"Total Columns: {len(data.dtype.names)}")

col_stats = []
for name in data.dtype.names:
    col = data[name]
    if np.issubdtype(col.dtype, np.floating):
        valid = np.isfinite(col) & (col != 0)
        n_valid = int(np.sum(valid))
    elif np.issubdtype(col.dtype, np.integer):
        valid = col != 0
        n_valid = int(np.sum(valid))
    elif np.issubdtype(col.dtype, np.bool_):
        n_valid = int(np.sum(col))
    else: # string/bytes
        valid = np.array([len(s.strip()) > 0 for s in col])
        n_valid = int(np.sum(valid))
    pct = (n_valid / n_rows) * 100.0
    col_stats.append({'Column': name, 'Valid_Count': n_valid, 'Valid_Pct': pct})

df_col_stats = pd.DataFrame(col_stats)
df_col_stats.to_csv('output/NEDLVS_84개_항목_전수조사_통계.csv', index=False, encoding='utf-8-sig')

print("\n=== 주요 물리/측광 파라미터 유효율 상위/하위 10개 ===")
for r in col_stats[:15]:
    print(f"  {r['Column']:20s}: {r['Valid_Count']:10,d} ({r['Valid_Pct']:5.1f}%)")
print("...")
for r in col_stats[-10:]:
    print(f"  {r['Column']:20s}: {r['Valid_Count']:10,d} ({r['Valid_Pct']:5.1f}%)")
