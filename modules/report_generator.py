import os
import datetime

class ReportGenerator:
    """분석 결과 종합 보고서 자동 생성기"""
    
    def __init__(self, output_dir: str = None):
        """Set output directory for reports."""
        self.output_dir = output_dir or os.path.join(os.getcwd(), 'output', 'reports')
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir, exist_ok=True)
            
    def _safe_format(self, value, format_str="{:.2f}", default="-"):
        """안전한 값 포맷팅"""
        if value is None:
            return default
        try:
            return format_str.format(float(value))
        except (ValueError, TypeError):
            return str(value)

    def generate_markdown(self, analysis_results: dict) -> str:
        """분석 결과를 Markdown 문자열로 변환.
        
        analysis_results should contain:
        {
            'target_name': str,            # 천체 이름/식별자
            'analysis_datetime': str,       # 분석 일시
            'input_mode': str,              # 입력 모드 (스펙트럼/SDSS/모의 etc)
            
            # 물리량
            'emission_lines': dict,         # 검출된 방출선 플럭스
            'ebv': float,                   # 성간 소광량
            'log_sfr': float,               # 별 생성률
            'metallicity': float,           # 금속량
            'metallicity_method': str,      # 금속량 산출 방법 (N2/O3N2)
            
            # BPT 분류
            'bpt_class': str,               # BPT 분류 결과
            'log_nii_ha': float,
            'log_oiii_hb': float,
            
            # AI 분류
            'predicted_type': str,          # 11대 은하 분류 결과
            'confidence': float,            # 분류 신뢰도
            'top_3_types': list,            # 상위 3개 분류 확률
            'evolution_cluster': str,       # 4대 진화 군집
            'gei_score': float,             # 은하진화지수 (0-100)
            'evolution_stage': str,         # 진화 단계 명칭
            
            # 선택적
            'log_mass': float,
            'color_ur': float,
            'z': float,
        }
        """
        
        target = analysis_results.get('target_name', 'Unknown Target')
        now_str = analysis_results.get('analysis_datetime', datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        mode = analysis_results.get('input_mode', '미상')
        
        # 2. 방출선 테이블 구성
        emission_lines = analysis_results.get('emission_lines', {})
        line_table_rows = []
        for line, flux in emission_lines.items():
            if flux is not None and flux > 0:
                detected = "✅"
                flux_str = f"{flux:.4f}"
            else:
                detected = "❌"
                flux_str = "미검출"
            line_table_rows.append(f"| {line} | - | {flux_str} | {detected} |")
            
        if not line_table_rows:
            line_table_rows.append("| 입력 없음 | - | - | - |")
            
        line_table = "\n".join(line_table_rows)
        
        # 물리량 안전 포맷팅
        ebv_str = self._safe_format(analysis_results.get('ebv'))
        sfr_str = self._safe_format(analysis_results.get('log_sfr'))
        z_str = self._safe_format(analysis_results.get('metallicity'))
        z_method = analysis_results.get('metallicity_method', 'N/A')
        
        # BPT 포맷팅
        bpt_class = analysis_results.get('bpt_class', '미상')
        nii_ha = self._safe_format(analysis_results.get('log_nii_ha'))
        oiii_hb = self._safe_format(analysis_results.get('log_oiii_hb'))
        
        bpt_interpretation = "일반적인 별 탄생 은하(SF)로 보입니다."
        if bpt_class == 'AGN':
            bpt_interpretation = "활동은하핵(AGN) 활동이 감지됩니다. 중심 블랙홀의 강한 강착 원반 복사가 방출선에 기여하고 있습니다."
        elif bpt_class == 'Composite':
            bpt_interpretation = "별 탄생과 AGN 활동이 혼합된 복합(Composite) 특성을 보입니다."
        elif bpt_class == 'LINER':
            bpt_interpretation = "저전리 방출선 영역(LINER)으로 분류됩니다. 늙은 항성종족이나 약한 AGN에 의한 이온화일 수 있습니다."
            
        # AI 포맷팅
        pred_type = analysis_results.get('predicted_type', '미분류')
        conf = analysis_results.get('confidence')
        conf_str = f"{conf:.1f}%" if conf is not None else "N/A"
        
        top3 = analysis_results.get('top_3_types', [])
        top3_lines = []
        for i, (t, p) in enumerate(top3[:3]):
            top3_lines.append(f"  {i+1}. {t} ({p:.1f}%)")
        if not top3_lines:
            top3_lines.append("  - 데이터 없음")
        top3_str = "\n".join(top3_lines)
        
        # 진화 포맷팅
        cluster = analysis_results.get('evolution_cluster', '미상')
        gei = analysis_results.get('gei_score')
        gei_str = f"{gei:.1f}" if gei is not None else "N/A"
        stage = analysis_results.get('evolution_stage', '미상')
        
        evo_interpretation = "현재 데이터로는 정확한 진화 단계를 파악하기 어렵습니다."
        if gei is not None:
            if gei < 30:
                evo_interpretation = "활발한 별 생성 단계에 있으며, 풍부한 가스를 바탕으로 성장 중인 젊은 은하입니다."
            elif gei < 70:
                evo_interpretation = "별 생성률이 점차 감소하는 전이기 은하로 추정됩니다 (Green Valley)."
            else:
                evo_interpretation = "가스가 대부분 고갈되어 별 생성이 거의 멈춘 늙고 안정한 은하입니다 (Red Sequence)."

        mass_str = self._safe_format(analysis_results.get('log_mass'))
        color_str = self._safe_format(analysis_results.get('color_ur'))

        markdown = f"""# 🌌 천체 분석 보고서

## 1. 분석 개요
- **분석 일시**: {now_str}
- **입력 방식**: {mode}
- **대상 천체**: {target}

## 2. 분광 분석 결과
| 방출선 | 파장 (Å) | 플럭스 | 검출 여부 |
|--------|---------|--------|----------|
{line_table}

## 3. 물리량 추출 결과
- **성간 소광량 E(B-V)**: {ebv_str} mag
- **별 생성률 (log SFR)**: {sfr_str} M☉/yr
- **금속량 12+log(O/H)**: {z_str} ({z_method})
- **항성 질량 (log M*)**: {mass_str} M☉
- **색지수 (u-r)**: {color_str}

## 4. BPT 진단 분류
- **분류 결과**: **{bpt_class}**
- **log([NII]/Hα)**: {nii_ha}
- **log([OIII]/Hβ)**: {oiii_hb}
- **해석**: {bpt_interpretation}

## 5. AI 머신러닝 분류 결과
- **예측 은하 유형**: **{pred_type}** (신뢰도 {conf_str})
- **상위 3개 분류**:
{top3_str}

## 6. 은하 진화 단계 진단
- **진화 군집**: {cluster}
- **은하 진화 지수 (GEI)**: {gei_str}점/100점
- **진화 단계**: {stage}
- **해석**: {evo_interpretation}

## 7. SDSS 10만 개 배경 데이터 대비 위치
대상 천체는 질량-별생성률 평면과 BPT 진단도 등 주요 은하 진화 물리량 공간에서 분석되었습니다. 
제시된 물리량과 분류 결과는 SDSS DR17 통계적 분포에 기반한 머신러닝 모델의 판단을 따릅니다.

---
*본 보고서는 GalaxyEvolution Studio에 의해 자동 생성되었습니다.*
"""
        return markdown

    def generate_html(self, markdown_content: str) -> str:
        """문자열 Markdown을 스타일링된 HTML로 변환.
        Use simple CSS for dark-themed, professional scientific document.
        Support tables, headers, bullet points.
        No external library needed - manual conversion of basic MD to HTML.
        """
        html_lines = []
        html_lines.append("<html>")
        html_lines.append("<head>")
        html_lines.append("<meta charset='utf-8'>")
        html_lines.append("<style>")
        html_lines.append("""
            body { font-family: 'Malgun Gothic', sans-serif; background-color: #1e1e1e; color: #d4d4d4; line-height: 1.6; padding: 20px; max-width: 900px; margin: 0 auto; }
            h1, h2, h3 { color: #569cd6; border-bottom: 1px solid #333; padding-bottom: 5px; }
            h1 { font-size: 2em; margin-bottom: 0.5em; }
            h2 { font-size: 1.5em; margin-top: 1.5em; }
            table { border-collapse: collapse; width: 100%; margin: 15px 0; background-color: #252526; }
            th, td { border: 1px solid #3c3c3c; padding: 10px; text-align: left; }
            th { background-color: #333333; font-weight: bold; color: #4ec9b0; }
            tr:nth-child(even) { background-color: #2a2a2b; }
            ul { margin-bottom: 15px; }
            li { margin-bottom: 5px; }
            strong { color: #ce9178; }
            hr { border: 0; height: 1px; background: #333; margin: 30px 0; }
            em { color: #808080; }
        """)
        html_lines.append("</style>")
        html_lines.append("</head>")
        html_lines.append("<body>")
        
        in_table = False
        in_list = False
        
        lines = markdown_content.split('\n')
        for line in lines:
            line = line.strip()
            
            if not line:
                if in_list:
                    html_lines.append("</ul>")
                    in_list = False
                continue
                
            # Headers
            if line.startswith('# '):
                html_lines.append(f"<h1>{line[2:]}</h1>")
                continue
            if line.startswith('## '):
                html_lines.append(f"<h2>{line[3:]}</h2>")
                continue
            if line.startswith('### '):
                html_lines.append(f"<h3>{line[4:]}</h3>")
                continue
                
            # Horizontal rule
            if line == '---':
                html_lines.append("<hr>")
                continue
                
            # Table processing
            if line.startswith('|'):
                if '---' in line:
                    continue # Skip separator
                
                cells = [c.strip() for c in line.split('|')[1:-1]]
                if not in_table:
                    html_lines.append("<table>")
                    html_lines.append("<tr>" + "".join(f"<th>{c}</th>" for c in cells) + "</tr>")
                    in_table = True
                else:
                    html_lines.append("<tr>" + "".join(f"<td>{c}</td>" for c in cells) + "</tr>")
                continue
            else:
                if in_table:
                    html_lines.append("</table>")
                    in_table = False
                    
            # Lists
            if line.startswith('- ') or line.startswith('* '):
                if not in_list:
                    html_lines.append("<ul>")
                    in_list = True
                content = line[2:]
                # Basic bold processing
                while '**' in content:
                    content = content.replace('**', '<strong>', 1).replace('**', '</strong>', 1)
                html_lines.append(f"<li>{content}</li>")
                continue
                
            if line.startswith('1.') or line.startswith('2.') or line.startswith('3.'):
                # Treating as unordered for simplicity in this basic parser
                if not in_list:
                    html_lines.append("<ul>")
                    in_list = True
                html_lines.append(f"<li>{line}</li>")
                continue
                
            if in_list and not line.startswith('- ') and not line.startswith('* '):
                html_lines.append("</ul>")
                in_list = False

            # Basic emphasis and bold
            formatted_line = line
            while '**' in formatted_line:
                formatted_line = formatted_line.replace('**', '<strong>', 1).replace('**', '</strong>', 1)
            while '*' in formatted_line:
                formatted_line = formatted_line.replace('*', '<em>', 1).replace('*', '</em>', 1)
                
            html_lines.append(f"<p>{formatted_line}</p>")
            
        if in_table:
            html_lines.append("</table>")
        if in_list:
            html_lines.append("</ul>")
            
        html_lines.append("</body>")
        html_lines.append("</html>")
        
        return "\n".join(html_lines)

    def generate_summary_card(self, analysis_results: dict) -> dict:
        """빠른 요약 카드 데이터 생성 (Streamlit 카드 UI용)."""
        
        target = analysis_results.get('target_name', 'Unknown')
        pred_type = analysis_results.get('predicted_type', '미분류')
        bpt = analysis_results.get('bpt_class', '미상')
        gei = analysis_results.get('gei_score')
        stage = analysis_results.get('evolution_stage', '-')
        sfr = analysis_results.get('log_sfr')
        metallicity = analysis_results.get('metallicity')
        
        metrics = []
        
        # 별생성률
        if sfr is not None:
            metrics.append({
                'label': '별 생성률 (log SFR)',
                'value': f"{sfr:.2f} M☉/yr",
                'delta': '주계열' if bpt == 'SF' else '비활성'
            })
            
        # 금속량
        if metallicity is not None:
            metrics.append({
                'label': '금속량 12+log(O/H)',
                'value': f"{metallicity:.2f}",
                'delta': '태양비'
            })
            
        # 진화 지수
        if gei is not None:
            metrics.append({
                'label': '진화 지수 (GEI)',
                'value': f"{gei:.1f}/100",
                'delta': stage
            })
            
        # 분류
        metrics.append({
            'label': 'AI 예측 유형',
            'value': pred_type,
            'delta': f"신뢰도 {analysis_results.get('confidence', 0):.1f}%"
        })

        return {
            'title': f"천체: {target}",
            'subtitle': f"분석 모드: {analysis_results.get('input_mode', 'N/A')}",
            'metrics': metrics
        }

    def save_report(self, content: str, filename: str, format: str = 'md') -> str:
        """보고서 파일 저장. Returns: 저장된 파일 경로."""
        if not filename.endswith(f".{format}"):
            filename = f"{filename}.{format}"
            
        filepath = os.path.join(self.output_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return filepath
        except Exception as e:
            print(f"보고서 저장 중 오류 발생: {e}")
            return ""
