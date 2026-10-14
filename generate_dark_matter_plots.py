import os
import shutil
import zipfile
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import skewnorm

# 1. Ensure Korean font (Malgun Gothic) without glyph breakage
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# Directories
OUT_DIR = 'output'
DOWNLOADS_DIR = r'C:\Users\neato\Downloads'
os.makedirs(OUT_DIR, exist_ok=True)

print("="*75)
print(">> [1/5] C++ 연산 데이터 파일 로드 중...")
print("="*75)

# Load C++ computed data
df_ngc = pd.read_csv('cpp_rotation_curve_ngc3198.csv')
df_m31 = pd.read_csv('cpp_rotation_curve_m31.csv')
df_bench = pd.read_csv('cpp_benchmark_results.csv')

print(f"  - NGC 3198 회전곡선 포인트: {len(df_ngc)} 개")
print(f"  - M31 안드로메다 회전곡선 포인트: {len(df_m31)} 개")
print(f"  - 대표 벤치마크 은하: {len(df_bench)} 개")

# -------------------------------------------------------------------------
# [Plot 1] NGC 3198 회전곡선 성분별 정밀 분해 차트
# -------------------------------------------------------------------------
print("\n>> [2/5] 그래프 1: NGC 3198 회전곡선 성분 분해 생성 중...")
fig1, ax1 = plt.subplots(figsize=(11, 7.5), dpi=300)
ax1.set_facecolor('#f8fafc')

# Begeman 1989 Real Observation Points
r_obs = np.array([0.8, 1.8, 3.2, 5.0, 7.5, 10.2, 13.5, 16.7, 20.1, 24.0, 27.8, 30.5])
v_obs = np.array([55.0, 92.0, 122.0, 142.0, 149.0, 151.0, 149.0, 150.0, 149.0, 150.0, 148.0, 149.0])
v_err = np.array([6.0, 5.0, 4.0, 4.0, 3.0, 3.0, 3.0, 3.0, 4.0, 4.0, 5.0, 6.0])

ax1.plot(df_ngc['Radius_kpc'], df_ngc['V_tot'], color='#0f172a', lw=3.0, label='총 관측 원운동 속도 $V_{\\mathrm{total}}(R)$')
ax1.plot(df_ngc['Radius_kpc'], df_ngc['V_dm'], color='#2563eb', lw=2.5, ls='--', label='암흑물질 헤일로 기여 $V_{\\mathrm{DM}}(R)$')
ax1.plot(df_ngc['Radius_kpc'], df_ngc['V_disk'], color='#dc2626', lw=2.0, ls='-.', label='항성 원반 기여 $V_{\\mathrm{stars}}(R)$ (가시 바리온)')
ax1.plot(df_ngc['Radius_kpc'], df_ngc['V_gas'], color='#16a34a', lw=1.8, ls=':', label='성간 가스 기여 $V_{\\mathrm{gas}}(R)$ (중성수소 HI)')
ax1.plot(df_ngc['Radius_kpc'], df_ngc['V_kepler'], color='#9333ea', lw=2.0, linestyle=(0, (4, 4)), alpha=0.85, label='케플러 예측선 $V \\propto R^{-1/2}$ (암흑물질 부재 시)')

ax1.errorbar(r_obs, v_obs, yerr=v_err, fmt='o', color='#0284c7', ecolor='#0284c7', elinewidth=1.8, capsize=4, capthick=1.5, markersize=6.5, label='실제 전파/광학 관측 데이터 (Begeman 1989 실측치)', zorder=5)

ax1.axvline(x=16.7, color='#64748b', ls=':', lw=1.5)
ax1.text(17.0, 30, '광학 반경 $R_{25} \\approx 16.7\\,\\mathrm{kpc}$', fontsize=10.5, color='#334155', fontweight='bold')
ax1.axvspan(16.7, 35.0, color='#38bdf8', alpha=0.08, label='외곽 중성수소(HI) 가스 영역 (암흑물질 85%+ 지배)')

