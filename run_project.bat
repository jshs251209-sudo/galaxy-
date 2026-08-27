@echo off
chcp 65001 >nul
title YSC 대회 프로젝트 서버 구동기

echo ===================================================
echo     YSC 대회 프로젝트 - 통합 런처 (Integrated Launcher)
echo ===================================================
echo.

echo [1/5] 필요 패키지 설치 확인 중...
pip install -r requirements.txt > nul 2>&1
echo 완료!
echo.

echo [2/5] 전체 파이프라인 (데이터 처리 및 머신러닝 학습) 실행 중...
echo (시간이 다소 소요될 수 있습니다. 진행 상황은 아래에 표시됩니다)
python run_pipeline.py
echo.
echo 파이프라인 실행 및 저장 완료!
echo.

echo [3/5] 은하 진화 대시보드 서버 시작 (Port: 8000)...
start "Galaxy Dashboard Server" cmd /c "python -m http.server --directory dashboard 8000"
echo 완료!
echo.

echo [4/5] 천체 스펙트럼 분석기 시작 (Port: 8501)...
start "Spectrum Analyzer Server" cmd /c "streamlit run spectrum_analyzer.py"
echo 완료!
echo.

echo [5/5] 통합 런처 웹페이지 여는 중...
timeout /t 3 /nobreak > nul
start launcher.html

echo.
echo ===================================================
echo 모든 서버가 실행되었습니다!
echo. 
echo - 웹 브라우저에서 포털 창이 자동으로 열립니다.
echo - 서버를 완전히 종료하려면 새로 뜬 검은색 터미널 창 2개를 모두 닫아주세요.
echo ===================================================
pause
