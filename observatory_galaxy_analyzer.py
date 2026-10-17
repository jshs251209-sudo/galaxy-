"""
observatory_galaxy_analyzer.py
================================================================================
[연구 과제 3] 천문대 관측 은하 진화 단계 판별 및 과거·미래 진화 예측 프로그램
================================================================================
천문대에서 직접 관측한 은하(또는 관측 카탈로그 은하)의 물리량(질량/등급, 거리/적색편이,
반경/시직경, 회전속도/속도분산, H-alpha 플럭스/별생성률, 광학 색지수, 방출선 플럭스비 등)을
입력하면:
  1. 결측된 보조 물리량(동역학 질량, 암흑물질 질량·분율, 비별생성률, 표면밀도 등)을 자동 유도하고,
  2. 차세대 5축 통합 은하 진화 지수 (Unified GEI v2.0, 0.000~1.000 및 100점 환산)를 산출하며,
  3. 현재 은하가 5단계 진화 단계(Stage I ~ Stage V) 중 어느 단계의 몇 % 지점에 있는지 판별하고,
  4. 미분방정식(ODE) 진화 모델을 통해 과거(-10 Gyr ~ 현재) 어떤 모습이었는지 복원하고
     향후(현재 ~ +10 Gyr) 어떻게 진화할 것인지 정량 예측 및 300 DPI 진단 리포트 차트를 생성합니다.

사용법:
  • 기본 실증 및 대표 관측 은하 진단 리포트 생성:
      python observatory_galaxy_analyzer.py
  • 특정 관측 은하 물리량 직접 입력 분석 (CLI 옵션):
      python observatory_galaxy_analyzer.py --name "천문대관측_NGC3198" --log_mstar 10.29 --log_sfr 0.08 --radius_kpc 16.7 --v_rot 150.0 --color_u_r 1.72
  • 대화형 입력 모드:
      python observatory_galaxy_analyzer.py --interactive
================================================================================
"""

import os
import sys
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

from modules.gei_evolution_engine import (
    EVOLUTION_STAGES,
    OBSERVATORY_BENCHMARK_GALAXIES,
    complete_galaxy_observables,
    compute_unified_gei,
    simulate_galaxy_evolution_trajectory
)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

REPORT_DIR = os.path.join("output", "observatory_reports")
os.makedirs(REPORT_DIR, exist_ok=True)


