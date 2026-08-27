import re

def rewrite_content():
    with open('index.html', 'r', encoding='utf-8') as f:
        html = f.read()

    # 1. Quick Start
    quick_start_old = r'<section id="quick-start">.*?</section>'
    quick_start_new = """<section id="quick-start">
    <div class="container">
        <h2 class="section-title">&#128640; 시스템 열람 지침</h2>
        <p class="section-desc">인가된 연구원만 열람 가능합니다. 아래 보안 단계를 숙지하십시오.</p>
        <div class="steps">
            <div class="step">
                <div class="step-num">1</div>
                <div class="step-body">
                    <h3>은하 진화 대시보드 접속</h3>
                    <p>
                        외부 서버 연동 없이 <strong>10만 개의 은하 기밀 데이터</strong>가 통째로 브라우저에 임베딩되어 있습니다.<br>
                        아래 [분석 도구 바로가기]에서 대시보드 버튼을 눌러 즉시 열람하십시오.
                    </p>
                </div>
            </div>
            <div class="step">
                <div class="step-body">
                    <h3>상관관계 추적</h3>
                    <p>
                        주계열, BPT, 색-질량 등 프리셋 버튼을 통해 은하의 물리·화학적 특성 변화를 시각적으로 추적합니다.<br>
                        특이점이 관측되면 즉시 로그에 보고하십시오.
                    </p>
                </div>
            </div>
            <div class="step">
                <div class="step-body">
                    <h3>실시간 판독기 가동</h3>
                    <p>
                        대시보드의 [판독기] 탭에서 미확인 타겟 은하의 방출선 플럭스를 직접 입력하십시오.<br>
                        백그라운드 데이터 위에서 실시간으로 타겟의 은하 유형, 금속성, 먼지 소광값을 즉시 연산합니다.
                    </p>
                </div>
            </div>
        </div>
    </div>
</section>"""
    html = re.sub(quick_start_old, quick_start_new, html, flags=re.DOTALL)

    # 2. Tools (Streamlit card)
    html = html.replace('href="http://localhost:8501" target="_blank"', 'href="#" onclick="alert(\'[접근 거부] 이 도구는 연구소 로컬 환경에서 run_project.bat을 통해서만 접근할 수 있는 1급 기밀 시스템입니다.\'); return false;"')

    # 3. Pipeline Intro
    html = html.replace('<code>run_project.bat</code> 실행 시, 내부적으로 다음 6단계가 순서대로 수행됩니다.', '연구소 내부망(로컬)에서 <code>run_project.bat</code> 실행 시, 다음 보안 파이프라인 6단계가 순차 가동됩니다.')

    # 4. FAQ
    faq_old = r'<section id="faq">.*?</section>'
    faq_new = """<section id="faq">
    <div class="container">
        <h2 class="section-title">&#10067; 비상 연락망 (FAQ)</h2>
        <p class="section-desc">오류 발생 시 다음 보안 지침을 따르십시오.</p>

        <div class="faq-item">
            <button class="faq-q">웹 대시보드에 접속이 안 됩니다.</button>
            <div class="faq-a">
                <div class="faq-inner">
                본 웹페이지는 자급식 오프라인 렌더링 시스템을 사용하므로 외부 서버가 필요하지 않습니다.<br>
                화면이 보이지 않는다면 브라우저의 보안 캐시를 지우고 새로고침을 시도하십시오.
                </div>
            </div>
        </div>
        <div class="faq-item">
            <button class="faq-q">천체 스펙트럼 분석기를 웹에서 실행할 수 있습니까?</button>
            <div class="faq-a">
                <div class="faq-inner">
                <strong>[접근 거부]</strong> 해당 시스템은 파이썬 연산 코어가 필요한 로컬망 전용입니다.<br>
                GitHub에서 전체 코드를 다운로드 받아 오프라인 PC에서 <code>run_project.bat</code>을 실행해야만 접근이 허가됩니다.
                </div>
            </div>
        </div>
        <div class="faq-item">
            <button class="faq-q">인터랙티브 HTML 그래프 카드들은 작동합니까?</button>
            <div class="faq-a">
                <div class="faq-inner">
                네. 하단의 <code>인터랙티브 그래프</code> 카드 3종은 웹에서도 즉시 렌더링되도록 모두 정적(Static) 파일 형식으로 동기화되어 있습니다. 안심하고 열람하십시오.
                </div>
            </div>
        </div>
        <div class="faq-item">
            <button class="faq-q">PC(로컬)에서 데이터를 재분석하고 싶습니다.</button>
            <div class="faq-a">
                <div class="faq-inner">
                로컬 환경에서 <code>data/raw/sdss_100k_raw.csv</code> 파일을 파기한 후 배치 파일을 재실행하십시오.<br>
                SDSS 관측소 서버에서 최신 기밀 데이터를 재수신하여 파이프라인을 처음부터 재가동합니다.
                </div>
            </div>
        </div>
    </div>
</section>"""
    html = re.sub(faq_old, faq_new, html, flags=re.DOTALL)

    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html)

if __name__ == '__main__':
    rewrite_content()
