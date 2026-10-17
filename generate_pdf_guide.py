# -*- coding: utf-8 -*-
"""
은하진화연구_종합안내서_도표분석_및_물리개념.pdf 생성 스크립트
ReportLab을 사용하여 출판 품질의 학술 안내서 PDF를 제작합니다.
"""

import os
import sys
import shutil
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, HRFlowable
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# 폰트 등록
font_regular = "C:/Windows/Fonts/malgun.ttf"
font_bold = "C:/Windows/Fonts/malgunbd.ttf"
pdfmetrics.registerFont(TTFont("Malgun", font_regular))
pdfmetrics.registerFont(TTFont("MalgunBold", font_bold))

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PDF = os.path.join(BASE_DIR, "은하진화연구_종합안내서_도표분석_및_물리개념.pdf")

doc = SimpleDocTemplate(
    OUTPUT_PDF,
    pagesize=A4,
    leftMargin=34,
    rightMargin=34,
    topMargin=36,
    bottomMargin=36
)

styles = getSampleStyleSheet()

title_style = ParagraphStyle(
    "DocTitle",
    fontName="MalgunBold",
    fontSize=20,
    leading=26,
    textColor=colors.HexColor("#0f172a"),
    alignment=1,
    spaceAfter=6
)

subtitle_style = ParagraphStyle(
    "DocSubTitle",
    fontName="Malgun",
    fontSize=10,
    leading=15,
    textColor=colors.HexColor("#475569"),
    alignment=1,
    spaceAfter=12
)

h1_style = ParagraphStyle(
    "Heading1",
    fontName="MalgunBold",
    fontSize=13,
    leading=17,
    textColor=colors.HexColor("#0369a1"),
    spaceBefore=12,
    spaceAfter=5
)

h2_style = ParagraphStyle(
    "Heading2",
    fontName="MalgunBold",
    fontSize=10.2,
    leading=14,
    textColor=colors.HexColor("#0f172a"),
    spaceBefore=8,
    spaceAfter=3
)

body_style = ParagraphStyle(
    "Body",
    fontName="Malgun",
    fontSize=8.6,
    leading=13.0,
    textColor=colors.HexColor("#1e293b"),
    spaceAfter=5
)

formula_style = ParagraphStyle(
    "FormulaBox",
    fontName="MalgunBold",
    fontSize=8.6,
    leading=13.5,
    textColor=colors.HexColor("#0c4a6e"),
    backColor=colors.HexColor("#f0f9ff"),
    borderPadding=6,
    spaceBefore=4,
    spaceAfter=6
)

bullet_style = ParagraphStyle(
    "Bullet",
    fontName="Malgun",
    fontSize=8.4,
    leading=12.6,
    textColor=colors.HexColor("#334155"),
    leftIndent=12,
    firstLineIndent=-8,
    spaceAfter=3
)

table_header_style = ParagraphStyle(
    "TableHeader",
    fontName="MalgunBold",
    fontSize=8.3,
    leading=11,
    textColor=colors.white,
    alignment=1
)

table_cell_style = ParagraphStyle(
    "TableCell",
    fontName="Malgun",
    fontSize=7.9,
    leading=11,
    textColor=colors.HexColor("#0f172a")
)

elements = []

# 표지 헤더
elements.append(Paragraph("🌌 YSC 2026 은하 진화 연구 종합 안내서 (최종 개정판)", title_style))
elements.append(Paragraph("은하 진화 지수(GEI v2.0) 수식 · 말름퀴스트 편향 보정 · 피어슨/스피어만 상관계수 · CEERS 배제 근거 · 직접 관측 입력 체계", subtitle_style))
elements.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#0284c7"), spaceAfter=10))

