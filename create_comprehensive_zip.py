r"""
YSC 대회 최종 연구 결과물 전체 통합 압축 패키징 스크립트
- 4대 남은 연구 과제(GEI v2.0, 3D 도표, 관측 분석 프로그램, 발표 차트) 및 기존 연구 전체 집대성
- 체계적인 6대 하위 폴더 구조로 정리하여 압축
- 대상 위치:
  1) 현재 작업 디렉토리
  2) 사용자 다운로드 폴더
"""

import os
import sys
import shutil
import zipfile
import time

if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def create_package():
    base_dir = os.path.abspath(os.path.dirname(__file__))
    downloads_dir = os.path.expanduser('~/Downloads')
    
    pkg_name = "YSC_2026_은하진화연구_최종완성_통합패키지"
    staging_dir = os.path.join(base_dir, "temp_final_package_staging", pkg_name)
    
    if os.path.exists(os.path.join(base_dir, "temp_final_package_staging")):
        shutil.rmtree(os.path.join(base_dir, "temp_final_package_staging"), ignore_errors=True)
    
    print("=" * 80)
    print(">> YSC 2026 과학탐구대회 최종 연구 통합 압축 패키징 시작")
    print("=" * 80)

    # 1. 서브 디렉토리 정의
    dirs = {
        "reports": os.path.join(staging_dir, "01_최종_연구보고서_및_설명서"),
        "presentation": os.path.join(staging_dir, "02_대회_최종발표차트_및_관측은하_정밀리포트_300DPI"),
        "plots_3d_gei": os.path.join(staging_dir, "03_3D_및_GEI_연구도표_시각화"),
        "programs": os.path.join(staging_dir, "04_은하분석_프로그램_및_웹대시보드"),
        "datasets": os.path.join(staging_dir, "05_연구_데이터셋_및_학술통계표"),
        "codes": os.path.join(staging_dir, "06_전체_파이썬_및_C++_소스코드")
    }
    for d in dirs.values():
        os.makedirs(d, exist_ok=True)

    # ---------------------------------------------------------
    # [1] 01_최종_연구보고서_및_설명서
    # ---------------------------------------------------------
    print("\n[1/6] 연구 보고서 및 문서 수납 중...")
    report_files = [
        "은하진화연구_보정방식_수식_및_방법론_핵심정리.pdf",
        "은하진화연구_종합안내서_도표분석_및_물리개념.pdf",
        "최종연구보고서_은하진화지수_3D도표_관측분석프로그램.md",
        "CEERS_JWST_은하_암흑물질_전수계산_결과보고서.md",
        "NEDLVS_Dark_Matter_Analysis_Report.md",
        "Comprehensive_Project_Report.md",
        "Comprehensive_Project_Report.pdf",
        "NEDLVS_Dark_Matter_Analysis_Report.pdf",
        "README.md",
        os.path.join("output", "CEERS_JWST_은하_암흑물질_전수계산_결과보고서.pdf"),
        os.path.join("output", "README_계산자료_안내.txt"),
        os.path.join("output", "00_README_CEERS_안내.txt")
    ]
    for rf in report_files:
        src = os.path.join(base_dir, rf)
        if os.path.exists(src):
            dst = os.path.join(dirs["reports"], os.path.basename(rf))
            shutil.copy2(src, dst)
            print(f"  -> 수납: {os.path.basename(rf)}")

    # ---------------------------------------------------------
    # [2] 02_대회_최종발표차트_및_관측은하_정밀리포트_300DPI
    # ---------------------------------------------------------
    print("\n[2/6] 300 DPI 최종 발표 차트 및 관측 리포트 수납 중...")
    pres_dir_src = os.path.join(base_dir, "output", "presentation_charts")
    if os.path.exists(pres_dir_src):
        for f in os.listdir(pres_dir_src):
            if f.endswith('.png'):
                shutil.copy2(os.path.join(pres_dir_src, f), os.path.join(dirs["presentation"], f))
                print(f"  -> 발표 차트 수납: {f}")

    # 마스터 차트들
    master_charts = [
        os.path.join("output", "CEERS_JWST_은하_암흑물질_종합분석차트(300DPI).png"),
        os.path.join("output", "CEERS_vs_NEDLVS_암흑물질_우주진화_비교차트(300DPI).png"),
        os.path.join("output", "전체은하_145만개_암흑물질_전수계산_분석도표.png"),
        os.path.join("output", "은하_회전곡선_암흑물질_종합분석차트.png"),
        os.path.join("output", "그래프_전체146만개_은하_암흑물질_전수분석.png")
    ]
    for mc in master_charts:
        src = os.path.join(base_dir, mc)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(dirs["presentation"], os.path.basename(mc)))
            print(f"  -> 마스터 차트 수납: {os.path.basename(mc)}")

    # 관측은하 개별 진단 리포트 (하위 폴더)
    obs_rep_sub = os.path.join(dirs["presentation"], "관측은하_개별진단리포트_6종")
    os.makedirs(obs_rep_sub, exist_ok=True)
    obs_rep_src = os.path.join(base_dir, "output", "observatory_reports")
    if os.path.exists(obs_rep_src):
        for f in os.listdir(obs_rep_src):
            if f.endswith('.png'):
                shutil.copy2(os.path.join(obs_rep_src, f), os.path.join(obs_rep_sub, f))
                print(f"  -> 개별 진단 리포트 수납: {f}")

    # ---------------------------------------------------------
    # [3] 03_3D_및_GEI_연구도표_시각화
    # ---------------------------------------------------------
    print("\n[3/6] 3D 및 GEI 연구 도표 시각화 자료 수납 중...")
    plot_3d_src = os.path.join(base_dir, "output", "3d_plots")
    if os.path.exists(plot_3d_src):
        for f in os.listdir(plot_3d_src):
            shutil.copy2(os.path.join(plot_3d_src, f), os.path.join(dirs["plots_3d_gei"], f))
            print(f"  -> 3D 도표 수납: {f}")

    gei_plots_src = os.path.join(base_dir, "output", "gei_plots")
    if os.path.exists(gei_plots_src):
        for f in os.listdir(gei_plots_src):
            shutil.copy2(os.path.join(gei_plots_src, f), os.path.join(dirs["plots_3d_gei"], f))
            print(f"  -> GEI 도표 수납: {f}")

    # 2D 기초 물리화학 도표 11종 (하위 폴더)
    plots_2d_sub = os.path.join(dirs["plots_3d_gei"], "2D_기초_물리화학_도표_11종")
    os.makedirs(plots_2d_sub, exist_ok=True)
    plots_main_src = os.path.join(base_dir, "output", "plots")
    if os.path.exists(plots_main_src):
        for f in os.listdir(plots_main_src):
            src_f = os.path.join(plots_main_src, f)
            if os.path.isfile(src_f) and (f.startswith("도표") or f.endswith(".png")):
                shutil.copy2(src_f, os.path.join(plots_2d_sub, f))
                print(f"  -> 2D 기초 도표 수납: {f}")

    # ---------------------------------------------------------
    # [4] 04_은하분석_프로그램_및_웹대시보드
    # ---------------------------------------------------------
    print("\n[4/6] 은하 분석 소프트웨어 및 웹앱 수납 중...")
    web_apps = [
        "observatory_analyzer_web.html",
        "galaxy_analyzer_web.html",
        "index.html",
        "dashboard_real_data.html",
        "observatory_galaxy_analyzer.py"
    ]
    for w in web_apps:
        src = os.path.join(base_dir, w)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(dirs["programs"], w))
            print(f"  -> 프로그램 파일 수납: {w}")

    # JSON 데이터
    json_src = os.path.join(base_dir, "output", "observatory_analyzer_data.json")
    if os.path.exists(json_src):
        shutil.copy2(json_src, os.path.join(dirs["programs"], "observatory_analyzer_data.json"))

    # dashboard 폴더 통째로 복사
    dash_src = os.path.join(base_dir, "dashboard")
    if os.path.exists(dash_src):
        shutil.copytree(dash_src, os.path.join(dirs["programs"], "dashboard"), dirs_exist_ok=True)
        print("  -> 대시보드 폴더(dashboard/) 수납 완료")

    # modules 폴더 통째로 복사
    mod_src = os.path.join(base_dir, "modules")
    if os.path.exists(mod_src):
        shutil.copytree(mod_src, os.path.join(dirs["programs"], "modules"), dirs_exist_ok=True)
        print("  -> 모듈 폴더(modules/) 수납 완료")

    # ---------------------------------------------------------
    # [5] 05_연구_데이터셋_및_학술통계표
    # ---------------------------------------------------------
    print("\n[5/6] 핵심 연구 데이터셋 및 통계 CSV 수납 중...")
    dataset_files = [
        os.path.join("output", "통합_은하진화지수_GEI_v2_3대카탈로그_비교통계.csv"),
        os.path.join("output", "천문대_관측은하_12종_진화지수_및_과거현재미래_궤적.csv"),
        "galaxy_master_complete_all.csv",
        "galaxy_master_complete_all.xlsx",
        "galaxy_master_complete_all.json",
        os.path.join("output", "CEERS_JWST_은하_암흑물질_전수계산_7만7천개.csv"),
        os.path.join("output", "NEDLVS_전체은하_암흑물질_전수계산_145만개.csv"),
        "cpp_benchmark_results.csv",
        "cpp_rotation_curve_ngc3198.csv",
        "cpp_rotation_curve_m31.csv"
    ]
    for df_path in dataset_files:
        src = os.path.join(base_dir, df_path)
        if os.path.exists(src):
            dst = os.path.join(dirs["datasets"], os.path.basename(df_path))
            shutil.copy2(src, dst)
            size_mb = os.path.getsize(dst) / (1024 * 1024)
            print(f"  -> 데이터셋 수납: {os.path.basename(df_path)} ({size_mb:.1f} MB)")

    # ---------------------------------------------------------
    # [6] 06_전체_파이썬_및_C++_소스코드
    # ---------------------------------------------------------
    print("\n[6/6] 소스코드 및 실행 배치파일 수납 중...")
    code_files = [
        "run_remaining_research_pipeline.py",
        "observatory_galaxy_analyzer.py",
        "process_ceers_dark_matter.py",
        "process_entire_nedlvs_dark_matter.py",
        "generate_dark_matter_plots.py",
        "generate_6core_physics_scatters.py",
        "data_processor.py",
        "data_fetcher.py",
        "plot_generators.py",
        "plot_interactive.py",
        "galaxy_classifier.py",
        "run_ml_pipeline.py",
        "galaxy_correlation_analyzer.py",
        "config.py",
        "dark_matter_calculator.cpp",
        "ceers_dark_matter_calculator.cpp",
        "run_project.bat"
    ]
    for cf in code_files:
        src = os.path.join(base_dir, cf)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(dirs["codes"], cf))
            print(f"  -> 소스코드 수납: {cf}")

    # 패키지 안내 README.txt 생성
    readme_txt = f"""================================================================================
  YSC 2026 과학탐구대회 — 은하 진화 다차원 분석 연구 최종 완성 통합 패키지
================================================================================
생성 일시: {time.strftime('%Y-%m-%d %H:%M:%S')}
프로젝트: 다차원 3D 위상공간 기반 은하 진화 지수(GEI v2.0) 개발 및 과거·미래 진화 규명
분석 표본: 총 1,585,532개 은하 (SDSS 5만, NASA/IPAC NED-LVS 145만, JWST CEERS 7.7만)

================================================================================
[폴더별 수록 내용 안내]
================================================================================

1. 01_최종_연구보고서_및_설명서
   - 최종연구보고서_은하진화지수_3D도표_관측분석프로그램.md : 4대 연구 완결 총괄 학술 보고서
   - CEERS_JWST_은하_암흑물질_전수계산_결과보고서.md / .pdf : JWST CEERS 초기우주 전수계산 보고서
   - NEDLVS_Dark_Matter_Analysis_Report.md / .pdf : 국소우주 145만 은하 암흑물질 보고서
   - Comprehensive_Project_Report.md / .pdf : 전체 프로젝트 통합 학술 보고서

2. 02_대회_최종발표차트_및_관측은하_정밀리포트_300DPI
   - 발표차트1_은하진화지수_GEI개발_및_과거현재미래_예측.png (300 DPI)
   - 발표차트2_3차원도표_NED_CEERS_SDSS_우주진화_비교분석.png (300 DPI)
   - 발표차트3_천문대_관측은하_진화단계_판별프로그램_실증.png (300 DPI)
   - 발표차트4_YSC대회_은하진화연구_최종종합_마스터차트.png (300 DPI 최종 종합 마스터 포스터)
   - 암흑물질 6패널 마스터 차트 및 CEERS 비교 차트
   - 관측은하_개별진단리포트_6종/ (CEERS-HighZ, M33, NGC 3198, M51a, M31, M87)

3. 03_3D_및_GEI_연구도표_시각화
   - 3D_도표1~4 (크기-질량-암흑물질, 다양체, 표면밀도-암흑물질 반비례, 동역학 스케일링)
   - GEI_도표1~2 (수식 검증, 5단계 분포, 과거-현재-미래 진화 궤적)
   - interactive_3d_ned_ceers_sdss_manifold.html (웹 브라우저 360도 회전 3D 다양체)
   - 2D_기초_물리화학_도표_11종/

4. 04_은하분석_프로그램_및_웹대시보드
   - observatory_analyzer_web.html : 천문대 관측 은하 진화 단계 판별 웹 프로그램 (무설치 즉시 실행)
   - galaxy_analyzer_web.html : 은하 사진 & 회절 분광 웹 분석기
   - index.html : 전체 연구 포털
   - dashboard_real_data.html 및 dashboard/ : 10만 개 은하 실시간 대시보드
   - observatory_galaxy_analyzer.py : 파이썬 관측 분석 CLI/대화형 프로그램

5. 05_연구_데이터셋_및_학술통계표
   - 통합_은하진화지수_GEI_v2_3대카탈로그_비교통계.csv : 3대 카탈로그 158.5만 은하 통계표
   - 천문대_관측은하_12종_진화지수_및_과거현재미래_궤적.csv : 12종 은하 과거·현재·미래 수치표
   - galaxy_master_complete_all.csv / .xlsx : SDSS DR18 50,000개 전처리 마스터 데이터셋
   - CEERS 7.7만 개 및 NED-LVS 145만 개 암흑물질 전수계산 CSV

6. 06_전체_파이썬_및_C++_소스코드
   - run_remaining_research_pipeline.py : 전체 연구 파이프라인 일괄 실행기
   - observatory_galaxy_analyzer.py : 천문대 관측 은하 분석 엔진
   - process_ceers_dark_matter.py / process_entire_nedlvs_dark_matter.py
   - dark_matter_calculator.cpp / ceers_dark_matter_calculator.cpp
   - run_project.bat : 원클릭 실행 배치 파일
================================================================================
"""
    with open(os.path.join(staging_dir, "00_패키지_전체_안내_README.txt"), "w", encoding="utf-8") as f:
        f.write(readme_txt)

    # ---------------------------------------------------------
    # ZIP 파일 압축 실행
    # ---------------------------------------------------------
    zip_filename = f"{pkg_name}.zip"
    zip_dest_workspace = os.path.join(base_dir, zip_filename)
    zip_dest_downloads = os.path.join(downloads_dir, zip_filename)

    print("\n" + "=" * 80)
    print(f">> [ZIP 생성 중] {zip_filename} 압축 시작...")
    print("=" * 80)

    start_t = time.time()
    with zipfile.ZipFile(zip_dest_workspace, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
        for root, _, files in os.walk(staging_dir):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, staging_dir)
                zipf.write(full_path, rel_path)

    elapsed = time.time() - start_t
    zip_size_mb = os.path.getsize(zip_dest_workspace) / (1024 * 1024)

    # Downloads 폴더에도 복사
    shutil.copy2(zip_dest_workspace, zip_dest_downloads)

    # Staging 임시 폴더 삭제
    shutil.rmtree(os.path.join(base_dir, "temp_final_package_staging"), ignore_errors=True)

    print(f"\n[완료] 통합 압축 파일 생성이 완료되었습니다!")
    print(f"  1) 작업 디렉토리: {zip_dest_workspace}")
    print(f"  2) 다운로드 폴더: {zip_dest_downloads}")
    print(f"  - 압축 파일 크기: {zip_size_mb:.2f} MB")
    print(f"  - 소요 시간: {elapsed:.1f}초")
    print("=" * 80)

if __name__ == '__main__':
    create_package()
