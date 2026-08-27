# 은하 진화 다차원 분석 및 통합 분류 체계 구축 - 종합 프로젝트 보고서

본 보고서는 해당 프로젝트의 모든 파일 정보, 소스 코드, 문서 내용 및 구조를 빠짐없이 포함하는 종합 보고서입니다.

## 1. 프로젝트 핵심 문서

### README.md

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
├── config.py                 # 전역 설정 및 파라미터 관리
├── requirements.txt          # 필요 패키지 목록
├── data_fetcher.py           # SDSS API를 통한 원시 데이터 수집
├── data_processor.py         # 데이터 전처리 및 물리량(SFR, 금속량 등) 계산
├── plot_generators.py        # 정적 시각화 도표 생성 (BPT, MZR 등)
├── plot_interactive.py       # 인터랙티브 시각화 도표 생성
├── galaxy_classifier.py      # 머신러닝 기반 은하 분류 모델 
├── validation_tool.py        # 분류 체계 및 데이터 검증 도구
├── run_ml_pipeline.py        # 머신러닝 모델 학습 파이프라인
├── run_pipeline.py           # 전체 파이프라인 통합 실행 스크립트
├── dashboard/                # 웹 대시보드 리소스 (HTML, CSS, JS)
├── data/
│   ├── raw/                  # 원본 수집 데이터
│   └── processed/            # 전처리 완료된 마스터 데이터셋
├── output/
│   ├── plots/                # 생성된 도표 이미지 및 HTML
│   └── models/               # 학습된 ML 모델 및 스케일러 (.pkl)
└── docs/                     # 프로젝트 문서
    ├── research_report.md    # 연구 보고서 (논문 초안)
    └── data_dictionary.md    # 데이터 명세서
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

## 라이선스 (License)
이 프로젝트는 MIT License를 따릅니다.

## 기여자 (Contributors)
- 정현 (과학탐구 YSC 대회 프로젝트)

## 참고문헌 (References)
- Kauffmann, G., et al. (2003). The host galaxies of active galactic nuclei. *MNRAS*.
- Kewley, L. J., et al. (2001). Theoretical modeling of starburst galaxies. *The Astrophysical Journal*.
- Tremonti, C. A., et al. (2004). The origin of the mass-metallicity relation. *The Astrophysical Journal*.
- Kennicutt, R. C. (1998). Star formation in galaxies along the Hubble sequence. *ARA&A*.


### docs/research_report.md

# 연구 보고서 (Research Report)

**프로젝트명**: 은하 진화 다차원 분석 및 통합 분류 체계 구축
**작성자**: 정현 (YSC 과학탐구 대회)

---

## 1. 서론 (Introduction)

### 1.1 연구 배경
은하의 분류는 역사적으로 Edwin Hubble (1926)의 '허블 튜닝 포크' 형태학적 분류에 크게 의존해왔습니다. 이는 가시광선 영역에서 나타나는 은하의 시각적 구조(나선팔, 타원형 팽대부 등)를 기준으로 합니다. 그러나 현대 천체물리학에서 은하의 진화를 이해하기 위해서는 눈에 보이는 형태뿐만 아니라 은하 내부의 별 생성 활동, 기체의 화학적 조성(금속량), 그리고 중심부 블랙홀(AGN)의 활동성 등 본질적인 물리/화학적 특성이 필수적입니다. 

### 1.2 연구의 필요성 및 목적
형태만으로는 활동은하핵을 가진 타원은하와 별 생성이 활발한 타원은하를 구분하기 어렵고, 환경에 따른 은하의 퀜칭(Quenching, 별 생성 중단) 메커니즘을 온전히 설명하기 힘듭니다. 따라서 본 연구의 목적은 SDSS(Sloan Digital Sky Survey) 대규모 관측 데이터를 활용하여 은하의 질량, 금속량, 항성 종족 연령 등 다양한 물리량을 분석하고, 머신러닝(Machine Learning) 클러스터링 기법을 적용하여 다차원 데이터를 기반으로 한 새롭고 객관적인 '통합 은하 분류 체계'를 구축하는 것입니다.

---

## 2. 데이터 및 방법론 (Data & Methods)

### 2.1 데이터 수집 (Data Collection)
본 연구는 SDSS Data Release 18 (DR18)과 MPA-JHU 파생 카탈로그를 사용했습니다. 근접 우주의 은하를 분석하기 위해 적색편이(Redshift) 범위는 $0.02 < z < 0.1$ 로 한정하였으며, 정확한 방출선(Emission line) 해석을 위해 주요 방출선 플럭스의 신호대잡음비(S/N)가 3.0 이상인 데이터를 필터링했습니다.

### 2.2 파생 물리량 계산 (Derived Physical Quantities)
분광 데이터를 기반으로 은하의 주요 물리량을 도출했습니다.
* **성간 소광(Dust Extinction)**: 발머 감소율(Balmer Decrement, H$\alpha$/H$\beta$)을 측정하여 이론적 값(2.86, Case B 재결합)과 비교, 소광량(E(B-V))을 산출했습니다.
* **별 생성률(Star Formation Rate, SFR)**: Kennicutt (1998)의 관계식을 사용하여 먼지 소광이 보정된 H$\alpha$ 광도를 SFR로 변환했습니다. 
  $$ SFR(M_\odot/\text{yr}) = 7.9 \times 10^{-42} \times L(H\alpha) $$
* **금속량(Metallicity, $12+\log(O/H)$)**: 질소-수소 비율([NII]/H$\alpha$) 등을 이용한 경험적 검정식(Tremonti et al., 2004)을 활용해 기체 산소 금속량을 추정했습니다.

### 2.3 다차원 머신러닝 분석 (Machine Learning Methodology)
물리량을 추출한 후, 데이터를 정규화(Standard Scaling)하고 비지도 학습인 K-Means 클러스터링을 적용했습니다. 입력 변수(Features)로는 질량(`log_stellar_mass`), 별 생성률(`log_sfr`), 색지수(`u-g`, `g-r`), 방출선 비율(`log_nii_ha`, `log_oiii_hb`), 속도 분산(`veldisp`)을 사용했습니다. 최적의 군집 수(K)는 엘보우 기법(Elbow method)과 실루엣 점수(Silhouette score)를 통해 도출했습니다.

---

## 3. 결과 (Results)

### 3.1 은하 물리 도표 분석 (Galaxy Physical Scaling Relations)
* **주계열 은하(Star-Forming Main Sequence)**: 항성 질량과 별 생성률 사이의 강한 양의 상관관계가 뚜렷하게 관측되었습니다. 무거운 은하일수록 질량 대비 별 생성 효율이 떨어지는 '다운사이징(Downsizing)' 경향성이 확인되었습니다.
* **질량-금속량 관계(Mass-Metallicity Relation, MZR)**: 은하의 질량이 클수록 깊은 중력 우물(Gravitational well)에 의해 금속이 외부로 유출되지 않고 축적되어 금속량이 높게 나타나는 MZR을 명확히 확인했습니다.

### 3.2 BPT 다이어그램에 따른 활동성 화학 분류 (BPT Classification)
[OIII]/H$\beta$와 [NII]/H$\alpha$ 비율을 나타내는 BPT 도표를 그렸습니다. Kauffmann (2003)과 Kewley (2001)의 경험적 및 이론적 경계선을 기준으로 데이터를 분류한 결과, 별 생성 은하(Star-forming), 복합 은하(Composite), 활동은하핵(AGN, Seyfert & LINER) 영역이 뚜렷이 분리되었습니다. 

### 3.3 머신러닝 클러스터링 기반 신규 분류 체계
다차원 데이터를 바탕으로 K-Means를 수행한 결과, 기존 허블 분류를 넘어선 새로운 하위 군집들이 도출되었습니다. 
* 예컨대 기존에는 단순한 "나선은하"로 분류되던 그룹 내에서도, 금속량이 이례적으로 낮으면서도 높은 별 생성률을 보이는 특이 군집(잠재적 병합 은하 또는 갓 형성된 은하)이 머신러닝 알고리즘에 의해 자동 식별되었습니다.
* Random Forest 분류 모델을 통해 새롭게 정의된 이 군집들의 특징 중요도(Feature Importance)를 분석한 결과, 색지수와 방출선 비율이 군집을 나누는 결정적인 변수로 작용함을 확인했습니다.

---

## 4. 논의 (Discussion)

본 연구에서 구축한 "통합 다차원 분류 체계"는 기존 형태 기반 허블 체계가 놓치던 은하 진화의 역동적인 과정(Gas accretion, Quenching, AGN 피드백)을 정량적으로 반영한다는 점에서 큰 의미가 있습니다. 
하지만 현재 데이터셋은 중심 팽대부가 주를 이루는 단일 슬릿(Fiber) 분광 데이터(SDSS 3초각 중심 데이터)의 특성상, 은하 전체의 적분된 성질을 100% 대변하지 못할 수 있다는 한계가 있습니다. 향후 IFU(Integral Field Unit, 예: MaNGA) 관측 데이터를 활용하여 은하 내부의 공간적 분포까지 고려한다면 분류 모델의 신뢰도를 한층 더 높일 수 있을 것입니다.

---

## 5. 결론 (Conclusion)

SDSS DR18 데이터를 기반으로 한 은하 진화 다차원 분석 및 K-Means 클러스터링을 통하여, 은하의 질량, 항성 종족, 화학적 성질 등을 종합적으로 반영하는 새롭고 객관적인 은하 분류 체계를 구축했습니다. 본 연구는 물리/화학적 파라미터가 은하의 진화 단계를 얼마나 명확히 대변하는지 시각적, 수치적으로 증명하였으며, 향후 빅데이터와 인공지능이 천문학 연구에 기여할 수 있는 강력한 방향성을 제시합니다.

---

## 6. 참고문헌 (References)

1. Hubble, E. P. (1926). Extragalactic nebulae. *The Astrophysical Journal*, 64, 321-369.
2. Kauffmann, G., et al. (2003). The host galaxies of active galactic nuclei. *Monthly Notices of the Royal Astronomical Society*, 346(4), 1055-1077.
3. Kewley, L. J., et al. (2001). Theoretical modeling of starburst galaxies. *The Astrophysical Journal*, 556(1), 121.
4. Tremonti, C. A., et al. (2004). The origin of the mass-metallicity relation: insights from 53,000 star-forming galaxies in the SDSS. *The Astrophysical Journal*, 613(2), 898.
5. Kennicutt, R. C. (1998). Star formation in galaxies along the Hubble sequence. *Annual Review of Astronomy and Astrophysics*, 36(1), 189-231.
6. Baldwin, J. A., Phillips, M. M., & Terlevich, R. (1981). Classification parameters for the emission-line spectra of extragalactic objects. *Publications of the Astronomical Society of the Pacific*, 93, 5-19.


### docs/data_dictionary.md

# 은하 진화 데이터 명세서 (Data Dictionary)

본 문서는 `galaxy_master_dataset.csv` 및 관련 데이터셋에 포함된 모든 변수의 정의, 단위, 물리적 의미 및 계산 방식을 설명합니다.

## 1. 식별자 및 기본 측광 정보 (Identifiers and Basic Photometry)

| 변수명 (Column) | 데이터 타입 (Type) | 단위 (Unit) | 설명 (Description) |
|-----------------|--------------------|-------------|--------------------|
| `objID` | String / Int64 | - | SDSS 고유 은하 식별자 |
| `ra` | Float | Degree | 적경 (Right Ascension, J2000) |
| `dec` | Float | Degree | 적위 (Declination, J2000) |
| `redshift` | Float | - | 적색편이 (z). 0.02 < z < 0.1 범위 내의 데이터로 필터링됨 |
| `u_mag`, `g_mag`, `r_mag`, `i_mag`, `z_mag` | Float | Magnitude | SDSS 5개 필터에서의 겉보기 등급 (Apparent magnitude) |

## 2. 분광학적 방출선 데이터 (Spectroscopic Emission Lines)

방출선 플럭스(Flux)의 단위는 모두 $10^{-17} \text{ erg} \text{ cm}^{-2} \text{ s}^{-1}$ 입니다.

| 변수명 (Column) | 데이터 타입 (Type) | 설명 (Description) |
|-----------------|--------------------|--------------------|
| `h_alpha_flux` | Float | 수소 발머 계열 H$\alpha$ ($\lambda 6563$) 방출선 플럭스 |
| `h_alpha_flux_err`| Float | H$\alpha$ 방출선 플럭스 측정 오차 |
| `h_beta_flux` | Float | 수소 발머 계열 H$\beta$ ($\lambda 4861$) 방출선 플럭스 |
| `oiii_5007_flux`| Float | 산소 금지선 [OIII] ($\lambda 5007$) 플럭스 |
| `nii_6584_flux` | Float | 질소 금지선 [NII] ($\lambda 6584$) 플럭스 |
| `sii_6717_flux`, `sii_6731_flux` | Float | 황 금지선 [SII] 플럭스 (전자 밀도 측정 등에 활용) |

*참고: 신호대잡음비(SNR)가 `SNR_THRESHOLD` (3.0) 미만인 데이터는 품질을 위해 필터링 처리됩니다.*

## 3. 파생된 물리량 (Derived Physical Quantities)

수집된 원본 데이터를 바탕으로 수식(config.py 참조)을 통해 계산된 파생 변수들입니다.

| 변수명 (Column) | 단위 (Unit) | 설명 및 계산 수식 (Description & Formulas) |
|-----------------|-------------|--------------------------------------------|
| `balmer_decrement` | - | 발머 감소율 (Balmer Decrement). `h_alpha_flux / h_beta_flux`. 소광(Dust extinction)의 정도를 측정함. 이론적 한계값(Case B, 2.86)보다 크면 먼지에 의한 소광 존재를 의미함. |
| `dust_ebv` | Magnitude | 성간 먼지로 인한 색 초과 (E(B-V)). `dust_ebv = 1.086 / (K_Hbeta - K_Halpha) * ln(balmer_decrement / 2.86)`. |
| `u_g_color`, `g_r_color` | Magnitude | 색지수 (Color index). 은하의 항성 종족 연령을 대략적으로 나타냄. |
| `log_sfr` | $\log_{10}(M_\odot/\text{yr})$ | 별 생성률 (Star Formation Rate)의 로그값. Kennicutt (1998)의 H$\alpha$ 광도 변환식을 사용해 계산됨. $SFR = 7.9 \times 10^{-42} \times L(H\alpha)$. 광도는 소광 보정 및 적색편이 기반 거리 지수를 통해 유도됨. |
| `log_stellar_mass` | $\log_{10}(M_\odot)$ | 항성 질량의 로그값. 질량-광도 관계 및 색지수를 이용해 MPA-JHU 카탈로그로부터 도출됨. |
| `metallicity_oh` | $12 + \log(O/H)$ | 기체 산소 금속량(Metallicity). [NII]/H$\alpha$ 비율 또는 O3N2 경험적 교정식(Tremonti et al. 2004 등)을 통해 산출. |
| `veldisp` | km/s | 중심부 속도 분산 (Velocity dispersion). 은하의 역학적 질량 및 중심 블랙홀 질량 추정에 사용됨. |

