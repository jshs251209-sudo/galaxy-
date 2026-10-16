# -*- coding: utf-8 -*-
"""
은하진화연구_종합안내서_도표분석_및_물리개념.pdf 생성 스크립트
ReportLab을 사용하여 출판 품질의 학술 안내서 PDF를 제작합니다.
"""

import os
import sys
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether, HRFlowable
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
    leftMargin=36,
    rightMargin=36,
    topMargin=40,
    bottomMargin=40
)

styles = getSampleStyleSheet()

# 커스텀 스타일
title_style = ParagraphStyle(
    "DocTitle",
    fontName="MalgunBold",
    fontSize=22,
    leading=28,
    textColor=colors.HexColor("#0f172a"),
    alignment=1, # Center
    spaceAfter=8
)

subtitle_style = ParagraphStyle(
    "DocSubTitle",
    fontName="Malgun",
    fontSize=11,
    leading=16,
    textColor=colors.HexColor("#475569"),
    alignment=1,
    spaceAfter=15
)

h1_style = ParagraphStyle(
    "Heading1",
    fontName="MalgunBold",
    fontSize=14,
    leading=18,
    textColor=colors.HexColor("#0369a1"),
    spaceBefore=14,
    spaceAfter=6
)

h2_style = ParagraphStyle(
    "Heading2",
    fontName="MalgunBold",
    fontSize=11,
    leading=15,
    textColor=colors.HexColor("#0f172a"),
    spaceBefore=10,
    spaceAfter=4
)

body_style = ParagraphStyle(
    "Body",
    fontName="Malgun",
    fontSize=9,
    leading=13.5,
    textColor=colors.HexColor("#1e293b"),
    spaceAfter=6
)

bullet_style = ParagraphStyle(
    "Bullet",
    fontName="Malgun",
    fontSize=8.5,
    leading=13,
    textColor=colors.HexColor("#334155"),
    leftIndent=14,
    firstLineIndent=-10,
    spaceAfter=3
)

table_header_style = ParagraphStyle(
    "TableHeader",
    fontName="MalgunBold",
    fontSize=8.5,
    leading=11,
    textColor=colors.white,
    alignment=1
)

table_cell_style = ParagraphStyle(
    "TableCell",
    fontName="Malgun",
    fontSize=8,
    leading=11,
    textColor=colors.HexColor("#0f172a")
)

callout_style = ParagraphStyle(
    "Callout",
    fontName="Malgun",
    fontSize=8.5,
    leading=13,
    textColor=colors.HexColor("#0c4a6e")
)

elements = []

# 표지 헤더
elements.append(Paragraph("🌌 YSC 2026 은하 진화 연구 종합 안내서", title_style))
elements.append(Paragraph("은하 진화 지수(GEI v2.0) 개발 · 8대 상관관계 도표 분석 · 적합성 3단계 분류 · 핵심 천체물리 개념 총정리", subtitle_style))
elements.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#0284c7"), spaceAfter=14))

# 1. 연구 개요 및 핵심 요약
elements.append(Paragraph("1. 연구 배경 및 핵심 연구 체계 요약", h1_style))
intro_text = (
    "본 연구는 NASA/IPAC NED-LVS(145만 개), JWST CEERS(7.7만 개), SDSS DR18(5만 개)의 전 우주적 대규모 관측 빅데이터를 통합하여, "
    "은하의 현재 진화 상태를 0.00부터 1.00까지 단일 수치로 정량화하는 <b>차세대 5축 통합 은하 진화 지수(Unified GEI v2.0)</b>를 개발하고, "
    "천문대 관측 은하의 현재 진화단계 판별 및 과거(-10 Gyr) 복원과 미래(+10 Gyr) 진화 궤적을 3차원 다양체 상에서 예측하는 통합 연구입니다."
)
elements.append(Paragraph(intro_text, body_style))

# 2. 핵심 4대 천체물리 개념 완벽 정리
elements.append(Paragraph("2. 핵심 4대 천체물리 개념 설명", h1_style))

