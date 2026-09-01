# SDSS 200개 핵심 물리량 및 11대 은하 분류 데이터 명세서 (Data Dictionary)

본 문서는 `galaxy_master_200params.json` (및 `galaxy_master_dataset.json`)에 수록된 **11대 은하 분류(총 55,000개 표본)**와 **200개 핵심 물리량(Standard 200 Parameters)**의 정의, 단위, 물리적 의미 및 계산 방식을 설명합니다.

---

## 1. 11대 은하 분류 체계 (11 Galaxy Morphological & Spectral Classes)

각 분류마다 **5,000개**의 은하 표본이 수록되어 있습니다 (총 55,000개).

| 번호 | 은하 분류명 (Class Name) | 영문 명칭 | 천문학적 정의 및 선별 기준 |
| :---: | :--- | :--- | :--- |
| **1** | **나선은하** | Spiral Galaxy | `gz_spiral = 1`, 뚜렷한 나선팔과 원반 구조를 가진 만기형 은하 |
| **2** | **막대나선은하** | Barred Spiral Galaxy | `gz2_bar_prob > 0.5`, 중심부를 가로지르는 막대 구조를 가진 나선은하 |
| **3** | **타원은하** | Elliptical Galaxy | `gz_elliptical = 1`, 회전타원체 형태의 균일한 광도 분포 및 늙은 항성군 은하 |
| **4** | **렌즈형은하** | Lenticular Galaxy (S0) | 원반과 팽대부는 존재하나 나선팔이 없고 별 생성이 억제된 중간형 은하 |
| **5** | **마젤란형 은하** | Magellanic Galaxy | log M* <= 9.2, 저질량·고별생성 왜소 불규칙/나선 은하 |
| **6** | **고리은하** | Ring Galaxy | `gz2_ring_prob > 0.3`, 외부 고리형 별 형성 영역을 가진 특이 은하 |
| **7** | **전파은하** | Radio Galaxy | FIRST 1.4 GHz 전파 연속체 플럭스 검출 및 고속도 분산 거대 은하 |
| **8** | **퀘이사** | Quasar (QSO) | `SpecObj.class = 'QSO'`, 초거대질량 블랙홀의 초고광도 활동은하핵 |
| **9** | **세이퍼트은하** | Seyfert Galaxy | BPT 진단 Seyfert 영역에 위치하며 고에너지 방출선을 내는 활동은하 |
| **10** | **불규칙은하** | Irregular Galaxy | `gz_uncertain = 1` 및 비대칭/특이 구조를 가진 왜소/불규칙 은하 |
| **11** | **병합은하** | Merger Galaxy | `gz_p_mg > 0.35`, 충돌/상호작용으로 조석 꼬리 및 왜곡이 발생한 은하 |

---

## 2. 200개 핵심 물리량 스키마 상세 명세

### ① 식별자 및 관측 메타데이터 (15개)
- `objID`, `specObjID`: SDSS 측광/분광 고유 식별 번호
- `ra`, `dec`: J2000 기준 천구 적경, 적위 [deg]
- `run`, `rerun`, `camcol`, `field`: SDSS 측광 관측 스트립 메타데이터
- `plate`, `mjd`, `fiberID`: 분광 관측 플레이트, 수정 율리우스일(MJD), 광섬유 번호
- `bptclass`: BPT 진단 분류 코드 (1: SF, 2: Low-SNR SF, 3: Composite, 4: Seyfert, 5: LINER, -1: Unclassified)
- `galaxy_type`: 은하의 11대 분류 명칭
- `zWarning`: 분광 분석 품질 경고 플래그 (0: 정상)
- `specClass`: 분광 1차 분류 (GALAXY, QSO)

### ② 분광학적 적색편이, 속도분산, 신호대잡음비 (10개)
- `z`, `zErr`: 분광 적색편이 및 오차
- `velDisp`, `velDispErr`, `vdispChi2`: 중심부 속도 분산 (sigma_v, [km/s]), 오차, 피팅 chi^2
- `snMedian_u, g, r, i, z`: 5개 밴드별 스펙트럼 중앙 S/N 비

### ③ 5종 측광 등급 시스템 (25개)
5개 대역(u, g, r, i, z) 각각에 대한 5종 겉보기 등급 [mag]:
- `psfMag_u/g/r/i/z`: 점광원 PSF 피팅 등급
- `fiberMag_u/g/r/i/z`: 3인치 분광 광섬유 내부 등급
- `petroMag_u/g/r/i/z`: 페트로시안(Petrosian) 총 등급
- `modelMag_u/g/r/i/z`: de Vaucouleurs 또는 Exponential 최적 모델 등급
- `cModelMag_u/g/r/i/z`: 복합(Composite) 모델 등급 (은하 색지수 표준)

### ④ 5종 측광 등급 측정 오차 (25개)
- `psfMagErr_u/g/r/i/z`, `fiberMagErr_u/g/r/i/z`, `petroMagErr_u/g/r/i/z`, `modelMagErr_u/g/r/i/z`, `cModelMagErr_u/g/r/i/z`

### ⑤ 우리은하 성간 소광 (5개)
- `extinction_u, extinction_g, extinction_r, extinction_i, extinction_z`: 파장별 소광량 [mag]

