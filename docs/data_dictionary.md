# YSC 2026 청소년과학탐구반 — 은하 물리량 및 분류 체계 명세서 (Data Dictionary)

본 문서는 프로젝트 마스터 데이터셋(`galaxy_master_200params.csv`) 및 대시보드(`dashboard_real_data.html`)에 탑재된 **3대 은하 분류 체계**, **암흑물질 유도량**, **회전곡선**, **광도**, **원소비** 및 **물리량 명세**를 수록합니다.

---

## 1. 다차원 은하 분류 체계 (Galaxy Classification Systems)

### ① [체계 1] 허블 4대 기본 형태 분류 (Morphology 4 Classes)
- **타원은하 (Elliptical Galaxy)**: 회전타원체 형태의 균일한 광도 분포 및 늙은 항성군 은하
- **나선은하 (Spiral Galaxy)**: 뚜렷한 나선팔과 원반 구조를 가진 만기형 별 생성 은하 (막대나선/고리 포함)
- **렌즈형은하 (Lenticular Galaxy, S0)**: 원반과 팽대부는 존재하나 나선팔이 없고 별 생성이 억제된 중간형 은하
- **불규칙은하 (Irregular Galaxy)**: 비대칭 구조, 왜소 은하, 조석 상호작용 및 폭발적 별 생성 은하

### ② [체계 2] 분광 및 활동은하핵 3대 활동성 분류 (Activity 3 Classes)
- **전파은하 (Radio Galaxy)**: FIRST 1.4 GHz 전파 연속체에서 강한 제트 및 싱크로트론 복사를 방출하는 거대 은하
- **세이퍼트 은하 (Seyfert Galaxy)**: 중심부에 고광도 활동은하핵(AGN)을 품고 있어 높은 전리 방출선([O III], [N II])을 강하게 방출하는 은하
- **퀘이사 (Quasar, QSO)**: 초거대질량 블랙홀의 극단적 물질 강착으로 은하 전체보다 밝은 중심 광도를 내는 초고광도 AGN
- **일반 은하 (Normal Galaxy)**: 비활동성 일반 항성 형성 은하

### ③ [체계 3] 세부 원반 및 특이 구조 5대 분류 (Detailed Structure 5 Classes)
- **마젤란형 은하 (Magellanic Galaxy)**: 저질량($\log M_* \le 9.2$), 비대칭 왜소 나선/불규칙 은하
- **나선은하 (Spiral Galaxy)**: 표준적인 2가닥 이상의 정상 나선팔을 가진 정상 나선은하
- **막대나선은하 (Barred Spiral Galaxy)**: 은하 중심부를 가로지르는 막대(Bar) 구조가 뚜렷한 나선은하
- **고리은하 (Ring Galaxy)**: 공명 또는 관통 충돌로 인해 외부 고리형 별 형성 띠를 형성한 특이 은하
- **불규칙 은하 (Irregular Galaxy)**: 나선이나 타원의 대칭성이 없는 비대칭 은하

---

## 2. 물리량 및 암흑물질 유도 모델 명세서 (Physical & Chemical Parameters)

*(※ 오차값 `*_err` 및 천구 좌표 `ra`, `dec`, 식별자 `specObjID`는 제외)*

