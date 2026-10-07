@echo off
chcp 65001 >nul
title GalaxyEvolution Studio - 온라인 공유 터널 구동기

echo =========================================================
echo    GalaxyEvolution Studio - 온라인 외부 공유 링크 생성기
echo =========================================================
echo.
python share_online_tunnel.py
pause