concepts = [
    ("① 바리온 (Baryon, 바리온 물질 질량 M_baryon)",
     "• <b>정의</b>: 양성자, 중성자 등 쿼크 3개로 구성된 일반 물질로, 빛(전자기파)과 상호작용하여 우리가 망원경으로 직접 관측할 수 있는 물질입니다. 은하의 바리온 질량은 <b>별들의 총질량(M_star)</b>과 <b>성간 가스(중성수소 HI, 분자수소 H2, 이온화 가스)의 총질량(M_gas)</b>의 합(M_baryon = M_star + M_gas)입니다.<br/>"
     "• <b>은하 진화에서의 핵심 역할</b>: 우주 전체 물질 중 약 84.3%는 중력으로만 상호작용하는 <b>암흑물질(Dark Matter)</b>이며, 바리온은 15.7%에 불과합니다. 그러나 암흑물질은 복사를 방출하지 못해 수축에 한계가 있는 반면, <b>바리온 가스는 빛을 방출하며 에너지를 잃고(복사 냉각) 은하 중심 수 kpc 이내로 깊숙이 수축하여 별을 형성</b>합니다. 따라서 은하 중심부(유효반경 R_e 내)는 바리온이 지배하고, 외곽으로 갈수록 암흑물질 분율(f_DM)이 압도적으로 높아집니다."),
    
    ("② 물리적 반경 (Physical Radius, R_kpc)",
     "• <b>정의</b>: 사진에서 측정된 은하의 겉보기 각크기(초각 arcsec)에 관측 거리 D [Mpc]를 곱하여 우주 공간 상의 실제 물리적 크기(반경 kpc, 1 kpc ≈ 3,260 광년)로 환산한 값입니다 (R_kpc ≈ D * θ_arcsec / 206.265).<br/>"
     "• <b>물리적 중요성</b>: 물리적 반경 R을 알아야만 ① 은하 내 별들이 얼마나 조밀하게 밀집해 있는지 나타내는 <b>항성 표면질량밀도(Σ_star = M_star / (2π R_e^2))</b>를 계산할 수 있고, ② 회전속도 V_rot과 결합하여 중력 평형에 따른 은하의 <b>총 동역학 질량(M_dyn = V_rot^2 * R / G)</b> 및 외곽 암흑물질 헤일로 질량을 산출할 수 있습니다."),

    ("③ 비별 생성률 (Specific Star Formation Rate, sSFR)",
     "• <b>정의</b>: 은하의 현재 별생성률(SFR [M_sun/yr])을 은하가 이미 보유한 총 항성 질량(M_star [M_sun])으로 나눈 값입니다 (sSFR = SFR / M_star [yr^-1], log sSFR = log SFR - log M_star).<br/>"
     "• <b>왜 단순 SFR 대신 sSFR을 써야 하는가?</b>: 단순 SFR은 은하의 체급(크기) 효과가 섞여 있어, 거대 타원은하가 작은 나선은하보다 절대 SFR이 높게 나타날 수 있습니다. 하지만 sSFR은 <b>'단위 항성 질량(1 M_sun)당 1년에 새로 형성하는 별의 비율'</b>이자, 그 역수(1/sSFR)는 현재 속도로 질량이 2배가 되는 데 걸리는 시간(Mass-doubling time)을 나타냅니다. 따라서 은하의 크기와 무관하게 현재 별을 활발히 만드는 단계인지(log sSFR > -10.2), 소광 전이 단계인지(-11.2 < log sSFR < -10.2), 완전 멈춘 단계인지(log sSFR < -11.2)를 판별하는 가장 결정적인 지표입니다."),

    ("④ 통합 은하 진화 지수 (Unified Galaxy Evolution Index, GEI v2.0)",
     "• <b>수학적 정의식</b>: GEI = 0.30·S_quench + 0.25·S_mass + 0.20·S_pop + 0.15·S_struct + 0.10·S_halo ∈ [0, 1]<br/>"
     "  - S_quench (30%, 별생성 소광): 비별생성률(sSFR) 감소 및 가스 고갈 대변<br/>"
     "  - S_mass (25%, 항성질량 성숙): 누적 별 질량(log M_star) 성장 대변<br/>"
     "  - S_pop (20%, 항성종족 노화): 광학 색지수(u-r), 4000Å 불연속면(Dn4000), 금속량(O/H) 결합<br/>"
     "  - S_struct (15%, 구조 수축): 중심 바리온 수축 및 표면질량밀도(log Σ_star) 대변<br/>"
     "  - S_halo (10%, 헤일로 성장): 총 동역학 질량(M_dyn) 및 실제 암흑물질 분율(f_DM) 대변<br/>"
     "• <b>5단계 진화 단계</b>: 1단계 원시 폭발별생성기(GEI<0.28) → 2단계 초기주계열 원반성장기(0.28~0.46) → 3단계 성숙주계열 나선안정기(0.46~0.64, 우리은하·M51) → 4단계 녹색계곡 전이·감쇠기(0.64~0.78, M31) → 5단계 완전소광 거대타원은하(0.78~1.00, M87)")
]