ax1.set_title('나선은하 회전곡선 성분별 분해 (NGC 3198 표준 평탄곡선 모델)', fontsize=15, fontweight='bold', pad=14, color='#0f172a')
ax1.set_xlabel('은하 중심으로부터의 반경 $R$ [kpc]', fontsize=12, fontweight='bold')
ax1.set_ylabel('원운동 회전속도 $V$ [km/s]', fontsize=12, fontweight='bold')
ax1.set_xlim(0, 35)
ax1.set_ylim(0, 185)
ax1.grid(True, ls='--', alpha=0.45, color='#cbd5e1')
ax1.legend(loc='lower right', frameon=True, facecolor='#ffffff', edgecolor='#cbd5e1', fontsize=10, framealpha=0.95)

callout1 = (
    "■ 케플러 모순과 암흑물질 입증\n"
    "• 가시광 물질만 존재할 경우: 외곽에서 $V \\propto R^{-1/2}$ 급격 하강 (보라색 점선)\n"
    "• 실제 관측: $30\\,\\mathrm{kpc}$ 외곽까지 $V \\approx 150\\,\\mathrm{km/s}$ 완벽 수평 유지\n"
    "• 광학 반경 $R_{25}$ 내부 실제 암흑물질 질량: $M_{\\mathrm{DM}} = 6.76 \\times 10^{10}\\,M_\\odot$\n"
    "• 광학 반경 $R_{25}$ 내부 암흑물질 비율: $f_{\\mathrm{DM}} = 77.5\\%$"
)
ax1.text(0.03, 0.96, callout1, transform=ax1.transAxes, verticalalignment='top', fontsize=9.5,
         bbox=dict(boxstyle='round,pad=0.6', facecolor='#ffffff', edgecolor='#94a3b8', alpha=0.95))

p1_file = os.path.join(OUT_DIR, '그래프1_NGC3198_회전곡선_암흑물질_분해.png')
fig1.savefig(p1_file, bbox_inches='tight')
plt.close(fig1)
print(f"  [+] 저장 완료: {p1_file}")

# -------------------------------------------------------------------------
# [Plot 2] 반경별 누적 질량 및 암흑물질 %비율 곡선
# -------------------------------------------------------------------------
print("\n>> [3/5] 그래프 2: 반경별 누적 질량과 암흑물질 비율 곡선 생성 중...")
fig2, (ax2_top, ax2_bottom) = plt.subplots(2, 1, figsize=(11, 10), dpi=300, sharex=True, gridspec_kw={'height_ratios': [1.2, 1.0]})
fig2.subplots_adjust(hspace=0.15)
ax2_top.set_facecolor('#f8fafc')
ax2_bottom.set_facecolor('#f8fafc')

# Top Panel: Mass M(<R)
ax2_top.plot(df_ngc['Radius_kpc'], df_ngc['M_tot_Msun'] / 1e10, color='#0f172a', lw=3.0, label='총 동역학 질량 $M_{\\mathrm{dyn}}(<R) = \\frac{V^2 R}{G}$')
ax2_top.plot(df_ngc['Radius_kpc'], df_ngc['M_dm_Msun'] / 1e10, color='#2563eb', lw=2.8, ls='--', label='실제 암흑물질 누적 질량 $M_{\\mathrm{DM}}(<R)$')
ax2_top.plot(df_ngc['Radius_kpc'], df_ngc['M_bar_Msun'] / 1e10, color='#dc2626', lw=2.2, ls='-.', label='가시 바리온 누적 질량 $M_{\\mathrm{bar}}(<R)$ ($M_* + M_{\\mathrm{gas}}$)')
ax2_top.fill_between(df_ngc['Radius_kpc'], df_ngc['M_bar_Msun'] / 1e10, df_ngc['M_tot_Msun'] / 1e10, color='#3b82f6', alpha=0.15, label='암흑물질 질량 영역 ($M_{\\mathrm{DM}}$)')