# 1. 은하 진화 지수(Unified GEI v2.0) 전체 수학적 수식
elements.append(Paragraph("1. 차세대 5축 통합 은하 진화 지수 (Unified GEI v2.0) 수학적 정의식", h1_style))
elements.append(Paragraph(
    "은하의 진화 상태를 단일 물리량으로만 판단할 때 발생하는 축퇴(Degeneracy)를 해결하기 위해, "
    "거리 편향이 완전히 배제된 5대 고유 물리 축을 시그모이드/선형 클리핑 정규화(0~1)하여 가중 결합한 지수입니다.",
    body_style
))
elements.append(Paragraph(
    "■ 통합 은하 진화 지수 (Unified GEI v2.0) 마스터 방정식:<br/>"
    "GEI_v2 = 0.30 · S_quench + 0.25 · S_mass + 0.20 · S_pop + 0.15 · S_struct + 0.10 · S_halo   (범위: 0.000 ≤ GEI_v2 ≤ 1.000)",
    formula_style
))

gei_sub_items = [
    "• <b>① 제1축: 별생성 소광 점수 S_quench (가중치 30%)</b> — 비별생성률 sSFR = SFR / M_* [yr^-1] 기반:<br/>"
    "  S_quench = clip( (-log10(sSFR) - 8.5) / 4.0,  0, 1 )   (폭발적 별생성 log sSFR = -8.5 일 때 0.0, 완전 소광 log sSFR = -12.5 일 때 1.0)",
    "• <b>② 제2축: 항성질량 성숙 점수 S_mass (가중치 25%)</b> — 누적 항성질량 log10(M_*/M_sun) 기반:<br/>"
    "  S_mass = clip( (log10(M_*) - 8.0) / 3.8,  0, 1 )   (왜소은하 10^8 M_sun 일 때 0.0, 거대 은하 10^11.8 M_sun 일 때 1.0)",
    "• <b>③ 제3축: 항성종족 노화 및 화학적 성숙 점수 S_pop (가중치 20%)</b> — 광학 색지수(u-r), 4000Å 불연속면(Dn4000), 금속함량 결합:<br/>"
    "  S_color = clip(((u - r) - 1.0)/1.8, 0, 1),  S_d4000 = clip((Dn4000 - 1.05)/1.05, 0, 1),  S_metal = clip(((12+log(O/H)) - 8.0)/1.1, 0, 1)<br/>"
    "  → S_pop = 0.45 · S_color + 0.35 · S_d4000 + 0.20 · S_metal",
    "• <b>④ 제4축: 구조적 중심 바리온 밀집 점수 S_struct (가중치 15%)</b> — 유효반경 내 항성 표면질량밀도 Σ_* = M_* / (2π R_e^2) 기반:<br/>"
    "  S_struct = clip( (log10(Σ_*) - 7.0) / 2.8,  0, 1 )   (중심부 바리온 수축 및 팽대부 성장을 정량화)",
    "• <b>⑤ 제5축: 암흑물질 헤일로 성숙 점수 S_halo (가중치 10%)</b> — 동역학 질량 M_dyn = V_rot^2 R_e / G 및 암흑물질 분율 f_DM = (M_dyn - M_bar)/M_dyn 기반:<br/>"
    "  S_halo = 0.55 · clip((log10(M_dyn) - 9.5)/3.0, 0, 1) + 0.45 · clip((f_DM - 0.15)/0.75, 0, 1)"
]
for item in gei_sub_items:
    elements.append(Paragraph(item, bullet_style))

elements.append(Paragraph(
    "<b>[5단계 진화 단계 판정 기준]</b> Stage I 원시 폭발별생성기(0.00~0.28) → Stage II 초기 주계열 원반성장기(0.28~0.46) → "
    "Stage III 성숙 주계열 나선안정기(0.46~0.64) → Stage IV 녹색계곡 전이·감쇠기(0.64~0.78) → Stage V 완전소광 거대타원은하(0.78~1.00)",
    body_style
))

# 2. 말름퀴스트 편향 보정 방법 및 3대 기술적 방법론 (상관계수, 이상치 필터, Hexbin)
elements.append(Paragraph("2. 말름퀴스트 편향(Malmquist Bias) 보정 방법 및 통계·시각화 방법론", h1_style))

