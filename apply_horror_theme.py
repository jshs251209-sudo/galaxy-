import re

def update_index_html():
    with open('index.html', 'r', encoding='utf-8') as f:
        content = f.read()

    new_css = """        /* ─── Retro Analog Horror CSS ─── */
        @import url('https://fonts.googleapis.com/css2?family=VT323&display=swap');
        @font-face {
            font-family: 'DungGeunMo';
            src: url('https://fastly.jsdelivr.net/gh/projectnoonnu/noonfonts_six@1.2/DungGeunMo.woff') format('woff');
            font-weight: normal; font-style: normal;
        }
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
        html { scroll-behavior: smooth; }
        body {
            font-family: 'DungGeunMo', 'VT323', monospace;
            background: #000;
            color: #d0d0d0;
            line-height: 1.6;
            overflow-x: hidden;
        }
        body::before {
            content: " "; display: block; position: fixed; top: 0; left: 0; bottom: 0; right: 0;
            background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.4) 50%),
                        linear-gradient(90deg, rgba(255, 0, 0, 0.08), rgba(0, 255, 0, 0.03), rgba(0, 0, 255, 0.08));
            z-index: 999; background-size: 100% 4px, 4px 100%; pointer-events: none;
        }
        .container { max-width: 1100px; margin: 0 auto; padding: 0 1.5rem; position: relative; z-index: 10; }
        a { color: #ffff00; text-decoration: none; border-bottom: 1px dashed #ffff00; transition: color .2s; }
        a:hover { color: #fff; border-bottom-style: solid; text-shadow: 2px 0 0 rgba(255,0,0,0.8), -2px 0 0 rgba(0,0,255,0.8); }
        h1, h2, h3 { color: #fff; text-transform: uppercase; letter-spacing: 1px; }
        h1 { text-shadow: 3px 3px 0px #f00, -2px -2px 0px #00f; }
        
        .hero { text-align: center; padding: 5rem 1rem 3rem; border-bottom: 2px solid #f00; background: #050505; }
        .hero-icon { font-size: 4.5rem; margin-bottom: .5rem; filter: grayscale(1) contrast(3); }
        .hero h1 { font-size: 3rem; margin-bottom: .6rem; }
        .hero .subtitle { color: #aaa; font-size: 1.3rem; max-width: 640px; margin: 0 auto 2rem; }
        .hero .badge { display: inline-block; background: #f00; color: #000; padding: .3rem .9rem; border: 2px solid #fff; font-size: 1rem; font-weight: bold; text-transform: uppercase; animation: blink 2s infinite; }
        @keyframes blink { 0%, 49% { opacity: 1; } 50%, 100% { opacity: 0; } }

        .nav-bar { position: sticky; top: 0; z-index: 100; background: #000; border-bottom: 2px solid #f00; padding: .65rem 0; }
        .nav-inner { display: flex; gap: 1rem; flex-wrap: wrap; justify-content: center; }
        .nav-inner a { padding: .45rem 1rem; font-size: 1.1rem; color: #fff; border: 1px solid #fff; background: #111; text-decoration: none; text-transform: uppercase; border-bottom: 1px solid #fff; }
        .nav-inner a:hover { background: #f00; color: #000; font-weight: bold; }

        section { padding: 3rem 0; border-bottom: 2px dashed #444; }
        .section-title { font-size: 2rem; margin-bottom: 1rem; color: #ffff00; }
        .section-desc { color: #aaa; margin-bottom: 2rem; font-size: 1.2rem; }

        .cards { display: grid; gap: 1.5rem; }
        .cards-2 { grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); }
        .cards-3 { grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); }
        .card { background: #000; border: 2px solid #f00; padding: 1.8rem; transition: background .1s; }
        .card:hover { background: #111; border-color: #fff; }
        .card-icon { font-size: 2.8rem; margin-bottom: .8rem; filter: grayscale(1); }
        .card h3 { font-size: 1.5rem; margin-bottom: .5rem; color: #fff; }
        .card p { color: #888; font-size: 1.1rem; border-bottom: none; }
        a.card { display: block; color: inherit; text-decoration: none; border-bottom: 2px solid #f00; }
        a.card:hover { text-decoration: none; border-bottom: 2px solid #fff; }

        .link-btn { display: inline-block; margin-top: 1rem; padding: .5rem 1.2rem; border: 2px solid #fff; font-size: 1.1rem; font-weight: bold; color: #000; background: #ccc; text-transform: uppercase; }
        .link-btn.blue, .link-btn.purple, .link-btn.gold, .link-btn.green { background: #fff; color: #000; border-color: #f00; }
        .link-btn:hover { background: #f00; color: #fff; }

        .steps { counter-reset: step; border-left: 2px solid #f00; margin-left: 1.5rem; }
        .step { display: flex; gap: 1.4rem; padding: 1.5rem 0 1.5rem 1.5rem; position: relative; border-bottom: 1px dashed #444; }
        .step-num { position: absolute; left: -1.2rem; top: 1.5rem; width: 35px; height: 35px; background: #000; border: 2px solid #f00; color: #f00; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 1.2rem; }
        .step-body h3 { font-size: 1.4rem; color: #ffff00; }
        .step-body p { color: #aaa; font-size: 1.1rem; }
        .step-body code { background: #222; padding: .2rem .5rem; border: 1px solid #f00; color: #ff5555; font-family: 'VT323', monospace; font-size: 1.1rem; }

        .faq-item { border-bottom: 1px dashed #f00; }
        .faq-q { width: 100%; text-align: left; background: none; border: none; color: #fff; font-size: 1.3rem; padding: 1.2rem 0; cursor: pointer; display: flex; justify-content: space-between; align-items: center; font-family: inherit; }
        .faq-q:hover { color: #f00; }
        .faq-a { max-height: 0; overflow: hidden; transition: max-height .2s ease-out; }
        .faq-inner { padding-bottom: 1.5rem; color: #aaa; font-size: 1.1rem; }
        
        table { width: 100%; border-collapse: collapse; margin: 1rem 0; background: #000; border: 2px solid #f00; }
        th, td { text-align: left; padding: .8rem; border: 1px solid #444; font-size: 1.1rem; }
        th { background: #111; color: #ffff00; border-bottom: 2px solid #f00; font-weight: bold; }
        td { color: #ccc; }
        
        footer { text-align: center; padding: 3rem 1rem; border-top: 4px double #f00; font-size: 1rem; color: #666; }
        
        h2:hover, h3:hover { text-shadow: 2px 0 0 rgba(255,0,0,0.8), -2px 0 0 rgba(0,0,255,0.8); }"""

    # Replace everything between <style> and </style>
    new_content = re.sub(r'<style>.*?</style>', f'<style>\n{new_css}\n    </style>', content, flags=re.DOTALL)
    
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(new_content)

