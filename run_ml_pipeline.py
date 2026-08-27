import galaxy_classifier

def run_pipeline():
    """
    머신러닝 파이프라인 (클러스터링 및 분류) 실행 진입점.
    run_pipeline.py (마스터 스크립트)에서 호출됩니다.
    """
    print("머신러닝 모델링 및 시각화 프로세스를 시작합니다.")
    galaxy_classifier.run_clustering_and_classification()
    print("머신러닝 프로세스 종료.")

if __name__ == "__main__":
    run_pipeline()