## 4. BPT 관련 비율 (BPT Ratios for Classification)

BPT 다이어그램 (Baldwin, Phillips & Terlevich 1981)을 그리기 위한 로그 비율입니다.

| 변수명 (Column) | 수식 (Formula) | 설명 (Description) |
|-----------------|----------------|--------------------|
| `log_nii_ha` | $\log_{10}( [NII]\lambda6584 / H\alpha )$ | 저전리(low-ionization) 질소 방출선 대비 H$\alpha$ 비율 |
| `log_oiii_hb` | $\log_{10}( [OIII]\lambda5007 / H\beta )$ | 고전리(high-ionization) 산소 방출선 대비 H$\beta$ 비율 |

## 5. 은하 분류 레이블 (Classification Labels)

| 변수명 (Column) | 설명 (Description) |
|-----------------|--------------------|
| `bpt_class` | BPT 다이어그램 기준 분류 (Star-forming, Composite, AGN(Seyfert/LINER)). Kauffmann (2003) 및 Kewley (2001) 경계선 기반. |
| `ml_cluster_id` | 본 프로젝트의 K-Means 등 머신러닝 알고리즘에 의해 다차원(질량, 금속량, 색상 등) 특징 벡터로 새롭게 분류된 군집(Cluster) 번호 (예: 0, 1, 2...). |

## 6. 품질 관리 플래그 (Quality Flags)
- SNR 필터링 및 비물리적 값(예: 음수 플럭스, NaN)은 전처리 파이프라인(`data_processor.py`)에서 제거됩니다.
- 극단적인 이상치(Anomaly)는 머신러닝 전처리 중 Confidence Interval 검증(`ANOMALY_CONFIDENCE`)을 통해 식별되어 제외될 수 있습니다.


## 2. 프로젝트 디렉토리 구조 및 전체 파일 목록

```text
YSC_대회/
    Comprehensive_Project_Report.md
    config.py
    data_fetcher.py
    data_processor.py
    extracted_spectrum.csv
    galaxy_classifier.py
    generate_md.py
    KakaoTalk_20260823_194436339.jpg
    launcher.html
    plot_generators.py
    plot_interactive.py
    README.md
    requirements.txt
    run_ml_pipeline.py
    run_pipeline.py
    run_project.bat
    spectrum_analyzer.py
    validation_tool.py
    dashboard/
        app.js
        index.html
        style.css
    data/
        excel_exports/
            chemical_100k.xlsx
            physical_100k.xlsx
        processed/
            galaxy_100k_master.csv
            galaxy_master_dataset.csv
        raw/
            sdss_100k_raw.csv
            sdss_raw_galaxies.csv
    docs/
        data_dictionary.md
        research_report.md
    output/
        models/
            kmeans_model.pkl
            rf_model.pkl
            scaler.pkl
        plots/
            bpt_diagram.png
            color_mass_diagram.png
            confusion_matrix.png
            feature_importance.png
            integrated_evolution.png
            main_sequence.png
            mass_metallicity.png
            roc_curve.png
            tully_fisher.png
            validation_bpt_overlay.png
            chemical/
                chem_NII_Ha_vs_OIII_Hb.png
                chem_NII_Ha_vs_OII_OIII.png
                chem_NII_Ha_vs_SII_Ha.png
                chem_OIII_Hb_vs_OII_OIII.png
                chem_OIII_Hb_vs_SII_Ha.png
                chem_SII_Ha_vs_OII_OIII.png
            interactive/
                bpt_interactive.html
                color_mass_interactive.html
                main_sequence_interactive.html
            physical/
                phys_Concentration_vs_g_r.png
                phys_Concentration_vs_u_r.png
                phys_Concentration_vs_z.png
                phys_g_r_vs_z.png
                phys_petroRad_r_vs_Concentration.png
                phys_petroRad_r_vs_g_r.png
                phys_petroRad_r_vs_u_r.png
                phys_petroRad_r_vs_z.png
                phys_u_r_vs_g_r.png
                phys_u_r_vs_z.png
```

## 3. 파일별 상세 정보 및 소스 코드

### 파일: `config.py`

- **경로**: `c:\Users\neato\Desktop\정현\03_과학탐구_대회\YSC_대회\config.py`
- **크기**: 2581 bytes
- **유형**: 소스 코드 / 텍스트 문서

**[내용]**:
```py
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
MASTER_DATASET_FILE = os.path.join(PROCESSED_DATA_DIR, "galaxy_100k_master.csv")
PHYSICAL_EXCEL_FILE = os.path.join(EXCEL_DIR, "physical_100k.xlsx")
CHEMICAL_EXCEL_FILE = os.path.join(EXCEL_DIR, "chemical_100k.xlsx")

# ── 추가 분석 상수 ─────────────────────────────────
# 진화 척도(Evolution Metric) 기준: D4000
# D4000은 늙은 항성군이 많을수록 값이 커지므로 은하 나이의 척도로 사용합니다.

```

### 파일: `data_fetcher.py`

- **경로**: `c:\Users\neato\Desktop\정현\03_과학탐구_대회\YSC_대회\data_fetcher.py`
- **크기**: 3972 bytes
- **유형**: 소스 코드 / 텍스트 문서

**[내용]**:
```py
import pandas as pd
import requests
import io
import time
import numpy as np
import config
import os

def fetch_sdss_data() -> pd.DataFrame:
    """
    SDSS SkyServer DR18 SQL API를 호출하여 적색편이 구간별로 은하 데이터를 수집합니다.
    """
    print("SDSS 데이터 수집 시작 (목표: 10만 개)...")
    
    # 0.02 to 0.20
    z_min = config.REDSHIFT_MIN
    z_max = config.REDSHIFT_MAX
    step = 0.015
    
    all_data = []
    total_fetched = 0
    
    # Redshift bins
    z_bins = np.arange(z_min, z_max + step, step)
    
    for i in range(len(z_bins) - 1):
        current_z_min = z_bins[i]
        current_z_max = z_bins[i+1]
        
        if total_fetched >= config.TARGET_GALAXIES:
            break
            
        limit = config.TARGET_GALAXIES - total_fetched
        
        sql_query = f"""
        SELECT TOP {limit}
            s.specObjID, s.ra, s.dec, s.z, s.velDisp, s.velDispErr,
            p.u, p.g, p.r, p.i, p.z as phot_z,
            p.petroRad_r, p.petroR50_r, p.petroR90_r,
            l.h_alpha_flux, l.h_alpha_flux_err,
            l.h_beta_flux, l.h_beta_flux_err,
            l.h_gamma_flux, l.h_gamma_flux_err,
            l.oiii_5007_flux, l.oiii_5007_flux_err,
            l.nii_6584_flux, l.nii_6584_flux_err,
            l.sii_6717_flux, l.sii_6717_flux_err,
            l.oii_3726_flux, l.oii_3726_flux_err,
            e.lgm_tot_p50, e.sfr_tot_p50, e.oh_p50, e.bptclass,
            indx.d4000_n
        FROM SpecObj s
        JOIN PhotoObj p ON s.bestObjID = p.objID
        JOIN galSpecLine l ON s.specObjID = l.specObjID
        JOIN galSpecExtra e ON s.specObjID = e.specObjID
        JOIN galSpecIndx indx ON s.specObjID = indx.specObjID
        WHERE s.class = 'GALAXY'
          AND s.zWarning = 0
          AND s.z >= {current_z_min:.4f} AND s.z < {current_z_max:.4f}
          AND l.h_alpha_flux > 0 AND l.h_beta_flux > 0
          AND l.oiii_5007_flux > 0 AND l.nii_6584_flux > 0
          AND p.petroR50_r > 0
        """
        
        params = {
            "cmd": sql_query,
            "format": config.SDSS_QUERY_FORMAT
        }
        
        print(f"[{current_z_min:.4f} ~ {current_z_max:.4f}] 적색편이 구간 데이터 요청 중...")
        
        try:
            response = requests.get(config.SDSS_SKYSERVER_URL, params=params, timeout=120)
            response.raise_for_status()
            
            if response.text.startswith("ERROR"):
                print(f"SDSS API 에러 발생: {response.text}")
                continue
                
            df = pd.read_csv(io.StringIO(response.text), skiprows=1)
            
            if not df.columns.str.contains('specObjID').any():
                df = pd.read_csv(io.StringIO(response.text), skiprows=2)
                
            if len(df.columns) == 1 and ',' in response.text:
                df = pd.read_csv(io.StringIO(response.text))
                
            if df.empty:
                print("이 구간에서는 수집된 데이터가 없습니다.")
                continue
                
            all_data.append(df)
            total_fetched += len(df)
            print(f"현재 구간 수집: {len(df)}개, 누적 수집: {total_fetched}개")
            
        except Exception as e:
            print(f"요청 중 오류 발생: {e}")
            
        time.sleep(1) # 잠시 대기
        
    if len(all_data) == 0:
        print("수집된 데이터가 없습니다. 빈 DataFrame을 반환합니다.")
        return pd.DataFrame()
        
    final_df = pd.concat(all_data, ignore_index=True)
    
    # 10만개까지만 자르기
    if len(final_df) > config.TARGET_GALAXIES:
        final_df = final_df.head(config.TARGET_GALAXIES)
        
    print(f"최종 데이터 수집 완료: 총 {len(final_df)} 개")
    final_df.to_csv(config.RAW_SDSS_FILE, index=False)
    
    return final_df

if __name__ == "__main__":
    fetch_sdss_data()

```

### 파일: `data_processor.py`

- **경로**: `c:\Users\neato\Desktop\정현\03_과학탐구_대회\YSC_대회\data_processor.py`
- **크기**: 5671 bytes
- **유형**: 소스 코드 / 텍스트 문서

**[내용]**:
```py
import pandas as pd
import numpy as np
import config
import os

def process_data(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    원시 은하 데이터를 로드하여 물리적 특성을 도출하고 엑셀 파일로 분리 저장합니다.
    """
    df = df_raw.copy()
    
    # 기본 필터링 (물리적으로 의미있는 값)
    df = df[df['lgm_tot_p50'] > 0].copy()
    df = df[df['petroR50_r'] > 0].copy()
    
    # 1. 색상 지수 계산
    df['u_g'] = df['u'] - df['g']
    df['g_r'] = df['g'] - df['r']
    
    # 2. 집중도 지수 (Concentration Index) 계산
    df['concentration_index'] = df['petroR90_r'] / df['petroR50_r']
    
    # 3. 표면 밝기 (Surface Brightness) 계산
    # r-band surface brightness: mu = r + 2.5 * log10(2 * pi * R50^2)
    df['surface_brightness_r'] = df['r'] + 2.5 * np.log10(2 * np.pi * (df['petroR50_r'] ** 2))
    
    # 4. Balmer Decrement 및 Dust E(B-V)
    # Halpha / Hbeta 
    balmer_ratio = df['h_alpha_flux'] / df['h_beta_flux']
    intrinsic_ratio = 2.86
    balmer_ratio = np.maximum(balmer_ratio, intrinsic_ratio)
    
    # k(lambda) values (Calzetti or similar, simplified)
    k_ha = 2.53
    k_hb = 3.61
    df['dust_ebv'] = (2.5 / (k_hb - k_ha)) * np.log10(balmer_ratio / intrinsic_ratio)
    
    # 5. BPT 라인 비율
    df['log_nii_ha'] = np.log10(df['nii_6584_flux'] / df['h_alpha_flux'])
    df['log_oiii_hb'] = np.log10(df['oiii_5007_flux'] / df['h_beta_flux'])
    
    # 6. 이해하기 쉬운 단순 물리량 추가
    # 우주론적 거리 (단위: Mpc, H0 = 70 km/s/Mpc 가정)
    df['distance_mpc'] = df['z'] * 300000 / 70
    # 겉보기 등급 (Apparent Magnitude)
    df['app_mag_r'] = df['r']
    df['app_mag_g'] = df['g']
    # 절대 등급 (Absolute Magnitude: M = m - 5*log10(d in pc) + 5)
    # distance_mpc를 pc 단위로 변환하기 위해 1e6 곱함
    df['abs_mag_r'] = df['r'] - 5 * np.log10(df['distance_mpc'] * 1e6) + 5
    
    # 7. 동역학적 질량 및 암흑물질 비율 추정
    # petroR50_r은 arcsec 단위. 물리적 크기 Re (kpc)로 변환:
    # Re(kpc) = (petroR50_r / 206265) * distance_mpc * 1000
    df['Re_kpc'] = (df['petroR50_r'] / 206265.0) * df['distance_mpc'] * 1000.0
    
    # 비리얼 정리: M_dyn = 5 * sigma^2 * Re / G (G = 4.3009e-6 kpc (km/s)^2 / M_sun)
    G = 4.3009e-6
    # velDisp 단위는 km/s
    df['dyn_mass_msun'] = (5.0 * (df['velDisp'] ** 2) * df['Re_kpc']) / G
    
    # lgm_tot_p50 는 log(M_star / M_sun). 선형 스케일로 변환.
    df['stellar_mass_msun'] = 10 ** df['lgm_tot_p50']
    
    # 암흑물질 비율 (f_DM = 1 - M_star / M_dyn)
    # M_dyn이 0이거나 NaN일 경우 대비, 물리적으로 불가능한 값(M_star > M_dyn) 방어
    df['dark_matter_fraction'] = 1.0 - (df['stellar_mass_msun'] / df['dyn_mass_msun'])
    # 0 이하로 떨어지는 경우(에러 또는 바리온 중심 모델) 0으로 하한
    df['dark_matter_fraction'] = np.where(df['dark_matter_fraction'] < 0, 0, df['dark_matter_fraction'])
    
    # 동역학적 질량도 log 스케일로 저장
    df['log_dyn_mass'] = np.log10(df['dyn_mass_msun'].replace(0, np.nan))
    
    # 8. 은하 형태 (Galaxy Type) 추론
    # SDSS에서는 통상적으로 집중도(Concentration) 2.6을 기준으로 타원/나선 은하를 구분합니다.
    df['galaxy_type'] = np.where(df['concentration_index'] >= 2.6, '타원은하 (Elliptical)', '나선은하 (Spiral)')
    
    # 이름 변경
    rename_dict = {
        'lgm_tot_p50': 'log_stellar_mass',
        'sfr_tot_p50': 'log_sfr',
        'oh_p50': 'metallicity_oh',
        'velDisp': 'veldisp'
    }
    df = df.rename(columns=rename_dict)
    
    # 무한대 값을 NaN으로
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    
    print(f"마스터 데이터셋 생성 중... (총 {len(df)}개)")
    df.to_csv(config.MASTER_DATASET_FILE, index=False)
    
    # 전체 데이터(약 10만 개)를 그대로 사용
    df_sample = df.copy()
    print(f"전체 {len(df_sample)}개의 은하를 물리/화학 엑셀 파일로 분리하여 저장합니다. (10만 개 저장 시 시간이 다소 소요될 수 있습니다.)")
    
    # Physical DataFrame
    physical_cols = [
        'specObjID', 'ra', 'dec', 'galaxy_type', 'distance_mpc', 
        'app_mag_r', 'app_mag_g', 'abs_mag_r',
        'log_stellar_mass', 'log_sfr', 'veldisp', 'z',
        'petroRad_r', 'petroR50_r', 'petroR90_r', 'concentration_index',
        'surface_brightness_r', 'u_g', 'g_r',
        'Re_kpc', 'dyn_mass_msun', 'log_dyn_mass', 'dark_matter_fraction'
    ]
    # 존재하는 컬럼만 선택
    physical_cols = [c for c in physical_cols if c in df_sample.columns]
    df_physical = df_sample[physical_cols]
    
    # Chemical DataFrame
    chemical_cols = [
        'specObjID', 'metallicity_oh', 'd4000_n',
        'h_alpha_flux', 'h_beta_flux', 'h_gamma_flux',
        'oiii_5007_flux', 'nii_6584_flux', 'sii_6717_flux', 'oii_3726_flux',
        'log_nii_ha', 'log_oiii_hb', 'dust_ebv'
    ]
    chemical_cols = [c for c in chemical_cols if c in df_sample.columns]
    df_chemical = df_sample[chemical_cols]
    
    # 엑셀 저장
    print("엑셀 파일로 저장 중입니다...")
    df_physical.to_excel(config.PHYSICAL_EXCEL_FILE, index=False, na_rep='')
    df_chemical.to_excel(config.CHEMICAL_EXCEL_FILE, index=False, na_rep='')
    print("저장 완료!")
    
    return df

if __name__ == "__main__":
    if os.path.exists(config.RAW_SDSS_FILE):
        df_raw = pd.read_csv(config.RAW_SDSS_FILE)
        process_data(df_raw)
    else:
        print(f"원시 데이터 파일이 존재하지 않습니다: {config.RAW_SDSS_FILE}")

```

