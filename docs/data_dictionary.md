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