def update_dashboard():
    with open('dashboard_real_data.html', 'r', encoding='utf-8') as f:
        content = f.read()
        
    new_css = """@import url('https://fonts.googleapis.com/css2?family=VT323&display=swap');
@font-face {
    font-family: 'DungGeunMo';
    src: url('https://fastly.jsdelivr.net/gh/projectnoonnu/noonfonts_six@1.2/DungGeunMo.woff') format('woff');
    font-weight: normal; font-style: normal;
}
:root { --bg: #000; --text: #d0d0d0; }
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
body { background: var(--bg); color: var(--text); font-family: 'DungGeunMo', 'VT323', monospace; line-height: 1.6; overflow-x: hidden; position: relative; }
body::before {
    content: " "; display: block; position: fixed; top: 0; left: 0; bottom: 0; right: 0;
    background: linear-gradient(rgba(18,16,16,0) 50%, rgba(0,0,0,0.4) 50%),
                linear-gradient(90deg, rgba(255,0,0,0.08), rgba(0,255,0,0.03), rgba(0,0,255,0.08));
    z-index: 999; background-size: 100% 4px, 4px 100%; pointer-events: none;
}
.hdr { text-align: center; padding: 2.5rem 1rem 1.5rem; border-bottom: 2px solid #f00; position: relative; z-index: 10; }
.hdr h1 { font-size: 2.5rem; color: #fff; text-shadow: 2px 2px 0px #f00, -2px -2px 0px #00f; text-transform: uppercase; letter-spacing: 2px; }
.hdr p { color: #aaa; margin-top: .4rem; font-size: 1.2rem; }
.badge { display: inline-block; background: #f00; color: #000; padding: .2rem .7rem; border: 2px solid #fff; font-size: 1rem; margin-top: .6rem; animation: blink 2s infinite; font-weight: bold; text-transform: uppercase; }
@keyframes blink { 0%, 49% { opacity: 1; } 50%, 100% { opacity: 0; } }
.container { max-width: 1300px; margin: 0 auto; padding: 1.5rem; position: relative; z-index: 10; }
.tabs { display: flex; gap: .6rem; flex-wrap: wrap; justify-content: center; margin-bottom: 1.5rem; }
.tab-btn { background: #000; border: 2px solid #f00; color: #f00; padding: .55rem 1.4rem; font-size: 1.2rem; cursor: pointer; transition: .1s; font-family: inherit; text-transform: uppercase; }
.tab-btn:hover { background: #f00; color: #000; }
.tab-btn.active { background: #f00; color: #000; border-color: #fff; font-weight: bold; }
.tab { display: none; } .tab.active { display: block; animation: glitch 0.2s linear; }
@keyframes glitch { 0% { transform: translate(2px, 2px); } 20% { transform: translate(-2px, -2px); } 40% { transform: translate(2px, -2px); } 60% { transform: translate(-2px, 2px); } 80% { transform: translate(2px, 2px); } 100% { transform: translate(0, 0); } }
.glass { background: #000; border: 2px solid #f00; padding: 1.4rem; margin-bottom: 1.2rem; }
.row { display: grid; gap: 1.2rem; } .row-4 { grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); }
.stat-card { text-align: center; padding: 1.2rem; border: 1px dashed #444; }
.stat-card .val { font-size: 2.5rem; font-weight: bold; color: #fff; text-shadow: 2px 2px 0 #f00; }
.stat-card .lbl { color: #ffff00; font-size: 1.1rem; margin-top: .3rem; text-transform: uppercase; }
.ctrls { display: flex; gap: 1rem; flex-wrap: wrap; margin-bottom: 1rem; }
.ctrl { flex: 1; min-width: 180px; }
.ctrl label { display: block; color: #fff; font-weight: bold; font-size: 1.1rem; margin-bottom: .3rem; }
select, input { width: 100%; padding: .55rem; border: 2px solid #f00; background: #000; color: #fff; font-family: inherit; font-size: 1.1rem; outline: none; }
select:focus, input:focus { border-color: #fff; }
.presets { display: flex; gap: .7rem; flex-wrap: wrap; margin-bottom: 1rem; }
.preset { background: #000; border: 2px solid #fff; color: #fff; padding: .4rem 1.1rem; cursor: pointer; font-family: inherit; font-size: 1.1rem; text-transform: uppercase; }
.preset:hover { background: #fff; color: #000; }
#plot { height: 62vh; min-height: 480px; border: 2px solid #444; background: #000; }
table { width: 100%; border-collapse: collapse; }
th, td { text-align: left; padding: .6rem .8rem; border-bottom: 1px dashed #444; font-size: 1.1rem; }
th { color: #ffff00; font-weight: bold; text-transform: uppercase; border-bottom: 2px solid #f00; }
td { color: #ccc; }
.type-badge { display: inline-block; padding: .15rem .6rem; border: 1px solid #fff; font-size: 1rem; text-transform: uppercase; }
.type-e { background: #000; color: #f00; border-color: #f00; }
.type-s { background: #000; color: #0f0; border-color: #0f0; }
footer { text-align: center; padding: 2rem 1rem; color: #555; font-size: 1rem; border-top: 2px solid #f00; }"""

    content = re.sub(r'<style>.*?</style>', f'<style>\n{new_css}\n</style>', content, flags=re.DOTALL)
    
    # Update Plotly layout in JS
    old_layout = """const layout={
        xaxis:{title:VARS[xk]||xk,gridcolor:'#1a2040',color:'#8aa'},
        yaxis:{title:VARS[yk]||yk,gridcolor:'#1a2040',color:'#8aa'},
        paper_bgcolor:'rgba(0,0,0,0)',plot_bgcolor:'rgba(0,0,0,0)',
        font:{color:'#c0c8d8'},margin:{t:30,b:50,l:60,r:20},
        hovermode:'closest',legend:{font:{color:'#aab'}}
    };"""
    
    new_layout = """const layout={
        xaxis:{title:VARS[xk]||xk,gridcolor:'#333',color:'#fff'},
        yaxis:{title:VARS[yk]||yk,gridcolor:'#333',color:'#fff'},
        paper_bgcolor:'#000',plot_bgcolor:'#000',
        font:{color:'#f00', family: 'VT323, DungGeunMo, monospace', size: 14},
        margin:{t:30,b:50,l:60,r:20},
        hovermode:'closest',legend:{font:{color:'#fff'}}
    };"""
    content = content.replace(old_layout, new_layout)
    
    with open('dashboard_real_data.html', 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == '__main__':
    update_index_html()
    update_dashboard()
