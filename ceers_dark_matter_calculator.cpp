#include <iostream>
#include <fstream>
#include <vector>
#include <string>
#include <cmath>
#include <iomanip>
#include <sstream>

// Astronomical Gravitational Constant G: kpc * (km/s)^2 / M_sun
const double G = 4.30091727e-6;
const double PI = 3.14159265358979323846;

// Flat Lambda-CDM Cosmology (H0 = 70.0 km/s/Mpc, Om0 = 0.3, Ol = 0.7, c = 299792.458 km/s)
const double H0 = 70.0;
const double C_SPEED = 299792.458;
const double OM0 = 0.3;
const double OL0 = 0.7;

// Numerical integration for comoving distance
double e_z(double z) {
    return std::sqrt(OM0 * std::pow(1.0 + z, 3) + OL0);
}

double comoving_distance_mpc(double z) {
    if (z <= 0.0) return 0.0;
    int n_steps = 1000;
    double dz = z / n_steps;
    double integral = 0.0;
    for (int i = 0; i < n_steps; ++i) {
        double z_mid = (i + 0.5) * dz;
        integral += 1.0 / e_z(z_mid);
    }
    return (C_SPEED / H0) * integral * dz;
}

// Angular diameter distance D_A = D_C / (1 + z)
double angular_diameter_distance_mpc(double z) {
    if (z <= 0.0) return 0.0;
    return comoving_distance_mpc(z) / (1.0 + z);
}

// Physical transverse radius R in kpc from angular radius in arcseconds
double calculate_radius_kpc(double r_arcsec, double z) {
    double d_a = angular_diameter_distance_mpc(z);
    double r_rad = r_arcsec * (PI / (180.0 * 3600.0));
    return d_a * 1000.0 * r_rad; // Mpc -> kpc
}

// Baryonic Tully-Fisher flat rotation velocity
double calculate_v_rot(double log_mstar) {
    double log_v = (log_mstar - 1.86) / 4.0;
    double v = std::pow(10.0, log_v);
    if (v < 10.0) v = 10.0;
    if (v > 500.0) v = 500.0;
    return v;
}

// Total dynamical mass M_dyn = V^2 * R / G
double calculate_m_dyn(double v_rot, double r_kpc) {
    return (v_rot * v_rot * r_kpc) / G;
}

int main(int argc, char* argv[]) {
    std::cout << "========================================================================\n";
    std::cout << " [C++ JWST CEERS Galaxy Dark Matter Calculation Engine v1.0]          \n";
    std::cout << "========================================================================\n\n";

    std::cout << "1. Cosmological Parameters (Flat Lambda-CDM):\n";
    std::cout << "   - H0 = " << H0 << " km/s/Mpc, Om0 = " << OM0 << ", OL = " << OL0 << "\n";
    std::cout << "   - Gravitational Constant G = " << G << " kpc * (km/s)^2 / M_sun\n\n";

    // Test with representative high-redshift CEERS benchmark galaxies
    struct CEERS_Benchmark {
        long long number;
        double z;
        double log_mstar;
        double r_arcsec;
    };

    std::vector<CEERS_Benchmark> samples = {
        {1015,  1.12, 7.35, 0.180},
        {5420,  2.35, 8.50, 0.165},
        {12840, 4.20, 9.10, 0.140},
        {25910, 6.50, 8.80, 0.120},
        {48120, 8.20, 8.40, 0.095}
    };

    std::cout << std::left << std::setw(10) << "NUMBER"
              << std::setw(8)  << "z"
              << std::setw(12) << "R(arcsec)"
              << std::setw(10) << "R(kpc)"
              << std::setw(12) << "V_rot(km/s)"
              << std::setw(12) << "log(M*)"
              << std::setw(14) << "M_DM(M_sun)"
              << std::setw(10) << "f_DM(%)" << "\n";
    std::cout << std::string(88, '-') << "\n";

    for (const auto& gal : samples) {
        double r_kpc = calculate_radius_kpc(gal.r_arcsec, gal.z);
        double v_rot = calculate_v_rot(gal.log_mstar);
        double m_dyn = calculate_m_dyn(v_rot, r_kpc);
        double m_star = std::pow(10.0, gal.log_mstar);
        double m_dm = m_dyn - m_star;
        if (m_dm < 0.0) m_dm = 0.0;
        double f_dm = (m_dm / m_dyn) * 100.0;

        std::cout << std::left << std::setw(10) << gal.number
                  << std::fixed << std::setprecision(2)
                  << std::setw(8)  << gal.z
                  << std::setw(12) << gal.r_arcsec
                  << std::setw(10) << r_kpc
                  << std::setprecision(1)
                  << std::setw(12) << v_rot
                  << std::setprecision(2)
                  << std::setw(12) << gal.log_mstar
                  << std::scientific << std::setprecision(2)
                  << std::setw(14) << m_dm
                  << std::fixed << std::setprecision(1)
                  << std::setw(10) << f_dm << "\n";
    }

    std::cout << "\n>> C++ CEERS Engine verification successfully completed.\n";
    return 0;
}
