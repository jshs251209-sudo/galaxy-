# 은하 물리량 및 화학적 조성 상관관계 통계 분석 가이드
(Galaxy Physical Properties & Chemical Abundance Correlation Analysis Guide)

본 문서는 은하 관측 자료(SDSS, NED 등)를 활용하여 은하의 물리적 특성(항성질량, 별 생성률, 광도, 회전속도)과 화학적 조성(기체상 금속함량 12+log(O/H)) 사이의 통계적 상관관계를 분석하고 은하 진화 경향을 도출하기 위한 전체 가이드입니다.

---

## 1. 연구 방법 및 통계학적 이론

### 1.1 각 분석의 천문학적 필요성
1. **항성질량($M_*$) - 별 생성률($\mathrm{SFR}$) 관계 (은하 주계열, SFMS)**
   - 나선은하와 같은 별 생성 은하들은 질량이 클수록 별 형성 활동도 활발한 뚜렷한 주계열($\log \mathrm{SFR} \propto 0.7 \times \log M_*$)을 형성합니다 (Noeske et al. 2007).
   - 이 관계는 은하가 지속적인 가스 공급을 통해 안정적으로 성장하는지, 아니면 가스 고갈이나 AGN 피드백 등으로 인해 별 생성이 멈추는 퀜칭(Quenching) 단계에 들어섰는지를 판단하는 핵심 기준선입니다.
2. **항성질량($M_*$) - 금속함량($12+\log(\mathrm{O/H})$) 관계 (질량-금속함량 관계, MZR)**
   - 은하의 질량이 증가할수록 성간물질의 산소 존재비(금속함량)가 증가하는 비선형적 상관성을 가집니다 (Tremonti et al. 2004).
   - 질량이 큰 은하는 중력 퍼텐셜 우물이 깊어 초신성 폭발 등에 의해 뿜어져 나오는 중원소 가스 유출(Outflow)을 억제하고 성간물질 내에 보존·재활용(Chemical Enrichment)할 수 있기 때문입니다.
3. **별 생성률($\mathrm{SFR}$) - 금속함량($12+\log(\mathrm{O/H})$) 관계 (기본 금속함량 관계, FMR)**
   - 동일 질량에서 SFR이 매우 높은 은하는 오히려 금속함량이 낮게 관측되는 경향(Anti-correlation)이 있습니다 (Mannucci et al. 2010).
   - 이는 외부 은하간 공간(IGM)에서 유입되는 저금속 원시 가스가 성간물질의 금속을 희석(Dilution)시키면서 동시에 폭발적인 별 생성을 유발하기 때문입니다.

### 1.2 Pearson과 Spearman 상관계수 병행 활용 이유
- **Pearson 상관계수 ($r$)**: 두 변수 간의 **선형적 비례 관계**를 측정합니다. 정규분포를 가정하며 극단적인 이상치에 취약합니다.
- **Spearman 순위 상관계수 ($\rho$)**: 두 변수 간의 **단조 증가/감소 관계**를 순위 기반으로 측정합니다. 비모수 검정으로 이상치에 강건하며, MZR 곡선과 같이 고질량에서 포화되는 비선형적 관계도 정확히 평가합니다.
- **해석**: $|\rho| > |r|$인 경우, 두 변수가 단순 직선이 아닌 멱법칙 또는 로그 곡선 형태의 비선형 상관성을 띠고 있음을 증명합니다.

### 1.3 $p$-value의 올바른 해석과 표본 크기의 함정
- **귀무가설 ($H_0$)**: 두 변수 간의 상관계수는 0이다 (아무런 관계가 없다).
- **$p < 0.001$**: 귀무가설을 기각하며, 통계적으로 극히 유의미함을 의미합니다.
- **주의점 (Large-$N$ Fallacy)**: 표본 수가 수만 개로 커지면, 물리적 상관성($r$)이 0.05로 매우 약하더라도 수학적으로 $p < 10^{-10}$이 나옵니다. 따라서 $p$-value만으로 결론을 내리지 않고 반드시 효과 크기인 $r$, $\rho$, 그리고 결정계수 $R^2$를 함께 해석해야 합니다.