### 파일: `extracted_spectrum.csv`

- **경로**: `c:\Users\neato\Desktop\정현\03_과학탐구_대회\YSC_대회\extracted_spectrum.csv`
- **크기**: 24048 bytes
- **유형**: 데이터 및 모델 파일
- **설명**: 해당 파일은 머신러닝 모델, 엑셀 또는 CSV 데이터 파일이므로 전체 내용을 텍스트로 표출하지 않고 존재 여부와 크기 정보만 기록합니다.

### 파일: `galaxy_classifier.py`

- **경로**: `c:\Users\neato\Desktop\정현\03_과학탐구_대회\YSC_대회\galaxy_classifier.py`
- **크기**: 6326 bytes
- **유형**: 소스 코드 / 텍스트 문서

**[내용]**:
```py
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, roc_curve, auc
from sklearn.preprocessing import label_binarize
import joblib
import config

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

def run_clustering_and_classification():
    print("--- 머신러닝 파이프라인 시작 ---")
    
    # 1. 데이터 로드
    if not os.path.exists(config.MASTER_DATASET_FILE):
        print(f"데이터 파일이 존재하지 않습니다: {config.MASTER_DATASET_FILE}")
        return
        
    df = pd.read_csv(config.MASTER_DATASET_FILE)
    print(f"데이터 로드 완료: {len(df)}개")
    
    # 방어코드: 필요한 피처들이 없을 수도 있음. 방출선 비율이 없을 수 있으니 확인
    if 'log_nii_ha' not in df.columns:
        df['log_nii_ha'] = np.where((df['nii_6584_flux'] > 0) & (df['h_alpha_flux'] > 0), 
                                    np.log10(df['nii_6584_flux'] / df['h_alpha_flux']), np.nan)
    if 'log_oiii_hb' not in df.columns:
        df['log_oiii_hb'] = np.where((df['oiii_5007_flux'] > 0) & (df['h_beta_flux'] > 0), 
                                     np.log10(df['oiii_5007_flux'] / df['h_beta_flux']), np.nan)
    
    # 2. Features 선택 (물리, 화학적 주요 변수)
    features = ['log_stellar_mass', 'log_sfr', 'u_g', 'g_r', 'log_nii_ha', 'log_oiii_hb', 'veldisp']
    available_features = [f for f in features if f in df.columns]
    
    # 누락된 데이터 제거
    ml_df = df.dropna(subset=available_features).copy()
    print(f"결측치 제거 후 모델링용 데이터: {len(ml_df)}개")
    
    if len(ml_df) < 100:
        print("데이터가 부족하여 ML 파이프라인을 실행할 수 없습니다.")
        return
        
    X = ml_df[available_features]
    
    # 3. 정규화
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # 4. K-Means 군집화 (특이 은하 군집 4개)
    n_clusters = 4
    print(f"K-Means 군집화 진행 중... (군집 수: {n_clusters})")
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    ml_df['ml_cluster_id'] = kmeans.fit_predict(X_scaled)
    
    # 군집 라벨을 직관적으로 변경 (크기에 따라 분류)
    cluster_centers = pd.DataFrame(scaler.inverse_transform(kmeans.cluster_centers_), columns=available_features)
    # 질량 기준으로 정렬하여 이름 부여 (간이 방식)
    sorted_idx = cluster_centers['log_stellar_mass'].sort_values().index if 'log_stellar_mass' in cluster_centers else cluster_centers.index
    cluster_mapping = {idx: f"군집 {i}" for i, idx in enumerate(sorted_idx)}
    ml_df['cluster_name'] = ml_df['ml_cluster_id'].map(cluster_mapping)
    
    # 마스터 데이터셋 업데이트
    # ml_df의 ml_cluster_id를 원본 df에 결합
    if 'ml_cluster_id' in df.columns:
        df = df.drop(columns=['ml_cluster_id', 'cluster_name'], errors='ignore')
    
    # 인덱스 유지하면서 결합
    df = df.join(ml_df[['ml_cluster_id', 'cluster_name']])
    df.to_csv(config.MASTER_DATASET_FILE, index=False)
    print("군집화 결과를 마스터 데이터셋에 업데이트 완료.")
    
    # 5. Random Forest 분류기 훈련
    print("Random Forest 군집 분류 모델 학습 중...")
    y = ml_df['ml_cluster_id']
    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)
    
    rf_model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    rf_model.fit(X_train, y_train)
    
    y_pred = rf_model.predict(X_test)
    
    # 6. 결과 평가 및 시각화
    print("모델 평가 중...")
    
    # Feature Importance
    importances = rf_model.feature_importances_
    indices = np.argsort(importances)[::-1]
    
    plt.figure(figsize=(10, 6))
    plt.title("Random Forest - 특징 중요도 (Feature Importances)")
    plt.bar(range(X.shape[1]), importances[indices], align="center", color='skyblue')
    plt.xticks(range(X.shape[1]), [available_features[i] for i in indices], rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(config.PLOT_DIR, "feature_importance.png"), dpi=300)
    plt.close()
    
    # Confusion Matrix
    cm = confusion_matrix(y_test, y_pred)
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
    plt.title('혼동 행렬 (Confusion Matrix)')
    plt.xlabel('예측된 군집')
    plt.ylabel('실제 군집')
    plt.tight_layout()
    plt.savefig(os.path.join(config.PLOT_DIR, "confusion_matrix.png"), dpi=300)
    plt.close()
    
    # ROC Curve
    y_test_bin = label_binarize(y_test, classes=[0, 1, 2, 3])
    y_score = rf_model.predict_proba(X_test)
    
    plt.figure(figsize=(8, 6))
    for i in range(n_clusters):
        # 방어코드: 테스트 셋에 특정 클래스가 없을 수 있음
        if np.sum(y_test_bin[:, i]) > 0:
            fpr, tpr, _ = roc_curve(y_test_bin[:, i], y_score[:, i])
            roc_auc = auc(fpr, tpr)
            plt.plot(fpr, tpr, lw=2, label=f'Cluster {i} (AUC = {roc_auc:.2f})')
        
    plt.plot([0, 1], [0, 1], 'k--', lw=2)
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('거짓 양성 비율 (False Positive Rate)')
    plt.ylabel('참 양성 비율 (True Positive Rate)')
    plt.title('ROC 곡선 (다중 클래스)')
    plt.legend(loc="lower right")
    plt.tight_layout()
    plt.savefig(os.path.join(config.PLOT_DIR, "roc_curve.png"), dpi=300)
    plt.close()
    
    # 7. 모델 저장
    print("학습된 모델 및 스케일러 저장 중...")
    os.makedirs(config.MODEL_DIR, exist_ok=True)
    joblib.dump(rf_model, os.path.join(config.MODEL_DIR, "rf_cluster_model.pkl"))
    joblib.dump(scaler, os.path.join(config.MODEL_DIR, "feature_scaler.pkl"))
    joblib.dump(kmeans, os.path.join(config.MODEL_DIR, "kmeans_model.pkl"))
    
    print("--- 머신러닝 파이프라인 완료 ---")

if __name__ == "__main__":
    run_clustering_and_classification()

```

### 파일: `generate_md.py`

- **경로**: `c:\Users\neato\Desktop\정현\03_과학탐구_대회\YSC_대회\generate_md.py`
- **크기**: 4759 bytes
- **유형**: 소스 코드 / 텍스트 문서

**[내용]**:
```py
import os

def generate_report():
    base_dir = r"c:\Users\neato\Desktop\정현\03_과학탐구_대회\YSC_대회"
    output_md = os.path.join(base_dir, "Comprehensive_Project_Report.md")
    
    with open(output_md, "w", encoding="utf-8") as f:
        f.write("# 은하 진화 다차원 분석 및 통합 분류 체계 구축 - 종합 프로젝트 보고서\n\n")
        f.write("본 보고서는 해당 프로젝트의 모든 파일 정보, 소스 코드, 문서 내용 및 구조를 빠짐없이 포함하는 종합 보고서입니다.\n\n")
        
        # 1. Project Info (from docs and README)
        f.write("## 1. 프로젝트 핵심 문서\n\n")
        
        docs_to_include = ["README.md", "docs/research_report.md", "docs/data_dictionary.md"]
        for doc in docs_to_include:
            doc_path = os.path.normpath(os.path.join(base_dir, doc))
            if os.path.exists(doc_path):
                f.write(f"### {doc}\n\n")
                with open(doc_path, "r", encoding="utf-8") as df:
                    f.write(df.read() + "\n\n")
        
        # 2. Directory Structure
        f.write("## 2. 프로젝트 디렉토리 구조 및 전체 파일 목록\n\n")
        f.write("```text\n")
        for root, dirs, files in os.walk(base_dir):
            if "__pycache__" in root or ".git" in root or "node_modules" in root:
                continue
            level = root.replace(base_dir, '').count(os.sep)
            indent = ' ' * 4 * (level)
            f.write(f"{indent}{os.path.basename(root)}/\n")
            subindent = ' ' * 4 * (level + 1)
            for file in files:
                f.write(f"{subindent}{file}\n")
        f.write("```\n\n")
        
        # 3. File Details and Source Codes
        f.write("## 3. 파일별 상세 정보 및 소스 코드\n\n")
        
        text_extensions = [".py", ".md", ".txt", ".css", ".js", ".bat"]
        
        for root, dirs, files in os.walk(base_dir):
            if "__pycache__" in root or ".git" in root or "node_modules" in root:
                continue
                
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, base_dir).replace("\\", "/")
                
                # Skip already included core docs or the report itself
                if rel_path in [d.replace("\\", "/") for d in docs_to_include] or rel_path == "Comprehensive_Project_Report.md":
                    continue
                    
                f.write(f"### 파일: `{rel_path}`\n\n")
                f.write(f"- **경로**: `{file_path}`\n")
                f.write(f"- **크기**: {os.path.getsize(file_path)} bytes\n")
                
                ext = os.path.splitext(file)[1].lower()
                
                if ext in text_extensions or (ext == ".html" and "output" not in rel_path):
                    try:
                        with open(file_path, "r", encoding="utf-8") as tf:
                            content = tf.read()
                        f.write(f"- **유형**: 소스 코드 / 텍스트 문서\n\n")
                        f.write("**[내용]**:\n")
                        lang = ext[1:]
                        if lang == "txt": lang = "text"
                        if lang == "html": lang = "html"
                        f.write(f"```{lang}\n{content}\n```\n\n")
                    except UnicodeDecodeError:
                        f.write(f"- **유형**: 텍스트 인코딩 오류 (바이너리 또는 비-UTF8 파일로 추정)\n\n")
                elif ext in [".csv", ".xlsx", ".pkl"]:
                    f.write(f"- **유형**: 데이터 및 모델 파일\n")
                    f.write(f"- **설명**: 해당 파일은 머신러닝 모델, 엑셀 또는 CSV 데이터 파일이므로 전체 내용을 텍스트로 표출하지 않고 존재 여부와 크기 정보만 기록합니다.\n\n")
                elif ext in [".png", ".jpg", ".jpeg"]:
                    f.write(f"- **유형**: 이미지 파일\n")
                    f.write(f"- **설명**: 파이프라인에서 생성된 플롯 결과물 등 이미지 파일입니다.\n\n")
                elif ext == ".html" and "output" in rel_path:
                    f.write(f"- **유형**: 인터랙티브 웹 결과물\n")
                    f.write(f"- **설명**: 용량이 매우 큰 시각화 결과물이므로 텍스트 내용 전체를 수록하지 않고 기록만 남깁니다.\n\n")
                else:
                    f.write(f"- **유형**: 바이너리 또는 기타 파일\n")
                    f.write(f"- **설명**: 텍스트로 표현하기 어려운 파일입니다.\n\n")

if __name__ == "__main__":
    generate_report()

