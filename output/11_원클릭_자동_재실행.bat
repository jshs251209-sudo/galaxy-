@echo off
chcp 65001 > nul
echo ================================================================================
echo   [JWST CEERS 은하 암흑물질 전수 계산 자동 재실행 스크립트]
echo ================================================================================
echo.
echo 1. C++ 고속 연산 엔진 컴파일 및 실행...
g++ -O3 -std=c++17 ceers_dark_matter_calculator.cpp -o ceers_dark_matter_calculator.exe
ceers_dark_matter_calculator.exe
echo.
echo 2. Python 풀스트림 전수 계산 및 300 DPI 차트 생성...
python process_ceers_dark_matter.py
echo.
echo ================================================================================
echo   모든 CEERS 연산 및 차트 생성이 성공적으로 완료되었습니다!
echo ================================================================================
pause