# Mass cross-over point
cross_r = 6.5
cross_m = np.interp(cross_r, df_ngc['Radius_kpc'], df_ngc['M_dm_Msun'] / 1e10)
ax2_top.plot(cross_r, cross_m, 'o', color='#b91c1c', markersize=8)
ax2_top.annotate(f'질량 역전 교차점 ($R \\approx {cross_r}\\,\\mathrm{{kpc}}$)\n암흑물질 질량이 바리온 질량을 추월',
                 xy=(cross_r, cross_m), xytext=(cross_r + 3.0, cross_m + 2.0),
                 arrowprops=dict(facecolor='#b91c1c', shrink=0.08, width=1.5, headwidth=6),
                 fontsize=10, fontweight='bold', color='#991b1b',
                 bbox=dict(boxstyle='round,pad=0.4', facecolor='#fee2e2', edgecolor='#f87171'))

ax2_top.set_title('반경에 따른 누적 질량 분포 및 암흑물질 질량 분율 ($M(<R)$ & $f_{\\mathrm{DM}}$)', fontsize=15, fontweight='bold', pad=14, color='#0f172a')
ax2_top.set_ylabel('누적 질량 [$10^{10}\\,M_\\odot$]', fontsize=12, fontweight='bold')
ax2_top.set_xlim(0, 35)
ax2_top.set_ylim(0, 18)
ax2_top.grid(True, ls='--', alpha=0.45, color='#cbd5e1')
ax2_top.legend(loc='upper left', frameon=True, facecolor='#ffffff', edgecolor='#cbd5e1', fontsize=9.5, framealpha=0.95)

# Bottom Panel: f_DM(%)
ax2_bottom.plot(df_ngc['Radius_kpc'], df_ngc['f_dm_percent'], color='#7c3aed', lw=3.0, label='암흑물질 질량 분율 $f_{\\mathrm{DM}}(<R) = \\frac{M_{\\mathrm{DM}}}{M_{\\mathrm{dyn}}} \\times 100\\%$')
ax2_bottom.axhline(y=50.0, color='#ef4444', ls='--', lw=1.8, label='50% 경계선 (암흑물질 우세 분기점)')
ax2_bottom.fill_between(df_ngc['Radius_kpc'], 0, 50, color='#fca5a5', alpha=0.15)
ax2_bottom.fill_between(df_ngc['Radius_kpc'], 50, 100, color='#c4b5fd', alpha=0.18)

# R25 annotation
f_r25 = np.interp(16.7, df_ngc['Radius_kpc'], df_ngc['f_dm_percent'])
ax2_bottom.plot(16.7, f_r25, 'o', color='#5b21b6', markersize=8)
ax2_bottom.annotate(f'광학 반경 $R_{{25}} = 16.7\\,\\mathrm{{kpc}}$: $f_{{\\mathrm{{DM}}}} = {f_r25:.1f}\\%$',
                    xy=(16.7, f_r25), xytext=(12.0, 85.0),
                    arrowprops=dict(facecolor='#5b21b6', shrink=0.08, width=1.5, headwidth=6),
                    fontsize=10.5, fontweight='bold', color='#4c1d95',
                    bbox=dict(boxstyle='round,pad=0.4', facecolor='#ede9fe', edgecolor='#a78bfa'))

ax2_bottom.set_xlabel('은하 중심으로부터의 반경 $R$ [kpc]', fontsize=12, fontweight='bold')
ax2_bottom.set_ylabel('암흑물질 비율 $f_{\\mathrm{DM}}$ [%]', fontsize=12, fontweight='bold')
ax2_bottom.set_ylim(0, 100)
ax2_bottom.grid(True, ls='--', alpha=0.45, color='#cbd5e1')
ax2_bottom.legend(loc='lower right', frameon=True, facecolor='#ffffff', edgecolor='#cbd5e1', fontsize=9.5, framealpha=0.95)

p2_file = os.path.join(OUT_DIR, '그래프2_반경별_암흑물질_질량과_비율_곡선.png')
fig2.savefig(p2_file, bbox_inches='tight')
plt.close(fig2)
print(f"  [+] 저장 완료: {p2_file}")

# -------------------------------------------------------------------------
# [Plot 3] M31 안드로메다 은하 전용 회전곡선 및 암흑물질 차트
# -------------------------------------------------------------------------
print("\n>> [4/5] 그래프 3: M31 안드로메다 은하 암흑물질 차트 생성 중...")
fig3, ax3 = plt.subplots(figsize=(11, 7.5), dpi=300)
ax3.set_facecolor('#f8fafc')

