# -*- coding: utf-8 -*-
"""
YSC 2026 은하 진화 연구 — 보정 방식 · 수식 · 통계 방법론 및 핵심 서술 사항 PDF 생성기
1) 은하진화연구_보정방식_수식_및_방법론_핵심정리.pdf
2) 은하진화연구_종합안내서_도표분석_및_물리개념.pdf
두 파일 모두 생성하고 다운로드 폴더에도 자동 복사합니다.
"""

import os
import shutil
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, HRFlowable, KeepTogether
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# 한글 폰트 등록 (맑은 고딕)
font_regular = "C:/Windows/Fonts/malgun.ttf"
font_bold = "C:/Windows/Fonts/malgunbd.ttf"
pdfmetrics.registerFont(TTFont("Malgun", font_regular))
pdfmetrics.registerFont(TTFont("MalgunBold", font_bold))

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_MAIN = os.path.join(BASE_DIR, "은하진화연구_보정방식_수식_및_방법론_핵심정리.pdf")
PDF_GUIDE = os.path.join(BASE_DIR, "은하진화연구_종합안내서_도표분석_및_물리개념.pdf")


def add_page_number(canvas, doc):
    """페이지 하단 쪽수 및 문서 제목 헤더/푸터 표시"""
    canvas.saveState()
    canvas.setFont("Malgun", 8)
    canvas.setFillColor(colors.HexColor("#64748b"))
    canvas.drawString(36, 22, "YSC 2026 은하 진화 연구 보고서 작성용 핵심 정리 문서 (보정 방식 · GEI v2.0 수식 · 통계 방법론)")
    canvas.drawRightString(A4[0] - 36, 22, f"- {doc.page} -")
    canvas.setStrokeColor(colors.HexColor("#e2e8f0"))
    canvas.setLineWidth(0.5)
    canvas.line(36, 34, A4[0] - 36, 34)
    canvas.restoreState()


