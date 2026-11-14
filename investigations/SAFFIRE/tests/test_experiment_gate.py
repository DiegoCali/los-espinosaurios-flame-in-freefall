import pytest
from scripts import run_experiment as gate


def test_complexity_gate_rejects_tiny_extra_parameter_improvement():
    best={"val_rmse":100.0,"num_params":1}
    assert gate.decision({"val_rmse":99.5,"num_params":2},best)=="discard"
    assert gate.decision({"val_rmse":97.0,"num_params":2},best)=="keep"
    assert gate.decision({"val_rmse":100.0,"num_params":1},best)=="discard"
    assert gate.decision({"val_rmse":99.8,"num_params":1},best)=="keep"


def test_gate_rejects_dirty_tree(monkeypatch):
    monkeypatch.setattr(gate,"git",lambda *args:" M train.py")
    with pytest.raises(RuntimeError,match="clean Git"):gate.check_tree()


def test_gate_rejects_protected_file_changes(monkeypatch):
    def fake(*args):
        if args[0]=="status":return ""
        if args[0]=="diff":return "prepare.py\ntrain.py"
        return "commit"
    monkeypatch.setattr(gate,"git",fake)
    with pytest.raises(RuntimeError,match="Protected"):gate.check_tree()


def test_gate_accepts_committed_train_only(monkeypatch):
    def fake(*args):
        if args[0]=="status":return ""
        if args[0]=="diff":return "train.py"
        return "abcdef"
    monkeypatch.setattr(gate,"git",fake)
    assert gate.check_tree()=="abcdef"
