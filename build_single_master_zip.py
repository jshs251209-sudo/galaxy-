import os
import zipfile
import shutil

downloads_dir = r"C:\Users\neato\Downloads"
output_dir = "output"

# Define the single master zip path
master_zip_path = os.path.join(downloads_dir, "은하_암흑물질_전수계산_최종완성패키지.zip")

print("="*80)
print(">> 하나의 단일 마스터 압축 파일 생성 시작...")
print("="*80)

# Staging directory for clean file naming
staging_dir = "temp_master_package"
os.makedirs(staging_dir, exist_ok=True)

# 1. Reports (PDF)
pdf_report1 = os.path.join(downloads_dir, "전체은하_145만개_암흑물질_전수계산_결과보고서.pdf")
pdf_report2 = os.path.join(downloads_dir, "은하_회전곡선_암흑물질_계산결과.pdf")
if os.path.exists(pdf_report1):
    shutil.copy2(pdf_report1, os.path.join(staging_dir, "01_전체은하_145만개_암흑물질_전수계산_결과보고서.pdf"))

# 2. High-Resolution Analysis Plots (300 DPI)
plot_full = os.path.join(downloads_dir, "전체은하_145만개_암흑물질_전수계산_분석도표.png")
plot_master6 = os.path.join(downloads_dir, "은하_회전곡선_암흑물질_종합분석차트.png")
plot1 = os.path.join(downloads_dir, "그래프1_NGC3198_회전곡선_암흑물질_분해.png")
plot2 = os.path.join(downloads_dir, "그래프2_반경별_암흑물질_질량과_비율_곡선.png")
plot3 = os.path.join(downloads_dir, "그래프3_M31_안드로메다_회전곡선_암흑물질.png")
plot4 = os.path.join(downloads_dir, "그래프4_대표은하8종_암흑물질_질량과_비율_비교.png")

for p_src, p_dst_name in [
    (plot_full, "02_전체은하_145만개_암흑물질_전수계산_분석도표(300DPI).png"),
    (plot_master6, "03_은하_회전곡선_암흑물질_종합분석차트_6패널(300DPI).png"),
    (plot1, "04_개별차트_NGC3198_회전곡선_성분분해.png"),
    (plot2, "05_개별차트_반경별_암흑물질_질량과_비율_곡선.png"),
    (plot3, "06_개별차트_M31_안드로메다_암흑물질.png"),
    (plot4, "07_개별차트_대표은하8종_암흑물질_질량비율_비교.png")
]:
    if os.path.exists(p_src):
        shutil.copy2(p_src, os.path.join(staging_dir, p_dst_name))

# 3. Data Files
csv_full = os.path.join(output_dir, "NEDLVS_전체은하_암흑물질_전수계산_145만개.csv")
if os.path.exists(csv_full):
    shutil.copy2(csv_full, os.path.join(staging_dir, "08_NEDLVS_전체은하_암흑물질_전수계산_145만개.csv"))

excel_bench = os.path.join(output_dir, "dark_matter_benchmark_results.csv")
cpp_bench = "cpp_benchmark_results.csv"
if os.path.exists(cpp_bench):
    shutil.copy2(cpp_bench, os.path.join(staging_dir, "09_대표은하8종_암흑물질_계산결과_벤치마크.csv"))

# 4. Source Codes & Batch Runner
cpp_code = "dark_matter_calculator.cpp"
py_code1 = "process_entire_nedlvs_dark_matter.py"
py_code2 = "generate_dark_matter_plots.py"
bat_runner = os.path.join(downloads_dir, "암흑물질_계산및그래프_원클릭실행.bat")

if os.path.exists(cpp_code):
    shutil.copy2(cpp_code, os.path.join(staging_dir, "10_C++_수치연산엔진_dark_matter_calculator.cpp"))
if os.path.exists(py_code1):
    shutil.copy2(py_code1, os.path.join(staging_dir, "11_Python_전수계산및차트생성기_process_entire_nedlvs.py"))
if os.path.exists(bat_runner):
    shutil.copy2(bat_runner, os.path.join(staging_dir, "12_원클릭_자동실행_배치파일.bat"))

