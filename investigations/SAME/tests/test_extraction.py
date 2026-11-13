"""Scientific checks on the processed SAME-R tables (skipped when the extraction has not been run)."""
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from analysis import physics as ph

P = Path(__file__).resolve().parents[1] / "data" / "processed"
pytestmark = pytest.mark.skipif(not (P / "size_dataset.csv").exists(), reason="run extraction/run_all.py first")


@pytest.fixture(scope="module")
def moments():
    return pd.read_csv(P / "nasa_moment_table.csv")


def test_reported_sigma_matches_moment_ratio(moments):
    m = moments[moments.usable_size_stats]
    rel = (m.sigma_g_from_ratio - m.sigma_g_hc).abs() / m.sigma_g_hc
    assert rel.max() < 0.02, "NASA sigma_g should equal exp(sqrt(ln(Dm/AMD)))"


def test_published_table1_is_hatch_choate_consistent():
    t = pd.read_csv(P / "published_table1_baseline.csv")
    dg = ph.dg_from_amd(t.amd_um, t.sigma_g)
    assert np.allclose(dg, t.dg_um, rtol=0.06, atol=0.004)


def test_qc_flags_catch_known_typos(moments):
    flagged = moments.loc[moments.qc_flags.fillna("") != "", "run"].tolist()
    assert 50 in flagged  # AMD = 65.14 µm
    assert 62 in flagged  # sigma_g = 20.66


def test_push_aging_matches_nasa_net_aging():
    pushes = pd.read_csv(P / "pushes.csv")
    nasa = pd.read_csv(P / "nasa_flow_aging_table.csv")
    diffs = []
    for _, r in nasa.dropna(subset=["net_aging_s"]).iterrows():
        mine = pushes[(pushes.test == r.run) & (pushes.aged_state == r.aged_state)]
        if len(mine):
            diffs.append(abs(mine.aging_s.iloc[0] - r.net_aging_s))
    # NASA's "net aging" averages over push sub-steps; run 54 (279 s push) differs by ~19 s.
    assert len(diffs) >= 10
    assert np.median(diffs) <= 6 and max(diffs) <= 20


def test_flow_velocity_anchor():
    tests = pd.read_csv(P / "tests.csv")
    nominal = tests[tests.flow_regime_hkp == "nominal_flow"].flow_velocity_cm_s
    assert nominal.between(7.5, 8.6).all()
    assert set(tests.flow_regime_hkp) <= {"nominal_flow", "no_flow", "low_flow", "unknown"}


def test_coagulation_reference_is_physical():
    c = pd.read_csv(P / "coagulation_reference.csv")
    assert c.k_coag_cm3_s.between(5e-10, 3e-9).all()


def test_model_tables_complete():
    s = pd.read_csv(P / "size_dataset.csv")
    d = pd.read_csv(P / "detection_dataset.csv")
    feats = ["aging_s", "flow_velocity_cm_s", "rt_r0"]
    assert s[s.include_in_model][feats].notna().all().all()
    assert d[d.include_in_model][feats].notna().all().all()
    assert s.include_in_model.sum() >= 40 and d.include_in_model.sum() >= 50


def test_tem_particle_counts():
    t = pd.read_csv(P / "tem_summary.csv").set_index("particle_set")
    assert int(t.loc["54_all_data", "n_particles"]) == 576


def test_material_audit_of_unlabeled_tests():
    a = pd.read_csv(P / "test_material_audit.csv").set_index("test")
    unk = [59, 61, 65, 66, 86, 90, 91, 99, 102, 103]
    assert set(a[a.material == "unknown"].index) == set(unk)
    assert not a.loc[unk, "probable_blank_or_purge"].drop(90).any()  # only test 90 is near-smokeless
    assert (a.loc[unk, "heat_duration_s"] >= 50).all()
    assert set(a.loc[[61, 90, 102], "fingerprint_class"]) == {"Kapton"}
    assert set(a.loc[[59, 65, 66, 86, 91, 99, 103], "fingerprint_class"]) == {"Silicone"}
    assert a.loc[92, "audit_result"] == "CONFLICT"
    lab = a[a.audit_result.isin(["agrees", "CONFLICT"])]
    assert (lab.audit_result == "agrees").mean() > 0.9
