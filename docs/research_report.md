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