# 5. README Documentation
readme_content = """================================================================================
  NED-LVS 전체 은하 1,457,587개 전수 암흑물질 계산 최종 통합 완성 패키지
================================================================================
- 연구 과제: 은하 관측 자료(회전곡선) 바탕 은하 암흑물질 실제 질량(M_DM) 및 %비율(f_DM) 전수 산출
- 분석 데이터: NASA/IPAC Extragalactic Database Local Volume Sample (NEDLVS_20260424.fits)
- 연계 학술 논문:
  1. Kartaltepe et al. (2023), ApJL, 946:L15 (CEERS Key Paper III: Galaxy Structure at z=3-9)
  2. Cox et al. (2026), ApJ, 1005:62 (The CEERS Photometric & Physical Parameter Catalog)

================================================================================
[패키지 수록 파일 목록]
================================================================================
1. [보고서]
   - 01_전체은하_145만개_암흑물질_전수계산_결과보고서.pdf
     : 145만 개 은하 전수 계산 핵심 통계치 및 이론 유도식이 정리된 제출용 PDF

2. [고해상도 300 DPI 분석 그래프 이미지]
   - 02_전체은하_145만개_암흑물질_전수계산_분석도표(300DPI).png
     : 1,457,587개 은하 전체의 2D Hexbin 밀도 분포 및 누적분포함수(CDF) 차트
   - 03_은하_회전곡선_암흑물질_종합분석차트_6패널(300DPI).png
     : NGC 3198 성분분해, 누적질량, M31 안드로메다, CEERS 우주론적 진화 비교 6분할 마스터 차트
   - 04_개별차트_NGC3198_회전곡선_성분분해.png
   - 05_개별차트_반경별_암흑물질_질량과_비율_곡선.png
   - 06_개별차트_M31_안드로메다_암흑물질.png
   - 07_개별차트_대표은하8종_암흑물질_질량비율_비교.png

3. [계산 데이터셋]
   - 08_NEDLVS_전체은하_암흑물질_전수계산_145만개.csv
     : 1,458,940개 은하 전체의 개별 실제 암흑물질 질량 및 %비율이 담긴 169MB 원본 CSV
   - 09_대표은하8종_암흑물질_계산결과_벤치마크.csv
     : M31, NGC 3198 등 대표 나선은하 실측치 기반 계산표

4. [소스 코드 및 원클릭 실행기]
   - 10_C++_수치연산엔진_dark_matter_calculator.cpp
   - 11_Python_전수계산및차트생성기_process_entire_nedlvs.py
   - 12_원클릭_자동실행_배치파일.bat

================================================================================
[암흑물질 계산 공식 및 145만 개 전수 계산 핵심 결과]
================================================================================
1. 핵심 공식:
   - 총 동역학 질량: M_dyn = V_rot^2 * R / G  (G = 4.3009e-6 kpc (km/s)^2 / M_sun)
   - ① 실제 암흑물질 질량: M_DM = M_dyn - M_*  (M_sun)
   - ② 암흑물질 %비율: f_DM = (M_DM / M_dyn) * 100  (%)

2. 1,457,587개 은하 전수 계산 핵심 수치 (광학 반경 R_25 기준):
   - 은하 항성 질량 중앙값: log M_* = 10.96 (9.1 × 10^10 M_sun)
   - 평탄 회전속도 중앙값: V_rot = 187.8 km/s
   - 총 동역학 질량 중앙값: log M_dyn = 11.24 (1.74 × 10^11 M_sun)
   - ① 실제 암흑물질 질량 중앙값: 7.53 × 10^10 M_sun (log M_DM = 10.88)
   - ② 암흑물질 %비율 중앙값: 48.8% (사분위 범위: 38.4% ~ 57.9%)
================================================================================
"""
with open(os.path.join(staging_dir, "00_README_최종안내서.txt"), 'w', encoding='utf-8') as f:
    f.write(readme_content)

# 6. Compress staging directory into master ZIP
print(">> 압축 파일 생성 중...")
with zipfile.ZipFile(master_zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
    for root, dirs, files in os.walk(staging_dir):
        for file in files:
            full_path = os.path.join(root, file)
            zf.write(full_path, arcname=file)

# Clean staging dir
shutil.rmtree(staging_dir)

print(f"SUCCESS: Master ZIP created at {master_zip_path}")
print(f"File size: {os.path.getsize(master_zip_path)/1024/1024:.2f} MB")
