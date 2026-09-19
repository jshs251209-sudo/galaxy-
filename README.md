# 은하 진화 다차원 분석 및 통합 분류 체계 구축 (Multidimensional Analysis of Galaxy Evolution and Construction of an Integrated Classification System)

## 프로젝트 개요 (Project Overview & Objectives)
본 프로젝트는 기존 허블 분류 체계(형태 중심)의 한계를 극복하고, 은하의 물리적/화학적 특성에 기반한 다차원적이고 객관적인 새로운 은하 분류 체계를 구축하기 위해 시작되었습니다. SDSS(Sloan Digital Sky Survey) DR18 데이터 및 MPA-JHU 카탈로그를 활용하여 은하의 질량, 별 생성률(SFR), 금속량(Metallicity), 그리고 BPT 방출선 비율 등을 종합적으로 분석합니다. 최종적으로 머신러닝 기법(K-Means, Random Forest)을 적용하여 새로운 은하 군집을 정의하고, 이를 시각적으로 탐구할 수 있는 웹 대시보드를 제공합니다.

## 설치 방법 (Installation)
Python 3.8 이상이 필요합니다. 아래 명령어를 통해 필요한 패키지를 설치하십시오.

```bash
pip install -r requirements.txt
```

## 빠른 시작 (Quick Start)
전체 데이터 수집, 전처리, 분석 및 모델 학습 파이프라인을 한 번에 실행하려면 다음 명령어를 실행합니다.

```bash
python run_pipeline.py
```
파이프라인이 완료되면 `output/` 디렉토리에 시각화 도표와 모델이 생성되며, 웹 대시보드를 통해 결과를 확인할 수 있습니다.

## 프로젝트 구조 (Project Structure)
```
YSC_대회/
├── config.py                         # 전역 설정 및 파라미터 관리
├── requirements.txt                  # 필요 패키지 목록
├── data_fetcher.py                   # SDSS API를 통한 원시 데이터 수집
├── data_processor.py                 # 데이터 전처리 및 물리량(SFR, 금속량 등) 계산
├── galaxy_correlation_analyzer.py    # [신규] 은하 물리량-화학조성 상관관계 통계 분석기
├── Galaxy_Correlation_Analysis_Colab.ipynb # [신규] Google Colab 즉시 실행용 노트북
├── plot_generators.py                # 정적 시각화 도표 생성 (BPT, MZR 등)
├── plot_interactive.py               # 인터랙티브 시각화 도표 생성
├── galaxy_classifier.py              # 머신러닝 기반 은하 분류 모델 
├── validation_tool.py                # 분류 체계 및 데이터 검증 도구
├── run_ml_pipeline.py                # 머신러닝 모델 학습 파이프라인
├── run_pipeline.py                   # 전체 파이프라인 통합 실행 스크립트
├── dashboard/                        # 웹 대시보드 리소스 (HTML, CSS, JS)
├── galaxy_analysis_output/           # [신규] 상관분석 결과 도표(PNG) 및 통계표(CSV)
├── data/
│   ├── raw/                          # 원본 수집 데이터
│   └── processed/                    # 전처리 완료된 마스터 데이터셋
├── output/
│   ├── plots/                        # 생성된 도표 이미지 및 HTML
│   └── models/                       # 학습된 ML 모델 및 스케일러 (.pkl)
└── docs/                             # 프로젝트 문서
    ├── galaxy_correlation_guide.md   # [신규] 상관분석 및 통계 이론 가이드
    ├── research_report.md            # 연구 보고서 (논문 초안)
    └── data_dictionary.md            # 데이터 명세서
```

## 데이터 출처 (Data Sources)
- **SDSS DR18**: 측광 및 분광 데이터 수집 (z < 0.1의 근거리 은하 중심).
- **MPA-JHU Catalog**: 별 생성률(SFR), 항성 질량, 방출선 플럭스(H-alpha, H-beta, [OIII], [NII] 등) 데이터를 포함한 파생 카탈로그.

## 주요 결과 요약 (Key Results Summary)
- 은하 주계열(Main Sequence) 및 질량-금속량 관계(MZR)의 뚜렷한 상관성 확인.
- BPT Diagram을 활용한 별 생성 은하(Star-forming)와 활동은하핵(AGN)의 명확한 분리.
- 다차원 변수를 활용한 K-Means 클러스터링을 통해 형태학적 분류로는 설명할 수 없었던 특이 은하 군집 발견.

## 웹 대시보드 사용법 (Web Dashboard)
데이터 분석 결과를 인터랙티브하게 탐색할 수 있습니다. `dashboard/index.html` 파일을 웹 브라우저로 열거나, 로컬 서버를 띄워 접속하십시오.
```bash
python -m http.server --directory dashboard 8000
```
접속 주소: `http://localhost:8000`

## 천체 스펙트럼 분석기 (Spectrum Analyzer)
1D 관측 스펙트럼(CSV) 또는 스마트폰 등으로 촬영한 **스펙트럼 회절 사진(JPG/PNG)**을 업로드하여 방출선을 자동 감지하고 분류(BPT)할 수 있습니다.
다음 명령어로 Streamlit 앱을 실행하세요.
```bash
streamlit run spectrum_analyzer.py
```

## 검증 도구 사용법 (Validation Tool)
데이터 품질 및 모델의 유효성을 검증하기 위해 `validation_tool.py`를 실행할 수 있습니다.
```bash
python validation_tool.py
```
이는 데이터의 이상치(Anomaly), 누락값, 그리고 물리량 교정식의 정상 작동 여부를 확인합니다.

## 은하 물리량 및 화학적 조성 상관관계 분석기 (Galaxy Correlation Analyzer)
은하의 항성질량($M_*$), 별 생성률(SFR), 기체 금속함량($12+\log(\mathrm{O/H})$) 간의 상관관계를 통계적(Pearson, Spearman, 회귀분석, p-value)으로 자동 분석하고 표본 크기($N=100, 300, 500, 1000$)에 따른 수렴성을 검증합니다.

```bash
python galaxy_correlation_analyzer.py
```
- **결과 저장 위치**: `galaxy_analysis_output/`
- **생성 결과물**:
  - `scatter_mass_vs_sfr.png` (은하 주계열, SFMS)
  - `scatter_mass_vs_metallicity.png` (질량-금속함량 관계, MZR)
  - `scatter_sfr_vs_metallicity.png` (SFR-금속함량 관계, FMR)
  - `three_core_relations_summary.png` (3대 핵심 관계 종합 도표)
  - `sample_size_convergence.png` (표본 크기별 상관계수 수렴성)
  - `galaxy_correlation_summary.csv` 및 `galaxy_type_correlation_summary.csv`
- **Google Colab 지원**: `Galaxy_Correlation_Analysis_Colab.ipynb`를 열어 브라우저에서 즉시 실행 가능합니다.

## 라이선스 (License)
이 프로젝트는 MIT License를 따릅니다.

## 기여자 (Contributors)
- 정현 (과학탐구 YSC 대회 프로젝트)

## 참고문헌 (References)
- Kauffmann, G., et al. (2003). The host galaxies of active galactic nuclei. *MNRAS*.
- Kewley, L. J., et al. (2001). Theoretical modeling of starburst galaxies. *The Astrophysical Journal*.
- Tremonti, C. A., et al. (2004). The origin of the mass-metallicity relation. *The Astrophysical Journal*.
- Kennicutt, R. C. (1998). Star formation in galaxies along the Hubble sequence. *ARA&A*.