ax3.plot(df_m31['Radius_kpc'], df_m31['V_tot'], color='#0f172a', lw=3.0, label='M31 총 회전속도 $V_{\\mathrm{total}}(R)$ (합성)')
ax3.plot(df_m31['Radius_kpc'], df_m31['V_dm'], color='#2563eb', lw=2.5, ls='--', label='암흑물질 헤일로 $V_{\\mathrm{DM}}(R)$')
ax3.plot(df_m31['Radius_kpc'], df_m31['V_disk'], color='#dc2626', lw=2.0, ls='-.', label='항성 원반 $V_{\\mathrm{disk}}(R)$')
ax3.plot(df_m31['Radius_kpc'], df_m31['V_bulge'], color='#ea580c', lw=1.8, ls=':', label='중심 팽대부 $V_{\\mathrm{bulge}}(R)$')

ax3.axvline(x=12.02, color='#64748b', ls=':', lw=1.5)
ax3.text(12.3, 50, 'NED-LVS 광학 반경 $R \\approx 12.0\\,\\mathrm{kpc}$', fontsize=10, color='#334155', fontweight='bold')

ax3.set_title('안드로메다 은하 (M31) 회전곡선 및 암흑물질 분해 (Chemin+2009 실측 모델)', fontsize=15, fontweight='bold', pad=14, color='#0f172a')
ax3.set_xlabel('은하 중심으로부터의 반경 $R$ [kpc]', fontsize=12, fontweight='bold')
ax3.set_ylabel('회전속도 $V$ [km/s]', fontsize=12, fontweight='bold')
ax3.set_xlim(0, 35)
ax3.set_ylim(0, 290)
ax3.grid(True, ls='--', alpha=0.45, color='#cbd5e1')
ax3.legend(loc='lower right', frameon=True, facecolor='#ffffff', edgecolor='#cbd5e1', fontsize=10, framealpha=0.95)

callout3 = (
    "■ 안드로메다 은하 (M31) 계산값\n"
    "• 거리: $D = 0.80\\,\\mathrm{Mpc}$, 평탄 회전속도: $V_{\\mathrm{rot}} = 250\\,\\mathrm{km/s}$\n"
    "• 항성 질량: $M_* = 6.37 \\times 10^{10}\\,M_\\odot$\n"
    "• 총 동역학 질량: $M_{\\mathrm{dyn}} = 1.75 \\times 10^{11}\\,M_\\odot$\n"
    "• ① 실제 암흑물질 질량: $M_{\\mathrm{DM}} = 1.11 \\times 10^{11}\\,M_\\odot$\n"
    "• ② 암흑물질 %비율: $f_{\\mathrm{DM}} = 63.5\\%$"
)
ax3.text(0.03, 0.96, callout3, transform=ax3.transAxes, verticalalignment='top', fontsize=9.5,
         bbox=dict(boxstyle='round,pad=0.6', facecolor='#ffffff', edgecolor='#94a3b8', alpha=0.95))

p3_file = os.path.join(OUT_DIR, '그래프3_M31_안드로메다_회전곡선_암흑물질.png')
fig3.savefig(p3_file, bbox_inches='tight')
plt.close(fig3)
print(f"  [+] 저장 완료: {p3_file}")

# -------------------------------------------------------------------------
# [Plot 4] 대표 벤치마크 은하 8종 암흑물질 vs 항성 질량 비교 막대 차트
# -------------------------------------------------------------------------
print("\n>> [5/5] 그래프 4: 대표 은하 8종 암흑물질 비교 차트 생성 중...")
fig4, ax4 = plt.subplots(figsize=(13, 7.5), dpi=300)
ax4.set_facecolor('#f8fafc')

names_short = ['안드로메다\n(M31)', 'NGC 3198\n(표준)', '삼각형자리\n(M33)', 'NGC 2403', '조각가은하\n(NGC 253)', '보데은하\n(M81)', '바람개비\n(M101)', '소용돌이\n(M51a)']
x = np.arange(len(df_bench))
w = 0.38