def generate_single_galaxy_diagnostic_chart(sim_result: dict, save_path: str):
    """
    입력된 관측 은하 1개에 대해 현재 진화 지수(GEI v2.0), 5대 물리 축 분해,
    과거(-10 Gyr) -> 현재(0 Gyr) -> 미래(+10 Gyr) 진화 궤적 및 3D 위상공간 위치를
    한 장의 300 DPI 고해상도 진단 리포트 이미지로 저장합니다.
    """
    cur = sim_result["current"]
    tdf = sim_result["trajectory_df"]
    nar = sim_result["narrative"]
    past_rep = nar["past_representative"]
    fut_rep = nar["future_representative"]

    fig = plt.figure(figsize=(18, 12.5), dpi=300)
    gs = gridspec.GridSpec(2, 2, hspace=0.30, wspace=0.22)

    # -------------------------------------------------------------------------
    # Panel 1 (좌상): 현재 진화 단계 게이지 & 과거-현재-미래 GEI(t) 진화 곡선
    # -------------------------------------------------------------------------
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.set_facecolor("#f8fafc")
    for st in EVOLUTION_STAGES:
        ax1.axhspan(st["gei_min"], st["gei_max"], color=st["color"], alpha=0.12)
        ax1.text(-9.8, 0.5 * (st["gei_min"] + st["gei_max"]),
                 f"{st['code']}: {st['name_kr'].split(': ')[1]}",
                 fontsize=8.8, fontweight="bold", color=st["color"], va="center")

    ax1.axvline(0.0, color="#0f172a", ls="--", lw=1.8, label="현재 관측 시점 (0 Gyr)")
    ax1.plot(tdf["dt_gyr"], tdf["gei_score"], "o-", color="#1e293b", lw=3.0, markersize=6, label="은하 진화 지수 궤적 GEI(t)")
    ax1.scatter([past_rep["dt_gyr"]], [past_rep["gei_score"]], color="#3b82f6", edgecolors="white", s=130, zorder=10,
                label=f"과거 ({past_rep['dt_gyr']:.0f} Gyr): GEI={past_rep['gei_score']:.3f} ({past_rep['stage_code']})")
    ax1.scatter([0.0], [cur["gei_score"]], color=cur["stage_color"], edgecolors="#0f172a", s=220, marker="*", linewidths=1.8, zorder=12,
                label=f"현재 (0 Gyr): GEI={cur['gei_score']:.3f} ({cur['stage_code']})")
    ax1.scatter([fut_rep["dt_gyr"]], [fut_rep["gei_score"]], color="#ef4444", edgecolors="white", s=130, marker="^", zorder=10,
                label=f"미래 (+{fut_rep['dt_gyr']:.0f} Gyr): GEI={fut_rep['gei_score']:.3f} ({fut_rep['stage_code']})")

    ax1.set_xlabel("상대 우주 시간 $\\Delta t$ [Gyr] (과거 $\\leftarrow 0 \\rightarrow$ 미래)", fontsize=11, fontweight="bold")
    ax1.set_ylabel("통합 은하 진화 지수 $\\mathrm{GEI}(t)$", fontsize=11, fontweight="bold")
    ax1.set_xlim(-10.2, 10.2)
    ax1.set_ylim(0.0, 1.0)
    ax1.grid(True, ls="--", alpha=0.4)
    ax1.legend(loc="lower right", fontsize=8.8, frameon=True, facecolor="white")
    ax1.set_title("(A) 관측 은하의 과거 복원 · 현재 진화 단계 · 미래 진화 지수 곡선", fontsize=12.5, fontweight="bold", pad=10)

    # -------------------------------------------------------------------------
    # Panel 2 (우상): 5대 핵심 물리 축 성숙도 분해 (5-Axis Physical Decomposition)
    # -------------------------------------------------------------------------
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.set_facecolor("#f8fafc")
    cats = [
        "별생성 소광도\n$S_{\\mathrm{quench}}$ (30%)",
        "항성질량 축적\n$S_{\\mathrm{mass}}$ (25%)",
        "항성종족 노화\n$S_{\\mathrm{pop}}$ (20%)",
        "구조적 표면밀도\n$S_{\\mathrm{struct}}$ (15%)",
        "암흑물질 헤일로\n$S_{\\mathrm{halo}}$ (10%)"
    ]
    p_vals = [past_rep["s_quench"], past_rep["s_mass"], past_rep["s_pop"], past_rep["s_struct"], past_rep["s_halo"]]
    c_vals = [cur["s_quench"], cur["s_mass"], cur["s_pop"], cur["s_struct"], cur["s_halo"]]
    f_vals = [fut_rep["s_quench"], fut_rep["s_mass"], fut_rep["s_pop"], fut_rep["s_struct"], fut_rep["s_halo"]]

    x_pos = np.arange(len(cats))
    w = 0.25
    ax2.bar(x_pos - w, p_vals, width=w, color="#93c5fd", edgecolor="#2563eb", lw=1.0, label=f"과거 ({past_rep['dt_gyr']:.0f} Gyr 전)")
    ax2.bar(x_pos, c_vals, width=w, color=cur["stage_color"], edgecolor="#0f172a", lw=1.2, label="현재 관측 시점 (0 Gyr)")
    ax2.bar(x_pos + w, f_vals, width=w, color="#fca5a5", edgecolor="#dc2626", lw=1.0, label=f"미래 (+{fut_rep['dt_gyr']:.0f} Gyr 후)")

    for i, v in enumerate(c_vals):
        ax2.text(x_pos[i], v + 0.03, f"{v:.2f}", ha="center", va="bottom", fontsize=9.2, fontweight="bold", color="#0f172a")

    ax2.set_xticks(x_pos)
    ax2.set_xticklabels(cats, fontsize=9.5, fontweight="bold")
    ax2.set_ylabel("정규화 물리 축 점수 [0.0 ~ 1.0]", fontsize=11, fontweight="bold")
    ax2.set_ylim(0, 1.15)
    ax2.grid(True, ls="--", alpha=0.4, axis="y")
    ax2.legend(loc="upper right", fontsize=9.0, frameon=True, facecolor="white")
    ax2.set_title("(B) 5대 물리 축별 과거 · 현재 · 미래 성숙도 점수 비교", fontsize=12.5, fontweight="bold", pad=10)

    # -------------------------------------------------------------------------
    # Panel 3 (좌하): 위상공간 (log M_* vs log sSFR) 및 반경-암흑물질 진화 궤적
    # -------------------------------------------------------------------------
    ax3 = fig.add_subplot(gs[1, 0])
    ax3.set_facecolor("#f8fafc")
    # 배경으로 12대 벤치마크 은하 표시
    for bk, bobs in OBSERVATORY_BENCHMARK_GALAXIES.items():
        bcur = compute_unified_gei(bobs)
        ax3.scatter([bcur["log_mstar"]], [bcur["log_ssfr"]], color="#94a3b8", s=45, alpha=0.6)
        ax3.text(bcur["log_mstar"] + 0.04, bcur["log_ssfr"] + 0.04, bcur["name"].split(" (")[0], fontsize=7.8, color="#64748b")

    ax3.plot(tdf["log_mstar"], tdf["log_ssfr"], "o-", color="#1e293b", lw=2.8, markersize=5, label="과거 → 현재 → 미래 진화 궤적")
    ax3.scatter([past_rep["log_mstar"]], [past_rep["log_ssfr"]], color="#3b82f6", s=110, zorder=10, label=f"과거 ({past_rep['dt_gyr']:.0f} Gyr)")
    ax3.scatter([cur["log_mstar"]], [cur["log_ssfr"]], color=cur["stage_color"], edgecolors="black", s=230, marker="*", zorder=12, label="현재 관측 위치")
    ax3.scatter([fut_rep["log_mstar"]], [fut_rep["log_ssfr"]], color="#ef4444", s=110, marker="^", zorder=10, label=f"미래 (+{fut_rep['dt_gyr']:.0f} Gyr)")

    ax3.axhline(-10.2, color="#10b981", ls="--", lw=1.4, label="주계열 / 녹색 계곡 경계")
    ax3.axhline(-11.2, color="#ef4444", ls="--", lw=1.4, label="녹색 계곡 / 완전 소광 경계")
    ax3.set_xlabel("항성 질량 $\\log_{10}(M_*/M_\\odot)$", fontsize=11, fontweight="bold")
    ax3.set_ylabel("비별생성률 $\\log_{10}(\\mathrm{sSFR}\\,[\\mathrm{yr}^{-1}])$", fontsize=11, fontweight="bold")
    ax3.set_xlim(8.0, 12.2)
    ax3.set_ylim(-13.0, -7.8)
    ax3.grid(True, ls="--", alpha=0.4)
    ax3.legend(loc="lower left", fontsize=8.8, frameon=True, facecolor="white")
    ax3.set_title("(C) 질량–비별생성률 위상공간 내 현재 위치 및 과거·미래 이동 경로", fontsize=12.5, fontweight="bold", pad=10)

    # -------------------------------------------------------------------------
    # Panel 4 (우하): 종합 진단 카드 (현재 진화단계, 과거 모습 복원, 미래 진화 예측 리포트)
    # -------------------------------------------------------------------------
    ax4 = fig.add_subplot(gs[1, 1])
    ax4.axis("off")
    report_txt = (
        f"■ 관측 은하 정밀 진화 판독 리포트: {cur.get('name', '사용자 관측 은하')}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"▶ [현재 진화 단계 판별]\n"
        f"  • 통합 은하 진화 지수 (GEI v2.0): {cur['gei_score']:.3f}  (100점 만점 기준 {cur['gei_100']:.1f}점)\n"
        f"  • 판별 진화 단계: {cur['stage_name_kr']} (단계 내 진행도 {cur['stage_progress_pct']:.1f}%)\n"
        f"  • 대응 형태학적 특징: {cur['morphology_typical']}\n"
        f"  • 핵심 물리량: log(M*)={cur['log_mstar']:.2f} $M_\\odot$ | log(SFR)={cur['log_sfr']:.2f} | log(sSFR)={cur['log_ssfr']:.2f}\n"
        f"                 반경 R={cur['radius_kpc']:.2f} kpc | V_rot={cur['v_rot']:.1f} km/s | 암흑물질 비율 f_DM={cur['f_dm_percent']:.1f}%\n\n"
        f"▶ [과거 모습 복원 ({past_rep['epoch_label']}, 우주 나이 {past_rep['cosmic_age_t_gyr']:.1f} Gyr)]\n"
        f"  • 과거 진화 지수: GEI = {past_rep['gei_score']:.3f} ({past_rep['stage_name_kr']})\n"
        f"  • 과거 물리 상태: log(M*)={past_rep['log_mstar']:.2f} $M_\\odot$, 반경 R={past_rep['radius_kpc']:.2f} kpc,\n"
        f"                    log(SFR)={past_rep['log_sfr']:.2f}, 색지수(u-r)={past_rep['color_u_r']:.2f}, f_DM={past_rep['f_dm_percent']:.1f}%\n"
        f"  • 복원 해석: {cur['past_summary']}\n\n"
        f"▶ [미래 진화 예측 ({fut_rep['epoch_label']})]\n"
        f"  • 미래 진화 지수: GEI = {fut_rep['gei_score']:.3f} ({fut_rep['stage_name_kr']})\n"
        f"  • 미래 물리 상태: log(M*)={fut_rep['log_mstar']:.2f} $M_\\odot$, 반경 R={fut_rep['radius_kpc']:.2f} kpc,\n"
        f"                    log(SFR)={fut_rep['log_sfr']:.2f}, 색지수(u-r)={fut_rep['color_u_r']:.2f}, f_DM={fut_rep['f_dm_percent']:.1f}%\n"
        f"  • 녹색 계곡 진입: {nar['time_to_green_valley']} | 완전 소광 도달: {nar['time_to_full_quenching']}"
    )
    ax4.text(
        0.02, 0.98, report_txt, transform=ax4.transAxes, va="top", ha="left",
        fontsize=9.6, linespacing=1.45, color="#0f172a",
        bbox=dict(boxstyle="round,pad=0.65", facecolor="#f8fafc", edgecolor=cur["stage_color"], lw=2.2)
    )
    ax4.set_title("(D) 관측 은하 과거 복원 · 현재 진화단계 · 미래 예측 종합 진단서", fontsize=12.5, fontweight="bold", pad=10)

    fig.suptitle(
        f"천문대 관측 은하 진화 단계 판별 리포트 — {cur.get('name', '관측 은하')}  [GEI = {cur['gei_score']:.3f} | {cur['stage_name_kr']}]",
        fontsize=15.5, fontweight="bold", y=0.98, color="#0f172a"
    )
    fig.savefig(save_path, bbox_inches="tight")
    plt.close(fig)


