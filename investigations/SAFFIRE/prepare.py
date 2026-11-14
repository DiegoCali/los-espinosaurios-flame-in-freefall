"""PROTECTED: fixed dataset, allowed inputs, folds and independent evaluation."""
from __future__ import annotations
import argparse
import csv
import importlib
import json
import time
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parent
DATA_PATH=ROOT/"data/processed/model_dataset.csv"
TARGET="co2_increase_180s_ppm"
INPUTS=("material","thickness_nominal_mm","flow_pre_cm_s","direction","ignition_duration_command_s","ignition_power_command_w","structured_pmma")
CATEGORICAL={"material","direction"}
SEED=164


def load_dataset(path=DATA_PATH):
    with Path(path).open(newline="",encoding="utf-8") as handle:
        reader=csv.DictReader(handle)
        required=set(INPUTS)|{TARGET,"test_id","source_file","method"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError("Dataset missing required columns")
        rows=list(reader)
    if len(rows)<3:raise ValueError("At least three independent test rows required")
    ids=[r["test_id"] for r in rows]
    if len(set(ids))!=len(ids):raise ValueError("Duplicate test IDs; frames are not independent tests")
    X={k:np.array([r[k] for r in rows],dtype=str if k in CATEGORICAL else float) for k in INPUTS}
    y=np.array([r[TARGET] for r in rows],dtype=float)
    if not np.all(np.isfinite(y)):raise ValueError("Target must be finite")
    for key,val in X.items():
        if key not in CATEGORICAL and not np.all(np.isfinite(val)):
            raise ValueError(f"Nonfinite input {key}")
    if not set(X["material"]).issubset({"Silicone","SIBAL","PMMA_Nomex","PMMA"}):raise ValueError("Unknown material")
    if not set(X["direction"]).issubset({"concurrent","opposed"}):raise ValueError("Unknown flow direction")
    if np.any(X["thickness_nominal_mm"]<=0) or np.any(X["flow_pre_cm_s"]<=0):raise ValueError("Positive thickness and flow required")
    return X,y,rows


def folds(n,seed=SEED):
    if n<=20:
        for i in range(n):
            mask=np.ones(n,dtype=bool);mask[i]=False
            yield np.flatnonzero(mask),np.array([i])
    else:
        order=np.random.default_rng(seed).permutation(n)
        for held in np.array_split(order,5):
            yield np.setdiff1d(np.arange(n),held),held


def evaluate_arrays(predict_fn,X,y,seed=SEED):
    n=len(y);prediction=np.empty(n,dtype=float)
    for fold,(training,held) in enumerate(folds(n,seed)):
        train_X={k:v[training].copy() for k,v in X.items()}
        eval_X={k:v[held].copy() for k,v in X.items()}
        pred=np.asarray(predict_fn(train_X,np.asarray(y)[training].copy(),eval_X,seed+fold),dtype=float).reshape(-1)
        if pred.shape!=(len(held),) or not np.all(np.isfinite(pred)):
            raise ValueError("Candidate must return one finite prediction per held-out row")
        prediction[held]=pred
    error=prediction-y
    return {"val_rmse":float(np.sqrt(np.mean(error**2))),"val_mae":float(np.mean(np.abs(error))),"val_max_abs_err":float(np.max(np.abs(error))),"predictions":prediction}


def evaluate_candidate(module=None):
    start=time.perf_counter()
    module=module or importlib.import_module("train")
    X,y,rows=load_dataset()
    result=evaluate_arrays(module.fit_predict,X,y)
    # Refit on all rows only AFTER generating all held-out predictions.
    fitted=np.asarray(module.fit_predict({k:v.copy() for k,v in X.items()},y.copy(),{k:v.copy() for k,v in X.items()},SEED))
    if fitted.shape!=y.shape or not np.all(np.isfinite(fitted)):raise ValueError("Invalid final fit")
    description=module.describe_model()
    if not {"formula","coefficients","num_params","model_name"}.issubset(description):raise ValueError("Incomplete model description")
    if not isinstance(description["num_params"],int) or description["num_params"]<1:raise ValueError("Invalid parameter count")
    predictions=result.pop("predictions")
    result.update({"model_name":description["model_name"],"num_params":description["num_params"],"elapsed_seconds":float(time.perf_counter()-start),"n_rows":len(rows),"target":TARGET,"inputs":list(INPUTS),"validation":"leave_one_test_out" if len(y)<=20 else "5_fold_seed_164","seed":SEED,"model":description,"cv_predictions":[{"test_id":r["test_id"],"observed":float(obs),"predicted":float(pred),"error":float(pred-obs),"source_file":r["source_file"],"method":"held_out_training_only_fit; fixed_folds"} for r,obs,pred in zip(rows,y,predictions)]})
    return result


def print_report(result):
    print("---")
    for key in ["model_name","val_rmse","val_mae","val_max_abs_err","num_params","elapsed_seconds"]:
        print(f"{key}: {result[key]}")


def main():
    parser=argparse.ArgumentParser();parser.add_argument("--check",action="store_true");parser.add_argument("--evaluate-output",type=Path);args=parser.parse_args()
    if args.check:
        X,y,rows=load_dataset();print(f"Validated {len(rows)} test rows; target={TARGET}; inputs={','.join(INPUTS)}")
    else:
        result=evaluate_candidate();print_report(result)
        if args.evaluate_output:
            args.evaluate_output.parent.mkdir(parents=True,exist_ok=True)
            args.evaluate_output.write_text(json.dumps(result,indent=2,allow_nan=False)+"\n")

if __name__=="__main__":main()
