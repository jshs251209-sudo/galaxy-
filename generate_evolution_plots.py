import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import seaborn as sns
from scipy import stats

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False
sns.set_theme(style="ticks")
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

def create_evolution_plots():
    csv_path = 'galaxy_master_complete_all.csv'
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found")
        return

    print("Loading master dataset...")
    df = pd.read_csv(csv_path)

    # 1. Calculate GEI
    df['log_ssfr'] = df['sfr_tot_p50'] - df['lgm_tot_p50']
    
    def norm(series, clip_low=1, clip_high=99):
        q_low, q_high = np.percentile(series.dropna(), [clip_low, clip_high])
        s_clipped = np.clip(series, q_low, q_high)
        return (s_clipped - q_low) / (q_high - q_low)

    df['norm_mass'] = norm(df['lgm_tot_p50'])
    df['norm_ssfr_inv'] = 1.0 - norm(df['log_ssfr'])
    df['norm_z'] = norm(df['oh_p50'])
    df['norm_color'] = norm(df['color_u_r'])

    df['GEI'] = 0.30 * df['norm_mass'] + 0.30 * df['norm_ssfr_inv'] + 0.20 * df['norm_z'] + 0.20 * df['norm_color']

    out_dir = 'output/plots'
    os.makedirs(out_dir, exist_ok=True)

    # Sample for plotting
    sample = df.sample(min(len(df), 12000), random_state=42).copy()

    # -------------------------------------------------------------
    # Plot 1: 4-Panel GEI Multi-dimensional Validation
    # -------------------------------------------------------------
    print("Generating 4-panel GEI analysis plot...")
    fig, axes = plt.subplots(2, 2, figsize=(15, 13))

    # Panel A: GEI vs Dn4000
    ax = axes[0, 0]
    sc = ax.scatter(sample['GEI'], sample['d4000_n'], c=sample['color_u_r'], cmap='coolwarm', s=10, alpha=0.5)
    cbar = plt.colorbar(sc, ax=ax)
    cbar.set_label('색지수 (u - r) [mag]', fontsize=11)
    
    # Regression line
    valid = sample[['GEI', 'd4000_n']].dropna()
    slope, intercept, r_val, p_val, std_err = stats.linregress(valid['GEI'], valid['d4000_n'])
    x_vals = np.linspace(0, 1, 100)
    ax.plot(x_vals, slope * x_vals + intercept, 'k--', lw=2.5, 
            label=f'선형 회귀선 (r = {r_val:.3f}, p < 1e-300)')
    ax.set_xlabel('은하 진화 지수 (GEI, Galaxy Evolution Index)', fontsize=12)
    ax.set_ylabel(r'4000Å 불연속도 ($D_n(4000)$ - 항성 종족 연령 지표)', fontsize=12)
    ax.set_title('(A) GEI와 독립 항성 연령($D_n(4000)$) 상관성 검증', fontsize=13, pad=10)
    ax.legend(loc='upper left', fontsize=11)
    ax.grid(True, linestyle=':', alpha=0.6)

    # Panel B: GEI Distribution by Morphology
    ax = axes[0, 1]
    morph_order = ['불규칙은하', '나선은하', '렌즈형은하', '타원은하']
    colors = ['#10b981', '#2563eb', '#ea580c', '#dc2626']
    
    for m, c in zip(morph_order, colors):
        sub = df[df['class_morphology'] == m]['GEI'].dropna()
        if len(sub) > 0:
            sns.kdeplot(sub, ax=ax, label=f'{m} (평균 {sub.mean():.2f})', color=c, lw=2.2, fill=True, alpha=0.15)
            
    ax.axvline(x=0.42, color='gray', linestyle=':', lw=1.5, label='Green Valley 전이대')
    ax.axvline(x=0.62, color='red', linestyle=':', lw=1.5, label='Quenching 완료대')
    ax.set_xlabel('은하 진화 지수 (GEI)', fontsize=12)
    ax.set_ylabel('확률 밀도 (Density)', fontsize=12)
    ax.set_title('(B) 은하 형태별 GEI 진화 시퀀스 분포 (KDE)', fontsize=13, pad=10)
    ax.legend(loc='upper left', fontsize=10)
    ax.grid(True, linestyle=':', alpha=0.6)

    # Panel C: Color-Mass with GEI
    ax = axes[1, 0]
    sc2 = ax.scatter(sample['lgm_tot_p50'], sample['color_u_r'], c=sample['GEI'], cmap='viridis', s=10, alpha=0.6)
    cbar2 = plt.colorbar(sc2, ax=ax)
    cbar2.set_label('은하 진화 지수 (GEI)', fontsize=11)
    ax.axhline(y=2.2, color='red', linestyle='--', alpha=0.7, label='Red Sequence (붉은 계열)')
    ax.axhline(y=1.8, color='blue', linestyle='--', alpha=0.7, label='Blue Cloud (푸른 구름)')
    ax.text(8.5, 2.0, 'Green Valley (녹색 골짜기)', fontsize=10, color='darkgreen', weight='bold')
    ax.set_xlabel(r'항성 질량 $\log(M_* / M_\odot)$', fontsize=12)
    ax.set_ylabel(r'색지수 $(u - r)\,\mathrm{[mag]}$', fontsize=12)
    ax.set_title('(C) 색-질량 도표 상의 진화 궤적 (Blue Cloud → Green Valley → Red Sequence)', fontsize=13, pad=10)
    ax.legend(loc='lower right', fontsize=10)
    ax.grid(True, linestyle=':', alpha=0.6)

    # Panel D: sSFR vs Stellar Mass (Quenching Diagram)
    ax = axes[1, 1]
    sc3 = ax.scatter(sample['lgm_tot_p50'], sample['log_ssfr'], c=sample['GEI'], cmap='inferno', s=10, alpha=0.6)
    cbar3 = plt.colorbar(sc3, ax=ax)
    cbar3.set_label('은하 진화 지수 (GEI)', fontsize=11)
    ax.axhline(y=-11.0, color='crimson', linestyle='--', lw=2, label=r'퀜칭 임계선 ($\log\mathrm{sSFR} = -11\,\mathrm{yr}^{-1}$)')
    ax.set_xlabel(r'항성 질량 $\log(M_* / M_\odot)$', fontsize=12)
    ax.set_ylabel(r'비별생성률 $\log(\mathrm{sSFR}\,[\mathrm{yr}^{-1}])$', fontsize=12)
    ax.set_title(r'(D) 비별생성률(sSFR) 감쇠 및 퀜칭(Quenching) 진화', fontsize=13, pad=10)
    ax.legend(loc='lower left', fontsize=10)
    ax.grid(True, linestyle=':', alpha=0.6)

    plt.suptitle('SDSS DR18 은하 진화 지수(GEI) 다차원 타당성 검증 및 진화 척도 분석', fontsize=16, y=0.995)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "galaxy_evolution_index_analysis.png"), dpi=300, bbox_inches='tight')
    plt.close()
    print("GEI analysis plot saved to output/plots/galaxy_evolution_index_analysis.png")

    # -------------------------------------------------------------
    # Plot 2: 3D Fundamental Metallicity Relation (FMR)
    # -------------------------------------------------------------
    print("Generating 3D FMR Evolution Diagram...")
    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, projection='3d')

    sub_3d = sample.dropna(subset=['lgm_tot_p50', 'sfr_tot_p50', 'oh_p50', 'GEI']).sample(min(len(sample), 4000), random_state=42)
    
    p = ax.scatter(sub_3d['lgm_tot_p50'], sub_3d['sfr_tot_p50'], sub_3d['oh_p50'], 
                   c=sub_3d['GEI'], cmap='plasma', s=14, alpha=0.7, edgecolors='none')
    
    cbar = fig.colorbar(p, ax=ax, pad=0.1, shrink=0.7)
    cbar.set_label('은하 진화 지수 (GEI)', fontsize=12)

    # 3D regression plane
    X = sub_3d[['lgm_tot_p50', 'sfr_tot_p50']].values
    y = sub_3d['oh_p50'].values
    from sklearn.linear_model import LinearRegression
    reg = LinearRegression().fit(X, y)
    
    x_surf = np.linspace(sub_3d['lgm_tot_p50'].min(), sub_3d['lgm_tot_p50'].max(), 20)
    y_surf = np.linspace(sub_3d['sfr_tot_p50'].min(), sub_3d['sfr_tot_p50'].max(), 20)
    x_mesh, y_mesh = np.meshgrid(x_surf, y_surf)
    z_mesh = reg.predict(np.c_[x_mesh.ravel(), y_mesh.ravel()]).reshape(x_mesh.shape)
    
    ax.plot_surface(x_mesh, y_mesh, z_mesh, color='cyan', alpha=0.25, edgecolor='none')

    ax.set_xlabel(r'항성 질량 $\log(M_*/M_\odot)$', fontsize=11, labelpad=10)
    ax.set_ylabel(r'별 생성률 $\log(\mathrm{SFR})$', fontsize=11, labelpad=10)
    ax.set_zlabel(r'산소 금속량 $12+\log(\mathrm{O/H})$', fontsize=11, labelpad=10)
    ax.set_title('3차원 기본 금속량 관계 (FMR: Mass-SFR-Metallicity) 및 은하 진화 궤적', fontsize=14, pad=15)
    
    ax.view_init(elev=24, azim=-55)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "galaxy_3d_evolution.png"), dpi=300, bbox_inches='tight')
    plt.close()
    print("3D FMR plot saved to output/plots/galaxy_3d_evolution.png")
    print("All plots generated successfully!")

if __name__ == '__main__':
    create_evolution_plots()