def print_detailed_console_report(sim_result: dict):
    """콘솔에 관측 은하의 현재 진화단계, 과거 모습 복원, 미래 진화 예측 리포트를 출력합니다."""
    cur = sim_result["current"]
    nar = sim_result["narrative"]
    tdf = sim_result["trajectory_df"]

    print("\n" + "=" * 88)
    print(f" 🔭 [천문대 관측 은하 진화 단계 분석 결과] : {cur.get('name', '관측 은하')}")
    print("=" * 88)
    print(f"  • 통합 은하 진화 지수 (GEI v2.0) : {cur['gei_score']:.4f}  (100점 환산: {cur['gei_100']:.1f} / 100)")
    print(f"  • 현재 은하 진화 단계 판별       : {cur['stage_name_kr']} (단계 내 진행률: {cur['stage_progress_pct']:.1f}%)")
    print(f"  • 전형적 형태 분류               : {cur['morphology_typical']}")
    print("-" * 88)
    print("  [5대 물리 축 정규화 점수 분해]")
    print(f"    1) 별생성 소광도 (S_quench, 30%) : {cur['s_quench']:.3f}   (log sSFR = {cur['log_ssfr']:.2f} yr^-1)")
    print(f"    2) 항성질량 성숙도 (S_mass, 25%) : {cur['s_mass']:.3f}   (log M* = {cur['log_mstar']:.2f} M_sun)")
    print(f"    3) 항성종족/화학 (S_pop, 20%)    : {cur['s_pop']:.3f}   (u-r = {cur['color_u_r']:.2f}, D4000 = {cur['d4000']:.2f}, 12+log(O/H) = {cur['oh_metallicity']:.2f})")
    print(f"    4) 구조적 밀집도 (S_struct, 15%) : {cur['s_struct']:.3f}   (log Σ* = {cur['log_sigma_star']:.2f} M_sun/kpc^2, R = {cur['radius_kpc']:.2f} kpc)")
    print(f"    5) 암흑물질 헤일로 (S_halo, 10%) : {cur['s_halo']:.3f}   (f_DM = {cur['f_dm_percent']:.1f}%, log M_dyn = {cur['log_mdyn']:.2f} M_sun)")
    print("-" * 88)
    print("  [과거 모습 복원 · 현재 상태 · 미래 진화 예측 요약]")
    print(f"    • {nar['past_narrative_kr']}")
    print(f"    • {nar['present_narrative_kr']}")
    print(f"    • {nar['future_narrative_kr']}")
    print(f"    • 녹색 계곡(Stage IV) 진입 시점 : {nar['time_to_green_valley']}")
    print(f"    • 완전 소광(Stage V) 도달 시점  : {nar['time_to_full_quenching']}")
    print("-" * 88)
    print("  [시간대별 (과거 -10 Gyr → 현재 0 Gyr → 미래 +10 Gyr) 진화 궤적 수치표]")
    cols_show = ["epoch_label", "cosmic_age_t_gyr", "log_mstar", "log_sfr", "log_ssfr", "radius_kpc", "f_dm_percent", "color_u_r", "gei_score", "stage_code"]
    disp_df = tdf[cols_show].copy()
    disp_df.columns = ["시점", "우주나이(Gyr)", "log(M*)", "log(SFR)", "log(sSFR)", "반경R(kpc)", "f_DM(%)", "색지수(u-r)", "GEI지수", "진화단계"]
    print(disp_df.to_string(index=False))
    print("=" * 88)


