import os
import sys
import time
import traceback
import subprocess
from datetime import datetime

# Import project modules
import config
try:
    import data_fetcher
    import data_processor
    import plot_generators
    import plot_interactive
    import run_ml_pipeline
except ImportError as e:
    print(f"[오류] 모듈 임포트 실패: {e}. 'requirements.txt'의 패키지들이 설치되었는지 확인하세요.")
    sys.exit(1)

def print_step(step_num, title):
    print("\n" + "="*50)
    print(f"단계 {step_num}: {title}")
    print("="*50)

def main():
    start_time = time.time()
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 은하 진화 다차원 분석 파이프라인 시작...\n")

    try:
        # 단계 1: 데이터 수집
        print_step(1, "SDSS 데이터 수집 (Data Fetching)")
        step1_start = time.time()
        # 원본 데이터 파일이 없을 경우에만 수집한다고 가정하거나, fetcher 내부에서 처리하도록 호출
        if not os.path.exists(config.RAW_SDSS_FILE):
            print(f"데이터를 다운로드합니다: {config.RAW_SDSS_FILE}")
            # data_fetcher 모듈의 메인 실행 함수 호출 (예시 이름)
            if hasattr(data_fetcher, 'fetch_data'):
                data_fetcher.fetch_data()
            else:
                print("data_fetcher에 fetch_data 함수가 없습니다. 스크립트로 실행합니다.")
                subprocess.run([sys.executable, "data_fetcher.py"], check=True)
        else:
            print(f"원본 데이터가 이미 존재합니다: {config.RAW_SDSS_FILE}")
        print(f"소요 시간: {time.time() - step1_start:.2f}초")

        # 단계 2: 데이터 전처리
        print_step(2, "데이터 전처리 및 물리량 계산 (Data Processing)")
        step2_start = time.time()
        if hasattr(data_processor, 'process_data'):
            import pandas as pd
            if os.path.exists(config.RAW_SDSS_FILE):
                df_raw = pd.read_csv(config.RAW_SDSS_FILE)
                data_processor.process_data(df_raw)
            else:
                print(f"원시 데이터 파일이 없습니다: {config.RAW_SDSS_FILE}")
        else:
            subprocess.run([sys.executable, "data_processor.py"], check=True)
        print(f"소요 시간: {time.time() - step2_start:.2f}초")

        # 단계 3: 시각화 도표 생성
        print_step(3, "정적 및 인터랙티브 시각화 생성 (Plot Generation)")
        step3_start = time.time()
        print("- 정적 도표 생성 중 (plot_generators)...")
        if hasattr(plot_generators, 'generate_all_plots'):
            plot_generators.generate_all_plots()
        else:
            subprocess.run([sys.executable, "plot_generators.py"], check=True)
            
        print("- 인터랙티브 도표 생성 중 (plot_interactive)...")
        if hasattr(plot_interactive, 'generate_interactive_plots'):
            plot_interactive.generate_interactive_plots()
        else:
            subprocess.run([sys.executable, "plot_interactive.py"], check=True)
        print(f"소요 시간: {time.time() - step3_start:.2f}초")

        # 단계 4: 머신러닝 파이프라인 실행
        print_step(4, "머신러닝 기반 은하 분류 모델 학습 (ML Pipeline)")
        step4_start = time.time()
        if hasattr(run_ml_pipeline, 'run_pipeline'):
            run_ml_pipeline.run_pipeline()
        else:
            subprocess.run([sys.executable, "run_ml_pipeline.py"], check=True)
        print(f"소요 시간: {time.time() - step4_start:.2f}초")

        # 단계 5: 요약 및 대시보드 데이터 내보내기 (선택적)
        print_step(5, "파이프라인 요약 및 대시보드 갱신")
        if os.path.exists(config.MASTER_DATASET_FILE):
            file_size = os.path.getsize(config.MASTER_DATASET_FILE) / (1024*1024)
            print(f"최종 마스터 데이터셋 크기: {file_size:.2f} MB")
            print(f"저장 위치: {config.MASTER_DATASET_FILE}")
            
        # 단계 6: 외부 데이터 검증 (Validation)
        print_step(6, "외부 은하 데이터 기반 타당성 검증 (Validation)")
        step6_start = time.time()
        try:
            import validation_tool
            if hasattr(validation_tool, 'run_validation'):
                validation_tool.run_validation()
        except ImportError:
            os.system(f"{sys.executable} validation_tool.py")
        print(f"소요 시간: {time.time() - step6_start:.2f}초")

        # 단계 7: 은하 물리량 및 화학적 조성 상관관계 통계 분석 (Correlation Analysis)
        print_step(7, "물리량 및 화학적 조성 상관관계 통계 분석 (Correlation Analysis)")
        step7_start = time.time()
        try:
            import galaxy_correlation_analyzer
            target_csv = "galaxy_master_complete_all.csv" if os.path.exists("galaxy_master_complete_all.csv") else config.MASTER_DATASET_FILE
            galaxy_correlation_analyzer.run_galaxy_analysis_pipeline(csv_path=target_csv)
        except Exception as err:
            print(f"[경고] 상관관계 분석 단계 건너뜀 또는 오류: {err}")
        print(f"소요 시간: {time.time() - step7_start:.2f}초")
            
        print(f"\n모든 분석 도표가 {config.PLOT_DIR} 및 galaxy_analysis_output/ 에 저장되었습니다.")
        print(f"학습된 모델이 {config.MODEL_DIR} 에 저장되었습니다.")
        
        total_time = time.time() - start_time
        print("\n" + "*"*50)
        print(f"전체 파이프라인 실행 완료! (총 소요 시간: {total_time:.2f}초)")
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 프로그램 종료.")
        print("대시보드를 확인하려면 'dashboard/index.html'을 열거나 서버를 실행하세요.")
        print("*"*50)

    except Exception as e:
        print("\n[오류] 파이프라인 실행 중 심각한 오류가 발생했습니다:")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