for title, desc in concepts:
    elements.append(Paragraph(title, h2_style))
    elements.append(Paragraph(desc, body_style))

elements.append(PageBreak())

# 3. 8대 물리량 상관관계 도표 오류 수정 및 분석
elements.append(Paragraph("3. 8대 물리량 상관관계 분석 (NED vs SDSS) & 기술적 오류 수정 내역", h1_style))
chart5_desc = (
    "기존 상관관계 그래프에서 발견된 기술적 오류(SFR 축의 0~120 선형 눈금 혼동, SFR=0 결측치로 인한 중앙값 선 왜곡, "
    "SDSS log SFR≈4.0 클리핑 아티팩트, 거리=0 결측치)를 완전히 수정하고, 상용로그(log10) 척도로 통일하여 "
    "피어슨(r), 스피어만(ρ), 로그 선형 회귀식(y = ax + b)을 재산출하였습니다."
)
elements.append(Paragraph(chart5_desc, body_style))

chart5_img = os.path.join(BASE_DIR, "output", "presentation_charts", "발표차트5_8대그래프_오류수정_NED_SDSS_비교_및_GEI도표선별.png")
if os.path.exists(chart5_img):
    elements.append(Image(chart5_img, width=520, height=295))
    elements.append(Spacer(1, 10))

# 4. 은하 진화 지수(GEI) 도표 3단계 적합성 분류표
elements.append(Paragraph("4. 은하 진화 지수(GEI v2.0) 제작을 위한 도표 3단계 적합성 분류", h1_style))

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
        Paragraph("• 단순 SFR은 은하 체급 효과가 섞여 있으므로 sSFR이나 주계열 편차(ΔMS)로 변환 필수.<br/>• SFR-M_DM은 M*를 통제한 편상관 분석 필요.<br/>• 광도 L은 M/L 및 소광 보정 후 사용.<br/>• BPT는 AGN 피드백 소광 보조 판별용으로 활용.", table_cell_style)
    ],
    [
        Paragraph("<font color='#dc2626'><b>[3등급]<br/>절대 사용 금지<br/>(GEI 100% 배제)</b></font>", table_cell_style),
        Paragraph("• 거리–항성질량 (Dist - M*)<br/>• 거리–별생성률 (Dist - SFR)<br/>• 거리–암흑물질 (Dist - M_DM)<br/>• 선형 오표기 SFR 도표<br/>• 거리=0 / 클리핑 미정제 도표", table_cell_style),
        Paragraph("<b>말름퀴스트 관측 선택 편향(Malmquist Bias, F = L / 4πd²)</b> 때문임. 먼 거리에서는 밝고 무거운 은하만 검출되는 관측 한계에 의한 가짜 상관이며, 완전 표본으로 통제 시 상관계수가 0으로 소멸하므로 은하 진화 지수에 절대 사용 금지.", table_cell_style)
    ]
]

t = Table(table_data, colWidths=[90, 195, 235])
t.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
    ("ALIGN", (0, 0), (-1, 0), "CENTER"),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
    ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#ecfdf5")),
    ("BACKGROUND", (0, 2), (-1, 2), colors.HexColor("#fffbeb")),
    ("BACKGROUND", (0, 3), (-1, 3), colors.HexColor("#fef2f2")),
    ("TOPPADDING", (0, 0), (-1, -1), 6),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
]))
elements.append(t)

elements.append(PageBreak())

# 5. 심화 검증 (질량 통제 분석 및 말름퀴스트 편향 제거)
elements.append(Paragraph("5. 3대 심화 검증 (질량 통제 편상관 · 말름퀴스트 편향 입증 · sSFR 직결성)", h1_style))
chart6_img = os.path.join(BASE_DIR, "output", "presentation_charts", "발표차트6_심화검증_질량통제_거리편향보정_도표적합성분류.png")
if os.path.exists(chart6_img):
    elements.append(Image(chart6_img, width=520, height=315))
    elements.append(Spacer(1, 10))

