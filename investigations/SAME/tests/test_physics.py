"""Moment-method and coagulation physics."""
import numpy as np
import pytest

from analysis import physics as ph


def test_hatch_choate_round_trip():
    n, dg, sg = 2.5e6, 0.12, 2.1
    m0, m1, m3 = (ph.lognormal_moment(n, dg, sg, k) for k in (0, 1, 3))
    n_, dg_, sg_, d05, d15 = ph.invert_three_moments(m0, m1, m3)
    assert n_ == pytest.approx(n)
    assert dg_ == pytest.approx(dg, rel=1e-9)
    assert sg_ == pytest.approx(sg, rel=1e-9)
    assert d05 == pytest.approx(ph.hatch_choate_dp(dg, sg, 0.5))
    assert d15 == pytest.approx(ph.hatch_choate_dp(dg, sg, 1.5))


def test_paper_figure1_example():
    # Urban et al. (2012) Fig. 1: Dg = 1.0, sigma_g = 1.6 -> D0.5 = 1.17, D1.5 = 1.39
    assert ph.hatch_choate_dp(1.0, 1.6, 0.5) == pytest.approx(1.12, abs=0.06)
    assert ph.hatch_choate_dp(1.0, 1.6, 1.5) == pytest.approx(1.39, abs=0.02)


def test_sigma_from_ratio_rejects_non_lognormal():
    assert np.isnan(ph.sigma_g_from_d15_d05(0.10, 0.20))
    assert ph.sigma_g_from_d15_d05(0.253, 0.110) == pytest.approx(2.49, abs=0.01)


def test_brownian_kernel_order_of_magnitude():
    k = ph.brownian_kernel_monodisperse(0.2)
    assert 3e-10 < k < 1.5e-9  # cm^3/s, continuum x slip for 0.2 µm


def test_coagulation_consistency():
    n0, k, t = 3e6, 1.25e-9, 126.0
    n1 = ph.coag_number(n0, k, t)
    assert ph.coag_coefficient_from_counts(n0, n1, t) == pytest.approx(k)
    assert ph.coag_dm_growth(0.3, n0, k, t) == pytest.approx(0.3 * (n0 / n1) ** (1 / 3))


def test_fraction_above_monotonic():
    f_num = ph.fraction_above(0.3, 0.1, 2.0, k=0)
    f_mass = ph.fraction_above(0.3, 0.1, 2.0, k=3)
    assert 0 < f_num < f_mass < 1
