import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

df = pd.read_csv('output/CEERS_JWST_은하_암흑물질_전수계산_7만7천개.csv')
z = df['Redshift_z'].values
log_mstar = df['log10_Mstar_Msun'].values
log_mdyn = df['log10_Mdyn_Msun'].values
log_mdm = df['log10_MDM_Msun'].values
fdm = df['f_DM_percent'].values
r_kpc = df['Radius_kpc'].values

# 1. Figure 1: z vs f_DM
plt.figure(figsize=(9, 7), dpi=300)
hb = plt.hexbin(z, fdm, gridsize=55, cmap='viridis', mincnt=1, bins='log')
cb = plt.colorbar(hb, pad=0.02)
cb.set_label('은하 수 (Log10 Count)', fontsize=11, fontweight='bold')
z_bins = np.linspace(0.2, 8.0, 20)
bin_centers = 0.5 * (z_bins[:-1] + z_bins[1:])
binned_fdm = [np.median(fdm[(z >= z_bins[i]) & (z < z_bins[i+1])]) for i in range(len(z_bins)-1)]
plt.plot(bin_centers, binned_fdm, 'r-o', linewidth=2.5, markersize=6, label=f'적색편이별 중앙값 (~{np.mean(binned_fdm):.1f}%)')
plt.xlabel('적색편이 (Redshift $z$)', fontsize=12, fontweight='bold')
plt.ylabel('암흑물질 질량 비율 $f_{\\mathrm{DM}}$ (%)', fontsize=12, fontweight='bold')
plt.title('JWST CEERS 은하 암흑물질 비율의 우주론적 진화 ($z = 0.1 \\sim 10$)', fontsize=13, fontweight='bold')
plt.xlim(0, 8.5)
plt.ylim(0, 100)
plt.grid(True, linestyle='--', alpha=0.5)
plt.legend(loc='lower right', frameon=True, fontsize=10)
plt.tight_layout()
plt.savefig('output/CEERS_그래프1_적색편이별_암흑물질비율_진화.png', dpi=300)
plt.close()

# 2. Figure 2: Mstar vs Mdyn
plt.figure(figsize=(9, 7), dpi=300)
hb = plt.hexbin(log_mstar, log_mdyn, gridsize=55, cmap='plasma', mincnt=1, bins='log')
cb = plt.colorbar(hb, pad=0.02)
cb.set_label('은하 수 (Log10 Count)', fontsize=11, fontweight='bold')
m_line = np.linspace(5.0, 11.5, 100)
plt.plot(m_line, m_line, 'k--', linewidth=2, label='바리온 한계 ($M_{\\mathrm{dyn}} = M_*$, 암흑물질 0%)')
plt.plot(m_line, m_line + np.log10(2), 'c-', linewidth=2, label='$M_{\\mathrm{dyn}} = 2M_*$ ($f_{\\mathrm{DM}} = 50\\%$)')
plt.plot(m_line, m_line + 1.0, 'm-', linewidth=2, label='$M_{\\mathrm{dyn}} = 10M_*$ ($f_{\\mathrm{DM}} = 90\\%$)')
plt.xlabel('항성 질량 $\\log_{10}(M_* / M_\\odot)$ [CEERS SED Fitting]', fontsize=12, fontweight='bold')
plt.ylabel('총 역학 질량 $\\log_{10}(M_{\\mathrm{dyn}} / M_\\odot)$', fontsize=12, fontweight='bold')
plt.title('JWST CEERS 항성 질량 대 총 역학 질량 스케일링 관계', fontsize=13, fontweight='bold')
plt.xlim(5.0, 11.5)
plt.ylim(6.0, 12.5)
plt.grid(True, linestyle='--', alpha=0.5)
plt.legend(loc='upper left', frameon=True, fontsize=10)
plt.tight_layout()
plt.savefig('output/CEERS_그래프2_항성질량_역학질량_관계.png', dpi=300)
plt.close()

# 3. Figure 3: f_DM PDF & CDF
plt.figure(figsize=(9, 7), dpi=300)
ax = plt.gca()
ax.hist(fdm, bins=50, range=(0, 100), density=True, color='royalblue', alpha=0.65, edgecolor='black', label='PDF (확률밀도)')
ax.set_xlabel('암흑물질 백분율 비율 $f_{\\mathrm{DM}}$ (%)', fontsize=12, fontweight='bold')
ax.set_ylabel('확률 밀도 (Density)', fontsize=12, fontweight='bold', color='royalblue')
ax.tick_params(axis='y', labelcolor='royalblue')
ax.set_xlim(0, 100)
ax.grid(True, linestyle='--', alpha=0.5)

ax_twin = ax.twinx()
sorted_fdm = np.sort(fdm)
cdf = np.arange(1, len(sorted_fdm) + 1) / len(sorted_fdm)
ax_twin.plot(sorted_fdm, cdf, color='crimson', linewidth=2.8, label='CDF (누적분포)')
ax_twin.set_ylabel('누적 비율 (CDF)', fontsize=12, fontweight='bold', color='crimson')
ax_twin.tick_params(axis='y', labelcolor='crimson')
ax_twin.set_ylim(0, 1.05)
med_fdm = np.median(fdm)
ax.axvline(med_fdm, color='black', linestyle='--', linewidth=2, label=f'중앙값: {med_fdm:.1f}%')
ax.set_title('JWST CEERS 전체 은하 암흑물질 비율 분포 및 CDF', fontsize=13, fontweight='bold')
ax.legend(loc='upper left', frameon=True, fontsize=10)
ax_twin.legend(loc='center left', frameon=True, fontsize=10)
plt.tight_layout()
plt.savefig('output/CEERS_그래프3_암흑물질비율_분포_및_CDF.png', dpi=300)
plt.close()

print("Individual CEERS plots successfully generated.")
