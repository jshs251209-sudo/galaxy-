#include <iostream>
#include <fstream>
#include <vector>
#include <string>
#include <cmath>
#include <iomanip>

// Astronomical Gravitational Constant G: kpc * (km/s)^2 / M_sun
const double G = 4.30091727e-6;
const double PI = 3.14159265358979323846;

struct BenchmarkGalaxy {
    std::string name;
    double dist_mpc;
    double diam_arcsec;
    double v_rot_kms;
    double m_star_msun;
    std::string ref;
};

// Calculate physical radius from angular diameter and distance
double calculate_radius_kpc(double diam_arcsec, double dist_mpc) {
    double r_rad = (diam_arcsec / 2.0) * (PI / (180.0 * 3600.0));
    return r_rad * dist_mpc * 1000.0;
}

// Calculate total dynamical mass
double calculate_m_dyn(double v_rot, double r_kpc) {
    return (v_rot * v_rot * r_kpc) / G;
}

// Freeman exponential disk circular velocity
double v_disk_freeman(double r, double rd, double v_max) {
    double y = r / (2.0 * rd);
    if (y <= 0.0) return 0.0;
    return v_max * (1.97 * std::pow(y, 1.22) / std::pow(y * y + 0.78, 1.43));
}

// Gas disk circular velocity (HI model)
double v_gas_disk(double r, double v_gas_max, double r_scale) {
    if (r <= 0.0) return 0.0;
    return v_gas_max * (r / (r + r_scale));
}

// Pseudo-isothermal dark matter halo circular velocity
double v_halo_iso(double r, double v_inf, double r_core) {
    if (r <= 0.0) return 0.0;
    double term = 1.0 - (r_core / r) * std::atan(r / r_core);
    if (term <= 0.0) return 0.0;
    return v_inf * std::sqrt(term);
}

