import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import os
import zipfile
import numpy as np
import pandas as pd
from astropy.io import fits

print("="*80)
print(">> [CEERS 전수조사 감사] 87,345개 전체 행 및 201개 전체 컬럼 전수 검증 시작...")
print("="*80)

fits_path = 'ceers_cat_v1.0.fits'
with fits.open(fits_path) as hdul:
    hdr = hdul[1].header
    data = hdul[1].data
    n_rows = len(data)
    cols = hdul[1].columns.names
    n_cols = len(cols)

print(f"  * 총 데이터 행 수 (Rows / 천체): {n_rows:,} 개")
print(f"  * 총 데이터 열 수 (Columns / 파라미터): {n_cols} 개")

# 1. Row-by-Row Complete Breakdown
star_flag = np.array(data['STAR_FLAG'])
bad_flag = np.array(data['BAD_REGION_FLAG'])
z_med = np.array(data['LP_Z_MED'])
z_best = np.array(data['LP_Z_BEST'])
mstar_med = np.array(data['LP_MASS_MED'])
mstar_best = np.array(data['LP_MASS_BEST'])
a_img = np.array(data['A_IMAGE'])
kron = np.array(data['KRON_RADIUS'])

z_valid = np.where((z_med > 0.005) & (z_med < 15.0), z_med, z_best)
mstar_valid = np.where((mstar_med > 3.0) & (mstar_med < 14.0), mstar_med, mstar_best)
r_kron = kron * a_img * 0.030

is_star = (star_flag == 1)
is_bad_region = (bad_flag == 1)
is_good_obj = (star_flag == 0) & (bad_flag == 0)
has_z = is_good_obj & np.isfinite(z_valid) & (z_valid >= 0.02) & (z_valid <= 12.0)
has_mass = has_z & np.isfinite(mstar_valid) & (mstar_valid >= 4.0) & (mstar_valid <= 13.0)
has_radius = has_mass & np.isfinite(r_kron) & (r_kron >= 0.02) & (r_kron <= 50.0)

print("\n=== [1] 데이터 행(Row) 기준 전수 감사 결과 ===")
print(f"  1. 카탈로그 전체 천체: {n_rows:,} 개 (100.0%)")
print(f"  2. 항성 (STAR_FLAG==1, 점광원): {is_star.sum():,} 개 ({is_star.sum()/n_rows*100:.2f}%)")
print(f"  3. 관측 결함 (BAD_REGION_FLAG==1, 가장자리/노이즈): {is_bad_region.sum():,} 개 ({is_bad_region.sum()/n_rows*100:.2f}%)")
print(f"  4. 순수 은하 천체 후보: {is_good_obj.sum():,} 개 ({is_good_obj.sum()/n_rows*100:.2f}%)")
print(f"  5. 적색편이 z 유효 은하: {has_z.sum():,} 개 ({has_z.sum()/n_rows*100:.2f}%)")
print(f"  6. 항성질량 M* 유효 은하: {has_mass.sum():,} 개 ({has_mass.sum()/n_rows*100:.2f}%)")
print(f"  7. 회전반경 R 유효 및 최종 계산 완료 은하: {has_radius.sum():,} 개 ({has_radius.sum()/n_rows*100:.2f}%)")

# 2. Column-by-Column Complete Breakdown (All 201 Columns)
print("\n=== [2] 201개 전체 컬럼 유효치 전수 집계 중... ===")
col_records = []
for idx, col in enumerate(cols, 1):
    arr = data[col]
    # Check if multidimensional
    if len(arr.shape) > 1:
        # Multidimensional array (e.g. 12 aperture fluxes)
        valid_cnt = np.sum(np.isfinite(arr).all(axis=1) & (arr[:, 0] > -90))
        shape_str = f"Array{arr.shape[1:]}"
    else:
        valid_cnt = np.sum(np.isfinite(arr) & (arr > -90))
        shape_str = "Scalar"
    
    valid_pct = (valid_cnt / n_rows) * 100.0
    
    # Categorize column
    clow = col.lower()
    if any(k in clow for k in ['number', 'x_image', 'y_image', 'ra', 'dec', 'cxx', 'cxy', 'cyy', 'theta', 'ellipticity', 'kron', 'a_image', 'b_image', 'iso_area', 'star_flag', 'bad_region', 'apcorr']):
        cat = "천체 식별, 위치 및 형태학 (SExtractor)"
    elif any(k in clow for k in ['f435w', 'f606w', 'f814w', 'f105w', 'f125w', 'f140w', 'f160w']):
        cat = "HST 다파장 측광 (0.435~1.6um)"
    elif any(k in clow for k in ['f115w', 'f150w', 'f200w', 'f277w', 'f356w', 'f410m', 'f444w']):
        cat = "JWST NIRCam 초정밀 측광 (1.15~4.44um)"
    elif any(k in clow for k in ['lp_', 'db_', 'ci_']):
        cat = "SED 물리량 피팅 (LePHARE, Dense Basis, CIGALE)"
    else:
        cat = "기타 관측 파라미터"
        
    col_records.append({
        'Index': idx,
        'Column': col,
        'Category': cat,
        'Format': shape_str,
        'Valid_Count': valid_cnt,
        'Valid_Pct': round(valid_pct, 4)
    })

df_cols = pd.DataFrame(col_records)
csv_cols_path = 'output/CEERS_201개_항목_전수조사_통계.csv'
df_cols.to_csv(csv_cols_path, index=False, encoding='utf-8-sig')
print(f"  - 201개 전체 항목 통계 저장 완료: {csv_cols_path}")

# Print Category-level Summary
print("\n=== [3] 파라미터 그룹별 유효율 통계 요약 ===")
grp = df_cols.groupby('Category').agg(
    Num_Columns=('Column', 'count'),
    Avg_Valid_Pct=('Valid_Pct', 'mean'),
    Min_Valid_Pct=('Valid_Pct', 'min'),
    Max_Valid_Pct=('Valid_Pct', 'max')
).reset_index()
print(grp.to_string(index=False))

# Update ZIP package with this 201-column audit CSV
zip_path = r"C:\Users\neato\Downloads\CEERS_JWST_은하_암흑물질_전수계산_최종완성패키지.zip"
if os.path.exists(zip_path):
    with zipfile.ZipFile(zip_path, 'a') as zf:
        zf.write(csv_cols_path, 'CEERS_201개_항목_전수조사_통계.csv')
    print(f"\n>> ZIP 패키지에 감사 CSV 추가 완료: {zip_path}")

# Copy standalone to Downloads
dst_csv = r"C:\Users\neato\Downloads\CEERS_201개_항목_전수조사_통계.csv"
import shutil
shutil.copy2(csv_cols_path, dst_csv)
print(f">> 다운로드 폴더 단독 복사 완료: {dst_csv}")
print("="*80)