### ⑥ 은하 크기 및 유효 반경 (20개)
- `petroRad_u/g/r/i/z`: 페트로시안 반경 [arcsec]
- `petroR50_u/g/r/i/z`: 50% 광도 반광 반경 (Half-light Radius, R_50) [arcsec]
- `petroR90_u/g/r/i/z`: 90% 광도 반경 (R_90) [arcsec]
- `deVRad_u/g/r/i/z`: de Vaucouleurs 프로파일 유효 반경 [arcsec]

### ⑦ 은하 형상 프로파일 및 축비 (20개)
- `expRad_u/g/r/i/z`: 지수형 원반 스케일 반경 [arcsec]
- `deVAB_u/g/r/i/z`: de Vaucouleurs 모델의 단축/장축 축비 (b/a)
- `expAB_u/g/r/i/z`: Exponential 모델의 단축/장축 축비 (b/a)
- `fracDeV_u/g/r/i/z`: de Vaucouleurs 프로파일의 기여도 분율 (0 ~ 1)

### ⑧ 스펙트럼 방출선 플럭스 (15개)
단위: 10^-17 erg s^-1 cm^-2
- 수소선: `h_alpha_flux` (6563A), `h_beta_flux` (4861A), `h_gamma_flux` (4340A), `h_delta_flux` (4101A)
- 산소선: `oiii_5007_flux`, `oiii_4959_flux`, `oii_3726_flux`, `oii_3729_flux`, `oi_6300_flux`
- 질소 및 황선: `nii_6584_flux`, `nii_6548_flux`, `sii_6717_flux`, `sii_6731_flux`
- 헬륨선: `hei_5876_flux`, `heii_4686_flux`

### ⑨ 방출선 플럭스 측정 오차 (15개)
- 상기 15개 방출선별 `_err`

### ⑩ 방출선 등가폭(EQW) 및 오차 (12개)
단위: [A] (음수는 방출선을 의미)
- `h_alpha_eqw`, `h_alpha_eqw_err`, `h_beta_eqw`, `h_beta_eqw_err`, `oiii_5007_eqw`, `oiii_5007_eqw_err`
- `nii_6584_eqw`, `nii_6584_eqw_err`, `sii_6717_eqw`, `sii_6731_eqw_err`, `oii_3726_eqw`, `oii_3726_eqw_err`

### ⑪ MPA-JHU 천체물리/화학 진화 파생량 (15개)
- `log_stellar_mass`, `lgm_tot_p16`, `lgm_tot_p84`: 전체 항성 질량 (log M*/M_sun) 및 16%/84% 한계
- `lgm_fib_p50`: 광섬유 내부 질량
- `log_sfr`, `sfr_tot_p16`, `sfr_tot_p84`: 별 생성률 (log SFR [M_sun/yr]) 및 한계
- `sfr_fib_p50`: 광섬유 내부 SFR
- `log_ssfr`: 비별생성률 (log(SFR/M*) [yr^-1])
- `metallicity_oh`, `oh_p16`, `oh_p84`: 기체 산소 풍부도 (12 + log(O/H))
- `d4000_n`, `d4000_n_err`: 4000A 불연속 지표 (항성 종족 평균 연령)
- `dust_ebv`: 성간 먼지로 인한 색 초과 E(B-V) [mag]

### ⑫ Galaxy Zoo 1 & 2 형태학적 확률 (12개)
- `gz_p_el`: 타원은하 판정 확률 (0 ~ 1)
- `gz_p_cs`: 나선/원반은하 판정 확률 (0 ~ 1)
- `gz_p_edge`: 측면(Edge-on) 나선은하 확률
- `gz_p_mg`: 충돌/병합은하(Merger) 확률
- `gz_spiral`, `gz_elliptical`, `gz_uncertain`: 1차 확정 플래그
- `gz2_bar_prob`: 은하 중심 막대(Bar) 구조 확률
- `gz2_ring_prob`: 고리(Ring) 구조 확률
- `gz2_merger_prob`: 병합/상호작용 징후 확률
- `gz2_irregular_prob`: 불규칙/특이 구조 확률
- `gz2_bulge_prominence`: 팽대부(Bulge) 돌출도/우세도

### ⑬ 다파장 서베이 연계 (2MASS, WISE, FIRST) (6개)
- `mag_j_2mass`, `mag_h_2mass`, `mag_k_2mass`: 2MASS 근적외선 J, H, Ks 등급 [mag]
- `mag_w1_wise`, `mag_w2_wise`: WISE 중적외선 3.4um, 4.6um 등급 [mag]
- `first_radio_flux`: FIRST 1.4 GHz 전파 연속체 플럭스 밀도 [mJy]

### ⑭ 파생 천체물리 진단 지수 (5개)
- `log_nii_ha`: log10([NII]6584 / H_alpha) (BPT x축)
- `log_oiii_hb`: log10([OIII]5007 / H_beta) (BPT y축)
- `log_sii_ha`: log10([SII]6717 / H_alpha) (충격파/이온화 진단)
- `color_u_r`: u - r 색지수 (u등급 - r등급)
- `concentration_index_r`: 빛 집중도 지수 (C = R_90 / R_50)