method_sections = [
    ("① 말름퀴스트 편향(Malmquist Bias)을 수학적으로 보정·제거한 방법",
     "• <b>편향 발생 원리</b>: 망원경 탐사는 검출 가능한 최소 겉보기 플럭스 한계(F_lim)가 존재합니다. 빛의 역제곱 법칙 F = L / (4π D^2)에 의해, "
     "거리 D가 먼 곳에서는 최소 검출 가능 광도 L_lim(D) = 4π D^2 F_lim 이상인 밝고 무거운 은하만 관측됩니다. 이를 항성질량으로 변환하면 "
     "<b>log10 M_*,lim(D) = log10 M_*,0 + 2 log10(D / D_0)</b>라는 가짜 양(+)의 경계선이 만들어집니다. 이 때문에 전체 겉보기 등급 제한 표본에서는 "
     "거리와 항성질량 사이에 r = +0.34의 가짜 양의 상관이 나타납니다.<br/>"
     "• <b>본 연구의 2단계 보정법</b>: (1) 최대 분석 거리 D_max = 240 Mpc에서도 100% 누락 없이 검출될 수 있는 완결 질량 문턱값(Completeness Limit) "
     "<b>log10(M_*/M_sun) ≥ 10.3</b>을 산출하고, (2) 해당 질량 구간에서 거리 60 ≤ D ≤ 240 Mpc의 <b>부피 완전 표본(Volume-Limited Complete Subsample)</b>을 추출했습니다. "
     "그 결과 거리-질량 상관계수가 <b>r = +0.34 → r = +0.005 (거의 0)</b>로 즉시 소멸함을 증명했고, GEI v2.0 수식에서 거리(D) 의존 항을 100% 배제했습니다."),

    ("② 피어슨 선형 상관계수(r)와 스피어만 순위 상관계수(ρ)를 함께 산출한 이유",
     "• <b>피어슨 상관계수 (r, Pearson Linear Correlation)</b>: r = Σ(x_i - x̄)(y_i - ȳ) / sqrt(Σ(x_i - x̄)^2 Σ(y_i - ȳ)^2). "
     "상용로그로 변환된 두 물리량(log X, log Y)이 얼마나 '직선(로그 공간 선형 = 실제 물리 공간 멱법칙 Y ∝ X^a)'에 가깝게 비례하는지 측정합니다. "
     "단, 극단적 이상치(Outlier) 몇 개에 의해 값이 쉽게 왜곡되는 한계가 있습니다.<br/>"
     "• <b>스피어만 순위 상관계수 (ρ, Spearman Rank Correlation)</b>: 실제 수치 대신 데이터를 크기 순으로 줄 세운 '순위(Rank, R(x_i), R(y_i))'를 이용해 계산합니다. "
     "따라서 관계가 직선이 아닌 곡선(비선형 단조 증가/감소)이거나 소수의 극단적 이상치가 섞여 있어도 흔들리지 않는 실제 물리적 경향성을 보여줍니다.<br/>"
     "• <b>동시 비교의 의의</b>: 예를 들어 질량-광도 관계는 r = 0.96, ρ = 0.96으로 일치하여 완벽한 선형 멱법칙임을 뜻하는 반면, "
     "질량-별생성률(M*-SFR)은 고질량 소광 은하들 때문에 선형 상관(r)과 순위 상관(ρ)이 차이를 보여 '주계열과 소광 은하군의 이원화(Bimodality)'를 진단할 수 있습니다."),

    ("③ 이상치 및 파이프라인 클리핑 제거 필터 (Outlier & Clipping Filter) 적용 방법",
     "• <b>1단계 (비물리적 거리 결측치 제거)</b>: 카탈로그에서 적색편이가 측정되지 않아 D ≤ 0.05 Mpc 또는 NaN으로 기록된 행을 제거하여 거리 축 수직 점선 아티팩트를 차단했습니다.<br/>"
     "• <b>2단계 (SFR=0 선형/로그 혼동 및 클리핑 경계 제거)</b>: 기존 분석에서 SFR=0 은하가 중앙값을 0으로 끌어내리거나, SDSS Brinchmann 파이프라인의 상·하한 그리드 한계값(log10 SFR = +4.0 또는 -4.0)에 점들이 일직선으로 쌓이는 현상을 막기 위해 <b>-3.8 &lt; log10(SFR) &lt; +3.5</b> 물리적 유효 구간 필터를 적용했습니다.<br/>"
     "• <b>3단계 (분위수 트리밍 및 표본수 문턱값)</b>: 각 변수 상·하위 0.5% 극단 측정 오류를 트리밍하고, 구간별 중앙값(Binned Median) 계산 시 빈(Bin) 내 은하 수가 <b>최소 N ≥ 20개 이상</b>인 구간만 연결하여 양 끝단 노이즈에 의한 꺾임 왜곡을 제거했습니다."),

    ("④ Hexbin 밀도(육각형 격자 상용로그 밀도, log10 N)의 개념과 사용 이유",
     "• <b>Hexbin 밀도란?</b>: 2차원 평면을 정육각형 타일(본 연구는 45×45 격자)로 촘촘히 나눈 뒤, 각 육각형 안에 들어가는 은하의 개수(N)를 세어 "
     "<b>상용로그 색상 척도(log10 N)</b>로 칠하는 2차원 확률밀도 시각화 기법입니다.<br/>"
     "• <b>왜 일반 산점도(Scatter Plot) 대신 사용했는가?</b>: 은하가 1만~5만 개 이상이면 일반 점 그래프에서는 중심부에서 수천 개의 점이 겹쳐 찍히는 "
     "<b>과밀 중첩 포화(Overplotting Saturation)</b>가 발생해 은하가 10개 모인 곳과 5,000개 모인 곳을 전혀 구분할 수 없습니다. "
     "정육각형은 모든 방향의 인접 중심 거리가 같아 방향 왜곡이 없고, log10 N으로 색상을 입히면 1개(log N=0)인 희귀 외곽 영역부터 1,000개(log N=3)가 밀집한 "
     "'별생성 주계열 능선'과 '소광 은하 군집'의 실제 밀도 구조를 한눈에 파악할 수 있습니다.")
]

