import os
import re
import html as _html
import datetime


class ReportGenerator:
    """분석 결과 종합 보고서 자동 생성기"""

    def __init__(self, output_dir: str = None):
        """Set output directory for reports."""
        self.output_dir = output_dir or os.path.join(os.getcwd(), 'output', 'reports')
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir, exist_ok=True)

    # ── 유틸 ─────────────────────────────────────────────
    @staticmethod
    def _safe_format(value, format_str="{:.2f}", default="-"):
        """안전한 값 포맷팅 (None/NaN/inf → default)"""
        if value is None:
            return default
        try:
            f = float(value)
            if f != f or f in (float('inf'), float('-inf')):
                return default
            return format_str.format(f)
        except (ValueError, TypeError):
            return str(value)

    @staticmethod
    def _pct(value):
        """0–1 또는 0–100 스케일 모두 허용 → '85.0%'"""
        if value is None:
            return "N/A"
        try:
            v = float(value)
        except (TypeError, ValueError):
            return "N/A"
        if v <= 1.0:
            v *= 100.0
        return "%.1f%%" % v

    @staticmethod
    def _bpt_interpretation(bpt_class, bpt_class_en=None):
        key = (bpt_class_en or bpt_class or '').lower()
        if 'seyfert' in key or '세이퍼트' in key or key == 'agn':
            return "활동은하핵(AGN, 세이퍼트) 특성이 강합니다. 중심 초대질량 블랙홀 강착원반의 강한 전리 복사가 [OIII] 방출을 증폭시킵니다."
        if 'composite' in key or '복합' in key:
            return "별 탄생과 AGN 활동이 혼합된 복합(Composite) 특성을 보입니다. 퀜칭이 진행 중인 전이 단계일 가능성이 있습니다."
        if 'liner' in key:
            return "저전리 핵방출선 영역(LINER)으로 분류됩니다. 늙은 항성종족(post-AGB)이나 약한 AGN에 의한 전리일 수 있습니다."
        if 'star' in key or '별생성' in key or key == 'sf':
            return "젊고 무거운 O/B형 별이 주변 가스를 전리시키는 일반적인 별 탄생(HII) 은하입니다."
        return "방출선 비가 부족하여 BPT 분류를 확정할 수 없습니다."

    # ── Markdown ─────────────────────────────────────────
    def generate_markdown(self, analysis_results: dict) -> str:
        """분석 결과를 Markdown 문자열로 변환.

        주요 키: target_name, analysis_datetime, input_mode, emission_lines(dict) 또는 line_table(list[dict]),
        ebv, log_sfr, metallicity, metallicity_method, bpt_class(_en), log_nii_ha, log_oiii_hb,
        predicted_type, confidence, top_3_types, evolution_cluster, gei_score, evolution_stage,
        log_mass, color_ur, z
        선택 키: morphology(dict), photometry(dict), percentiles(list[dict]), sfms(dict),
        similar_vote(dict), sii_bpt_class, electron_density, d4000, notes(list[str])
        """
        a = analysis_results or {}
        target = a.get('target_name', 'Unknown Target')
        now_str = a.get('analysis_datetime', datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        mode = a.get('input_mode', '미상')
        f = self._safe_format

        # 방출선 표
        line_rows = []
        if a.get('line_table'):
            for r in a['line_table']:
                line_rows.append("| %s | %s | %s | %s | %s |" % (
                    r.get('선', r.get('key', '-')), f(r.get('정지파장(Å)'), "{:.2f}"),
                    f(r.get('적분플럭스'), "{:.4g}"), f(r.get('S/N'), "{:.1f}"), f(r.get('EW(Å)'), "{:.2f}")))
        else:
            for line, flux in (a.get('emission_lines') or {}).items():
                ok = flux is not None and flux > 0
                line_rows.append("| %s | - | %s | %s | - |" % (line, f(flux, "{:.4g}") if ok else "미검출",
                                                               "-" if not ok else "검출"))
        if not line_rows:
            line_rows.append("| 입력 없음 | - | - | - | - |")
        line_table = "\n".join(line_rows)

        bpt_class = a.get('bpt_class', '미상')
        bpt_interp = self._bpt_interpretation(bpt_class, a.get('bpt_class_en'))

        # AI
        pred_type = a.get('predicted_type', '미분류')
        conf_str = self._pct(a.get('confidence'))
        top3 = a.get('top_3_types') or []
        top3_lines = ["  %d. %s (%s)" % (i + 1, t, self._pct(p)) for i, (t, p) in enumerate(top3[:3])]
        top3_str = "\n".join(top3_lines) if top3_lines else "  - 데이터 없음"
        cov = a.get('feature_coverage')
        cov_str = ""
        if cov is not None:
            cov_str = "\n- **입력 특성 커버리지(중요도 가중)**: %s — 낮을수록 예측 불확실" % self._pct(cov)

        # 진화
        cluster = a.get('evolution_cluster', '미상')
        gei = a.get('gei_score')
        stage = a.get('evolution_stage', '미상')
        evo_interp = "현재 데이터(질량·색·SFR·금속량 중 일부 누락)로는 GEI를 산출할 수 없습니다."
        if gei is not None:
            if gei < 30:
                evo_interp = "활발한 별 생성 단계로, 풍부한 가스를 바탕으로 성장 중인 젊은 은하입니다 (Blue Cloud)."
            elif gei < 65:
                evo_interp = "별 생성률이 감소하는 전이기 은하로 추정됩니다 (Green Valley)."
            else:
                evo_interp = "가스가 대부분 고갈되어 별 생성이 거의 멈춘 성숙한 은하입니다 (Red Sequence)."

        md = []
        md.append("# 🌌 천체 분석 보고서\n")
        md.append("## 1. 분석 개요")
        md.append("- **분석 일시**: %s" % now_str)
        md.append("- **입력 방식**: %s" % mode)
        md.append("- **대상 천체**: %s" % target)
        if a.get('roi_description'):
            md.append("- **선택 영역**: %s" % a['roi_description'])
        md.append("")

        # 형태/측광 (이미지 모드)
        morph = a.get('morphology')
        phot = a.get('photometry')
        sec = 2
        if morph or phot:
            md.append("## %d. 영역 측광 · 형태 분석" % sec)
            sec += 1
            if phot:
                md.append("| 항목 | 값 |")
                md.append("|------|----|")
                for k, v in phot.items():
                    md.append("| %s | %s |" % (k, v))
                md.append("")
            if morph:
                md.append("- **형태 판정**: **%s** (%s)" % (morph.get('class', '-'), morph.get('class_en', '-')))
                for r in morph.get('reasons', [])[:8]:
                    md.append("  - %s" % r)
            md.append("")

        md.append("## %d. 분광 분석 결과" % sec)
        sec += 1
        md.append("| 방출선 | 정지파장 (Å) | 적분 플럭스 | S/N | EW (Å) |")
        md.append("|--------|-------------|-------------|-----|--------|")
        md.append(line_table)
        if a.get('d4000') is not None:
            md.append("\n- **D4000 (4000Å 단절 지수)**: %s — 1.5 이상이면 늙은 항성종족 우세" % f(a.get('d4000')))
        md.append("")

        md.append("## %d. 물리량 추출 결과" % sec)
        sec += 1
        md.append("- **성간 소광량 E(B−V)**: %s mag" % f(a.get('ebv'), "{:.3f}"))
        md.append("- **별 생성률 log SFR**: %s (M☉/yr)" % f(a.get('log_sfr')))
        md.append("- **금속량 12+log(O/H)**: %s (%s)" % (f(a.get('metallicity'), "{:.3f}"), a.get('metallicity_method', 'N/A')))
        if a.get('electron_density') is not None:
            md.append("- **전자밀도 n_e ([SII])**: %s cm⁻³" % f(a.get('electron_density'), "{:.0f}"))
        md.append("- **항성 질량 log M★**: %s (M☉)" % f(a.get('log_mass')))
        md.append("- **색지수 u−r**: %s" % f(a.get('color_ur')))
        md.append("- **적색편이 z**: %s" % f(a.get('z'), "{:.4f}"))
        md.append("")

        md.append("## %d. BPT 진단 분류" % sec)
        sec += 1
        md.append("- **[NII]-BPT 분류**: **%s**" % bpt_class)
        if a.get('sii_bpt_class'):
            md.append("- **[SII]-BPT 분류 (Kewley 2006)**: %s" % a['sii_bpt_class'])
        md.append("- **log([NII]/Hα)**: %s" % f(a.get('log_nii_ha')))
        md.append("- **log([OIII]/Hβ)**: %s" % f(a.get('log_oiii_hb')))
        md.append("- **해석**: %s" % bpt_interp)
        md.append("")

        md.append("## %d. AI 머신러닝 분류 결과" % sec)
        sec += 1
        md.append("- **예측 은하 유형**: **%s** (신뢰도 %s)%s" % (pred_type, conf_str, cov_str))
        md.append("- **상위 3개 분류**:")
        md.append(top3_str)
        vote = a.get('similar_vote')
        if vote:
            md.append("- **유사 SDSS 은하 투표 (kNN)**: " + ", ".join("%s %s" % (k, self._pct(v)) for k, v in list(vote.items())[:3]))
        md.append("")

        md.append("## %d. 은하 진화 단계 진단" % sec)
        sec += 1
        md.append("- **진화 군집**: %s" % cluster)
        md.append("- **은하 진화 지수 (GEI)**: %s / 100" % (f(gei, "{:.1f}") if gei is not None else "N/A"))
        md.append("- **진화 단계**: %s" % stage)
        sfms = a.get('sfms')
        if sfms:
            md.append("- **주계열 대비 ΔMS**: %+.2f dex → %s" % (sfms['delta_ms'], sfms['state']))
        md.append("- **해석**: %s" % evo_interp)
        md.append("")

        pcts = a.get('percentiles')
        md.append("## %d. SDSS 배경 데이터 대비 위치" % sec)
        sec += 1
        if pcts:
            md.append("| 물리량 | 대상 값 | 백분위 | SDSS 중앙값 |")
            md.append("|--------|---------|--------|-------------|")
            for r in pcts:
                md.append("| %s | %s | %s%% | %s |" % (r['물리량'], r['대상 값'], r['백분위(%)'], r['SDSS 중앙값']))
        else:
            md.append("대상 천체는 BPT 진단도·주계열·질량-금속량·색-질량 공간에서 SDSS 은하 분포와 비교되었습니다.")
        md.append("")

        notes = a.get('notes') or []
        if notes:
            md.append("## %d. 주의 사항" % sec)
            for n in notes:
                md.append("- %s" % n)
            md.append("")

        md.append("---")
        md.append("_본 보고서는 GalaxyEvolution Studio에 의해 자동 생성되었습니다._")
        return "\n".join(md)

    # ── HTML ─────────────────────────────────────────────
    @staticmethod
    def _inline(text: str) -> str:
        t = _html.escape(text, quote=False)
        t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', t)
        t = re.sub(r'(?<![\w*])_(.+?)_(?![\w*])', r'<em>\1</em>', t)
        t = re.sub(r'`(.+?)`', r'<code>\1</code>', t)
        return t

    def generate_html(self, markdown_content: str) -> str:
        """Markdown → 다크 테마 HTML (외부 라이브러리 없이 표/헤더/목록/강조 지원)"""
        out = ["<html>", "<head>", "<meta charset='utf-8'>", "<title>천체 분석 보고서</title>", "<style>", """
            body { font-family: 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif; background-color: #0f172a; color: #e2e8f0; line-height: 1.7; padding: 24px; max-width: 920px; margin: 0 auto; }
            h1, h2, h3 { color: #60a5fa; border-bottom: 1px solid #1e293b; padding-bottom: 6px; }
            h1 { font-size: 2em; }
            h2 { font-size: 1.4em; margin-top: 1.6em; }
            table { border-collapse: collapse; width: 100%; margin: 12px 0; background-color: #111827; }
            th, td { border: 1px solid #334155; padding: 8px 10px; text-align: left; }
            th { background-color: #1e293b; color: #93c5fd; }
            tr:nth-child(even) { background-color: #0b1220; }
            li { margin-bottom: 4px; }
            strong { color: #fbbf24; }
            code { background: #1e293b; padding: 1px 4px; border-radius: 3px; }
            hr { border: 0; height: 1px; background: #334155; margin: 30px 0; }
            em { color: #94a3b8; }
        """, "</style>", "</head>", "<body>"]

        in_table = False
        list_depth = 0

        def close_lists():
            nonlocal list_depth
            while list_depth > 0:
                out.append("</ul>")
                list_depth -= 1

        for raw in markdown_content.split('\n'):
            line = raw.rstrip()
            stripped = line.strip()
            if not stripped:
                close_lists()
                if in_table:
                    out.append("</table>")
                    in_table = False
                continue
            if stripped.startswith('|'):
                close_lists()
                if re.match(r'^\|[\s\-|:]+\|$', stripped):
                    continue
                cells = [c.strip() for c in stripped.strip('|').split('|')]
                if not in_table:
                    out.append("<table>")
                    out.append("<tr>" + "".join("<th>%s</th>" % self._inline(c) for c in cells) + "</tr>")
                    in_table = True
                else:
                    out.append("<tr>" + "".join("<td>%s</td>" % self._inline(c) for c in cells) + "</tr>")
                continue
            if in_table:
                out.append("</table>")
                in_table = False
            m = re.match(r'^(#{1,3})\s+(.*)$', stripped)
            if m:
                close_lists()
                lvl = len(m.group(1))
                out.append("<h%d>%s</h%d>" % (lvl, self._inline(m.group(2)), lvl))
                continue
            if stripped == '---':
                close_lists()
                out.append("<hr>")
                continue
            m = re.match(r'^(\s*)(?:[-*]|\d+\.)\s+(.*)$', line)
            if m:
                depth = len(m.group(1)) // 2 + 1
                while list_depth < depth:
                    out.append("<ul>")
                    list_depth += 1
                while list_depth > depth:
                    out.append("</ul>")
                    list_depth -= 1
                out.append("<li>%s</li>" % self._inline(m.group(2)))
                continue
            close_lists()
            out.append("<p>%s</p>" % self._inline(stripped))

        close_lists()
        if in_table:
            out.append("</table>")
        out += ["</body>", "</html>"]
        return "\n".join(out)

    # ── 요약 카드 ─────────────────────────────────────────
    def generate_summary_card(self, analysis_results: dict) -> dict:
        """빠른 요약 카드 데이터 생성 (Streamlit 카드 UI용)."""
        a = analysis_results or {}
        metrics = []
        sfr = a.get('log_sfr')
        if sfr is not None:
            sf_like = any(s in str(a.get('bpt_class_en', a.get('bpt_class', ''))) for s in ('Star', '별생성'))
            metrics.append({'label': '별 생성률 (log SFR)', 'value': "%.2f M☉/yr" % sfr,
                            'delta': '별생성 활동' if sf_like else None})
        met = a.get('metallicity')
        if met is not None:
            metrics.append({'label': '금속량 12+log(O/H)', 'value': "%.2f" % met,
                            'delta': '태양(8.69) 대비 %+.2f' % (met - 8.69)})
        gei = a.get('gei_score')
        if gei is not None:
            metrics.append({'label': '진화 지수 (GEI)', 'value': "%.1f/100" % gei, 'delta': a.get('evolution_stage')})
        metrics.append({'label': 'AI 예측 유형', 'value': str(a.get('predicted_type', '미분류')).split(' (')[0],
                        'delta': "신뢰도 %s" % self._pct(a.get('confidence', 0))})
        return {
            'title': "천체: %s" % a.get('target_name', 'Unknown'),
            'subtitle': "분석 모드: %s" % a.get('input_mode', 'N/A'),
            'metrics': metrics
        }

    def save_report(self, content: str, filename: str, format: str = 'md') -> str:
        """보고서 파일 저장. Returns: 저장된 파일 경로."""
        if not filename.endswith(".%s" % format):
            filename = "%s.%s" % (filename, format)
        filepath = os.path.join(self.output_dir, filename)
        try:
            with open(filepath, 'w', encoding='utf-8') as fh:
                fh.write(content)
            return filepath
        except Exception as e:
            print("보고서 저장 중 오류 발생: %s" % e)
            return ""
