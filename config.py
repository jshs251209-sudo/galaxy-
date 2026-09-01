"""
프로젝트 전역 설정 파일 (config.py)
===========================================
은하 진화 다차원 분석 및 관측 소프트웨어 (버전 2.0)
"""

import os

# ── 경로 설정 ──────────────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
RAW_DATA_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DATA_DIR = os.path.join(DATA_DIR, "processed")
EXCEL_DIR = os.path.join(DATA_DIR, "excel_exports")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")
PLOT_DIR = os.path.join(OUTPUT_DIR, "plots")
PHYSICAL_PLOT_DIR = os.path.join(PLOT_DIR, "physical")
CHEMICAL_PLOT_DIR = os.path.join(PLOT_DIR, "chemical")
MODEL_DIR = os.path.join(OUTPUT_DIR, "models")

# 디렉토리 자동 생성
for d in [DATA_DIR, RAW_DATA_DIR, PROCESSED_DATA_DIR, EXCEL_DIR, OUTPUT_DIR,
          PLOT_DIR, PHYSICAL_PLOT_DIR, CHEMICAL_PLOT_DIR, MODEL_DIR]:
    os.makedirs(d, exist_ok=True)

# ── BPT 진단 도표 파라미터 ────────────────────────
BPT_KAUFFMANN_PARAMS = [0.61, 0.05, 1.3]
BPT_KEWLEY_PARAMS = [0.61, 0.47, 1.19]

# ── SDSS API 설정 ──────────────────────────────────
SDSS_SKYSERVER_URL = "https://skyserver.sdss.org/dr18/SkyServerWS/SearchTools/SqlSearch"
SDSS_QUERY_FORMAT = "csv"

# ── 데이터 수집 파라미터 (10만 개 목표) ────────────
REDSHIFT_MIN = 0.02
REDSHIFT_MAX = 0.20       # 더 많은 데이터를 위해 최대 적색편이 확장
TARGET_GALAXIES = 100000  # 목표 수집 수
CHUNK_SIZE = 10000        # API 타임아웃 방지를 위한 1회 요청 단위
SNR_THRESHOLD = 3.0       # 방출선 신호대잡음비 임계값

# ── 파일 경로 ──────────────────────────────────────
RAW_SDSS_FILE = os.path.join(RAW_DATA_DIR, "sdss_100k_raw.csv")
MASTER_DATASET_FILE = os.path.join(PROCESSED_DATA_DIR, "galaxy_master_200params.csv")
MASTER_JSON_FILE = os.path.join(PROCESSED_DATA_DIR, "galaxy_master_200params.json")
MASTER_JSON_LEGACY = os.path.join(PROCESSED_DATA_DIR, "galaxy_master_dataset.json")
MASTER_CSV_200_FILE = os.path.join(PROCESSED_DATA_DIR, "galaxy_master_200params.csv")
PHYSICAL_EXCEL_FILE = os.path.join(EXCEL_DIR, "physical_100k.xlsx")
CHEMICAL_EXCEL_FILE = os.path.join(EXCEL_DIR, "chemical_100k.xlsx")

EXPORT_EXCEL = False  # Set to True to enable Excel export (default CSV)
# 진화 척도(Evolution Metric) 기준: D4000
# D4000은 늙은 항성군이 많을수록 값이 커지므로 은하 나이의 척도로 사용합니다.
