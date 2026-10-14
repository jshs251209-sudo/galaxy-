import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
from bs4 import BeautifulSoup

with open(r'C:\Users\neato\.gemini\antigravity\brain\93eb8b76-45c2-4a0f-91fc-55c786cc6336\.system_generated\steps\292\content.md', 'r', encoding='utf-8') as f:
    soup = BeautifulSoup(f.read(), 'html.parser')

for p in soup.find_all(['p', 'div', 'span']):
    t = p.get_text()
    if 'pixel scale' in t and len(t) < 500:
        print('P:', t)