for title, desc in method_sections:
    elements.append(Paragraph(title, h2_style))
    elements.append(Paragraph(desc, body_style))

elements.append(PageBreak())

# 3. CEERS 제외 이유 및 3차원 도표 활용 방식, 직접 관측 입력 프로그램 설명
elements.append(Paragraph("3. JWST CEERS 제외 사유 · 3차원 도표 활용 원리 · 직접 관측 입력 프로그램", h1_style))

more_sections = [
    ("⑤ JWST CEERS 자료를 천문대 관측 기준 및 8대 상관 분석에서 제외한 4가지 이유",
     "1) <b>우주 시대(Cosmic Epoch) 불일치</b>: NED-LVS와 SDSS는 적색편이 z &lt; 0.1 (최근 10억 년 이내)의 현대 국소 우주 은하인 반면, "
     "JWST CEERS는 z = 0.5 ~ 10 (우주 초기 5억~80억 년 전)의 원시 은하입니다. 초기 우주는 우주의 평균 가스 밀도와 별생성률이 지금보다 10~30배 이상 높았기 때문에, "
     "두 자료를 한 평면에 그대로 섞으면 '은하 개체의 진화'가 아니라 '우주 배경 시대의 차이'가 섞이는 교란이 발생합니다.<br/>"
     "2) <b>관측 파장대 및 물리량 산출 방식의 이질성</b>: SDSS/NED는 정밀 광학 분광(Spectroscopy)을 통해 회전속도(V_rot), Dn4000, 방출선 플럭스를 직접 측정하지만, "
     "CEERS는 적외선 광대역 측광(Photometric SED 피팅)에 의존하여 동역학적 회전속도(V_rot)와 직접적인 암흑물질 질량(M_DM) 측정치가 존재하지 않습니다.<br/>"
     "3) <b>지상 천문대 관측 가능 범위와의 불일치</b>: 우리 연구팀이 학교·지역 천문대 광학 망원경과 CCD로 직접 관측할 수 있는 대상은 100% 국소 우주(D &lt; 100 Mpc) 은하입니다. "
     "따라서 직접 관측 은하를 판별하는 기준 배경(Reference Cloud)은 반드시 동일한 국소 우주 표본인 <b>NED-LVS + SDSS DR18</b>로만 구성해야 과학적 정합성이 성립합니다."),

    ("⑥ 3차원 도표를 단독 정적 이미지로만 쓰지 않고 2차원 질량 통제 + 대화형 3D로 결합한 이유",
     "• <b>정적 3차원 도표의 시선 방향 투영 착시(Projection Degeneracy)</b>: 종이나 화면에 고정된 3D 산점도는 바라보는 각도(Azimuth, Elevation)에 따라 "
     "서로 다른 평면에 있는 은하들이 겹쳐 보이거나, 정량적인 상관계수(r)와 중앙값 추세선을 정확히 읽을 수 없는 한계가 있습니다.<br/>"
     "• <b>본 연구의 해결책 (2D 질량 통제 편상관 + 대화형 WebGL 3D 다양체 결합)</b>: "
     "첫째, 정량적 법칙 증명을 위해서는 제3변수(항성질량 M_*)를 좁은 구간으로 고정한 <b>'질량 통제 편상관 분석(Mass-Controlled Partial Correlation)'</b>을 수행하여 "
     "체급 착시 없이 주계열 편차(ΔMS)와 암흑물질 분율(f_DM)의 순수 물리 관계를 입증했습니다. "
     "둘째, 연구 과제 2에서 구축한 <b>3차원 진화 다양체(log M_* - log SFR - log M_DM [ΔMS], log M_* - log sSFR - f_DM, log M_* - log R_e - f_DM)</b>를 "
     "웹 분석기(observatory_analyzer_web.html)에 탑재하여 마우스로 360도 회전하며 우리 팀 관측 은하의 3차원 위치와 ±10 Gyr 진화 궤적을 입체적으로 분석하도록 구현했습니다."),

    ("⑦ [핵심 개편] 미관측 은하 프리셋 폐기 → '우리 팀 직접 관측 은하 입력 프로그램'으로 전면 개편",
     "• <b>문제점 해결</b>: 우리가 직접 관측하지 않은 문헌 카탈로그 은하 12종을 마치 우리가 관측한 것처럼 전면에 배치했던 구성을 전면 폐기했습니다.<br/>"
     "• <b>망원경·CCD 원시 관측값 자동 물리량 환산기 탑재</b>: 천문대에서 직접 측정한 <b>① 겉보기 등급(m_r [mag])</b>, <b>② 사진 반빛 각반경(θ_e [arcsec])</b>, "
     "<b>③ 후퇴속도(v_r [km/s]) 또는 거리(D [Mpc])</b>, <b>④ 광학 색지수(u-r)</b>를 입력하면, 허블 법칙(D = v_r / H_0), 거리 지수 공식(M_r = m_r - 5 log10(D) - 25), "
     "삼각법 물리 반경 공식(R_kpc = D · θ_arcsec / 206.265)을 통해 항성질량(log M_*), 물리적 반경(R_kpc), 회전속도(V_rot), 별생성률(log SFR)을 자동 산출합니다.<br/>"
     "• <b>우리 팀 관측 일지(My Observation Log) 기록 및 CSV 내보내기</b>: 직접 입력하거나 천체사진(JPG/PNG/FITS)에서 측광한 우리 팀의 관측 은하들을 "
     "[우리 팀 관측 일지]에 누적 등록하여 여러 관측 은하들을 3D 다양체 위에서 동시에 비교하고 CSV 파일로 저장할 수 있습니다.")
]

