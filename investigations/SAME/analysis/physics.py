"""Aerosol physics used by the SAME analysis: moment method, log-normal relations, coagulation.

Notation (Urban et al. 2012; Hatch-Choate relations):
    M_k = integral D^k f_N(D) dD                (k = 0, 1, 3)
    D0.5 = AMD = M1/M0                          count (arithmetic) mean diameter
    D1.5 = Dm  = (M3/M0)^(1/3)                  diameter of average mass
    D_p  = Dg * exp(p * ln^2 sigma_g)           for a log-normal distribution
    => ln^2 sigma_g = ln(D1.5 / D0.5)
"""
from __future__ import annotations

import numpy as np

K_B = 1.380649e-23        # J/K
AIR_VISCOSITY = 1.83e-5   # Pa s at ~25 C
MEAN_FREE_PATH = 0.066e-6  # m at 1 atm, ~25 C


def hatch_choate_dp(dg, sigma_g, p):
    return np.asarray(dg) * np.exp(p * np.log(sigma_g) ** 2)


def sigma_g_from_d15_d05(d15, d05):
    r = np.asarray(d15, float) / np.asarray(d05, float)
    with np.errstate(invalid="ignore"):
        return np.where(r > 1, np.exp(np.sqrt(np.log(np.where(r > 1, r, np.nan)))), np.nan)


def dg_from_amd(amd, sigma_g):
    return np.asarray(amd) / np.exp(0.5 * np.log(sigma_g) ** 2)


def lognormal_moment(n, dg, sigma_g, k):
    """M_k = N * Dg^k * exp(k^2 ln^2 sigma_g / 2)."""
    return n * dg ** k * np.exp(0.5 * k ** 2 * np.log(sigma_g) ** 2)


def invert_three_moments(m0, m1, m3):
    """(M0, M1, M3) -> (N, Dg, sigma_g, D0.5, D1.5); same units as the moments' length scale."""
    d05 = m1 / m0
    d15 = (m3 / m0) ** (1 / 3)
    sg = sigma_g_from_d15_d05(d15, d05)
    return m0, dg_from_amd(d05, sg), sg, d05, d15


def lognormal_pdf_dlnd(d, dg, sigma_g):
    """Normalised number distribution dN/(N dlnD)."""
    ls = np.log(sigma_g)
    return np.exp(-((np.log(d) - np.log(dg)) ** 2) / (2 * ls ** 2)) / (np.sqrt(2 * np.pi) * ls)


def fraction_above(d_cut, dg, sigma_g, k=0):
    """Fraction of the k-th moment carried by particles larger than d_cut (log-normal)."""
    from scipy.stats import norm

    mu = np.log(dg) + k * np.log(sigma_g) ** 2  # moment-weighted median shifts by k ln^2 sigma
    return 1 - norm.cdf((np.log(d_cut) - mu) / np.log(sigma_g))


# --------------------------------------------------------------------------- coagulation
def cunningham(d_m):
    kn = 2 * MEAN_FREE_PATH / d_m
    return 1 + kn * (1.257 + 0.4 * np.exp(-1.1 / kn))


def brownian_kernel_monodisperse(d_um, temp_k=298.15):
    """Coagulation coefficient K (cm^3/s) for equal spheres, continuum kernel x slip correction.

    dN/dt = -K N^2 / 2 convention is NOT used: here 1/N - 1/N0 = K t with K = 4 k T Cc / (3 mu),
    i.e. the kernel K11 = 8kTCc/(3mu) divided by two.
    """
    d = np.asarray(d_um) * 1e-6
    k_m3 = 4 * K_B * temp_k * cunningham(d) / (3 * AIR_VISCOSITY)
    return k_m3 * 1e6


def coag_coefficient_from_counts(n0, n1, dt_s):
    """Constant-kernel Smoluchowski estimate: 1/N - 1/N0 = K t (cm^3/s when N in #/cm^3)."""
    return (1.0 / np.asarray(n1) - 1.0 / np.asarray(n0)) / np.asarray(dt_s)


def coag_number(n0, k, t):
    return n0 / (1 + k * n0 * t)


def coag_dm_growth(dm0, n0, k, t):
    """Diameter of average mass under mass-conserving coagulation: Dm ∝ N^(-1/3)."""
    return dm0 * (1 + k * n0 * t) ** (1 / 3)


SELF_PRESERVING_SIGMA_G_CONTINUUM = 1.32  # Friedlander; cited by Urban et al. (2012)