elements.append(Paragraph("<b>[심화 검증 결과 요약]</b>", h2_style))
elements.append(Paragraph("• <b>질량 통제 분석 (Panel A)</b>: 항성 질량(log M*)을 통제하면, 별생성이 소광된 은하(ΔMS < -0.6)일수록 암흑물질 분율(f_DM)이 더 높게 나타나는 음(-)의 편상관(r = -0.35 ~ -0.52)이 명확히 규명되어 거대 헤일로에 의한 소광(Halo Quenching)을 입증함.", bullet_style))
elements.append(Paragraph("• <b>말름퀴스트 편향 보정 (Panel B)</b>: 겉보기 밝기 한계 전체 표본(r = +0.34)과 달리, 부피 완전 표본(Volume-limited sample, log M* ≥ 10.3, 60 ≤ D ≤ 240 Mpc)으로 통제 시 거리-질량 상관계수가 r = +0.005 ≈ 0으로 소멸하여 거리 상관이 순수한 관측 편향임을 수학적으로 입증함.", bullet_style))
elements.append(Paragraph("• <b>비별생성률 직결성 (Panel C)</b>: 단순 log SFR은 항성 나이 지표 Dn4000과의 상관이 r = -0.06에 불과하지만, 비별생성률(-log sSFR)은 r = +0.78의 강력한 상관을 보여 은하 진화 지수의 핵심 축으로 반드시 sSFR을 써야 함을 증명함.", bullet_style))

# 6. 각 그래프별 상세 제작 방법론
elements.append(Spacer(1, 8))
elements.append(Paragraph("6. 연구 도표별 제작 방법론 (데이터 파이프라인 · 알고리즘)", h1_style))
method_text = (
    "<b>① 데이터 로드 및 정제</b>: SDSS DR18(5만 개), NED-LVS(145만 개), JWST CEERS(7.7만 개)의 FITS 및 CSV 원자료에서 "
    "거리 D > 0.05 Mpc, 유효반경 R > 0.1 kpc, 항성질량 10^7 ~ 10^12.5 M_sun, SFR 이상치 클리핑 제거 필터를 적용했습니다.<br/>"
    "<b>② Hexbin 밀도 및 구간별 중앙값(Binned Median)</b>: 수만 개의 중첩된 점을 효과적으로 분석하기 위해 45×45 육각형 격자 상용로그 밀도(log10 N)를 배경에 배치하고, "
    "x축을 14~16개 등간격 구간으로 나누어 각 구간 표본이 20개 이상인 경우 중앙값(Median, 빨간 실선)과 25%~75% 사분위 범위(IQR, 분홍 음영)를 계산하여 이상치에 흔들리지 않는 물리 법칙을 도출했습니다.<br/>"
    "<b>③ 통계량 산출</b>: SciPy를 통해 피어슨 선형 상관계수(r)와 스피어만 순위 상관계수(ρ), 그리고 로그 공간 1차 선형 회귀 기울기(y = ax + b, 멱법칙 지수)를 자동 도출했습니다."
)
elements.append(Paragraph(method_text, body_style))

# 7. 관측 은하 분석 프로그램(웹 2종) 사용 설명 및 파일 업로드 가이드
elements.append(Spacer(1, 8))
elements.append(Paragraph("7. 관측 은하 분석 웹 프로그램 2종 안내 & 파일 업로드 가이드", h1_style))
web_guide_text = (
    "<b>1) 천문대 관측 은하 진화 분석기 (observatory_analyzer_web.html)</b>:<br/>"
    "• 12종 대표 관측 은하 프리셋(M31, M33, M51, M81, M82, M87, M101, 우리은하 등) 원클릭 로드 및 수동 물리량 입력 지원.<br/>"
    "• <b>파일 업로드 지원</b>: 은하 사진(JPG, PNG, WebP, BMP) 업로드 시 표면밝기(R50, R90), 집중도(C), RGB 색비율을 자동 측광하여 M*, SFR, 반경, 색지수를 역산 후 GEI v2.0 분석 실행. 천문 FITS(.fits) 및 관측 표(CSV, JSON, TXT) 업로드 시 다중 은하 드롭다운 선택 기능 제공.<br/>"
    "• <b>출력</b>: GEI v2.0 점수 및 5단계 판정, 6대 KPI, 과거(-10 Gyr) 복원 및 미래(+10 Gyr) 소광 예측 카드, 3D 다중 카탈로그 인터랙티브 궤적, 시간대별 수치 표.<br/><br/>"
    "<b>2) 은하 사진 형태·Sérsic·BPT 분광 분석기 (galaxy_analyzer_web.html)</b>:<br/>"
    "• 고해상도 천체 사진 업로드 시 브라우저 멈춤 방지를 위해 400×400 표준 과학 그리드로 자동 정규화.<br/>"
    "• CAS 형태학(집중도 C, 비대칭도 A), Gini 계수, M20 모멘트, Sérsic 프로파일 지수(n) 자동 피팅, BPT 방출선 위상공간 투영."
)
elements.append(Paragraph(web_guide_text, body_style))

# 빌드 실행
doc.build(elements)
print(f"[완료] PDF 생성 완료: {OUTPUT_PDF}")