bars_star = ax4.bar(x - w/2, np.log10(df_bench['M_star_Msun']), width=w, color='#3b82f6', edgecolor='#1d4ed8', lw=1.2, label='항성 질량 $\\log_{10}(M_* / M_\\odot)$ (가시 바리온)')
bars_dm = ax4.bar(x + w/2, np.log10(df_bench['M_DM_Msun']), width=w, color='#8b5cf6', edgecolor='#6d28d9', lw=1.2, label='실제 암흑물질 질량 $\\log_{10}(M_{\\mathrm{DM}} / M_\\odot)$')

# Print % on top of DM bars
for i in range(len(df_bench)):
    f_pct = df_bench['f_DM_percent'].iloc[i]
    y_h = np.log10(df_bench['M_DM_Msun'].iloc[i])
    ax4.text(x[i] + w/2, y_h + 0.12, f'{f_pct:.1f}%', ha='center', va='bottom', fontsize=10, fontweight='bold', color='#4c1d95')

ax4.set_title('NED-LVS 대표 은하 8종의 암흑물질 실제 질량 및 %비율 비교', fontsize=15, fontweight='bold', pad=14, color='#0f172a')
ax4.set_xticks(x)
ax4.set_xticklabels(names_short, fontsize=10.5, fontweight='bold')
ax4.set_ylabel('로그 질량 [$\\log_{10}(M / M_\\odot)$]', fontsize=12, fontweight='bold')
ax4.set_ylim(8.5, 12.0)
ax4.grid(True, ls='--', alpha=0.45, color='#cbd5e1', axis='y')
ax4.legend(loc='upper left', frameon=True, facecolor='#ffffff', edgecolor='#cbd5e1', fontsize=10, framealpha=0.95)

p4_file = os.path.join(OUT_DIR, '그래프4_대표은하8종_암흑물질_질량과_비율_비교.png')
fig4.savefig(p4_file, bbox_inches='tight')
plt.close(fig4)
print(f"  [+] 저장 완료: {p4_file}")

# -------------------------------------------------------------------------
# Copy all generated plots to Downloads folder
# -------------------------------------------------------------------------
print("\n>> 생성된 모든 그래프 이미지를 다운로드 폴더로 복사 중...")
generated_plots = [
    '그래프1_NGC3198_회전곡선_암흑물질_분해.png',
    '그래프2_반경별_암흑물질_질량과_비율_곡선.png',
    '그래프3_M31_안드로메다_회전곡선_암흑물질.png',
    '그래프4_대표은하8종_암흑물질_질량과_비율_비교.png'
]

for p in generated_plots:
    src = os.path.join(OUT_DIR, p)
    dst = os.path.join(DOWNLOADS_DIR, p)
    shutil.copy2(src, dst)
    print(f"  -> 복사 완료: {dst}")

# -------------------------------------------------------------------------
# Update the ZIP archive in Downloads with all plots & C++ source & binary!
# -------------------------------------------------------------------------
zip_path = os.path.join(DOWNLOADS_DIR, '은하_회전곡선_암흑물질_계산자료.zip')
print(f"\n>> 다운로드 폴더 압축 파일 갱신 중: {zip_path}...")

with zipfile.ZipFile(zip_path, 'a', zipfile.ZIP_DEFLATED) as zf:
    # Add C++ source and binary
    if os.path.exists('dark_matter_calculator.cpp'):
        zf.write('dark_matter_calculator.cpp', 'C++_소스코드_dark_matter_calculator.cpp')
    if os.path.exists('dark_matter_calculator.exe'):
        zf.write('dark_matter_calculator.exe', 'C++_실행파일_dark_matter_calculator.exe')
    # Add Python plot script
    zf.write('generate_dark_matter_plots.py', 'Python_그래프생성스크립트.py')
    # Add all generated plots
    for p in generated_plots:
        zf.write(os.path.join(OUT_DIR, p), f'그래프_{p}')

print("[!] 모든 C++ 및 파이썬 파이프라인과 그래프 생성이 성공적으로 완료되었습니다!")
print("="*75)