def build_clean_pdf(output_path: str):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=38,
        bottomMargin=44
    )

    # 스타일 정의
    title_style = ParagraphStyle(
        "DocTitle",
        fontName="MalgunBold",
        fontSize=19,
        leading=25,
        textColor=colors.HexColor("#0f172a"),
        alignment=1,
        spaceAfter=4
    )

    subtitle_style = ParagraphStyle(
        "DocSubTitle",
        fontName="Malgun",
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor("#475569"),
        alignment=1,
        spaceAfter=10
    )

    h1_style = ParagraphStyle(
        "Heading1",
        fontName="MalgunBold",
        fontSize=12.5,
        leading=17,
        textColor=colors.HexColor("#0369a1"),
        spaceBefore=11,
        spaceAfter=5
    )

    h2_style = ParagraphStyle(
        "Heading2",
        fontName="MalgunBold",
        fontSize=10.0,
        leading=14,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=7,
        spaceAfter=3
    )

    body_style = ParagraphStyle(
        "Body",
        fontName="Malgun",
        fontSize=8.7,
        leading=13.4,
        textColor=colors.HexColor("#1e293b"),
        spaceAfter=5
    )

    bullet_style = ParagraphStyle(
        "Bullet",
        fontName="Malgun",
        fontSize=8.5,
        leading=13.0,
        textColor=colors.HexColor("#334155"),
        leftIndent=12,
        firstLineIndent=-8,
        spaceAfter=3
    )

    formula_style = ParagraphStyle(
        "Formula",
        fontName="MalgunBold",
        fontSize=8.8,
        leading=14.0,
        textColor=colors.HexColor("#0c4a6e"),
        alignment=0
    )

    th_style = ParagraphStyle(
        "TH",
        fontName="MalgunBold",
        fontSize=8.3,
        leading=11.5,
        textColor=colors.white,
        alignment=1
    )

    td_style = ParagraphStyle(
        "TD",
        fontName="Malgun",
        fontSize=8.0,
        leading=11.8,
        textColor=colors.HexColor("#0f172a")
    )

    td_center_style = ParagraphStyle(
        "TDCenter",
        fontName="MalgunBold",
        fontSize=8.0,
        leading=11.8,
        textColor=colors.HexColor("#0f172a"),
        alignment=1
    )

    def make_formula_box(html_text, bg="#f0f9ff", border="#0284c7"):
        tbl = Table([[Paragraph(html_text, formula_style)]], colWidths=[523])
        tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(bg)),
            ("BOX", (0, 0), (-1, -1), 1.0, colors.HexColor(border)),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]))
        return tbl

    def make_styled_table(data, col_widths, header_bg="#0f172a", stripe_bg="#f8fafc"):
        t = Table(data, colWidths=col_widths)
        style_cmds = [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(header_bg)),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]
        for r_idx in range(1, len(data)):
            if r_idx % 2 == 0:
                style_cmds.append(("BACKGROUND", (0, r_idx), (-1, r_idx), colors.HexColor(stripe_bg)))
        t.setStyle(TableStyle(style_cmds))
        return t

    elements = []

    # =========================================================================
    # 표지 타이틀
    # =========================================================================
    elements.append(Paragraph("🌌 은하 진화 연구: 보정 방식 · 수식 · 방법론 핵심 정리집", title_style))
    elements.append(Paragraph(
        "말름퀴스트 편향 보정 · GEI v2.0 수식 · 피어슨/스피어만 상관계수 · 이상치 클리핑 필터 · Hexbin 밀도 · CEERS 배제 사유 · 3D/2D 분석 · 직접 관측 환산식",
        subtitle_style
    ))
    elements.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#0284c7"), spaceAfter=8))

    # =========================================================================
    # 1. 말름퀴스트 편향(Malmquist Bias) 보정 방법 설명
    # =========================================================================
    elements.append(Paragraph("1. 말름퀴스트 관측 선택 편향(Malmquist Bias) 보정 방식", h1_style))
    elements.append(Paragraph(
        "거리(Distance)가 포함된 상관관계 도표(거리–항성질량, 거리–별생성률, 거리–암흑물질)에서 나타나는 양(+)의 상관관계(r = +0.16 ~ +0.34)는 "
        "실제 우주의 물리적 현상이 아니라 <b>망원경의 검출 플럭스 한계로 인해 발생하는 '말름퀴스트 관측 선택 편향(Malmquist Bias)'</b>입니다.",
        body_style
    ))

    elements.append(make_formula_box(
        "■ [말름퀴스트 편향의 수학적 유도]<br/>"
        "• 빛의 역제곱 법칙:  F = L / (4π D²)   (F: 관측 겉보기 플럭스, L: 은하 고유 광도, D: 관측 거리)<br/>"
        "• 망원경의 최소 검출 플럭스 한계가 F_lim 일 때, 거리 D에서 관측 가능한 최소 은하 광도 L_lim(D)는:<br/>"
        "  L_lim(D) = 4π D² · F_lim   ⇒   항성질량(M_* ∝ L) 환산 시:   log10 M_*,lim(D) = log10 M_*,0 + 2 · log10(D / D_0)<br/>"
        "• 즉, 거리가 멀어질수록 검출 하한선이 2·log10(D) 기울기로 상승하여 가벼운 왜소은하는 누락되고 무거운 은하만 표본에 남음."
    ))
    elements.append(Spacer(1, 5))

    malm_table = [
        [Paragraph("<b>보정 단계</b>", th_style), Paragraph("<b>적용 방법 및 수학적 조건</b>", th_style), Paragraph("<b>거리–질량 상관계수 결과</b>", th_style)],
        [
            Paragraph("<b>보정 전</b><br/>(겉보기 등급 제한 표본)", td_center_style),
            Paragraph("카탈로그 전체 은하(log10 M_* = 7.5 ~ 12.2, D = 0.5 ~ 300 Mpc)를 그대로 투영. 먼 거리에서 저질량 은하가 대거 누락됨.", td_style),
            Paragraph("<font color='#dc2626'><b>r = +0.34 (가짜 양의 상관)</b></font><br/>거리-암흑물질 r = +0.29", td_center_style)
        ],
        [
            Paragraph("<b>1단계 보정</b><br/>(완결 질량 한계선 산출)", td_center_style),
            Paragraph("최대 분석 거리 D_max = 240 Mpc에서도 100% 누락 없이 관측 가능한 <b>완결 질량 문턱값(Completeness Limit) log10(M_*/M_sun) ≥ 10.3</b>을 도출.", td_style),
            Paragraph("검출 한계 경계선<br/>log M_*,lim(D) 규명", td_center_style)
        ],
        [
            Paragraph("<b>2단계 보정</b><br/>(부피 완전 표본 추출)", td_center_style),
            Paragraph("<b>log10(M_*/M_sun) ≥ 10.3</b> 이고 <b>60 ≤ D ≤ 240 Mpc</b>인 <b>부피 완전 표본(Volume-Limited Complete Subsample)</b>만 추출하여 재검증.", td_style),
            Paragraph("<font color='#059669'><b>r = +0.005 ≈ 0 (상관 소멸)</b></font><br/>순수 관측 편향임이 증명됨", td_center_style)
        ],
        [
            Paragraph("<b>3단계 반영</b><br/>(GEI 지수 설계 원칙)", td_center_style),
            Paragraph("거리(D)가 포함된 3개 도표는 <b>[3등급: 사용 금지]</b>로 분류하고, 은하 진화 지수(GEI v2.0) 수식에서 거리 의존 항을 100% 배제함.", td_style),
            Paragraph("<font color='#0369a1'><b>거리 무관 고유 진화도 달성</b></font>", td_center_style)
        ]
    ]
    elements.append(make_styled_table(malm_table, [105, 295, 123]))

    # =========================================================================
    # 2. 차세대 5축 통합 은하 진화 지수 (Unified GEI v2.0) 수식 정리
    # =========================================================================
    elements.append(Paragraph("2. 차세대 5축 통합 은하 진화 지수 (Unified GEI v2.0) 전체 수식", h1_style))
    elements.append(Paragraph(
        "은하의 진화 상태를 단일 변수(색지수 또는 별생성률 하나)로만 평가할 때 생기는 축퇴(Degeneracy)를 해결하기 위해, "
        "관측 거리 편향이 제거된 <b>5대 핵심 물리 축을 [0, 1] 구간으로 정규화(clip(x,0,1) = min(max(x,0),1))하여 가중 합산</b>한 지수입니다.",
        body_style
    ))

    elements.append(make_formula_box(
        "■ [통합 은하 진화 지수 (Unified GEI v2.0) 마스터 방정식]<br/>"
        "GEI_v2 = 0.30 · S_quench  +  0.25 · S_mass  +  0.20 · S_pop  +  0.15 · S_struct  +  0.10 · S_halo     (0.000 ≤ GEI_v2 ≤ 1.000)<br/>"
        "• 100점 만점 환산 지수:   GEI_100 = 100 × GEI_v2   [점]"
    ))
    elements.append(Spacer(1, 5))

    gei_axes_table = [
        [
            Paragraph("<b>물리 축 (가중치)</b>", th_style),
            Paragraph("<b>정규화 수식 (0.000 ~ 1.000)</b>", th_style),
            Paragraph("<b>입력 물리량 및 천체물리학적 의미</b>", th_style)
        ],
        [
            Paragraph("<b>① 별생성 소광</b><br/>S_quench (30%)", td_center_style),
            Paragraph("<b>S_quench = clip( (-log10(sSFR) - 8.5) / 4.0, 0, 1 )</b><br/>단, sSFR = SFR / M_* [yr^-1]", td_style),
            Paragraph("단위 항성질량당 별생성률(sSFR)의 감소(=가스 고갈 및 소광 진행도). 폭발적 별생성(-8.5)일 때 0, 완전 소광(-12.5)일 때 1.", td_style)
        ],
        [
            Paragraph("<b>② 항성질량 성숙</b><br/>S_mass (25%)", td_center_style),
            Paragraph("<b>S_mass = clip( (log10(M_*/M_sun) - 8.0) / 3.8, 0, 1 )</b>", td_style),
            Paragraph("우주 역사 동안 축적된 누적 별 질량(Downsizing 성숙도). 왜소은하(10^8 M_sun)일 때 0, 거대 타원은하(10^11.8 M_sun)일 때 1.", td_style)
        ],
        [
            Paragraph("<b>③ 항성종족 노화</b><br/>S_pop (20%)", td_center_style),
            Paragraph("<b>S_pop = 0.45·S_color + 0.35·S_D4000 + 0.20·S_metal</b><br/>"
                      "• S_color = clip(((u-r) - 1.0)/1.8, 0, 1)<br/>"
                      "• S_D4000 = clip((Dn4000 - 1.05)/1.05, 0, 1)<br/>"
                      "• S_metal = clip(((12+log O/H) - 8.0)/1.1, 0, 1)", td_style),
            Paragraph("광학 색지수(u-r 적색화), 4000Å 스펙트럼 불연속면(Dn4000 항성 연령), 성간 금속함량(12+log O/H 화학적 농축)을 통합 평가.", td_style)
        ],
        [
            Paragraph("<b>④ 구조적 밀집도</b><br/>S_struct (15%)", td_center_style),
            Paragraph("<b>S_struct = clip( (log10(Σ_*) - 7.0) / 2.8, 0, 1 )</b><br/>단, Σ_* = M_* / (2π R_e²) [M_sun/kpc²]", td_style),
            Paragraph("유효반경(R_e) 내 항성 표면질량밀도(Σ_*). 바리온 가스의 복사 냉각 수축 및 중심 팽대부(Bulge) 성장도를 정량화.", td_style)
        ],
        [
            Paragraph("<b>⑤ 암흑물질 헤일로</b><br/>S_halo (10%)", td_center_style),
            Paragraph("<b>S_halo = 0.55·S_Mdyn + 0.45·S_fDM</b><br/>"
                      "• S_Mdyn = clip((log10 M_dyn - 9.5)/3.0, 0, 1)<br/>"
                      "• S_fDM = clip((f_DM - 0.15)/0.75, 0, 1)", td_style),
            Paragraph("동역학 질량(M_dyn = V_rot² R_e / G)과 암흑물질 분율(f_DM = (M_dyn - M_bar)/M_dyn). 거대 헤일로 성숙 및 가열 소광 잠재력.", td_style)
        ]
    ]
    elements.append(make_styled_table(gei_axes_table, [88, 220, 215]))
    elements.append(Spacer(1, 5))

    stage_table = [
        [Paragraph("<b>진화 단계</b>", th_style), Paragraph("<b>GEI v2.0 범위</b>", th_style), Paragraph("<b>단계 명칭 및 대표 형태</b>", th_style), Paragraph("<b>물리적 특징 및 대표 은하 예시</b>", th_style)],
        [Paragraph("<b>Stage I</b>", td_center_style), Paragraph("0.00 ~ 0.28", td_center_style), Paragraph("원시 폭발적 별생성기 (Irr / Blue Compact)", td_style), Paragraph("가스 분율 높음, 매우 푸른 색지수(u-r<1.4), 높은 sSFR (예: M82 초기, 왜소 불규칙은하)", td_style)],
        [Paragraph("<b>Stage II</b>", td_center_style), Paragraph("0.28 ~ 0.46", td_center_style), Paragraph("초기 주계열 원반 성장기 (Sc / Sd)", td_style), Paragraph("나선팔 원반 확장, 활발한 별생성 주계열 상단 위치 (예: M33, NGC 2403)", td_style)],
        [Paragraph("<b>Stage III</b>", td_center_style), Paragraph("0.46 ~ 0.64", td_center_style), Paragraph("성숙 주계열 나선 안정기 (Sb / Sbc)", td_style), Paragraph("원반과 팽대부 공존, 별생성률과 가스 유입의 평형 상태 (예: 우리은하, M51, M101)", td_style)],
        [Paragraph("<b>Stage IV</b>", td_center_style), Paragraph("0.64 ~ 0.78", td_center_style), Paragraph("녹색 계곡 전이·감쇠기 (Sa / S0)", td_style), Paragraph("찬 가스 고갈 시작, 중심부 팽대부 비대화, 별생성 급감 (예: M31 안드로메다, M81)", td_style)],
        [Paragraph("<b>Stage V</b>", td_center_style), Paragraph("0.78 ~ 1.00", td_center_style), Paragraph("완전 소광 거대 타원은하 (E / cD)", td_style), Paragraph("별생성 완전 정지(log sSFR<-11.5), 거대 암흑물질 헤일로 및 적색 계열 (예: M87)", td_style)],
    ]
    elements.append(make_styled_table(stage_table, [58, 68, 162, 235]))

    elements.append(PageBreak())

    # =========================================================================
    # 3. 피어슨 선형 상관계수(r) vs 스피어만 순위 상관계수(ρ) 설명
    # =========================================================================
    elements.append(Paragraph("3. 통계량 산출: 피어슨 선형 상관계수(r)와 스피어만 순위 상관계수(ρ) 비교", h1_style))
    elements.append(Paragraph(
        "은하 물리량 간의 관계를 분석할 때 피어슨 상관계수(r) 하나만 사용하면, 소수의 이상치(Outlier)나 비선형 진화 경로(소광 은하 분리 현상) 때문에 "
        "물리적 상관성을 오판할 수 있습니다. 이를 방지하기 위해 본 연구는 <b>피어슨(r)과 스피어만(ρ) 상관계수를 동시에 산출</b>했습니다.",
        body_style
    ))

    corr_table = [
        [Paragraph("<b>구분</b>", th_style), Paragraph("<b>피어슨 선형 상관계수 (Pearson r)</b>", th_style), Paragraph("<b>스피어만 순위 상관계수 (Spearman ρ)</b>", th_style)],
        [
            Paragraph("<b>수학적 정의식</b>", td_center_style),
            Paragraph("<b>r = Σ(x_i - x̄)(y_i - ȳ) / √[Σ(x_i - x̄)² Σ(y_i - ȳ)²]</b><br/>(상용로그 변환된 실제 물리량 수치 x_i, y_i를 직접 사용)", td_style),
            Paragraph("<b>ρ = 1 - [6 Σ d_i²] / [N(N² - 1)]</b>   (단, d_i = Rank(x_i) - Rank(y_i))<br/>(실제 값 대신 크기 순서대로 매긴 '순위 Rank'만 사용)", td_style)
        ],
        [
            Paragraph("<b>측정하는 물리적 의미</b>", td_center_style),
            Paragraph("로그 공간에서의 <b>'직선 비례성(Linearity)'</b> 측정.<br/>즉, 두 물리량이 단일 멱법칙(Y ∝ X^a) 직선을 얼마나 잘 따르는지 평가.", td_style),
            Paragraph("모양에 구애받지 않는 <b>'단조 증감 경향성(Monotonicity)'</b> 측정.<br/>관계가 곡선으로 휘어져도 X가 커질 때 Y가 커지는지 평가.", td_style)
        ],
        [
            Paragraph("<b>이상치(Outlier) 민감도</b>", td_center_style),
            Paragraph("<b>매우 민감함 (취약)</b>: 극단적인 이상치 몇 개만 있어도 제곱합이 폭증하여 r값이 크게 깎이거나 왜곡됨.", td_style),
            Paragraph("<b>매우 강건함 (Robust)</b>: 극단적 이상치도 단지 '1등' 또는 '꼴찌' 순위로만 취급되므로 상관계수가 흔들리지 않음.", td_style)
        ],
        [
            Paragraph("<b>본 연구에서의 진단 활용</b>", td_center_style),
            Paragraph("• <b>질량–광도(M* - L)</b>: r = 0.96, ρ = 0.96으로 일치 → 이상치 없는 완벽한 선형 멱법칙 입증.", td_style),
            Paragraph("• <b>질량–별생성률(M* - SFR)</b>: 고질량 영역에서 소광 은하들이 아래로 갈라지며 r과 ρ의 차이 발생 → <b>이원화(Bimodality) 구조 진단</b>.", td_style)
        ]
    ]
    elements.append(make_styled_table(corr_table, [88, 217, 218]))

    # =========================================================================
    # 4. 이상치 및 파이프라인 클리핑 제거 필터 (Outlier & Clipping Filter)
    # =========================================================================
    elements.append(Paragraph("4. 이상치 및 파이프라인 클리핑 제거 필터 (Outlier & Clipping Filter) 적용 방법", h1_style))
    elements.append(Paragraph(
        "초기 8개 상관관계 그래프에서 발견된 비물리적 아티팩트(선형/로그 축 혼동, 바닥 끌림, 상·하단 수평 줄무늬, 거리=0 수직선)를 제거하기 위해 "
        "데이터 전처리 파이프라인(verify_and_fix_8panel_ned_sdss.py)에 <b>4단계 정밀 클리핑·이상치 제거 필터</b>를 적용했습니다.",
        body_style
    ))

    filter_table = [
        [Paragraph("<b>필터 단계</b>", th_style), Paragraph("<b>제거 대상 아티팩트 (초기 그래프 문제점)</b>", th_style), Paragraph("<b>적용한 수학적 필터 조건 및 해결 원리</b>", th_style)],
        [
            Paragraph("<b>1단계: 거리 결측 필터</b>", td_center_style),
            Paragraph("적색편이 미측정 은하가 D = 0 Mpc로 기록되어 거리 그래프 좌측 끝에 수직 점선이 생성됨.", td_style),
            Paragraph("<b>0.5 &lt; D [Mpc] &lt; 350.0</b> 및 유한값(isfinite) 조건 적용 → 비물리적 거리 결측치 100% 제거.", td_style)
        ],
        [
            Paragraph("<b>2단계: SFR 파이프라인 클리핑 제거</b>", td_center_style),
            Paragraph("• NED에서 SFR ≤ 0 은하가 중앙값 선을 바닥(0)으로 끌어내림.<br/>• SDSS MPA-JHU 파이프라인의 격자 상·하한(log SFR = ±4.0)에 점들이 수평 일직선으로 쌓임.", td_style),
            Paragraph("<b>-3.8 &lt; log10(SFR [M_sun/yr]) &lt; +3.5</b> 필터 적용 → 상·하한 그리드 클리핑 경계값 및 SFR=0 결측 아티팩트 완전 제거.", td_style)
        ],
        [
            Paragraph("<b>3단계: 질량·헤일로 물리 범위 필터</b>", td_center_style),
            Paragraph("구상성단/왜소 노이즈 및 은하단 전체 중력 퍼텐셜이 섞인 초거대 cD 은하의 비정상 암흑물질 질량.", td_style),
            Paragraph("<b>7.5 &lt; log10(M_*/M_sun) &lt; 12.2</b> 및 <b>8.5 &lt; log10(M_DM/M_sun) &lt; 13.8</b>, 유효반경 <b>R_e &gt; 0.1 kpc</b> 적용.", td_style)
        ],
        [
            Paragraph("<b>4단계: 구간 표본수 문턱값 (N_bin ≥ 20)</b>", td_center_style),
            Paragraph("x축 양 끝단에서 은하가 1~3개뿐인 구간의 이상치 때문에 빨간 중앙값 선이 급격히 꺾임.", td_style),
            Paragraph("x축을 14개 등간격 구간으로 나눈 뒤, <b>구간 내 은하 수 N ≥ 20개 이상인 구간만 중앙값(Median)과 사분위수(IQR) 산출</b>.", td_style)
        ]
    ]
    elements.append(make_styled_table(filter_table, [95, 205, 223]))

    # =========================================================================
    # 5. Hexbin 밀도(육각형 격자 상용로그 밀도) 설명 및 사용 이유
    # =========================================================================
    elements.append(Paragraph("5. Hexbin 밀도(log10 N)의 개념과 일반 산점도 대신 사용한 이유", h1_style))
    elements.append(Paragraph(
        "• <b>Hexbin(육각형 격자 밀도)이란?</b>: 2차원 그래프 평면을 <b>45×45개의 정육각형(Hexagon) 타일</b>로 촘촘하게 분할한 뒤, 각 육각형 안에 들어가는 "
        "은하의 개수(N)를 세어 <b>상용로그 척도(log10 N)</b>로 색상을 입히는 2차원 확률밀도 시각화 기법입니다.<br/>"
        "• <b>왜 일반 점 그래프(Scatter Plot) 대신 사용했는가?</b>:<br/>"
        "  1) <b>과밀 중첩 포화(Overplotting Saturation) 해결</b>: 은하가 14,000~50,000개에 달하면 일반 점 그래프에서는 중심부에 수천 개의 점이 겹쳐 찍혀 "
        "은하가 20개 모인 곳과 5,000개 모인 곳을 전혀 구분할 수 없습니다.<br/>"
        "  2) <b>정육각형의 기하학적 등방성(Isotropy)</b>: 사각형 격자(2D 히스토그램)는 대각선 거리가 가로·세로보다 √2배 길어 대각선 방향의 은하 주계열(Main Sequence)을 "
        "계단 모양으로 왜곡하지만, 정육각형은 6방향 인접 중심 거리가 모두 같아 방향 왜곡이 없습니다.<br/>"
        "  3) <b>상용로그(log10 N) 색상의 1,000배 동적 범위 표현</b>: 선형 개수(N)로 칠하면 가장 밀집된 중심부 1~2칸만 진하게 보이고 나머지는 전부 흐려집니다. "
        "반면 <b>log10 N</b>을 쓰면 1개(log N=0)인 외곽 전이 영역부터 1,000개(log N=3)가 밀집한 '별생성 주계열 능선'과 '소광 은하 군집'을 동시에 선명하게 판독할 수 있습니다.",
        body_style
    ))

    elements.append(PageBreak())

    # =========================================================================
    # 6. JWST CEERS 자료를 제외한 이유 설명
    # =========================================================================
    elements.append(Paragraph("6. JWST CEERS 자료를 천문대 관측 기준 및 8대 상관 분석에서 제외한 이유", h1_style))
    elements.append(Paragraph(
        "초기 우주 적외선 탐사 자료인 <b>JWST CEERS (적색편이 z = 0.5 ~ 10, 우주 초기 5억~80억 년 전)</b>를 본 연구의 국소 우주 상관관계 분석 및 "
        "우리 팀 천문대 관측 은하 판별 기준 배경(Reference Cloud)에서 제외한 과학적 이유는 다음 3가지입니다.",
        body_style
    ))

    ceers_table = [
        [Paragraph("<b>배제 사유 핵심 항목</b>", th_style), Paragraph("<b>천체물리학적·관측적 상세 근거</b>", th_style)],
        [
            Paragraph("<b>① 우주 시대(Cosmic Epoch)<br/>불일치 및 교란 방지</b>", td_center_style),
            Paragraph("NED-LVS와 SDSS는 적색편이 z &lt; 0.1(최근 10억 년 이내)의 <b>현대 국소 우주 은하</b>인 반면, CEERS는 z = 0.5 ~ 10의 <b>극초기 원시 우주 은하</b>입니다. 초기 우주는 우주 평균 가스 밀도와 별생성률이 지금보다 10~30배 이상 높았기 때문에, 이를 한 그래프에 섞으면 <b>'은하 개체의 진화 단계'와 '우주 배경 시대의 차이'가 뒤섞이는 교란(Confounding)</b>이 발생합니다.", td_style)
        ],
        [
            Paragraph("<b>② 관측 파장대 이질성 및<br/>회전속도(V_rot) 측정치 부재</b>", td_center_style),
            Paragraph("SDSS와 NED는 광학 분광 및 HI 전파 관측을 통해 회전속도(V_rot), Dn4000, 방출선 플럭스를 직접 측정하지만, CEERS는 적외선 광대역 측광(SED 피팅)에만 의존하므로 <b>직접 측정된 회전속도(V_rot)와 동역학적 암흑물질 질량(M_DM)이 존재하지 않아</b> 동일한 물리 기준으로 비교할 수 없습니다.", td_style)
        ],
        [
            Paragraph("<b>③ 지상 천문대 직접 관측<br/>가능 범위와의 정합성</b>", td_center_style),
            Paragraph("우리 연구팀이 학교 및 지역 천문대의 광학 망원경과 CCD 카메라로 직접 관측할 수 있는 은하는 100% 국소 우주(D &lt; 100 Mpc) 은하입니다. 따라서 우리 팀이 관측한 은하를 판별하는 기준 배경 역시 동일한 국소 우주 표본인 <b>NED-LVS + SDSS DR18</b>로만 구성해야 과학적 정합성이 성립합니다.", td_style)
        ]
    ]
    elements.append(make_styled_table(ceers_table, [125, 398]))

    # =========================================================================
    # 7. 3차원 도표를 단독 정적 이미지로 쓰지 않고 2D 질량 통제 + 대화형 3D로 결합한 이유
    # =========================================================================
    elements.append(Paragraph("7. 3차원 도표의 한계와 본 연구의 해결책 (2D 질량 통제 편상관 + 대화형 3D 결합)", h1_style))
    elements.append(Paragraph(
        "• <b>정적(고정된 2차원 종이) 3차원 도표의 한계 — 시선 방향 투영 착시(Projection Degeneracy)</b>:<br/>"
        "  3차원 공간(X, Y, Z)의 점들을 고정된 각도에서 2차원 화면에 투영하면, 시선 방향(Line-of-Sight) 앞뒤에 놓인 서로 다른 질량·암흑물질의 은하들이 "
        "한 점에 겹쳐 보이는 착시가 발생하며, 정확한 상관계수(r, ρ)와 중앙값 오차 범위를 정량적으로 읽을 수 없습니다.<br/>"
        "• <b>본 연구의 이중 해결책</b>:<br/>"
        "  1) <b>엄밀한 물리 법칙 증명에는 '2D 질량 통제 편상관 분석(Mass-Controlled Partial Correlation)' 적용</b>: 제3변수인 항성질량(log M_*)을 좁은 구간으로 고정하여 "
        "체급 착시를 완벽히 제거한 상태에서 주계열 편차(ΔMS)와 암흑물질 분율(f_DM)의 순수 음(-)의 상관관계(r = -0.35 ~ -0.52)를 입증했습니다.<br/>"
        "  2) <b>입체적 구조 탐색에는 'WebGL 대화형 3D 다양체(4종 모드)' 적극 활용</b>: 웹 분석기(observatory_analyzer_web.html)에 "
        "① <b>log M_* – log SFR – log M_DM [ΔMS 분석]</b>, ② <b>log M_* – log sSFR – f_DM</b>, ③ <b>log M_* – log R_e – f_DM</b>, ④ <b>log M_* – log V_rot – log R_e</b>의 "
        "4가지 3차원 모드를 탑재하여 마우스로 360° 회전하며 우리 팀 관측 은하의 입체 궤적을 확인하도록 구현했습니다.",
        body_style
    ))

    # =========================================================================
    # 8. 우리 팀 직접 관측 은하 입력 프로그램 및 원시 관측값 자동 환산 공식
    # =========================================================================
    elements.append(Paragraph("8. 우리 팀 직접 관측 은하 입력 프로그램 설계 및 원시 관측값 환산 공식", h1_style))
    elements.append(Paragraph(
        "기존에 우리가 관측하지 않은 문헌 카탈로그 은하 12종을 프리셋으로 전면에 두었던 방식을 폐기하고, "
        "<b>우리 팀이 천문대 망원경과 CCD로 직접 측정한 원시 관측값을 입력하면 물리량으로 자동 환산하여 진화 단계를 판별하고 [우리 팀 관측 일지]에 기록하는 프로그램</b>으로 전면 개편했습니다.",
        body_style
    ))

    elements.append(make_formula_box(
        "■ [천문대 망원경·CCD 원시 관측값 → 은하 물리량 자동 환산 수식]<br/>"
        "① 분광 후퇴속도 v_r [km/s] → 관측 거리 D [Mpc] (허블 법칙, H_0 = 70 km/s/Mpc):    D = v_r / H_0<br/>"
        "② CCD 겉보기 등급 m_r [mag] → 절대등급 M_r 및 광도 L_r (거리 지수 공식):    M_r = m_r - 5·log10(D [pc] / 10),   log10(L_r/L_sun) = -0.4·(M_r - 4.64)<br/>"
        "③ 색지수 (u - r) 기반 질량 대 광도비(Bell et al.) → 항성질량 M_*:    log10(M_*/L_r) = -0.306 + 0.55·(u - r) - 0.15   ⇒   log10 M_* = log10 L_r + log10(M_*/L_r)<br/>"
        "④ 사진 반빛 각반경 θ_e [arcsec] → 물리적 반경 R_e [kpc] (소각 근사 삼각법):    R_e [kpc] = D [Mpc] × 1000 × (θ_e [arcsec] / 206,265)"
    ))

    # =========================================================================
    # 9. 핵심 4대 천체물리 개념 및 GEI 도표 3단계 적합성 분류
    # =========================================================================
    elements.append(Paragraph("9. 핵심 4대 천체물리 개념 요약 및 GEI 도표 3단계 적합성 분류", h1_style))
    concept_table = [
        [Paragraph("<b>핵심 개념</b>", th_style), Paragraph("<b>정의 수식</b>", th_style), Paragraph("<b>은하 진화 연구에서의 핵심 물리적 의미</b>", th_style)],
        [Paragraph("<b>바리온 (Baryon)</b>", td_center_style), Paragraph("M_bar = M_* + M_gas", td_center_style), Paragraph("빛을 방출하며 복사 냉각(Radiative Cooling)을 통해 은하 중심 수 kpc 이내로 수축하여 별을 만드는 일반 물질(우주 물질의 15.7%). 중심부는 바리온, 외곽 헤일로는 암흑물질(84.3%)이 지배함.", td_style)],
        [Paragraph("<b>물리적 반경 (R_e)</b>", td_center_style), Paragraph("R_kpc = D · θ / 206.265", td_center_style), Paragraph("겉보기 각크기(arcsec)에 거리 D를 곱해 구한 실제 반경[kpc]. 항성 표면밀도(Σ_* = M_*/2πR_e²)와 동역학 총질량(M_dyn = V_rot² R_e / G)을 산출하는 필수 기준 척도.", td_style)],
        [Paragraph("<b>비별 생성률 (sSFR)</b>", td_center_style), Paragraph("sSFR = SFR / M_* [yr^-1]", td_center_style), Paragraph("단순 SFR의 은하 체급(크기) 착시를 제거한 '단위 항성질량당 별생성률'. 역수(1/sSFR)는 질량 배가 시간이며, 주계열(>-10.2)·녹색계곡·완전소광(<-11.2)을 가르는 제1 지표.", td_style)],
        [Paragraph("<b>도표 3단계 분류</b>", td_center_style), Paragraph("1등급 / 2등급 / 3등급", td_center_style), Paragraph("• <b>1등급(즉시 채택)</b>: M*-sSFR, M*-색지수, M*-Dn4000, Σ*-f_DM, M*-M_DM, M*-L<br/>• <b>2등급(검증/변환 후 사용)</b>: 단순 M*-SFR(→sSFR 변환), SFR-M_DM(→질량 통제), BPT<br/>• <b>3등급(절대 금지)</b>: 거리(D)가 포함된 모든 도표(말름퀴스트 편향)", td_style)]
    ]
    elements.append(make_styled_table(concept_table, [85, 110, 328]))

    # =========================================================================
    # 10. 시각 검증 도표 부록 (발표차트 5 & 발표차트 6)
    # =========================================================================
    elements.append(PageBreak())
    elements.append(Paragraph("10. [부록] 8대 상관관계 오류 수정 및 말름퀴스트·질량통제 심화 검증 도표", h1_style))
    chart5_img = os.path.join(BASE_DIR, "output", "presentation_charts", "발표차트5_8대그래프_오류수정_NED_SDSS_비교_및_GEI도표선별.png")
    if os.path.exists(chart5_img):
        elements.append(Image(chart5_img, width=515, height=282))
        elements.append(Spacer(1, 8))

    chart6_img = os.path.join(BASE_DIR, "output", "presentation_charts", "발표차트6_심화검증_질량통제_거리편향보정_도표적합성분류.png")
    if os.path.exists(chart6_img):
        elements.append(Image(chart6_img, width=515, height=302))

    doc.build(elements, onFirstPage=add_page_number, onLaterPages=add_page_number)
    print(f"[완료] PDF 생성 완료: {output_path}")


if __name__ == "__main__":
    build_clean_pdf(PDF_MAIN)
    shutil.copy2(PDF_MAIN, PDF_GUIDE)
    print(f"[완료] 안내서 PDF 동기화 완료: {PDF_GUIDE}")

    downloads_dir = r"C:\Users\neato\Downloads"
    if os.path.exists(downloads_dir):
        for p in [PDF_MAIN, PDF_GUIDE]:
            dst = os.path.join(downloads_dir, os.path.basename(p))
            shutil.copy2(p, dst)
            print(f"[완료] 다운로드 폴더 복사 완료: {dst}")