for title, desc in more_sections:
    elements.append(Paragraph(title, h2_style))
    elements.append(Paragraph(desc, body_style))

# 4. 핵심 4대 천체물리 개념 요약 및 도표 적합성 분류
elements.append(Paragraph("4. 핵심 4대 천체물리 개념 (바리온 · 물리적 반경 · 비별생성률 · GEI) 및 도표 적합성", h1_style))
table_data = [
    [
        Paragraph("<b>분류 등급</b>", table_header_style),
        Paragraph("<b>해당 도표 및 물리량 관계</b>", table_header_style),
        Paragraph("<b>물리적·통계적 판정 근거 및 반영 원칙</b>", table_header_style)
    ],
    [
        Paragraph("<font color='#059669'><b>[1등급]<br/>즉시 사용 가능<br/>(GEI 핵심 채택)</b></font>", table_cell_style),
        Paragraph("• 항성질량–비별생성률 (M* - sSFR)<br/>• 항성질량–광학 색지수 (M* - u-r)<br/>• 항성질량–항성연령 (M* - Dn4000)<br/>• 표면밀도–암흑물질 (Σ* - f_DM)<br/>• 항성질량–암흑물질 (M* - M_DM)<br/>• 항성질량–광도 (M* - L, r=0.96)", table_cell_style),
        Paragraph("관측 거리 편향 없이 은하 고유의 별생성 소광, 질량 축적, 항성 종족 노화, 중심 바리온 수축, 헤일로 성장을 직접 대변하므로 GEI v2.0 5대 핵심 축으로 직접 채택함.", table_cell_style)
    ],
    [
        Paragraph("<font color='#d97706'><b>[2등급]<br/>추가 검증 후<br/>조건부 사용 가능</b></font>", table_cell_style),
        Paragraph("• 단순 질량–별생성률 (M* - SFR)<br/>• 광도–암흑물질 (L - M_DM)<br/>• 별생성률–암흑물질 (SFR - M_DM)<br/>• 질량–금속함량 (M* - O/H)<br/>• BPT 방출선 이온화 진단도", table_cell_style),
        Paragraph("• 단순 SFR은 은하 체급 효과가 섞여 있으므로 sSFR이나 주계열 편차(ΔMS)로 변환 필수.<br/>• SFR-M_DM은 M*를 통제한 편상관/3D(M*-SFR-M_DM) 분석 필요.<br/>• BPT는 AGN 피드백 소광 보조 판별용으로 활용.", table_cell_style)
    ],
    [
        Paragraph("<font color='#dc2626'><b>[3등급]<br/>절대 사용 금지<br/>(GEI 100% 배제)</b></font>", table_cell_style),
        Paragraph("• 거리–항성질량 (Dist - M*)<br/>• 거리–별생성률 (Dist - SFR)<br/>• 거리–암흑물질 (Dist - M_DM)<br/>• 선형 오표기 SFR / 미정제 도표", table_cell_style),
        Paragraph("<b>말름퀴스트 관측 선택 편향(Malmquist Bias, F = L / 4πD²)</b> 때문임. 부피 완전 표본(log M* ≥ 10.3)으로 통제 시 상관계수가 r = +0.005 ≈ 0으로 소멸하므로 은하 진화 지수에 절대 사용 금지.", table_cell_style)
    ]
]