def run_interactive_cli():
    """사용자가 콘솔에서 직접 천문대 망원경·CCD 원시 관측값 또는 물리량을 입력하여 분석하는 대화형 모드"""
    print("\n" + "=" * 84)
    print(" 🔭 우리 팀 직접 관측 은하 입력 · 진화 단계(GEI v2.0) 판별기 (대화형 입력 모드)")
    print("    • 망원경·CCD 원시 측정값(겉보기 등급 m_r, 각반경 arcsec, 후퇴속도 km/s)을 입력하면")
    print("      물리량(항성질량 M*, 물리적 반경 R_kpc, 별생성률 SFR)으로 자동 환산합니다.")
    print("    • 값을 모르는 항목은 Enter를 누르면 천체물리 스케일링 법칙으로 자동 추정됩니다.")
    print("=" * 84)

    def ask_float(prompt_str, default_val=None):
        raw = input(prompt_str).strip()
        if not raw:
            return default_val
        try:
            return float(raw)
        except ValueError:
            return default_val

    name = input("1. 직접 관측한 은하 이름/ID (예: 2026-관측은하-01): ").strip() or "우리팀_직접관측은하_01"
    v_rec = ask_float("2. 분광 후퇴속도 v_r [km/s] (예: 1150, 모르면 Enter): ")
    dist_mpc = ask_float("3. 은하 거리 D [Mpc] (예: 16.4, 모르면 Enter -> 후퇴속도로 자동 계산): ")
    if dist_mpc is None and v_rec is not None and v_rec > 0:
        dist_mpc = round(v_rec / 70.0, 2)
        print(f"   -> 허블 법칙(H0=70 km/s/Mpc) 자동 환산 거리: D = {dist_mpc:.2f} Mpc")

    m_r_app = ask_float("4. CCD 겉보기 등급 m_r [mag] (예: 10.4, 직접 log M* 입력 시 Enter): ")
    theta_arcsec = ask_float("5. 사진 반빛 각반경 θ_e [arcsec] (예: 85.0, 직접 R_kpc 입력 시 Enter): ")
    color_u_r = ask_float("6. 광학 색지수 (u - r) [mag] (예: 1.75, 모르면 Enter): ")

    abs_mag_r = None
    if m_r_app is not None and dist_mpc is not None and dist_mpc > 0:
        abs_mag_r = m_r_app - 5.0 * np.log10(dist_mpc * 1e6 / 10.0)
        print(f"   -> 거리 지수 공식 자동 환산 절대등급: M_r = {abs_mag_r:.2f} mag")

    radius_kpc = None
    if theta_arcsec is not None and dist_mpc is not None and dist_mpc > 0:
        radius_kpc = dist_mpc * 1000.0 * (theta_arcsec / 206265.0)
        print(f"   -> 삼각법 자동 환산 물리적 반경: R_e = {radius_kpc:.2f} kpc")

    log_mstar = ask_float("7. 항성 질량 log10(M*/M_sun) (원시 등급으로 자동 환산하려면 Enter): ")
    if radius_kpc is None:
        radius_kpc = ask_float("8. 물리적 반경 R [kpc] (예: 6.8, 모르면 Enter): ")
    v_rot = ask_float("9. 회전 속도 V_rot [km/s] (예: 175.0, 모르면 Enter): ")
    log_sfr = ask_float("10. 별생성률 log10(SFR [M_sun/yr]) (자동 환산하려면 Enter): ")
    ha_flux = None
    if log_sfr is None:
        ha_flux = ask_float("    -> H-alpha 관측 플럭스 [10^-17 erg/s/cm^2] (모르면 Enter): ")

    obs_input = {
        "name": name,
        "dist_mpc": dist_mpc,
        "z": (v_rec / 299792.458) if v_rec is not None else None,
        "log_mstar": log_mstar,
        "abs_mag_r": abs_mag_r,
        "radius_kpc": radius_kpc,
        "v_rot": v_rot,
        "log_sfr": log_sfr,
        "h_alpha_flux": ha_flux,
        "color_u_r": color_u_r,
    }
    sim = simulate_galaxy_evolution_trajectory(obs_input)
    print_detailed_console_report(sim)

    safe_name = "".join(c if c.isalnum() or c in ("_", "-") else "_" for c in name)
    chart_path = os.path.join(REPORT_DIR, f"관측은하_진단리포트_{safe_name}.png")
    generate_single_galaxy_diagnostic_chart(sim, chart_path)
    print(f"\n[+] 고해상도(300 DPI) 진화 진단 리포트 차트가 생성되었습니다: {chart_path}")