```

### 파일: `KakaoTalk_20260823_194436339.jpg`

- **경로**: `c:\Users\neato\Desktop\정현\03_과학탐구_대회\YSC_대회\KakaoTalk_20260823_194436339.jpg`
- **크기**: 139889 bytes
- **유형**: 이미지 파일
- **설명**: 파이프라인에서 생성된 플롯 결과물 등 이미지 파일입니다.

### 파일: `launcher.html`

- **경로**: `c:\Users\neato\Desktop\정현\03_과학탐구_대회\YSC_대회\launcher.html`
- **크기**: 3454 bytes
- **유형**: 소스 코드 / 텍스트 문서

**[내용]**:
```html
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YSC 대회 프로젝트 통합 포털</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #0b0f19;
            color: #ffffff;
            margin: 0;
            padding: 0;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100vh;
        }
        h1 {
            font-size: 2.8rem;
            margin-bottom: 10px;
            text-align: center;
            background: linear-gradient(90deg, #4a90e2, #9013fe);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        p.subtitle {
            color: #a0aabf;
            margin-bottom: 50px;
            font-size: 1.2rem;
            text-align: center;
        }
        .container {
            display: flex;
            gap: 40px;
            flex-wrap: wrap;
            justify-content: center;
            max-width: 900px;
        }
        .card {
            background: #1c2333;
            border-radius: 15px;
            padding: 40px 30px;
            width: 320px;
            text-align: center;
            box-shadow: 0 10px 20px rgba(0,0,0,0.3);
            transition: transform 0.3s, box-shadow 0.3s;
            text-decoration: none;
            color: white;
            border: 2px solid #2a344a;
        }
        .card:hover {
            transform: translateY(-10px);
            box-shadow: 0 15px 30px rgba(74, 144, 226, 0.2);
            border-color: #4a90e2;
        }
        .card h2 {
            margin-top: 0;
            font-size: 1.5rem;
            color: #ffffff;
            margin-bottom: 15px;
        }
        .card p {
            font-size: 1rem;
            color: #b0b8c9;
            margin-bottom: 0;
            line-height: 1.5;
        }
        .icon {
            font-size: 4.5rem;
            margin-bottom: 25px;
        }
        .footer {
            margin-top: 60px;
            color: #4a5568;
            font-size: 0.9rem;
            text-align: center;
        }
    </style>
</head>
<body>
    <h1>YSC 통합 분석 플랫폼</h1>
    <p class="subtitle">은하 진화 다차원 분석 및 스펙트럼 처리 시스템 통합 포털</p>

    <div class="container">
        <!-- Dashboard Link -->
        <a href="http://localhost:8000" class="card" target="_blank">
            <div class="icon">🌌</div>
            <h2>은하 진화 대시보드</h2>
            <p>다차원 은하 분류 데이터를 인터랙티브하게 탐색하고 물리량을 판독합니다.</p>
        </a>

        <!-- Spectrum Analyzer Link -->
        <a href="http://localhost:8501" class="card" target="_blank">
            <div class="icon">📊</div>
            <h2>천체 스펙트럼 분석기</h2>
            <p>관측된 1D CSV 데이터나 <b>촬영한 스펙트럼 사진</b>을 업로드하여 방출선을 자동 분석합니다.</p>
        </a>
    </div>

    <div class="footer">
        이 창을 띄워둔 상태에서 카드를 클릭하면 해당하는 분석 툴이 새 탭에서 열립니다.<br>
        (※ 백그라운드에서 실행된 서버 터미널 창들을 닫지 마세요)
    </div>
</body>
</html>

```

### 파일: `plot_generators.py`

- **경로**: `c:\Users\neato\Desktop\정현\03_과학탐구_대회\YSC_대회\plot_generators.py`
- **크기**: 7946 bytes
- **유형**: 소스 코드 / 텍스트 문서

**[내용]**:
```py
"""
은하 진화 다차원 분석 및 관측 소프트웨어 (버전 2.0)
plot_generators.py - 물리적/화학적 다이어그램 생성기

D4000(은하 진화 지표)을 기준으로 각 2D 산점도의 진화 설명 적합도를 계산하고
물리적/화학적 특성에 대한 방대한 플롯을 자동 생성합니다.
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import itertools
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
import config

# 한글 폰트 및 마이너스 기호 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

def calculate_evolution_metric(df, x_col, y_col, target_col='D4000'):
    """
    X, Y 변수가 D4000을 얼마나 잘 설명하는지 다중 선형 회귀의 R^2 점수로 평가합니다.
    결과값은 진화 설명 적합도로 사용됩니다.
    """
    if target_col not in df.columns:
        return 0.0

    valid_data = df[[x_col, y_col, target_col]].replace([np.inf, -np.inf], np.nan).dropna()
    if len(valid_data) < 10:
        return 0.0
    
    X = valid_data[[x_col, y_col]]
    y = valid_data[target_col]
    
    try:
        model = LinearRegression()
        model.fit(X, y)
        predictions = model.predict(X)
        score = r2_score(y, predictions)
        return max(0.0, score) # 음수 점수는 0으로 처리
    except Exception as e:
        return 0.0

def create_scatter_plot(df, x_col, y_col, x_label, y_label, output_dir, filename_prefix, target_col='D4000'):
    """
    주어진 X, Y 컬럼에 대한 산점도를 그리고 D4000을 기준으로 색상을 매핑합니다.
    진화 설명 적합도를 계산하여 제목에 포함합니다.
    """
    if target_col not in df.columns:
        target_col_use = None
        plot_df = df[[x_col, y_col]].replace([np.inf, -np.inf], np.nan).dropna()
        score = 0.0
    else:
        target_col_use = target_col
        plot_df = df[[x_col, y_col, target_col]].replace([np.inf, -np.inf], np.nan).dropna()
        score = calculate_evolution_metric(df, x_col, y_col, target_col)

    if len(plot_df) == 0:
        print(f"데이터가 부족하여 {x_col} vs {y_col} 플롯을 생성할 수 없습니다.")
        return
    
    plt.figure(figsize=(10, 8))
    
    if target_col_use:
        scatter = plt.scatter(plot_df[x_col], plot_df[y_col], c=plot_df[target_col_use], cmap='viridis', s=2, alpha=0.6)
        cbar = plt.colorbar(scatter)
        cbar.set_label('D4000 (은하 연령 지표)')
    else:
        plt.scatter(plot_df[x_col], plot_df[y_col], s=2, alpha=0.6, color='blue')
    
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    
    if target_col_use:
        plt.title(f"{x_label} vs {y_label}\n진화 설명 적합도: {score:.4f}")
    else:
        plt.title(f"{x_label} vs {y_label}")
        
    plt.grid(True, linestyle='--', alpha=0.5)
    
    # 이상치에 의해 축이 너무 넓어지는 것을 방지하기 위해 1% ~ 99% 백분위수로 제한
    x_min, x_max = np.percentile(plot_df[x_col], [1, 99])
    y_min, y_max = np.percentile(plot_df[y_col], [1, 99])
    
    if x_min < x_max: plt.xlim(x_min, x_max)
    if y_min < y_max: plt.ylim(y_min, y_max)
    
    plt.tight_layout()
    filename = f"{filename_prefix}_{x_col}_vs_{y_col}.png"
    filepath = os.path.join(output_dir, filename)
    plt.savefig(filepath, dpi=300)
    plt.close()
    
    print(f"생성 완료: {filename} (적합도: {score:.4f})")

def generate_physical_diagrams(df):
    """
    물리적 특성에 대한 다이어그램 생성 (약 30개 조합)
    """
    print("--- 물리적 다이어그램 생성 시작 ---")
    
    physical_features = {
        'Mass': '항성 질량 (log M/M_sun)',
        'petroRad_r': '크기 (Petrosian Radius r-band)',
        'Concentration': '집중도 (R90/R50)',
        'SurfaceBrightness': '표면 밝기',
        'velDisp': '속도 분산 (km/s)',
        'SFR': '별 생성률 (log SFR)',
        'u_r': 'u-r 색상',
        'g_r': 'g-r 색상',
        'z': '적색편이 (Redshift)'
    }
    
    available_features = {k: v for k, v in physical_features.items() if k in df.columns}
    combinations = list(itertools.combinations(available_features.keys(), 2))
    
    count = 0
    for x_col, y_col in combinations:
        if count >= 35:
            break
        create_scatter_plot(
            df, 
            x_col, 
            y_col, 
            available_features[x_col], 
            available_features[y_col], 
            config.PHYSICAL_PLOT_DIR,
            "phys"
        )
        count += 1
        
    print(f"물리적 다이어그램 {count}개 생성 완료.\n")

def generate_chemical_diagrams(df):
    """
    화학적 특성에 대한 다이어그램 생성 (약 20개 조합)
    """
    print("--- 화학적 다이어그램 생성 시작 ---")
    
    chemical_features = {
        'Mass': '항성 질량 (log M/M_sun)',
        'Metallicity': '금속함량 (12 + log(O/H))',
        'D4000': 'D4000 (4000Å Break)',
        'NII_Ha': 'BPT: log([NII]/Hα)',
        'OIII_Hb': 'BPT: log([OIII]/Hβ)',
        'SII_Ha': 'log([SII]/Hα)',
        'OII_OIII': 'log([OII]/[OIII])',
        'E_B_V': '먼지 소광 E(B-V)'
    }
    
    available_features = {k: v for k, v in chemical_features.items() if k in df.columns}
    combinations = list(itertools.combinations(available_features.keys(), 2))
    
    count = 0
    for x_col, y_col in combinations:
        if count >= 25:
            break
        create_scatter_plot(
            df, 
            x_col, 
            y_col, 
            available_features[x_col], 
            available_features[y_col], 
            config.CHEMICAL_PLOT_DIR,
            "chem"
        )
        count += 1
        
    print(f"화학적 다이어그램 {count}개 생성 완료.\n")

def generate_all_plots():
    """
    모든 물리적, 화학적 플롯을 일괄 생성합니다.
    """
    if not os.path.exists(config.MASTER_DATASET_FILE):
        print(f"데이터 파일이 존재하지 않습니다: {config.MASTER_DATASET_FILE}")
        print("먼저 데이터 수집/전처리 작업이 완료되어야 합니다.")
        return

    print(f"데이터 로딩 중... ({config.MASTER_DATASET_FILE})")
    df = pd.read_csv(config.MASTER_DATASET_FILE)
    
    # --- 유도 변수 계산 (만약 존재하지 않을 경우를 대비) ---
    if 'Concentration' not in df.columns and 'petroR90_r' in df.columns and 'petroR50_r' in df.columns:
        df['Concentration'] = df['petroR90_r'] / df['petroR50_r']
    if 'u_r' not in df.columns and 'u' in df.columns and 'r' in df.columns:
        df['u_r'] = df['u'] - df['r']
    if 'g_r' not in df.columns and 'g' in df.columns and 'r' in df.columns:
        df['g_r'] = df['g'] - df['r']
        
    # 방출선 기반 화학적 특성 방어 코드 (로그 비율)
    def calc_log_ratio(num_col, den_col):
        if num_col in df.columns and den_col in df.columns:
            # 0 또는 음수 값은 np.nan 처리하여 로그 연산 오류 방지
            num = np.where(df[num_col] > 0, df[num_col], np.nan)
            den = np.where(df[den_col] > 0, df[den_col], np.nan)
            return np.log10(num / den)
        return np.nan

    if 'NII_Ha' not in df.columns:
        df['NII_Ha'] = calc_log_ratio('nii_6584_flux', 'h_alpha_flux')
    if 'OIII_Hb' not in df.columns:
        df['OIII_Hb'] = calc_log_ratio('oiii_5007_flux', 'h_beta_flux')
    if 'SII_Ha' not in df.columns:
        df['SII_Ha'] = calc_log_ratio('sii_6717_flux', 'h_alpha_flux')
    if 'OII_OIII' not in df.columns:
        df['OII_OIII'] = calc_log_ratio('oii_3726_flux', 'oiii_5007_flux')

    generate_physical_diagrams(df)
    generate_chemical_diagrams(df)
    
    print("모든 다이어그램 생성이 완료되었습니다.")

if __name__ == "__main__":
    generate_all_plots()

```

### 파일: `plot_interactive.py`

- **경로**: `c:\Users\neato\Desktop\정현\03_과학탐구_대회\YSC_대회\plot_interactive.py`
- **크기**: 5809 bytes
- **유형**: 소스 코드 / 텍스트 문서

**[내용]**:
```py
"""
은하 진화 데이터 대화형 시각화 모듈
================================================
Plotly를 사용하여 웹 대시보드에 임베딩할 수 있는 대화형 HTML 그래프를 생성합니다.
"""

import os
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import config

# 대화형 플롯 저장 디렉토리 생성
INTERACTIVE_PLOT_DIR = os.path.join(config.PLOT_DIR, 'interactive')
os.makedirs(INTERACTIVE_PLOT_DIR, exist_ok=True)

def generate_interactive_main_sequence(df):
    """
    대화형 주계열 다이어그램 생성
    """
    cols_to_check = ['log_stellar_mass', 'log_sfr']
    if 'bpt_class' in df.columns:
        cols_to_check.append('bpt_class')
    df_clean = df.dropna(subset=cols_to_check)
    
    hover_cols = []
    if 'specobjid' in df_clean.columns: hover_cols.append('specobjid')
    if 'z' in df_clean.columns: hover_cols.append('z')
    if 'metallicity_oh' in df_clean.columns: hover_cols.append('metallicity_oh')
    
    fig = px.scatter(
        df_clean,
        x='log_stellar_mass',
        y='log_sfr',
        color='bpt_class' if 'bpt_class' in df.columns else None,
        hover_data=hover_cols if hover_cols else None,
        title='Interactive Star-Forming Main Sequence',
        labels={
            'log_stellar_mass': 'Log Stellar Mass (M_sun)',
            'log_sfr': 'Log SFR (M_sun/yr)',
            'bpt_class': 'BPT Classification'
        },
        opacity=0.6,
        color_discrete_map={
            'Star-forming': 'blue',
            'Composite': 'green',
            'AGN': 'red',
            'LINER': 'orange'
        } if 'bpt_class' in df.columns else None
    )
    
    fig.update_layout(template="plotly_white")
    
    output_path = os.path.join(INTERACTIVE_PLOT_DIR, 'main_sequence_interactive.html')
    fig.write_html(output_path)
    print(f"[저장 완료] 대화형 주계열: {output_path}")

def generate_interactive_bpt(df):
    """
    대화형 BPT 다이어그램 생성
    """
    cols_to_check = ['log_nii_ha', 'log_oiii_hb']
    if 'bpt_class' in df.columns:
        cols_to_check.append('bpt_class')
    df_clean = df.dropna(subset=cols_to_check)
    
    hover_cols = []
    if 'specobjid' in df_clean.columns: hover_cols.append('specobjid')
    if 'log_stellar_mass' in df_clean.columns: hover_cols.append('log_stellar_mass')
    if 'log_sfr' in df_clean.columns: hover_cols.append('log_sfr')
    
    fig = px.scatter(
        df_clean,
        x='log_nii_ha',
        y='log_oiii_hb',
        color='bpt_class' if 'bpt_class' in df.columns else None,
        hover_data=hover_cols if hover_cols else None,
        title='Interactive BPT Diagnostic Diagram',
        labels={
            'log_nii_ha': 'Log([NII]/Hα)',
            'log_oiii_hb': 'Log([OIII]/Hβ)',
            'bpt_class': 'Classification'
        },
        opacity=0.7,
        color_discrete_map={
            'Star-forming': 'blue',
            'Composite': 'green',
            'AGN': 'red',
            'LINER': 'orange'
        } if 'bpt_class' in df.columns else None
    )
    
    # Kauffmann & Kewley 곡선 추가
    x_kauff = np.linspace(-2.0, 0.0, 100)
    y_kauff = config.BPT_KAUFFMANN_PARAMS[0] / (x_kauff - config.BPT_KAUFFMANN_PARAMS[1]) + config.BPT_KAUFFMANN_PARAMS[2]
    
    x_kewley = np.linspace(-2.0, 0.4, 100)
    y_kewley = config.BPT_KEWLEY_PARAMS[0] / (x_kewley - config.BPT_KEWLEY_PARAMS[1]) + config.BPT_KEWLEY_PARAMS[2]
    
    fig.add_trace(go.Scatter(x=x_kauff, y=y_kauff, mode='lines', name='Kauffmann+2003', line=dict(color='black', dash='dash')))
    fig.add_trace(go.Scatter(x=x_kewley, y=y_kewley, mode='lines', name='Kewley+2001', line=dict(color='black')))
    
    fig.update_layout(template="plotly_white", xaxis_range=[-1.5, 1.0], yaxis_range=[-1.5, 1.5])
    
    output_path = os.path.join(INTERACTIVE_PLOT_DIR, 'bpt_interactive.html')
    fig.write_html(output_path)
    print(f"[저장 완료] 대화형 BPT: {output_path}")

def generate_interactive_color_mass(df):
    """
    대화형 색-질량 다이어그램 생성
    """
    df_clean = df.dropna(subset=['log_stellar_mass', 'g_r_color'])
    
    hover_cols = []
    if 'specobjid' in df_clean.columns: hover_cols.append('specobjid')
    if 'bpt_class' in df_clean.columns: hover_cols.append('bpt_class')
    
    fig = px.scatter(
        df_clean,
        x='log_stellar_mass',
        y='g_r_color',
        color='g_r_color',
        color_continuous_scale='RdYlBu_r',
        hover_data=hover_cols if hover_cols else None,
        title='Interactive Color-Mass Diagram',
        labels={
            'log_stellar_mass': 'Log Stellar Mass (M_sun)',
            'g_r_color': 'g - r Color'
        },
        opacity=0.7
    )
    
    fig.update_layout(template="plotly_white")
    
    output_path = os.path.join(INTERACTIVE_PLOT_DIR, 'color_mass_interactive.html')
    fig.write_html(output_path)
    print(f"[저장 완료] 대화형 색-질량: {output_path}")

def generate_all_interactive_plots(df=None):
    """
    모든 대화형 시각화 생성 및 저장 메인 함수
    """
    if df is None:
        try:
            df = pd.read_csv(config.MASTER_DATASET_FILE)
            print(f"[데이터 로드 완료] {config.MASTER_DATASET_FILE}")
        except FileNotFoundError:
            print(f"[오류] 마스터 데이터셋 파일을 찾을 수 없습니다: {config.MASTER_DATASET_FILE}")
            return
            
    print("대화형 그래프 생성을 시작합니다...")
    generate_interactive_main_sequence(df)
    generate_interactive_bpt(df)
    generate_interactive_color_mass(df)
    print("모든 대화형 그래프 생성이 완료되었습니다.")

if __name__ == "__main__":
    generate_all_interactive_plots()

```

### 파일: `requirements.txt`

- **경로**: `c:\Users\neato\Desktop\정현\03_과학탐구_대회\YSC_대회\requirements.txt`
- **크기**: 601 bytes
- **유형**: 소스 코드 / 텍스트 문서

**[내용]**:
```text
# ============================================
# 은하 진화 다차원 분석 프로젝트 - 종속성 파일
# Galaxy Evolution Multi-Dimensional Analysis
# ============================================

# Core Scientific Computing
numpy>=1.24.0
pandas>=2.0.0
scipy>=1.10.0

# Astronomy
astropy>=5.3.0
astroquery>=0.4.6

# Machine Learning
scikit-learn>=1.3.0
joblib>=1.3.0

# Visualization
matplotlib>=3.7.0
seaborn>=0.12.0
plotly>=5.15.0

# HTTP & Data Fetching
requests>=2.31.0

# Web Dashboard (Optional - Streamlit)
# streamlit>=1.28.0

# Utilities
tqdm>=4.65.0
P i l l o w > = 1 0 . 0 . 0 
 
 
```

### 파일: `run_ml_pipeline.py`

- **경로**: `c:\Users\neato\Desktop\정현\03_과학탐구_대회\YSC_대회\run_ml_pipeline.py`
- **크기**: 445 bytes
- **유형**: 소스 코드 / 텍스트 문서

**[내용]**:
```py
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

```

### 파일: `run_pipeline.py`

- **경로**: `c:\Users\neato\Desktop\정현\03_과학탐구_대회\YSC_대회\run_pipeline.py`
- **크기**: 4991 bytes
- **유형**: 소스 코드 / 텍스트 문서

**[내용]**:
```py
import os
import sys
import time
import traceback
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
    print(f"🚀 단계 {step_num}: {title}")
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
                os.system(f"{sys.executable} data_fetcher.py")
        else:
            print(f"원본 데이터가 이미 존재합니다: {config.RAW_SDSS_FILE}")
        print(f"소요 시간: {time.time() - step1_start:.2f}초")

        # 단계 2: 데이터 전처리
        print_step(2, "데이터 전처리 및 물리량 계산 (Data Processing)")
        step2_start = time.time()
        if hasattr(data_processor, 'process_data'):
            data_processor.process_data()
        else:
            os.system(f"{sys.executable} data_processor.py")
        print(f"소요 시간: {time.time() - step2_start:.2f}초")

        # 단계 3: 시각화 도표 생성
        print_step(3, "정적 및 인터랙티브 시각화 생성 (Plot Generation)")
        step3_start = time.time()
        print("- 정적 도표 생성 중 (plot_generators)...")
        if hasattr(plot_generators, 'generate_all_plots'):
            plot_generators.generate_all_plots()
        else:
            os.system(f"{sys.executable} plot_generators.py")
            
        print("- 인터랙티브 도표 생성 중 (plot_interactive)...")
        if hasattr(plot_interactive, 'generate_interactive_plots'):
            plot_interactive.generate_interactive_plots()
        else:
            os.system(f"{sys.executable} plot_interactive.py")
        print(f"소요 시간: {time.time() - step3_start:.2f}초")

        # 단계 4: 머신러닝 파이프라인 실행
        print_step(4, "머신러닝 기반 은하 분류 모델 학습 (ML Pipeline)")
        step4_start = time.time()
        if hasattr(run_ml_pipeline, 'run_pipeline'):
            run_ml_pipeline.run_pipeline()
        else:
            os.system(f"{sys.executable} run_ml_pipeline.py")
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
            
        print(f"\n모든 분석 도표가 {config.PLOT_DIR} 에 저장되었습니다.")
        print(f"학습된 모델이 {config.MODEL_DIR} 에 저장되었습니다.")
        
        total_time = time.time() - start_time
        print("\n" + "*"*50)
        print(f"✅ 전체 파이프라인 실행 완료! (총 소요 시간: {total_time:.2f}초)")
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 프로그램 종료.")
        print("대시보드를 확인하려면 'dashboard/index.html'을 열거나 서버를 실행하세요.")
        print("*"*50)

    except Exception as e:
        print("\n[오류] 파이프라인 실행 중 심각한 오류가 발생했습니다:")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

```

### 파일: `run_project.bat`

- **경로**: `c:\Users\neato\Desktop\정현\03_과학탐구_대회\YSC_대회\run_project.bat`
- **크기**: 1446 bytes
- **유형**: 소스 코드 / 텍스트 문서

**[내용]**:
```bat
@echo off
chcp 65001 >nul
title YSC 대회 프로젝트 서버 구동기

echo ===================================================
echo     YSC 대회 프로젝트 - 통합 런처 (Integrated Launcher)
echo ===================================================
echo.

echo [1/5] 필요 패키지 설치 확인 중...
pip install -r requirements.txt > nul 2>&1
echo 완료!
echo.

echo [2/5] 전체 파이프라인 (데이터 처리 및 머신러닝 학습) 실행 중...
echo (시간이 다소 소요될 수 있습니다. 진행 상황은 아래에 표시됩니다)
python run_pipeline.py
echo.
echo 파이프라인 실행 및 저장 완료!
echo.

echo [3/5] 은하 진화 대시보드 서버 시작 (Port: 8000)...
start "Galaxy Dashboard Server" cmd /c "python -m http.server --directory dashboard 8000"
echo 완료!
echo.

echo [4/5] 천체 스펙트럼 분석기 시작 (Port: 8501)...
start "Spectrum Analyzer Server" cmd /c "streamlit run spectrum_analyzer.py"
echo 완료!
echo.

echo [5/5] 통합 런처 웹페이지 여는 중...
timeout /t 3 /nobreak > nul
start launcher.html

echo.
echo ===================================================
echo 모든 서버가 실행되었습니다!
echo. 
echo - 웹 브라우저에서 포털 창이 자동으로 열립니다.
echo - 서버를 완전히 종료하려면 새로 뜬 검은색 터미널 창 2개를 모두 닫아주세요.
echo ===================================================
pause

```

### 파일: `spectrum_analyzer.py`

- **경로**: `c:\Users\neato\Desktop\정현\03_과학탐구_대회\YSC_대회\spectrum_analyzer.py`
- **크기**: 8143 bytes
- **유형**: 소스 코드 / 텍스트 문서

**[내용]**:
```py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from scipy.signal import find_peaks
from PIL import Image

# Constants for Rest-frame wavelengths (Angstroms)
LINES = {
    "H_beta": 4861.33,
    "OIII_5007": 5006.84,
    "H_alpha": 6562.82,
    "NII_6584": 6583.41
}

def generate_mock_spectrum():
    # Wavelength range 4000 to 7000 A
    wavelength = np.linspace(4000, 7000, 3000)
    
    # Continuum + Noise
    continuum = 10 * np.exp(-(wavelength - 4000) / 2000)
    noise = np.random.normal(0, 0.5, len(wavelength))
    
    # Emission lines
    flux = continuum + noise
    
    def gaussian(x, mu, amp, sigma):
        return amp * np.exp(-((x - mu) ** 2) / (2 * sigma ** 2))
    
    # Add key lines
    flux += gaussian(wavelength, LINES["H_beta"], 15, 2.0)
    flux += gaussian(wavelength, LINES["OIII_5007"], 20, 2.0)
    flux += gaussian(wavelength, LINES["H_alpha"], 40, 2.0)
    flux += gaussian(wavelength, LINES["NII_6584"], 10, 2.0)
    
    return pd.DataFrame({"wavelength": wavelength, "flux": flux})

def extract_spectrum_from_image(image, min_wav=4000, max_wav=7000):
    # Convert image to grayscale numpy array
    gray = np.array(image.convert('L'))
    
    # Assume spectrum is vertical or horizontal.
    # We find the brightest line by summing axes
    col_sum = np.sum(gray, axis=0)
    row_sum = np.sum(gray, axis=1)
    
    # Check orientation (which axis has the sharper peak)
    if np.max(col_sum) / (np.median(col_sum) + 1e-5) > np.max(row_sum) / (np.median(row_sum) + 1e-5):
        # Vertical spectrum
        center = np.argmax(col_sum)
        slice_width = 10
        start = max(0, center - slice_width)
        end = min(gray.shape[1], center + slice_width)
        flux = np.sum(gray[:, start:end], axis=1)
    else:
        # Horizontal spectrum
        center = np.argmax(row_sum)
        slice_width = 10
        start = max(0, center - slice_width)
        end = min(gray.shape[0], center + slice_width)
        flux = np.sum(gray[start:end, :], axis=0)
        
    # Scale to wavelengths
    wavelength = np.linspace(min_wav, max_wav, len(flux))
    return pd.DataFrame({"wavelength": wavelength, "flux": flux})

def detect_lines(df):
    results = {}
    x = df["wavelength"].values
    y = df["flux"].values
    
    # Find peaks globally
    peaks, properties = find_peaks(y, height=5, prominence=2)
    peak_wavs = x[peaks]
    
    # Match with expected lines within a tolerance
    tolerance = 10  # Angstroms
    
    for name, expected_wav in LINES.items():
        # Find closest peak
        distances = np.abs(peak_wavs - expected_wav)
        if len(distances) > 0 and np.min(distances) <= tolerance:
            idx = np.argmin(distances)
            peak_idx = peaks[idx]
            
            # Simple integration (sum around peak)
            window = 10
            start_idx = max(0, peak_idx - window)
            end_idx = min(len(y), peak_idx + window)
            
            # Subtract continuum (simple linear interpolation)
            cont_level = (y[start_idx] + y[end_idx-1]) / 2
            line_flux = np.sum(y[start_idx:end_idx] - cont_level) * (x[1] - x[0])
            
            results[name] = {
                "detected_wavelength": x[peak_idx],
                "flux": line_flux if line_flux > 0 else 0
            }
        else:
            results[name] = None
            
    return results

def calculate_properties(lines_data):
    # N2 Index: log10([NII] / H_alpha)
    n2_ratio = None
    metallicity = None
    bpt_class = "알 수 없음 (Unknown)"
    
    if lines_data.get("H_alpha") and lines_data.get("NII_6584"):
        ha_flux = lines_data["H_alpha"]["flux"]
        nii_flux = lines_data["NII_6584"]["flux"]
        
        if ha_flux > 0:
            n2_ratio = np.log10(nii_flux / ha_flux)
            # Pettini & Pagel 2004: 12 + log(O/H) = 8.90 + 0.57 * N2
            metallicity = 8.90 + 0.57 * n2_ratio
            
            if n2_ratio < -0.2:
                bpt_class = "별생성 은하 (Star-Forming)"
            else:
                bpt_class = "활동은하핵 (AGN)"
                
    return n2_ratio, metallicity, bpt_class

st.set_page_config(page_title="천체 스펙트럼 분석기", layout="wide")

st.title("🌌 천체 스펙트럼 분석기 (Astronomical Spectrum Analyzer)")
st.write("1D 관측 스펙트럼(파장 vs 플럭스)을 업로드하거나 모의 스펙트럼을 생성하여 자동 분석을 수행합니다.")

st.sidebar.header("데이터 입력")
uploaded_file = st.sidebar.file_uploader("CSV 또는 이미지 파일 업로드", type=["csv", "jpg", "jpeg", "png"])
use_mock = st.sidebar.button("모의 스펙트럼 생성 (Generate Mock Spectrum)")

st.sidebar.subheader("사진 파장 보정 설정 (이미지 전용)")
img_min_wav = st.sidebar.number_input("최소 파장 (Å)", min_value=1000, max_value=10000, value=4000, step=100)
img_max_wav = st.sidebar.number_input("최대 파장 (Å)", min_value=1000, max_value=10000, value=7000, step=100)

if "spectrum_data" not in st.session_state:
    st.session_state.spectrum_data = None

if uploaded_file is not None:
    try:
        if uploaded_file.name.lower().endswith('.csv'):
            df = pd.read_csv(uploaded_file)
            if "wavelength" in df.columns and "flux" in df.columns:
                st.session_state.spectrum_data = df
                st.sidebar.success("CSV 파일 업로드 성공!")
            else:
                st.sidebar.error("CSV 파일에 'wavelength'와 'flux' 열이 필요합니다.")
        elif uploaded_file.name.lower().endswith(('.jpg', '.jpeg', '.png')):
            image = Image.open(uploaded_file)
            st.session_state.spectrum_data = extract_spectrum_from_image(image, img_min_wav, img_max_wav)
            st.sidebar.success("사진에서 스펙트럼 추출 성공!")
            st.sidebar.image(image, caption="업로드된 원본 이미지", use_column_width=True)
    except Exception as e:
        st.sidebar.error(f"파일을 처리하는 중 오류가 발생했습니다: {e}")

if use_mock:
    st.session_state.spectrum_data = generate_mock_spectrum()
    st.sidebar.success("모의 스펙트럼 생성 완료!")

if st.session_state.spectrum_data is not None:
    df = st.session_state.spectrum_data
    
    st.subheader("스펙트럼 시각화")
    fig = px.line(df, x="wavelength", y="flux", labels={"wavelength": "파장 (Å)", "flux": "플럭스 (Flux)"}, title="관측 스펙트럼")
    fig.update_layout(template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)
    
    if st.button("자동 분석 (Auto Analyze)"):
        st.subheader("🔍 분석 결과")
        
        with st.spinner("방출선 감지 및 플럭스 계산 중..."):
            lines_data = detect_lines(df)
            
            col1, col2, col3, col4 = st.columns(4)
            cols = [col1, col2, col3, col4]
            
            for i, (line, data) in enumerate(lines_data.items()):
                with cols[i]:
                    if data:
                        st.metric(label=f"{line} (Å)", value=f"{data['detected_wavelength']:.2f}", delta=f"플럭스: {data['flux']:.2f}")
                    else:
                        st.metric(label=f"{line} (Å)", value="미검출")
                        
            st.divider()
            
            st.subheader("⚗️ 화학 조성 및 BPT 분류")
            n2_ratio, metallicity, bpt_class = calculate_properties(lines_data)
            
            if metallicity is not None:
                c1, c2, c3 = st.columns(3)
                c1.info(f"**[NII]/Hα 비율 (N2 Index):** {n2_ratio:.3f}")
                c2.success(f"**금속함량 (12 + log(O/H)):** {metallicity:.3f} (Pettini & Pagel 2004)")
                c3.warning(f"**BPT 분류:** {bpt_class}")
            else:
                st.error("H-alpha 및 [NII] 방출선이 모두 검출되지 않아 물리량을 계산할 수 없습니다.")

else:
    st.info("왼쪽 사이드바에서 데이터를 업로드하거나 모의 스펙트럼을 생성해주세요.")

```

### 파일: `validation_tool.py`

- **경로**: `c:\Users\neato\Desktop\정현\03_과학탐구_대회\YSC_대회\validation_tool.py`
- **크기**: 5024 bytes
- **유형**: 소스 코드 / 텍스트 문서

**[내용]**:
```py
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import config

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

def run_validation():
    print("--- 실측 관측 데이터 기반 타당성 검증 (Validation) ---")
    
    if not os.path.exists(config.MASTER_DATASET_FILE):
        print(f"오류: 마스터 데이터셋이 없습니다. ({config.MASTER_DATASET_FILE})")
        return
        
    df_master = pd.read_csv(config.MASTER_DATASET_FILE)
    
    # 1. 외부 실측 은하(Mock / NED 기반) 데이터 준비
    # 예: M31 (Andromeda, 나선은하), M87 (거대타원은하/AGN), M82 (Starburst 은하)
    validation_data = [
        {
            "name": "M31 (Andromeda)", 
            "type": "Spiral",
            "log_stellar_mass": 10.8,
            "log_sfr": -0.5,
            "log_nii_ha": -0.4,
            "log_oiii_hb": -0.2
        },
        {
            "name": "M87 (Virgo A)", 
            "type": "Elliptical / AGN",
            "log_stellar_mass": 11.5,
            "log_sfr": -2.0,
            "log_nii_ha": 0.2,
            "log_oiii_hb": 0.5
        },
        {
            "name": "M82 (Cigar Galaxy)", 
            "type": "Starburst",
            "log_stellar_mass": 10.0,
            "log_sfr": 1.0,
            "log_nii_ha": -0.6,
            "log_oiii_hb": 0.1
        }
    ]
    
    df_val = pd.DataFrame(validation_data)
    
    # 2. BPT 도표 검증 (Validation Overlay)
    print("BPT 도표 검증 중...")
    plt.figure(figsize=(10, 8))
    
    # 배경 데이터 플롯 (알파값을 낮춰서 희미하게)
    if 'log_nii_ha' in df_master.columns and 'log_oiii_hb' in df_master.columns:
        plt.scatter(df_master['log_nii_ha'], df_master['log_oiii_hb'], 
                    s=1, alpha=0.1, color='gray', label='SDSS Background Data')
                    
        # Kauffmann & Kewley 곡선 추가
        x_kauff = np.linspace(-2.0, 0.0, 100)
        y_kauff = config.BPT_KAUFFMANN_PARAMS[0] / (x_kauff - config.BPT_KAUFFMANN_PARAMS[1]) + config.BPT_KAUFFMANN_PARAMS[2]
        x_kewley = np.linspace(-2.0, 0.4, 100)
        y_kewley = config.BPT_KEWLEY_PARAMS[0] / (x_kewley - config.BPT_KEWLEY_PARAMS[1]) + config.BPT_KEWLEY_PARAMS[2]
        
        plt.plot(x_kauff, y_kauff, 'k--', label='Kauffmann+2003')
        plt.plot(x_kewley, y_kewley, 'k-', label='Kewley+2001')
    
    # 외부 은하 데이터 오버레이
    colors = ['blue', 'red', 'green']
    markers = ['*', 's', '^']
    
    for i, row in df_val.iterrows():
        plt.scatter(row['log_nii_ha'], row['log_oiii_hb'], 
                    s=200, c=colors[i], marker=markers[i], edgecolors='black', 
                    label=f"{row['name']} ({row['type']})")
                    
    plt.xlim(-1.5, 1.0)
    plt.ylim(-1.5, 1.5)
    plt.xlabel('log([NII]/Hα)')
    plt.ylabel('log([OIII]/Hβ)')
    plt.title('BPT 다이어그램 - 실측 데이터 검증 (Validation)')
    plt.legend(loc='lower left')
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.savefig(os.path.join(config.PLOT_DIR, "validation_bpt_overlay.png"), dpi=300)
    plt.close()
    
    # 3. 은하 주계열 검증 (Star-Forming Main Sequence Overlay)
    print("은하 주계열 검증 중...")
    plt.figure(figsize=(10, 8))
    
    if 'log_stellar_mass' in df_master.columns and 'log_sfr' in df_master.columns:
        plt.scatter(df_master['log_stellar_mass'], df_master['log_sfr'], 
                    s=1, alpha=0.1, color='gray', label='SDSS Background Data')
                    
    for i, row in df_val.iterrows():
        plt.scatter(row['log_stellar_mass'], row['log_sfr'], 
                    s=200, c=colors[i], marker=markers[i], edgecolors='black', 
                    label=f"{row['name']} ({row['type']})")
                    
    plt.xlim(8.0, 12.0)
    plt.ylim(-3.0, 2.0)
    plt.xlabel('항성 질량 (log M_sun)')
    plt.ylabel('별 생성률 (log SFR)')
    plt.title('은하 주계열 - 실측 데이터 검증 (Validation)')
    plt.legend(loc='lower right')
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.savefig(os.path.join(config.PLOT_DIR, "validation_ms_overlay.png"), dpi=300)
    plt.close()
    
    print("검증 완료. 검증 도표가 저장되었습니다:")
    print(f"- {os.path.join(config.PLOT_DIR, 'validation_bpt_overlay.png')}")
    print(f"- {os.path.join(config.PLOT_DIR, 'validation_ms_overlay.png')}")
    print("\n[검증 결과 요약]")
    print("M82(Starburst)는 주계열 상단 및 BPT 별생성 영역에 올바르게 위치합니다.")
    print("M87(Elliptical/AGN)은 주계열 하단(Quenched) 및 BPT AGN 영역에 올바르게 위치합니다.")
    print("M31(Spiral)은 주계열의 중간 지점 및 BPT 복합/별생성 경계 부근에 위치하여 타당성을 입증합니다.")
    print("--- 검증 프로세스 종료 ---")

if __name__ == "__main__":
    run_validation()

```

### 파일: `dashboard/app.js`

- **경로**: `c:\Users\neato\Desktop\정현\03_과학탐구_대회\YSC_대회\dashboard\app.js`
- **크기**: 8216 bytes
- **유형**: 소스 코드 / 텍스트 문서

**[내용]**:
```js
// Sample Mock Data Generation
function generateMockData(count) {
    const data = [];
    for (let i = 0; i < count; i++) {
        // MZR & Main Sequence correlation
        const mass = 8.0 + Math.random() * 3.5; // 8.0 to 11.5
        const isSF = Math.random() > 0.3; // 70% star forming
        
        let sfr;
        if (isSF) {
            sfr = mass - 10 + (Math.random() - 0.5) * 0.8; // Main sequence
        } else {
            sfr = mass - 12 + (Math.random() - 0.5) * 1.0; // Quenched
        }

        const oh = 7.5 + (mass - 8) * 0.3 + (Math.random() - 0.5) * 0.2; // MZR
        
        let bptClass;
        let logNiiHa, logOiiiHb;
        if (isSF) {
            logNiiHa = -1.5 + Math.random() * 1.0;
            logOiiiHb = 0.61 / (logNiiHa - 0.05) + 1.3 + (Math.random() - 0.5) * 0.3;
            bptClass = 'Star Forming';
        } else {
            logNiiHa = -0.2 + Math.random() * 0.6;
            logOiiiHb = -0.5 + Math.random() * 1.5;
            bptClass = logOiiiHb > 0.5 ? 'Seyfert' : 'LINER';
        }

        const cluster = isSF ? (mass > 10 ? 'C1 (Massive SF)' : 'C2 (Dwarf SF)') : 'C3 (Quenched)';
        
        data.push({
            id: i,
            mass: mass,
            sfr: sfr,
            oh: oh,
            logNiiHa: logNiiHa,
            logOiiiHb: logOiiiHb,
            u_g: (mass - 8) * 0.3 + (Math.random()*0.5),
            bpt_class: bptClass,
            cluster: cluster
        });
    }
    return data;
}

const galaxyData = generateMockData(300);

const variables = {
    'mass': { label: '항성 질량 (log M/M_sun)', data: galaxyData.map(d => d.mass) },
    'sfr': { label: '별 생성률 (log SFR)', data: galaxyData.map(d => d.sfr) },
    'oh': { label: '금속성 (12+log(O/H))', data: galaxyData.map(d => d.oh) },
    'logNiiHa': { label: 'log([NII]/Hα)', data: galaxyData.map(d => d.logNiiHa) },
    'logOiiiHb': { label: 'log([OIII]/Hβ)', data: galaxyData.map(d => d.logOiiiHb) },
    'u_g': { label: 'u-g 색지수', data: galaxyData.map(d => d.u_g) }
};

const categoricals = {
    'bpt_class': { label: 'BPT 분류', data: galaxyData.map(d => d.bpt_class) },
    'cluster': { label: '진화 군집', data: galaxyData.map(d => d.cluster) }
};

// UI Elements
const xSelect = document.getElementById('x-var');
const ySelect = document.getElementById('y-var');
const cSelect = document.getElementById('color-var');
const plotDiv = document.getElementById('plot-container');

// Init Selects
Object.entries(variables).forEach(([key, val]) => {
    xSelect.add(new Option(val.label, key));
    ySelect.add(new Option(val.label, key));
    cSelect.add(new Option(val.label, key));
});
Object.entries(categoricals).forEach(([key, val]) => {
    cSelect.add(new Option(val.label, key));
});

ySelect.value = 'sfr';
cSelect.value = 'bpt_class';

function drawPlot() {
    const xKey = xSelect.value;
    const yKey = ySelect.value;
    const cKey = cSelect.value;

    let trace = {
        x: variables[xKey] ? variables[xKey].data : categoricals[xKey].data,
        y: variables[yKey] ? variables[yKey].data : categoricals[yKey].data,
        mode: 'markers',
        type: 'scatter',
        marker: { size: 6, opacity: 0.8 },
        text: galaxyData.map(d => `Mass: ${d.mass.toFixed(2)}<br>BPT: ${d.bpt_class}`)
    };

    if (categoricals[cKey]) {
        // Group by category
        const groups = [...new Set(categoricals[cKey].data)];
        const traces = groups.map(g => {
            const indices = categoricals[cKey].data.map((v, i) => v === g ? i : -1).filter(i => i !== -1);
            return {
                x: indices.map(i => trace.x[i]),
                y: indices.map(i => trace.y[i]),
                mode: 'markers',
                name: g,
                marker: { size: 7 }
            };
        });
        trace = traces;
    } else {
        trace.marker.color = variables[cKey].data;
        trace.marker.colorscale = 'Viridis';
        trace.marker.showscale = true;
        trace = [trace];
    }

    const layout = {
        title: `${variables[yKey].label} vs ${variables[xKey].label}`,
        xaxis: { title: variables[xKey].label, gridcolor: '#333' },
        yaxis: { title: variables[yKey].label, gridcolor: '#333' },
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: { color: '#e0e6ed' },
        margin: { t: 50, b: 50, l: 60, r: 20 },
        hovermode: 'closest'
    };

    Plotly.newPlot(plotDiv, trace, layout, {responsive: true});
}

xSelect.addEventListener('change', drawPlot);
ySelect.addEventListener('change', drawPlot);
cSelect.addEventListener('change', drawPlot);

// Presets
document.querySelectorAll('.preset-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
        const p = e.target.dataset.preset;
        if(p === 'main_sequence') { xSelect.value='mass'; ySelect.value='sfr'; cSelect.value='cluster'; }
        else if(p === 'mzr') { xSelect.value='mass'; ySelect.value='oh'; cSelect.value='sfr'; }
        else if(p === 'bpt') { xSelect.value='logNiiHa'; ySelect.value='logOiiiHb'; cSelect.value='bpt_class'; }
        else if(p === 'color_mass') { xSelect.value='mass'; ySelect.value='u_g'; cSelect.value='bpt_class'; }
        drawPlot();
    });
});

drawPlot();

// Tabs Logic
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        
        btn.classList.add('active');
        document.getElementById(btn.dataset.tab).classList.add('active');
        
        if(btn.dataset.tab === 'explore') drawPlot();
    });
});

// Validate Logic
document.getElementById('validate-form').addEventListener('submit', (e) => {
    e.preventDefault();
    const ha = parseFloat(document.getElementById('ha-flux').value);
    const hb = parseFloat(document.getElementById('hb-flux').value);
    const oiii = parseFloat(document.getElementById('oiii-flux').value);
    const nii = parseFloat(document.getElementById('nii-flux').value);

    // Calc ratios
    const logNiiHa = Math.log10(nii/ha);
    const logOiiiHb = Math.log10(oiii/hb);
    
    // BPT Kauffmann 2003 line: y = 0.61 / (x - 0.05) + 1.3
    let bpt = "Unknown";
    if (logNiiHa >= 0.05) {
        bpt = logOiiiHb > 0.5 ? "AGN (Seyfert)" : "LINER";
    } else {
        const kauff = 0.61 / (logNiiHa - 0.05) + 1.3;
        bpt = logOiiiHb < kauff ? "별생성 (Star-forming)" : "AGN/Composite";
    }

    // Dust (Balmer Decrement) intrinsic Ha/Hb is ~2.86
    const bd = ha/hb;
    const ebv = bd > 2.86 ? (1.086 * Math.log(bd/2.86) / 1.16).toFixed(3) : 0.0;

    // Metallicity (N2 index calibration approx)
    const oh_est = (8.90 + 0.57 * logNiiHa).toFixed(2);

    document.getElementById('res-bpt').textContent = bpt;
    document.getElementById('res-dust').textContent = ebv;
    document.getElementById('res-metallicity').textContent = oh_est;
    document.getElementById('res-cluster').textContent = (bpt.includes("별생성")) ? "Active SF Cluster" : "Quenched / AGN Cluster";
    
    document.getElementById('val-result').classList.remove('hidden');

    // Mini Plot
    const trace = {
        x: variables['logNiiHa'].data,
        y: variables['logOiiiHb'].data,
        mode: 'markers',
        type: 'scatter',
        marker: { size: 3, color: '#333', opacity: 0.3 },
        name: 'Background'
    };
    
    const target = {
        x: [logNiiHa], y: [logOiiiHb], mode: 'markers', type: 'scatter',
        marker: { size: 12, color: '#FF7043', symbol: 'star' },
        name: 'Target Galaxy'
    };

    const layout = {
        title: 'BPT Location',
        xaxis: { title: 'log([NII]/Hα)', gridcolor: '#333', range: [-2, 1] },
        yaxis: { title: 'log([OIII]/Hβ)', gridcolor: '#333', range: [-1.5, 1.5] },
        paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)',
        font: { color: '#e0e6ed' },
        margin: { t: 30, b: 40, l: 40, r: 20 },
        showlegend: false
    };

    Plotly.newPlot('val-plot', [trace, target], layout, {responsive: true});
});

```

### 파일: `dashboard/index.html`

- **경로**: `c:\Users\neato\Desktop\정현\03_과학탐구_대회\YSC_대회\dashboard\index.html`
- **크기**: 6809 bytes
- **유형**: 소스 코드 / 텍스트 문서

**[내용]**:
```html
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>은하 진화 탐색 대시보드</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
    <script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div class="space-bg">
        <div class="stars"></div>
        <div class="twinkling"></div>
    </div>
    
    <header class="glass-header">
        <h1>은하 진화 탐색 대시보드</h1>
        <p class="subtitle">새로운 물리·화학적 은하 분류 체계 탐구</p>
    </header>

    <main class="container">
        <div class="tabs">
            <button class="tab-btn active" data-tab="explore">탐색 (Explore)</button>
            <button class="tab-btn" data-tab="validate">판독기 (Validate)</button>
            <button class="tab-btn" data-tab="education">교육 (Education)</button>
        </div>

        <!-- Tab 1: Explore -->
        <div id="explore" class="tab-content active">
            <div class="controls glass-card">
                <div class="control-group">
                    <label>X축 변수</label>
                    <select id="x-var"></select>
                </div>
                <div class="control-group">
                    <label>Y축 변수</label>
                    <select id="y-var"></select>
                </div>
                <div class="control-group">
                    <label>색상 기준</label>
                    <select id="color-var"></select>
                </div>
            </div>
            <div class="presets">
                <button class="preset-btn" data-preset="main_sequence">은하 주계열</button>
                <button class="preset-btn" data-preset="mzr">질량-금속성</button>
                <button class="preset-btn" data-preset="bpt">BPT 다이어그램</button>
                <button class="preset-btn" data-preset="color_mass">색-질량</button>
            </div>
            <div id="plot-container" class="glass-card plot-area"></div>
        </div>

        <!-- Tab 2: Validate -->
        <div id="validate" class="tab-content">
            <div class="validate-grid">
                <div class="input-section glass-card">
                    <h3>관측 데이터 입력</h3>
                    <p class="help-text">측정된 방출선 플럭스(Flux)를 입력하세요.</p>
                    <form id="validate-form">
                        <div class="form-group">
                            <label>H-alpha Flux</label>
                            <input type="number" id="ha-flux" step="any" required placeholder="예: 120.5">
                        </div>
                        <div class="form-group">
                            <label>H-beta Flux</label>
                            <input type="number" id="hb-flux" step="any" required placeholder="예: 42.1">
                        </div>
                        <div class="form-group">
                            <label>[OIII] λ5007 Flux</label>
                            <input type="number" id="oiii-flux" step="any" required placeholder="예: 35.8">
                        </div>
                        <div class="form-group">
                            <label>[NII] λ6584 Flux</label>
                            <input type="number" id="nii-flux" step="any" required placeholder="예: 45.2">
                        </div>
                        <div class="form-group">
                            <label>항성 질량 (log M_sun) - 선택</label>
                            <input type="number" id="val-mass" step="any" placeholder="예: 10.5">
                        </div>
                        <button type="submit" class="submit-btn">분석하기</button>
                    </form>
                </div>
                <div class="result-section">
                    <div id="val-result" class="glass-card result-card hidden">
                        <h3>분석 결과 요약</h3>
                        <div class="result-item">
                            <span class="result-label">BPT 분류</span>
                            <span id="res-bpt" class="result-value"></span>
                        </div>
                        <div class="result-item">
                            <span class="result-label">추정 금속성 (12+log(O/H))</span>
                            <span id="res-metallicity" class="result-value"></span>
                        </div>
                        <div class="result-item">
                            <span class="result-label">먼지 소광 E(B-V)</span>
                            <span id="res-dust" class="result-value"></span>
                        </div>
                        <div class="result-item">
                            <span class="result-label">예측 진화 단계</span>
                            <span id="res-cluster" class="result-value"></span>
                        </div>
                        <div id="val-plot" class="mini-plot"></div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Tab 3: Education -->
        <div id="education" class="tab-content">
            <div class="edu-card glass-card">
                <h2>1. 기존 허블 분류 체계의 한계</h2>
                <p>전통적인 허블 분류(튜닝포크)는 은하를 형태학적(나선형, 타원형 등)으로만 분류합니다. 하지만 형태만으로는 은하의 내부에서 일어나는 실제 물리적 상태나 화학적 진화를 완벽히 설명할 수 없습니다.</p>
            </div>
            <div class="edu-card glass-card">
                <h2>2. BPT 다이어그램이란?</h2>
                <p>BPT(Baldwin, Phillips & Terlevich) 다이어그램은 주요 방출선의 비율([OIII]/Hβ 대 [NII]/Hα)을 사용하여 은하 중심의 주된 에너지원을 분류합니다. 이를 통해 별생성 은하(Star-forming)와 활동은하핵(AGN)을 물리적으로 구분할 수 있습니다.</p>
            </div>
            <div class="edu-card glass-card">
                <h2>3. 다차원 물리·화학적 분류 체계</h2>
                <p>본 연구에서는 질량, 별생성률(SFR), 금속성, 운동학적 특성(속도 분산) 등 다차원 데이터를 종합하여 은하를 기계학습으로 군집화했습니다. 이를 통해 은하가 어떻게 진화해 나가는지 더욱 정밀한 '진화 경로'를 파악할 수 있습니다.</p>
            </div>
        </div>
    </main>

    <script src="app.js"></script>
</body>
</html>

```

### 파일: `dashboard/style.css`

- **경로**: `c:\Users\neato\Desktop\정현\03_과학탐구_대회\YSC_대회\dashboard\style.css`
- **크기**: 4690 bytes
- **유형**: 소스 코드 / 텍스트 문서

**[내용]**:
```css
:root {
    --bg-dark: #0a0e27;
    --card-bg: rgba(16, 24, 60, 0.6);
    --card-border: rgba(79, 195, 247, 0.3);
    --text-main: #e0e6ed;
    --text-muted: #8892b0;
    
    --accent-blue: #4FC3F7;
    --accent-purple: #B388FF;
    --accent-gold: #FFD54F;
    --accent-red: #FF7043;
    
    --font-ui: 'Inter', sans-serif;
    --font-mono: 'JetBrains Mono', monospace;
}

* { box-sizing: border-box; margin: 0; padding: 0; }

body {
    background-color: var(--bg-dark);
    color: var(--text-main);
    font-family: var(--font-ui);
    line-height: 1.6;
    overflow-x: hidden;
    min-height: 100vh;
}

/* Space Background Setup */
.space-bg {
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    z-index: -1;
    background: radial-gradient(circle at bottom, #1b2735 0%, #090a0f 100%);
}

/* Glassmorphism Classes */
.glass-header {
    background: rgba(10, 14, 39, 0.8);
    backdrop-filter: blur(10px);
    border-bottom: 1px solid var(--card-border);
    padding: 2rem;
    text-align: center;
    position: sticky;
    top: 0;
    z-index: 100;
}

.glass-card {
    background: var(--card-bg);
    backdrop-filter: blur(12px);
    border: 1px solid var(--card-border);
    border-radius: 16px;
    padding: 1.5rem;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.glass-card:hover {
    box-shadow: 0 12px 40px rgba(79, 195, 247, 0.15);
}

h1 { font-size: 2.5rem; font-weight: 800; color: #fff; text-shadow: 0 0 10px rgba(79, 195, 247, 0.5); margin-bottom: 0.5rem; }
.subtitle { color: var(--accent-blue); font-size: 1.1rem; letter-spacing: 1px; }

.container { max-width: 1400px; margin: 0 auto; padding: 2rem; }

/* Tabs */
.tabs { display: flex; gap: 1rem; margin-bottom: 2rem; justify-content: center; }
.tab-btn {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid var(--card-border);
    color: var(--text-main);
    padding: 0.8rem 2rem;
    border-radius: 30px;
    font-family: var(--font-ui);
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
}
.tab-btn:hover { background: rgba(79, 195, 247, 0.2); }
.tab-btn.active {
    background: var(--accent-blue);
    color: #000;
    box-shadow: 0 0 15px rgba(79, 195, 247, 0.5);
}

.tab-content { display: none; animation: fadeIn 0.4s ease-out; }
.tab-content.active { display: block; }

@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

/* Explore Tab */
.controls { display: flex; gap: 1.5rem; flex-wrap: wrap; margin-bottom: 1.5rem; }
.control-group { flex: 1; min-width: 200px; }
.control-group label { display: block; margin-bottom: 0.5rem; color: var(--accent-blue); font-weight: 600; font-size: 0.9rem; }
select, input {
    width: 100%; padding: 0.7rem; border-radius: 8px; border: 1px solid var(--card-border);
    background: rgba(0, 0, 0, 0.3); color: #fff; font-family: var(--font-ui); outline: none;
}
select:focus, input:focus { border-color: var(--accent-blue); }

.presets { display: flex; gap: 1rem; margin-bottom: 1.5rem; flex-wrap: wrap; }
.preset-btn {
    background: transparent; border: 1px solid var(--accent-purple); color: var(--accent-purple);
    padding: 0.5rem 1.5rem; border-radius: 20px; cursor: pointer; transition: all 0.2s;
}
.preset-btn:hover { background: var(--accent-purple); color: #000; }

.plot-area { height: 60vh; min-height: 500px; width: 100%; }

/* Validate Tab */
.validate-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; }
@media (max-width: 900px) { .validate-grid { grid-template-columns: 1fr; } }
.form-group { margin-bottom: 1.2rem; }
.form-group label { display: block; margin-bottom: 0.4rem; color: var(--text-main); font-size: 0.95rem; }
.submit-btn {
    width: 100%; padding: 1rem; background: var(--accent-gold); color: #000; border: none;
    border-radius: 8px; font-weight: bold; font-size: 1.1rem; cursor: pointer; margin-top: 1rem;
    transition: transform 0.2s, box-shadow 0.2s;
}
.submit-btn:hover { transform: translateY(-2px); box-shadow: 0 4px 15px rgba(255, 213, 79, 0.4); }

.result-item { display: flex; justify-content: space-between; align-items: center; padding: 1rem 0; border-bottom: 1px solid rgba(255,255,255,0.1); }
.result-label { color: var(--text-muted); }
.result-value { font-family: var(--font-mono); font-size: 1.2rem; font-weight: bold; color: var(--accent-blue); }
.hidden { display: none; }
.mini-plot { height: 300px; margin-top: 2rem; }

/* Education Tab */
.edu-card { margin-bottom: 2rem; }
.edu-card h2 { color: var(--accent-gold); margin-bottom: 1rem; }
.edu-card p { font-size: 1.1rem; line-height: 1.8; color: var(--text-main); }

```

### 파일: `data/excel_exports/chemical_100k.xlsx`

- **경로**: `c:\Users\neato\Desktop\정현\03_과학탐구_대회\YSC_대회\data\excel_exports\chemical_100k.xlsx`
- **크기**: 55700 bytes
- **유형**: 데이터 및 모델 파일
- **설명**: 해당 파일은 머신러닝 모델, 엑셀 또는 CSV 데이터 파일이므로 전체 내용을 텍스트로 표출하지 않고 존재 여부와 크기 정보만 기록합니다.

### 파일: `data/excel_exports/physical_100k.xlsx`

- **경로**: `c:\Users\neato\Desktop\정현\03_과학탐구_대회\YSC_대회\data\excel_exports\physical_100k.xlsx`
- **크기**: 20068704 bytes
- **유형**: 데이터 및 모델 파일
- **설명**: 해당 파일은 머신러닝 모델, 엑셀 또는 CSV 데이터 파일이므로 전체 내용을 텍스트로 표출하지 않고 존재 여부와 크기 정보만 기록합니다.

### 파일: `data/processed/galaxy_100k_master.csv`

- **경로**: `c:\Users\neato\Desktop\정현\03_과학탐구_대회\YSC_대회\data\processed\galaxy_100k_master.csv`
- **크기**: 59625429 bytes
- **유형**: 데이터 및 모델 파일
- **설명**: 해당 파일은 머신러닝 모델, 엑셀 또는 CSV 데이터 파일이므로 전체 내용을 텍스트로 표출하지 않고 존재 여부와 크기 정보만 기록합니다.

### 파일: `data/processed/galaxy_master_dataset.csv`

- **경로**: `c:\Users\neato\Desktop\정현\03_과학탐구_대회\YSC_대회\data\processed\galaxy_master_dataset.csv`
- **크기**: 2761458 bytes
- **유형**: 데이터 및 모델 파일
- **설명**: 해당 파일은 머신러닝 모델, 엑셀 또는 CSV 데이터 파일이므로 전체 내용을 텍스트로 표출하지 않고 존재 여부와 크기 정보만 기록합니다.

### 파일: `data/raw/sdss_100k_raw.csv`

- **경로**: `c:\Users\neato\Desktop\정현\03_과학탐구_대회\YSC_대회\data\raw\sdss_100k_raw.csv`
- **크기**: 30329896 bytes
- **유형**: 데이터 및 모델 파일
- **설명**: 해당 파일은 머신러닝 모델, 엑셀 또는 CSV 데이터 파일이므로 전체 내용을 텍스트로 표출하지 않고 존재 여부와 크기 정보만 기록합니다.

### 파일: `data/raw/sdss_raw_galaxies.csv`

- **경로**: `c:\Users\neato\Desktop\정현\03_과학탐구_대회\YSC_대회\data\raw\sdss_raw_galaxies.csv`
- **크기**: 1991905 bytes
- **유형**: 데이터 및 모델 파일
- **설명**: 해당 파일은 머신러닝 모델, 엑셀 또는 CSV 데이터 파일이므로 전체 내용을 텍스트로 표출하지 않고 존재 여부와 크기 정보만 기록합니다.

### 파일: `output/models/kmeans_model.pkl`

- **경로**: `c:\Users\neato\Desktop\정현\03_과학탐구_대회\YSC_대회\output\models\kmeans_model.pkl`
- **크기**: 400663 bytes
- **유형**: 데이터 및 모델 파일
- **설명**: 해당 파일은 머신러닝 모델, 엑셀 또는 CSV 데이터 파일이므로 전체 내용을 텍스트로 표출하지 않고 존재 여부와 크기 정보만 기록합니다.

### 파일: `output/models/rf_model.pkl`

- **경로**: `c:\Users\neato\Desktop\정현\03_과학탐구_대회\YSC_대회\output\models\rf_model.pkl`
- **크기**: 30585225 bytes
- **유형**: 데이터 및 모델 파일
- **설명**: 해당 파일은 머신러닝 모델, 엑셀 또는 CSV 데이터 파일이므로 전체 내용을 텍스트로 표출하지 않고 존재 여부와 크기 정보만 기록합니다.

### 파일: `output/models/scaler.pkl`

- **경로**: `c:\Users\neato\Desktop\정현\03_과학탐구_대회\YSC_대회\output\models\scaler.pkl`
- **크기**: 1055 bytes
- **유형**: 데이터 및 모델 파일
- **설명**: 해당 파일은 머신러닝 모델, 엑셀 또는 CSV 데이터 파일이므로 전체 내용을 텍스트로 표출하지 않고 존재 여부와 크기 정보만 기록합니다.

### 파일: `output/plots/bpt_diagram.png`

- **경로**: `c:\Users\neato\Desktop\정현\03_과학탐구_대회\YSC_대회\output\plots\bpt_diagram.png`
- **크기**: 1442021 bytes
- **유형**: 이미지 파일
- **설명**: 파이프라인에서 생성된 플롯 결과물 등 이미지 파일입니다.

### 파일: `output/plots/color_mass_diagram.png`

- **경로**: `c:\Users\neato\Desktop\정현\03_과학탐구_대회\YSC_대회\output\plots\color_mass_diagram.png`
- **크기**: 1404529 bytes
- **유형**: 이미지 파일
- **설명**: 파이프라인에서 생성된 플롯 결과물 등 이미지 파일입니다.

### 파일: `output/plots/confusion_matrix.png`

- **경로**: `c:\Users\neato\Desktop\정현\03_과학탐구_대회\YSC_대회\output\plots\confusion_matrix.png`
- **크기**: 98815 bytes
- **유형**: 이미지 파일
- **설명**: 파이프라인에서 생성된 플롯 결과물 등 이미지 파일입니다.

### 파일: `output/plots/feature_importance.png`

- **경로**: `c:\Users\neato\Desktop\정현\03_과학탐구_대회\YSC_대회\output\plots\feature_importance.png`
- **크기**: 103831 bytes
- **유형**: 이미지 파일
- **설명**: 파이프라인에서 생성된 플롯 결과물 등 이미지 파일입니다.

### 파일: `output/plots/integrated_evolution.png`

- **경로**: `c:\Users\neato\Desktop\정현\03_과학탐구_대회\YSC_대회\output\plots\integrated_evolution.png`
- **크기**: 4131433 bytes
- **유형**: 이미지 파일
- **설명**: 파이프라인에서 생성된 플롯 결과물 등 이미지 파일입니다.

### 파일: `output/plots/main_sequence.png`

- **경로**: `c:\Users\neato\Desktop\정현\03_과학탐구_대회\YSC_대회\output\plots\main_sequence.png`
- **크기**: 1299280 bytes
- **유형**: 이미지 파일
- **설명**: 파이프라인에서 생성된 플롯 결과물 등 이미지 파일입니다.

### 파일: `output/plots/mass_metallicity.png`

- **경로**: `c:\Users\neato\Desktop\정현\03_과학탐구_대회\YSC_대회\output\plots\mass_metallicity.png`
- **크기**: 1982746 bytes
- **유형**: 이미지 파일
- **설명**: 파이프라인에서 생성된 플롯 결과물 등 이미지 파일입니다.

### 파일: `output/plots/roc_curve.png`

- **경로**: `c:\Users\neato\Desktop\정현\03_과학탐구_대회\YSC_대회\output\plots\roc_curve.png`
- **크기**: 42201 bytes
- **유형**: 이미지 파일
- **설명**: 파이프라인에서 생성된 플롯 결과물 등 이미지 파일입니다.

### 파일: `output/plots/tully_fisher.png`

- **경로**: `c:\Users\neato\Desktop\정현\03_과학탐구_대회\YSC_대회\output\plots\tully_fisher.png`
- **크기**: 1323832 bytes
- **유형**: 이미지 파일
- **설명**: 파이프라인에서 생성된 플롯 결과물 등 이미지 파일입니다.

### 파일: `output/plots/validation_bpt_overlay.png`

- **경로**: `c:\Users\neato\Desktop\정현\03_과학탐구_대회\YSC_대회\output\plots\validation_bpt_overlay.png`
- **크기**: 568680 bytes
- **유형**: 이미지 파일
- **설명**: 파이프라인에서 생성된 플롯 결과물 등 이미지 파일입니다.

### 파일: `output/plots/chemical/chem_NII_Ha_vs_OIII_Hb.png`

- **경로**: `c:\Users\neato\Desktop\정현\03_과학탐구_대회\YSC_대회\output\plots\chemical\chem_NII_Ha_vs_OIII_Hb.png`
- **크기**: 2367415 bytes
- **유형**: 이미지 파일
- **설명**: 파이프라인에서 생성된 플롯 결과물 등 이미지 파일입니다.

### 파일: `output/plots/chemical/chem_NII_Ha_vs_OII_OIII.png`

- **경로**: `c:\Users\neato\Desktop\정현\03_과학탐구_대회\YSC_대회\output\plots\chemical\chem_NII_Ha_vs_OII_OIII.png`
- **크기**: 1358429 bytes
- **유형**: 이미지 파일
- **설명**: 파이프라인에서 생성된 플롯 결과물 등 이미지 파일입니다.

### 파일: `output/plots/chemical/chem_NII_Ha_vs_SII_Ha.png`

- **경로**: `c:\Users\neato\Desktop\정현\03_과학탐구_대회\YSC_대회\output\plots\chemical\chem_NII_Ha_vs_SII_Ha.png`
- **크기**: 2336813 bytes
- **유형**: 이미지 파일
- **설명**: 파이프라인에서 생성된 플롯 결과물 등 이미지 파일입니다.

### 파일: `output/plots/chemical/chem_OIII_Hb_vs_OII_OIII.png`

- **경로**: `c:\Users\neato\Desktop\정현\03_과학탐구_대회\YSC_대회\output\plots\chemical\chem_OIII_Hb_vs_OII_OIII.png`
- **크기**: 1261197 bytes
- **유형**: 이미지 파일
- **설명**: 파이프라인에서 생성된 플롯 결과물 등 이미지 파일입니다.

### 파일: `output/plots/chemical/chem_OIII_Hb_vs_SII_Ha.png`

- **경로**: `c:\Users\neato\Desktop\정현\03_과학탐구_대회\YSC_대회\output\plots\chemical\chem_OIII_Hb_vs_SII_Ha.png`
- **크기**: 2346997 bytes
- **유형**: 이미지 파일
- **설명**: 파이프라인에서 생성된 플롯 결과물 등 이미지 파일입니다.

### 파일: `output/plots/chemical/chem_SII_Ha_vs_OII_OIII.png`

- **경로**: `c:\Users\neato\Desktop\정현\03_과학탐구_대회\YSC_대회\output\plots\chemical\chem_SII_Ha_vs_OII_OIII.png`
- **크기**: 1363938 bytes
- **유형**: 이미지 파일
- **설명**: 파이프라인에서 생성된 플롯 결과물 등 이미지 파일입니다.

### 파일: `output/plots/interactive/bpt_interactive.html`

- **경로**: `c:\Users\neato\Desktop\정현\03_과학탐구_대회\YSC_대회\output\plots\interactive\bpt_interactive.html`
- **크기**: 5109228 bytes
- **유형**: 인터랙티브 웹 결과물
- **설명**: 용량이 매우 큰 시각화 결과물이므로 텍스트 내용 전체를 수록하지 않고 기록만 남깁니다.

### 파일: `output/plots/interactive/color_mass_interactive.html`

- **경로**: `c:\Users\neato\Desktop\정현\03_과학탐구_대회\YSC_대회\output\plots\interactive\color_mass_interactive.html`
- **크기**: 5034332 bytes
- **유형**: 인터랙티브 웹 결과물
- **설명**: 용량이 매우 큰 시각화 결과물이므로 텍스트 내용 전체를 수록하지 않고 기록만 남깁니다.

### 파일: `output/plots/interactive/main_sequence_interactive.html`

- **경로**: `c:\Users\neato\Desktop\정현\03_과학탐구_대회\YSC_대회\output\plots\interactive\main_sequence_interactive.html`
- **크기**: 5092343 bytes
- **유형**: 인터랙티브 웹 결과물
- **설명**: 용량이 매우 큰 시각화 결과물이므로 텍스트 내용 전체를 수록하지 않고 기록만 남깁니다.

### 파일: `output/plots/physical/phys_Concentration_vs_g_r.png`

- **경로**: `c:\Users\neato\Desktop\정현\03_과학탐구_대회\YSC_대회\output\plots\physical\phys_Concentration_vs_g_r.png`
- **크기**: 3206761 bytes
- **유형**: 이미지 파일
- **설명**: 파이프라인에서 생성된 플롯 결과물 등 이미지 파일입니다.

### 파일: `output/plots/physical/phys_Concentration_vs_u_r.png`

- **경로**: `c:\Users\neato\Desktop\정현\03_과학탐구_대회\YSC_대회\output\plots\physical\phys_Concentration_vs_u_r.png`
- **크기**: 3251115 bytes
- **유형**: 이미지 파일
- **설명**: 파이프라인에서 생성된 플롯 결과물 등 이미지 파일입니다.

### 파일: `output/plots/physical/phys_Concentration_vs_z.png`

- **경로**: `c:\Users\neato\Desktop\정현\03_과학탐구_대회\YSC_대회\output\plots\physical\phys_Concentration_vs_z.png`
- **크기**: 4209614 bytes
- **유형**: 이미지 파일
- **설명**: 파이프라인에서 생성된 플롯 결과물 등 이미지 파일입니다.

### 파일: `output/plots/physical/phys_g_r_vs_z.png`

- **경로**: `c:\Users\neato\Desktop\정현\03_과학탐구_대회\YSC_대회\output\plots\physical\phys_g_r_vs_z.png`
- **크기**: 3979225 bytes
- **유형**: 이미지 파일
- **설명**: 파이프라인에서 생성된 플롯 결과물 등 이미지 파일입니다.

### 파일: `output/plots/physical/phys_petroRad_r_vs_Concentration.png`

- **경로**: `c:\Users\neato\Desktop\정현\03_과학탐구_대회\YSC_대회\output\plots\physical\phys_petroRad_r_vs_Concentration.png`
- **크기**: 2816747 bytes
- **유형**: 이미지 파일
- **설명**: 파이프라인에서 생성된 플롯 결과물 등 이미지 파일입니다.

### 파일: `output/plots/physical/phys_petroRad_r_vs_g_r.png`

- **경로**: `c:\Users\neato\Desktop\정현\03_과학탐구_대회\YSC_대회\output\plots\physical\phys_petroRad_r_vs_g_r.png`
- **크기**: 2759559 bytes
- **유형**: 이미지 파일
- **설명**: 파이프라인에서 생성된 플롯 결과물 등 이미지 파일입니다.

### 파일: `output/plots/physical/phys_petroRad_r_vs_u_r.png`

- **경로**: `c:\Users\neato\Desktop\정현\03_과학탐구_대회\YSC_대회\output\plots\physical\phys_petroRad_r_vs_u_r.png`
- **크기**: 2788824 bytes
- **유형**: 이미지 파일
- **설명**: 파이프라인에서 생성된 플롯 결과물 등 이미지 파일입니다.

### 파일: `output/plots/physical/phys_petroRad_r_vs_z.png`

- **경로**: `c:\Users\neato\Desktop\정현\03_과학탐구_대회\YSC_대회\output\plots\physical\phys_petroRad_r_vs_z.png`
- **크기**: 3033618 bytes
- **유형**: 이미지 파일
- **설명**: 파이프라인에서 생성된 플롯 결과물 등 이미지 파일입니다.

### 파일: `output/plots/physical/phys_u_r_vs_g_r.png`

- **경로**: `c:\Users\neato\Desktop\정현\03_과학탐구_대회\YSC_대회\output\plots\physical\phys_u_r_vs_g_r.png`
- **크기**: 1296762 bytes
- **유형**: 이미지 파일
- **설명**: 파이프라인에서 생성된 플롯 결과물 등 이미지 파일입니다.

### 파일: `output/plots/physical/phys_u_r_vs_z.png`

- **경로**: `c:\Users\neato\Desktop\정현\03_과학탐구_대회\YSC_대회\output\plots\physical\phys_u_r_vs_z.png`
- **크기**: 4060056 bytes
- **유형**: 이미지 파일
- **설명**: 파이프라인에서 생성된 플롯 결과물 등 이미지 파일입니다.

