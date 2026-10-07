# -*- coding: utf-8 -*-
"""
GalaxyEvolution Studio - 원클릭 온라인 외부 공유 터널 생성기
Streamlit 앱(app.py)을 로컬에서 실행하고, 외부 누구나 접속 가능한 임시 HTTPS 공개 주소를 자동 생성합니다.
"""

import os
import sys
import time
import subprocess
import urllib.request
import json

def check_and_run():
    print("=" * 60)
    print("🌌 GalaxyEvolution Studio - 온라인 외부 공유 링크 생성기")
    print("=" * 60)

    # 1. Start Streamlit in background if not already running
    print("\n[1/3] 로컬 Streamlit 앱 구동 확인 중 (Port 8501)...")
    try:
        urllib.request.urlopen("http://localhost:8501", timeout=2)
        print(" -> 이미 로컬 Streamlit 앱이 실행 중입니다.")
    except Exception:
        print(" -> Streamlit 앱을 백그라운드에서 새로 시작합니다...")
        subprocess.Popen([sys.executable, "-m", "streamlit", "run", "app.py", "--server.port=8501", "--server.headless=true"])
        time.sleep(4)

    # 2. Try Localtunnel via npx
    print("\n[2/3] 외부 공개 터널(HTTPS) 연결 중...")
    print(" -> Cloudflare / Localtunnel 네트워크를 통해 전세계 공유 링크를 발급합니다.")
    
    try:
        # Check if npx is available
        lt_proc = subprocess.Popen(["npx", "localtunnel", "--port", "8501"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        for line in lt_proc.stdout:
            if "your url is:" in line.lower():
                url = line.strip().split()[-1]
                print("\n" + "=" * 60)
                print("🎉 외부 공유 링크가 성공적으로 생성되었습니다!")
                print(f"👉 접속 URL: {url}")
                print("=" * 60)
                print("\n※ 주의: 이 창을 닫으면 외부 링크 접속이 종료됩니다.")
                print("※ 비밀번호 확인 창이 뜨면 본인의 외부 IP를 입력하면 열립니다.")
                break
        lt_proc.wait()
    except Exception as e:
        print(f"\n[안내] npx 로컬터널 실행 중 오류 또는 Node.js 미설치: {e}")
        print("\n대안 안내:")
        print("1. GitHub Pages에 배포된 완전 웹 버전 사용:")
        print("   👉 https://jshs251209-sudo.github.io/galaxy-/galaxy_analyzer_web.html")
        print("2. 로컬 브라우저에서 직접 열기:")
        print("   👉 http://localhost:8501")

if __name__ == "__main__":
    check_and_run()
