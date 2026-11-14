import ast
import json
from collections import defaultdict,Counter
from pathlib import Path
import numpy as np
import pytest
import prepare
import train
from extraction.common import ROOT,PROCESSED,INVENTORY,read_csv
from extraction.telemetry import response_at_horizon,PSI_TO_KPA,median_bins
from analysis.build_analysis_json import build,pointer


def test_conversions_have_physical_units():
    assert 14.6959487755*PSI_TO_KPA==pytest.approx(101.325,abs=1e-6)
    # 1 mW/cm2 = 10 W/m2 = .01 kW/m2.
    assert .001/(.01**2)/1000==pytest.approx(.01)


def test_horizon_excludes_late_fire_and_rejects_incomplete_windows():
    t=np.arange(-30,220,dtype=float)+.5
    gas=np.where(t<0,3300,np.where(t<150,5000,np.where(t<180,3375,10000)))
    value,scale=response_at_horizon(t,gas)
    assert value==75
    assert scale==0
    with pytest.raises(ValueError):response_at_horizon(t[t<160],gas[t<160])


def test_signed_negative_response_is_preserved():
    t=np.arange(-30,180)+.5
    value,_=response_at_horizon(t,np.where(t<0,3500,3490))
    assert value==-10


def test_bins_are_medians_and_keep_count():
    t,v,n=median_bins(np.array([-.1,.1,.2,.3,1.1]),{"co2":np.array([1,2,3,1000,4])})
    assert t.tolist()==[-.5,.5,1.5]
    assert v["co2"].tolist()==[1,3,4]
    assert n.tolist()==[1,3,1]


def test_only_nine_test_rows_and_no_result_features():
    X,y,rows=prepare.load_dataset()
    assert len(y)==9
    assert len({r["test_id"] for r in rows})==9
    assert set(X)==set(prepare.INPUTS)
    assert not any(any(token in key for token in ("burn","co2","peak","test_id","outcome")) for key in X)
    assert np.any(y<0)


def test_loocv_never_passes_heldout_target_or_id():
    y=np.arange(9,dtype=float)+100
    X={"condition":np.arange(9)}
    visited=[]
    def spy(training,target,evaluation,seed):
        assert set(training)=={"condition"}
        held=int(evaluation["condition"][0])
        assert held not in training["condition"]
        assert y[held] not in target
        assert len(target)==8
        visited.append(held)
        return np.full(len(evaluation["condition"]),np.mean(target))
    result=prepare.evaluate_arrays(spy,X,y)
    assert visited==list(range(9))
    expected=(np.sum(y)-y)/8
    assert result["val_rmse"]==pytest.approx(np.sqrt(np.mean((expected-y)**2)))
    assert result["val_max_abs_err"]==pytest.approx(np.max(np.abs(expected-y)))


def test_fixed_five_fold_for_larger_datasets():
    first=list(prepare.folds(25));second=list(prepare.folds(25))
    assert len(first)==5
    assert sorted(np.concatenate([held for _,held in first]).tolist())==list(range(25))
    for (training,a),(_,b) in zip(first,second):
        assert np.array_equal(a,b)
        assert not set(training)&set(a)


@pytest.mark.parametrize("bad",[lambda a,b,c,d:np.array([np.nan]),lambda a,b,c,d:np.ones(3)])
def test_invalid_candidate_is_rejected(bad):
    with pytest.raises(ValueError):prepare.evaluate_arrays(bad,{"x":np.arange(3)},np.arange(3))


def test_candidate_determinism_and_input_immutability():
    X,y,_=prepare.load_dataset();saved={k:v.copy() for k,v in X.items()};sy=y.copy()
    first=train.fit_predict(X,y,X,164);second=train.fit_predict(X,y,X,164)
    assert first.shape==y.shape
    assert np.all(np.isfinite(first))
    assert np.array_equal(first,second)
    assert all(np.array_equal(X[k],v) for k,v in saved.items())
    assert np.array_equal(y,sy)
    assert {"formula","coefficients","model_name","num_params"}<=train.describe_model().keys()