| 분류 | 변수명 (Parameter) | 단위 / 표현 | 천문학적 정의 및 유도 공식 |
| :--- | :--- | :---: | :--- |
| **광도** | **`abs_mag_r`** | $\text{mag}$ | 허블 법칙 기반 광도거리($D_L$)를 보정한 은하의 $r$밴드 절대 등급 |
| **광도** | **`log_luminosity_r`** | $\log(L_r/L_\odot)$ | 태양 $r$밴드 절대등급($M_{r,\odot}=4.68$) 대비 복사 광도 $\log(L/L_\odot) = 0.4 \times (4.68 - M_r)$ |
| **은하 질량** | **`lgm_tot_p50`** | $\log(M_*/M_\odot)$ | 스펙트럼 에너지 분포(SED) 피팅으로 얻은 은하 총 항성 질량 중앙값 |
| **은하 질량** | **`log_dyn_mass`** | $\log(M_{\text{dyn}}/M_\odot)$ | 비리얼 정리 기반 동역학적 총 질량 $M_{\text{dyn}} = \frac{5 \sigma_v^2 R_e}{G}$ |
| **회전곡선** | **`v_rot`** | $\text{km/s}$ | 은하 회전곡선의 평탄 회전속도 $V_{\text{rot}} = \sqrt{2}\,\sigma_v$ |
| **회전곡선** | **`log_v_rot`** | $\log(\text{km/s})$ | 은하 회전속도의 상용로그값 |
| **동역학** | **`velDisp`** | $\text{km/s}$ | 은하 중심부 별들의 무작위 시선속도 분산값 ($\sigma_v$) |
| **암흑물질** | **`log_dark_matter_mass`** | $\log(M_{\text{DM}}/M_\odot)$ | 회전곡선 총 질량과 항성 질량의 차이로 유도된 암흑물질 질량 $M_{\text{DM}} = M_{\text{dyn}} - M_*$ |
| **암흑물질** | **`dark_matter_fraction`** | 분율 ($0 \sim 1$) | 은하 전체 동역학 질량 대비 암흑물질 비율 $f_{\text{DM}} = \frac{M_{\text{DM}}}{M_{\text{dyn}}} = 1 - \frac{M_*}{M_{\text{dyn}}}$ |
| **원소비** | **`oh_p50`** | $12+\log(\text{O/H})$ | 가스 내부 산소 함유 원소비 (산소 풍부도 / 금속성) |
| **원소비** | **`log_n_o`** | $\log(\text{N/O})$ | $[\text{N II}]\lambda6584 / [\text{O II}]\lambda3726$ 플럭스 비율로 유도된 질소-산소 원소비 |
| **원소비** | **`log_oii_oiii`** | $\log([\text{O II}]/[\text{O III}])$ | $[\text{O II}]\lambda3726 / [\text{O III}]\lambda5007$ 플럭스 비 (가스 전리 파라미터 지표) |
| **원소비** | **`log_s_o`** | $\log([\text{S II}]/[\text{O III}])$ | 황-산소 방출선 비율 (충격파 및 저이온화 가스 밀도 지표) |
| **진단비율** | **`log_nii_ha`** | - | BPT x축 비율 $\log([\text{N II}]\lambda6584 / \text{H}\alpha)$ |
| **진단비율** | **`log_oiii_hb`** | - | BPT y축 비율 $\log([\text{O III}]\lambda5007 / \text{H}\beta)$ |
| **플럭스** | **`h_alpha_flux`** | $10^{-17}\,\text{erg/s/cm}^2$ | 수소 $\text{H}\alpha$ ($6563\text{\AA}$) 방출선 플럭스 (젊은 항성 형성 지표) |
| **플럭스** | **`h_beta_flux`** | $10^{-17}\,\text{erg/s/cm}^2$ | 수소 $\text{H}\beta$ ($4861\text{\AA}$) 방출선 플럭스 (발머 감쇄 먼지 소광 분석용) |
| **플럭스** | **`h_gamma_flux`** | $10^{-17}\,\text{erg/s/cm}^2$ | 수소 $\text{H}\gamma$ ($4340\text{\AA}$) 방출선 플럭스 |
| **플럭스** | **`oiii_5007_flux`** | $10^{-17}\,\text{erg/s/cm}^2$ | 산소 $[\text{O III}]$ ($5007\text{\AA}$) 방출선 플럭스 (고에너지 이온화원 지표) |
| **플럭스** | **`nii_6584_flux`** | $10^{-17}\,\text{erg/s/cm}^2$ | 질소 $[\text{N II}]$ ($6584\text{\AA}$) 방출선 플럭스 |
| **플럭스** | **`sii_6717_flux`** | $10^{-17}\,\text{erg/s/cm}^2$ | 황 $[\text{S II}]$ ($6717\text{\AA}$) 방출선 플럭스 (성간 가스 전자밀도 지표) |
| **플럭스** | **`oii_3726_flux`** | $10^{-17}\,\text{erg/s/cm}^2$ | 산소 $[\text{O II}]$ ($3726\text{\AA}$) 방출선 플럭스 (별 생성률 지표) |
| **측광** | **`u, g, r, i`** | $\text{mag}$ | 자외선($u$), 녹색($g$), 적색($r$), 근적외선($i$) 파장 겉보기 등급 |
| **색지수** | **`color_u_r`** | $\text{mag}$ | 은하의 색 이분성(Color Bimodality)을 정의하는 $(u - r)$ 색지수 |
| **크기** | **`petroRad_r`** | $\text{arcsec}$ | $r$밴드 페트로시안 반지름 |
| **크기** | **`petroR50_r`** | $\text{arcsec}$ | 은하 총 광도의 50%가 수용되는 유효 반광반경 ($R_{50}$) |
| **크기** | **`petroR90_r`** | $\text{arcsec}$ | 은하 총 광도의 90%가 수용되는 외곽 광도반경 ($R_{90}$) |
| **크기** | **`r_e_kpc`** | $\text{kpc}$ | 각지름거리($D_A$)로 변환한 물리적 유효 반경 |
| **적색편이** | **`z`** | - | 분광 관측을 통해 정밀 측정한 도플러 적색편이 |
| **적색편이** | **`phot_z`** | - | 광대역 측광 필터 비율로 추정한 측광 적색편이 |
| **항성형성** | **`sfr_tot_p50`** | $\log(M_\odot/\text{yr})$ | 연간 총 별 생성률 $\log(\text{SFR})$ |
| **연령** | **`d4000_n`** | Index | $4000\text{\AA}$ 감쇄폭 지표 $D_n(4000)$ (늙은 항성 비율 및 은하 연령 지표) |