def main():
    parser = argparse.ArgumentParser(description="우리 팀 직접 관측 은하 입력 · 진화 단계 판별 및 과거·미래 진화 예측 프로그램")
    parser.add_argument("--interactive", action="store_true", help="대화형 직접 관측값 입력 모드 실행")
    parser.add_argument("--benchmark", action="store_true", help="문헌 카탈로그 기준 은하 5종 알고리즘 검증 리포트 생성")
    parser.add_argument("--name", type=str, default=None, help="직접 관측한 은하 이름/ID")
    parser.add_argument("--m_r", type=float, default=None, help="CCD 관측 겉보기 등급 m_r [mag]")
    parser.add_argument("--theta_arcsec", type=float, default=None, help="사진 관측 각반경 theta_e [arcsec]")
    parser.add_argument("--v_rec", type=float, default=None, help="분광 후퇴속도 v_r [km/s]")
    parser.add_argument("--dist_mpc", type=float, default=None, help="거리 [Mpc]")
    parser.add_argument("--z", type=float, default=None, help="적색편이 z")
    parser.add_argument("--log_mstar", type=float, default=None, help="항성 질량 log10(M*/M_sun)")
    parser.add_argument("--abs_mag_r", type=float, default=None, help="r밴드 절대등급 M_r")
    parser.add_argument("--radius_kpc", type=float, default=None, help="은하 물리적 반경 R [kpc]")
    parser.add_argument("--v_rot", type=float, default=None, help="회전 속도 V_rot [km/s]")
    parser.add_argument("--log_sfr", type=float, default=None, help="별생성률 log10(SFR [M_sun/yr])")
    parser.add_argument("--h_alpha_flux", type=float, default=None, help="H-alpha 플럭스 [10^-17 erg/s/cm^2]")
    parser.add_argument("--color_u_r", type=float, default=None, help="광학 색지수 (u - r)")
    args = parser.parse_args()

    if args.interactive:
        run_interactive_cli()
        return

    if any(v is not None for v in [args.name, args.log_mstar, args.m_r, args.theta_arcsec, args.v_rec]):
        dist_mpc = args.dist_mpc
        if dist_mpc is None and args.v_rec is not None and args.v_rec > 0:
            dist_mpc = args.v_rec / 70.0
        abs_mag_r = args.abs_mag_r
        if abs_mag_r is None and args.m_r is not None and dist_mpc is not None and dist_mpc > 0:
            abs_mag_r = args.m_r - 5.0 * np.log10(dist_mpc * 1e6 / 10.0)
        radius_kpc = args.radius_kpc
        if radius_kpc is None and args.theta_arcsec is not None and dist_mpc is not None and dist_mpc > 0:
            radius_kpc = dist_mpc * 1000.0 * (args.theta_arcsec / 206265.0)

        obs_in = {
            "name": args.name or "우리팀_직접관측은하",
            "dist_mpc": dist_mpc,
            "z": args.z if args.z is not None else ((args.v_rec / 299792.458) if args.v_rec else None),
            "log_mstar": args.log_mstar,
            "abs_mag_r": abs_mag_r,
            "radius_kpc": radius_kpc,
            "v_rot": args.v_rot,
            "log_sfr": args.log_sfr,
            "h_alpha_flux": args.h_alpha_flux,
            "color_u_r": args.color_u_r,
        }
        sim = simulate_galaxy_evolution_trajectory(obs_in)
        print_detailed_console_report(sim)
        safe_name = "".join(c if c.isalnum() or c in ("_", "-") else "_" for c in obs_in["name"])
        out_png = os.path.join(REPORT_DIR, f"관측은하_진단리포트_{safe_name}.png")
        generate_single_galaxy_diagnostic_chart(sim, out_png)
        print(f"[+] 직접 관측 은하 진단 리포트 차트 저장 완료: {out_png}")
        return

    # 기본 안내 및 문헌 기준 은하(국소 우주 지상 관측 기준, CEERS 제외) 알고리즘 검증 실행
    print("=" * 88)
    print(" 🔭 우리 팀 직접 관측 은하 진화 분석기 (observatory_galaxy_analyzer.py)")
    print("    • 직접 관측값 대화형 입력: python observatory_galaxy_analyzer.py --interactive")
    print("    • 원시 관측값 CLI 입력 예: python observatory_galaxy_analyzer.py --name '관측은하_01' --m_r 10.4 --theta_arcsec 85 --v_rec 1150 --color_u_r 1.75")
    print("    • 아래는 GEI v2.0 알고리즘 검증용 국소 우주 표준 문헌 은하(CEERS 초기우주 제외) 5종 벤치마크 결과입니다.")
    print("=" * 88)
    showcase_keys = [
        "M82 (시가 은하 - 폭발적 별생성)",
        "M33 (삼각형자리 은하)",
        "M51a (소용돌이 은하)",
        "M31 (안드로메다 은하)",
        "M87 (처녀자리 A 거대 타원은하)",
    ]
    for sk in showcase_keys:
        obs = OBSERVATORY_BENCHMARK_GALAXIES[sk]
        sim = simulate_galaxy_evolution_trajectory(obs)
        print_detailed_console_report(sim)
        short_id = sk.split(" (")[0].replace(" ", "_")
        out_png = os.path.join(REPORT_DIR, f"관측은하_진단리포트_{short_id}.png")
        generate_single_galaxy_diagnostic_chart(sim, out_png)
        print(f"  -> [알고리즘 검증 리포트 생성 완료] {out_png}")


if __name__ == "__main__":
    main()

