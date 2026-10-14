import os
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

print(f"Total rows inspected: {n_rows:,}")

# Audit critical columns for dark matter computation
dist = data['DistMpc']
diam = data['Diam']
mstar = data['Mstar']
z = data['z']
objtype = data['objtype']

# Is it a galaxy?
is_galaxy = np.isin(objtype, [b'G', b'GPair', b'GTrpl', b'G_Lens'])

# Validity masks
has_dist = np.isfinite(dist) & (dist > 0)
has_diam = np.isfinite(diam) & (diam > 0)
has_mstar = np.isfinite(mstar) & (mstar > 0)
has_z = np.isfinite(z) & (z != 0)

print("\n=== [1] 전체 1,983,357개 행의 주요 컬럼 유효성 전수조사 ===")
print(f"1. 은하 분류 (G, GPair, GTrpl, G_Lens): {np.sum(is_galaxy):,d}개 ({np.sum(is_galaxy)/n_rows*100:.2f}%)")
print(f"2. 거리 (DistMpc > 0) 유효치:           {np.sum(has_dist):,d}개 ({np.sum(has_dist)/n_rows*100:.2f}%)")
print(f"3. 시직경 (Diam > 0) 유효치:            {np.sum(has_diam):,d}개 ({np.sum(has_diam)/n_rows*100:.2f}%)")
print(f"4. 항성 질량 (Mstar > 0) 유효치:        {np.sum(has_mstar):,d}개 ({np.sum(has_mstar)/n_rows*100:.2f}%)")
print(f"5. 적색편이 (z != 0) 유효치:           {np.sum(has_z):,d}개 ({np.sum(has_z)/n_rows*100:.2f}%)")

# Intersections
has_all_3 = has_dist & has_diam & has_mstar
has_all_4 = has_dist & has_diam & has_mstar & is_galaxy

print("\n=== [2] 암흑물질 계산 조건 충족 여부 전수조사 ===")
print(f"A. 거리 + 시직경 + 항성질량 모두 유효한 행: {np.sum(has_all_3):,d}개 ({np.sum(has_all_3)/n_rows*100:.2f}%)")
print(f"B. 순수 은하 중 3대 물리량 모두 유효한 행: {np.sum(has_all_4):,d}개 ({np.sum(has_all_4)/n_rows*100:.2f}%)")

# Detailed breakdown of why rows were missing
missing_mstar_only = has_dist & has_diam & (~has_mstar)
missing_diam_only = has_dist & (~has_diam) & has_mstar
missing_dist_only = (~has_dist) & has_diam & has_mstar
missing_all_phot = (~has_dist) & (~has_diam) & (~has_mstar)

print("\n=== [3] 결측 원인 상세 전수 분석 (524,417개 미계산 행의 정체) ===")
print(f"- 항성 질량(Mstar) 결측 (측광 필터 부재 또는 미관측): {np.sum(missing_mstar_only):,d}개")
print(f"- 은하 시직경(Diam) 결측 (점원 또는 미분해 천체):     {np.sum(missing_diam_only):,d}개")
print(f"- 거리(DistMpc) 결측 (스펙트럼 미확보):              {np.sum(missing_dist_only):,d}개")
print(f"- 비은하 천체 (퀘이사 QSO, 전파원, 적외선원 등):     {np.sum(~is_galaxy):,d}개")
