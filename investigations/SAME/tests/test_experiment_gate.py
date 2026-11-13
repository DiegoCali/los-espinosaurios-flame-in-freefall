"""Gate run before every AutoResearch attempt: the candidate honours the train.py contract."""
import importlib.util
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load(path: Path):
    spec = importlib.util.spec_from_file_location("cand", path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


@pytest.fixture(scope="module")
def cand():
    return _load(ROOT / "train.py")


def _synthetic(n, rng, detection=False):
    mats = np.array(["Kapton", "Lampwick", "Pyrell", "Silicone", "Teflon"])
    X = {
        "material": mats[rng.integers(0, 5, n)],
        "aging_s": rng.choice([37.0, 566.0, 830.0], n),
        "flow_velocity_cm_s": rng.choice([0.0, 8.1], n),
        "rt_r0": rng.uniform(1.2, 1.5, n),
    }
    X["no_flow"] = (X["flow_velocity_cm_s"] < 0.5).astype(float)
    if detection:
        X["push_index"] = rng.integers(1, 3, n).astype(float)
        Y = rng.integers(0, 2, (n, 2))
        Y[:2] = [[0, 1], [1, 0]]  # both classes present
    else:
        X["aged"] = (X["aging_s"] > 120).astype(float)
        Y = rng.normal(0, 1, (n, 5))
    return X, Y


def test_contract_functions(cand):
    for name in ("fit_predict_size", "fit_predict_detection", "describe_model"):
        assert callable(getattr(cand, name))
    d = cand.describe_model()
    assert {"model_name", "num_params"} <= set(d)
    assert int(d["num_params"]) >= 1


def test_size_shape_and_determinism(cand):
    rng = np.random.default_rng(1)
    Xtr, Ytr = _synthetic(40, rng)
    Xte, _ = _synthetic(3, rng)
    a = np.asarray(cand.fit_predict_size(Xtr, Ytr.copy(), Xte, 0))
    b = np.asarray(cand.fit_predict_size(Xtr, Ytr.copy(), Xte, 0))
    assert a.shape == (3, 5) and np.all(np.isfinite(a))
    np.testing.assert_allclose(a, b)


def test_detection_probabilities(cand):
    rng = np.random.default_rng(2)
    Xtr, Ytr = _synthetic(50, rng, detection=True)
    Xte, _ = _synthetic(4, rng, detection=True)
    p = np.asarray(cand.fit_predict_detection(Xtr, Ytr.copy(), Xte, 0))
    assert p.shape == (4, 2) and np.all(np.isfinite(p))
    assert np.all((p >= 0) & (p <= 1))


def test_static_gate_passes():
    import sys

    sys.path.insert(0, str(ROOT))
    from scripts.run_experiment import static_gate

    assert static_gate((ROOT / "train.py").read_text()) == []