def test_train_imports_and_data_access_are_restricted():
    code=(ROOT/"train.py").read_text();tree=ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node,ast.Import):assert all(n.name=="numpy" for n in node.names)
        if isinstance(node,ast.ImportFrom):assert node.module in {"__future__","prepare"}
        if isinstance(node,ast.Call) and isinstance(node.func,ast.Name):assert node.func.id not in {"open","eval","exec","__import__"}
    assert "II-" not in code
    assert "test_id" not in code
    assert "load_dataset" not in code


def test_targets_recompute_from_extracted_series():
    groups=defaultdict(list)
    for row in read_csv(PROCESSED/"sensor_timeseries.csv"):groups[row["test_id"]].append(row)
    for row in read_csv(PROCESSED/"model_dataset.csv"):
        series=groups[row["test_id"]]
        t=np.array([float(r["time_since_ignition_s"]) for r in series])
        c=np.array([float(r["co2_ppm"]) for r in series])
        target,_=response_at_horizon(t,c)
        assert float(row[prepare.TARGET])==pytest.approx(target,abs=1e-7)


def test_each_metric_has_traceability_and_null_reason():
    rows=read_csv(PROCESSED/"metrics.csv")
    seen=set()
    for r in rows:
        assert (r["test_id"],r["metric"]) not in seen
        seen.add((r["test_id"],r["metric"]))
        assert all(r[k] for k in ("source_file","source_channels","method","selection_reason","conclusion"))
        if not r["value"]:assert r["reason_if_null"]
    assert sum(r["metric"]=="spread_rate_reported_mm_s" and bool(r["value"]) for r in rows)==2
    assert all(not r["value"] for r in rows if r["metric"] in ("hrr_peak_kw","smoke_alarm_delay_s","flow_cut_extinction_delay_s"))


def test_electrical_events_validate_and_flow_discrepancy_is_retained():
    assert all(r["status"]=="pass" for r in read_csv(PROCESSED/"validation_checks.csv"))
    rows=read_csv(PROCESSED/"model_dataset.csv")
    assert float(rows[5]["flow_pre_cm_s"])==pytest.approx(25,abs=.1)


def test_image_sampling_has_every_test_and_real_horizon_coverage():
    rows=read_csv(PROCESSED/"image_frame_audit.csv")
    assert len(rows)==27
    assert len({r["test_id"] for r in rows})==9
    assert all(float(r["time_mismatch_s"])<=2 for r in rows)
    assert all(r["archive_member"] for r in rows)


def test_json_schema_evidence_and_csv_consistency():
    doc=build()
    required={"experiment","psi_investigation","generated_at","data_inventory_summary","data_plan","tests","autoresearch","predictive_model","findings","relevance_ranking","key_insights","data_quality","limitations","dashboard_hints"}
    assert required<=doc.keys()
    assert doc["psi_investigation"]=="PSI-99"
    assert {k:v for k,v in doc.items() if k.endswith("psi_investigation")}=={"psi_investigation":"PSI-99"}
    assert doc["data_inventory_summary"]["identified_psi_investigation"]=="PSI-99"
    assert 6<=len(doc["key_insights"])<=10
    counts=Counter(r["objective"] for r in doc["key_insights"])
    assert all(counts[x]>=2 for x in doc["challenge_objectives"])
    for r in doc["key_insights"]:
        for path in r["evidence"]:pointer(doc,path)
    for test,row in zip(doc["tests"],read_csv(PROCESSED/"model_dataset.csv")):
        assert test["results"][prepare.TARGET]["value"]==float(row[prepare.TARGET])
    assert len(doc["predictive_model"]["cv_predictions"])==9
    assert all(e["status"].startswith("analyst_design_assumption") for e in doc["relevance_ranking"]["environment_assumptions"].values())
    json.dumps(doc,allow_nan=False)


def test_json_determinism_except_generation_time():
    a=build();b=build();a.pop("generated_at");b.pop("generated_at")
    assert a==b


def test_relevance_has_each_test_in_each_environment():
    doc=build()
    for rows in doc["relevance_ranking"]["environments"].values():
        assert len(rows)==9
        assert len({r["test_id"] for r in rows})==9
        assert all(0<=r["score"]<=100 for r in rows)
        assert all(not r["transfer_to_environment_validated"] for r in rows)