t = Table(table_data, colWidths=[85, 190, 250])
t.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
    ("ALIGN", (0, 0), (-1, 0), "CENTER"),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
    ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#ecfdf5")),
    ("BACKGROUND", (0, 2), (-1, 2), colors.HexColor("#fffbeb")),
    ("BACKGROUND", (0, 3), (-1, 3), colors.HexColor("#fef2f2")),
    ("TOPPADDING", (0, 0), (-1, -1), 5),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ("LEFTPADDING", (0, 0), (-1, -1), 5),
    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
]))
elements.append(t)

elements.append(PageBreak())

# 5. 핵심 발표 차트 수록
elements.append(Paragraph("5. 8대 물리량 상관관계 오류 수정 및 심화 검증 도표", h1_style))
chart5_img = os.path.join(BASE_DIR, "output", "presentation_charts", "발표차트5_8대그래프_오류수정_NED_SDSS_비교_및_GEI도표선별.png")
if os.path.exists(chart5_img):
    elements.append(Image(chart5_img, width=515, height=285))
    elements.append(Spacer(1, 8))

chart6_img = os.path.join(BASE_DIR, "output", "presentation_charts", "발표차트6_심화검증_질량통제_거리편향보정_도표적합성분류.png")
if os.path.exists(chart6_img):
    elements.append(Image(chart6_img, width=515, height=305))

# 빌드 실행
doc.build(elements)
print(f"[완료] PDF 생성 완료: {OUTPUT_PDF}")

# 다운로드 폴더에도 복사
downloads_pdf = r"C:\Users\neato\Downloads\은하진화연구_종합안내서_도표분석_및_물리개념.pdf"
try:
    shutil.copy2(OUTPUT_PDF, downloads_pdf)
    print(f"[완료] 다운로드 폴더 복사 완료: {downloads_pdf}")
except Exception as e:
    print(f"[경고] 다운로드 폴더 복사 실패: {e}")