int main() {
    std::cout << "========================================================================\n";
    std::cout << " [C++ Galaxy Dark Matter Engine v1.0 - Fast Numerical Astrophysics]     \n";
    std::cout << "========================================================================\n\n";

    // 1. Process Benchmark Galaxies
    std::vector<BenchmarkGalaxy> galaxies = {
        {"MESSIER 031 (Andromeda)", 0.80, 6200.0, 250.0, 6.37e10, "Chemin et al. (2009)"},
        {"NGC 3198 (Classic Flat)", 14.46, 475.8,  150.0, 1.96e10, "Begeman (1989)"},
        {"MESSIER 033 (Triangulum)", 0.85, 2150.6, 120.0, 3.91e9,  "Corbelli & Salucci (2000)"},
        {"NGC 2403",                 3.16, 716.5,  135.0, 6.61e9,  "Fraternali et al. (2002)"},
        {"NGC 0253 (Sculptor)",      3.51, 1843.6, 205.0, 4.75e10, "Hlavacek-Larrondo (2011)"},
        {"MESSIER 081 (Bode)",       3.59, 1510.0, 235.0, 4.86e10, "de Blok et al. (2008)"},
        {"MESSIER 101 (Pinwheel)",   6.91, 1051.2, 210.0, 4.48e10, "Walter et al. (2008)"},
        {"MESSIER 051a (Whirlpool)", 8.59, 706.5,  215.0, 8.45e10, "Sofue (1996)"}
    };

    std::ofstream csv_bench("cpp_benchmark_results.csv");
    csv_bench << "Galaxy,Dist_Mpc,Radius_kpc,V_rot_kms,M_star_Msun,M_dyn_Msun,M_DM_Msun,f_DM_percent,Reference\n";

    std::cout << std::left << std::setw(26) << "Galaxy Name"
              << std::right << std::setw(9) << "R (kpc)"
              << std::setw(10) << "V (km/s)"
              << std::setw(15) << "M_star (Msun)"
              << std::setw(15) << "M_dyn (Msun)"
              << std::setw(15) << "M_DM (Msun)"
              << std::setw(11) << "f_DM (%)" << "\n";
    std::cout << std::string(101, '-') << "\n";

    for (const auto& g : galaxies) {
        double r_kpc = calculate_radius_kpc(g.diam_arcsec, g.dist_mpc);
        double m_dyn = calculate_m_dyn(g.v_rot_kms, r_kpc);
        double m_dm = std::max(0.0, m_dyn - g.m_star_msun);
        double f_dm = (m_dm / m_dyn) * 100.0;

        std::cout << std::left << std::setw(26) << g.name
                  << std::right << std::fixed << std::setprecision(2) << std::setw(9) << r_kpc
                  << std::setprecision(1) << std::setw(10) << g.v_rot_kms
                  << std::scientific << std::setprecision(2) << std::setw(15) << g.m_star_msun
                  << std::setw(15) << m_dyn
                  << std::setw(15) << m_dm
                  << std::fixed << std::setprecision(1) << std::setw(10) << f_dm << "%\n";

        csv_bench << "\"" << g.name << "\","
                  << g.dist_mpc << ","
                  << r_kpc << ","
                  << g.v_rot_kms << ","
                  << g.m_star_msun << ","
                  << m_dyn << ","
                  << m_dm << ","
                  << f_dm << ",\""
                  << g.ref << "\"\n";
    }
    csv_bench.close();
    std::cout << "\n[+] Benchmark CSV saved: cpp_benchmark_results.csv\n\n";

    // 2. Compute Precision Radial Profile for NGC 3198 (Classic Textbook Flat RC)
    std::ofstream csv_rc_ngc3198("cpp_rotation_curve_ngc3198.csv");
    csv_rc_ngc3198 << "Radius_kpc,V_tot,V_dm,V_disk,V_gas,V_kepler,M_tot_Msun,M_dm_Msun,M_bar_Msun,f_dm_percent\n";

    double rd_ngc3198 = 2.63;
    double v_disk_max = 95.0;
    double v_gas_max = 32.0;
    double r_gas_scale = 5.5;
    double v_inf = 145.0;
    double rc = 2.5;

    for (int i = 1; i <= 350; ++i) {
        double radius = i * 0.1; // 0.1 to 35.0 kpc
        double v_d = v_disk_freeman(radius, rd_ngc3198, v_disk_max);
        double v_g = v_gas_disk(radius, v_gas_max, r_gas_scale);
        double v_b = std::sqrt(v_d * v_d + v_g * v_g);
        double v_halo = v_halo_iso(radius, v_inf, rc);
        double v_total = std::sqrt(v_b * v_b + v_halo * v_halo);

        // Keplerian line assuming visible peak
        double r_peak = 5.8;
        double v_b_peak = 96.0;
        double v_kep = (radius >= r_peak) ? (v_b_peak * std::sqrt(r_peak / radius)) : v_b;

        double m_total = calculate_m_dyn(v_total, radius);
        double m_b = calculate_m_dyn(v_b, radius);
        double m_dark = std::max(0.0, m_total - m_b);
        double f_dark = (m_dark / m_total) * 100.0;

        csv_rc_ngc3198 << radius << ","
                       << v_total << ","
                       << v_halo << ","
                       << v_d << ","
                       << v_g << ","
                       << v_kep << ","
                       << m_total << ","
                       << m_dark << ","
                       << m_b << ","
                       << f_dark << "\n";
    }
    csv_rc_ngc3198.close();
    std::cout << "[+] NGC 3198 Radial Profile CSV saved: cpp_rotation_curve_ngc3198.csv\n";

    // 3. Compute Precision Radial Profile for M31 (Andromeda)
    std::ofstream csv_rc_m31("cpp_rotation_curve_m31.csv");
    csv_rc_m31 << "Radius_kpc,V_tot,V_dm,V_disk,V_bulge,M_tot_Msun,M_dm_Msun,M_star_Msun,f_dm_percent\n";

    // M31: V_rot ~ 250 km/s, Rd ~ 5.3 kpc, Bulge ~ 140 km/s (Carignan+2006)
    for (int i = 1; i <= 350; ++i) {
        double radius = i * 0.1;
        // Bulge: Hernquist-like
        double v_bulge = 140.0 * std::sqrt(radius / (radius + 1.2));
        double v_disk_m31 = 175.0 * (1.97 * std::pow(radius / 10.6, 1.22) / std::pow(std::pow(radius / 10.6, 2) + 0.78, 1.43));
        double v_stars = std::sqrt(v_bulge * v_bulge + v_disk_m31 * v_disk_m31);
        double v_halo_m31 = 230.0 * std::sqrt(std::max(0.0, 1.0 - (5.0 / radius) * std::atan(radius / 5.0)));
        double v_tot_m31 = std::sqrt(v_stars * v_stars + v_halo_m31 * v_halo_m31);

        double m_tot_m31 = calculate_m_dyn(v_tot_m31, radius);
        double m_stars_m31 = calculate_m_dyn(v_stars, radius);
        double m_dm_m31 = std::max(0.0, m_tot_m31 - m_stars_m31);
        double f_dm_m31 = (m_dm_m31 / m_tot_m31) * 100.0;

        csv_rc_m31 << radius << ","
                   << v_tot_m31 << ","
                   << v_halo_m31 << ","
                   << v_disk_m31 << ","
                   << v_bulge << ","
                   << m_tot_m31 << ","
                   << m_dm_m31 << ","
                   << m_stars_m31 << ","
                   << f_dm_m31 << "\n";
    }
    csv_rc_m31.close();
    std::cout << "[+] M31 Andromeda Radial Profile CSV saved: cpp_rotation_curve_m31.csv\n";
    std::cout << "\n[!] C++ computation finished successfully with 0 errors.\n";
    return 0;
}