### 1.4 표본 크기(Sample Size) 검증의 의의
- 소규모 표본($N=100$)에서는 표본오차와 이상치로 인해 상관계수가 크게 요동칩니다.
- $N=100 \rightarrow 300 \rightarrow 500 \rightarrow 1,000$으로 표본을 확장하며 반복 복원/비복원 추출(Bootstrapping)을 수행할 때, 상관계수와 오차막대가 참값으로 수렴(대수의 법칙)하는 안정성을 검증합니다. 이를 통해 연구의 최소 유효 표본 크기를 확정합니다.

### 1.5 상관관계와 인과관계의 구분
- 높은 상관계수가 직접적인 원인-결과를 보장하지는 않습니다.
- 은하 진화에서 항성질량, 별 생성률, 금속함량은 공통의 숨은 원인인 **"암흑물질 헤일로 질량($M_{halo}$)"**과 유입/유출 가스 순환 메커니즘에 의해 복합적으로 지배됩니다.

---

## 2. 데이터 형식 및 컬럼 매핑

프로그램(`galaxy_correlation_analyzer.py`)은 아래와 같은 열 이름을 자동으로 감지하여 표준화합니다:

| 물리량 | 표준 컬럼명 | 대체 가능 컬럼명 (자동 감지) | 단위 | 스케일 변환 규칙 |
| :--- | :--- | :--- | :--- | :--- |
| **항성질량 ($M_*$)** | `stellar_mass` | `lgm_tot_p50`, `mstar`, `mass`, `log_mass` | $M_\odot$ 또는 $\log_{10}(M_\odot)$ | 중앙값 > 50이면 선형 척도로 판단하여 $\log_{10}$ 자동 변환 |
| **별 생성률 (SFR)** | `sfr` | `sfr_tot_p50`, `star_formation_rate`, `log_sfr` | $M_\odot/\mathrm{yr}$ 또는 $\log_{10}$ | 양수 선형이면 $\log_{10}(\mathrm{SFR})$ 자동 변환 |
| **금속함량** | `metallicity` | `oh_p50`, `12+log(o/h)`, `12_log_oh`, `z_gas` | $12+\log(\mathrm{O/H})$ | 유효 관측 범위($6.5 \sim 9.8$) 자동 필터링 |
| **은하 유형** | `galaxy_type` | `bptclass`, `class_activity`, `type`, `morphology` | 범주형 | 하위 집단별 상관계수 비교 분석 활성화 |
| **회전속도** | `rotation_velocity` | `v_rot`, `vrot`, `veldisp` | $\mathrm{km/s}$ | 역학적 질량 평가용 |
| **광도** | `luminosity` | `log_luminosity_r`, `lum_r`, `abs_mag_r` | $\log_{10}(L_\odot)$ | 광도-질량 상관분석용 |

---

## 3. 프로그램 실행 방법

### 로컬 환경에서 실행
```bash
python galaxy_correlation_analyzer.py
```
- 프로젝트 루트에 `galaxy_master_complete_all.csv`가 존재하면 실제 5만 개 관측 데이터를 즉시 분석합니다.
- 파일이 없을 경우 1,200개의 가상 은하 관측 데이터를 자동 생성하여 검증을 수행합니다.

### Google Colab에서 실행
- 프로젝트 루트에 생성된 `Galaxy_Correlation_Analysis_Colab.ipynb` 파일을 Google Drive에 업로드하거나,
- 새 Colab 노트북에 `galaxy_correlation_analyzer.py`의 전체 코드를 붙여넣어 실행합니다.

---

## 4. 자동 생성되는 결과물 목록 (`galaxy_analysis_output/`)

1. `scatter_mass_vs_sfr.png`: 은하 주계열(SFMS) 고해상도 산점도 및 선형 회귀선 (300 DPI)
2. `scatter_mass_vs_metallicity.png`: 질량-금속함량(MZR) 산점도 및 선형 회귀선 (300 DPI)
3. `scatter_sfr_vs_metallicity.png`: SFR-금속함량(FMR) 산점도 및 선형 회귀선 (300 DPI)
4. `three_core_relations_summary.png`: 3대 핵심 관계 3분할 종합 도표
5. `sample_size_convergence.png`: 표본 크기($N$) 증가에 따른 상관계수($r, \rho$) 수렴 그래프
6. `sample_size_convergence_results.csv`: 표본 크기별 평균 및 표준오차 데이터표
7. `galaxy_type_correlation_summary.csv`: 은하 형태/분광 유형별 상관계수 비교표
8. `galaxy_correlation_summary.csv`: 전체 종합 상관계수 및 회귀 분석 통계표
