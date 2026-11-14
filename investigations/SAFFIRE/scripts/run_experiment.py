#!/usr/bin/env python3
"""Immutable experiment gate: clean Git, train.py-only diff, timeout and ledger."""
from __future__ import annotations
import argparse
import csv
import json
import math
import subprocess
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from prepare import ROOT

COLUMNS=("attempt","commit","model_name","val_rmse","val_mae","val_max_abs_err","num_params","status","description")
MAX_ATTEMPTS=15

def git(*args):
    return subprocess.run(["git",*args],cwd=ROOT,check=True,capture_output=True,text=True).stdout.strip()

def check_tree():
    if git("status","--porcelain","--untracked-files=all"):
        raise RuntimeError("Require a clean Git tree including untracked files; commit candidate first")
    changed=git("diff","--name-only","baseline-v1..HEAD").splitlines()
    if set(changed)-{"train.py"}:
        raise RuntimeError(f"Protected files differ from baseline-v1: {changed}")
    return git("rev-parse","HEAD")

def decision(result,best):
    if best is None:return "keep"
    improvement=best["val_rmse"]-result["val_rmse"]
    if improvement<=max(1e-9,abs(best["val_rmse"])*0.001):return "discard"
    # A model adding parameters must improve RMSE by at least 2% per added parameter.
    added=max(0,result["num_params"]-best["num_params"])
    if added and improvement/best["val_rmse"] < .02*added:return "discard"
    return "keep"

def main():
    parser=argparse.ArgumentParser();parser.add_argument("--run-id",default="saffire-run-01");parser.add_argument("--description",required=True);parser.add_argument("--timeout",type=int,default=60);args=parser.parse_args()
    if "/" in args.run_id or ".." in args.run_id:raise ValueError("Invalid run ID")
    commit=check_tree()
    directory=ROOT/"runs/autoresearch"/args.run_id;directory.mkdir(parents=True,exist_ok=True)
    ledger=directory/"results.tsv"
    if ledger.exists():
        with ledger.open(newline="") as handle:previous=list(csv.DictReader(handle,delimiter="\t"))
    else:previous=[]
    if len(previous)>=MAX_ATTEMPTS:raise RuntimeError("15-attempt budget exhausted")
    if previous and any(r["commit"]==commit for r in previous):raise RuntimeError("Commit already evaluated")
    attempt=len(previous)+1
    if not previous and commit!=git("rev-parse","baseline-v1"):
        raise RuntimeError("First attempt must be the tagged constant baseline")
    best_path=directory/"best.json"
    best=json.loads(best_path.read_text()) if best_path.exists() else None
    result_path=directory/f"attempt-{attempt:02d}.json"
    log_path=directory/f"attempt-{attempt:02d}.log"
    row={k:"" for k in COLUMNS};row.update(attempt=attempt,commit=commit,status="crash",description=args.description.replace("\t"," ").replace("\n"," "))
    try:
        with log_path.open("w") as log:
            run=subprocess.run([sys.executable,str(ROOT/"prepare.py"),"--evaluate-output",str(result_path)],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,timeout=args.timeout)
        if run.returncode!=0:raise RuntimeError(f"Evaluation exited {run.returncode}; see {log_path}")
        result=json.loads(result_path.read_text())
        if any(not math.isfinite(float(result[k])) for k in ("val_rmse","val_mae","val_max_abs_err")):raise ValueError("Nonfinite metric")
        for key in ("model_name","val_rmse","val_mae","val_max_abs_err","num_params"):row[key]=result[key]
        row["status"]=decision(result,best)
        result.update(commit=commit,attempt=attempt,status=row["status"],description=args.description)
        result_path.write_text(json.dumps(result,indent=2,allow_nan=False)+"\n")
        if row["status"]=="keep":best_path.write_text(json.dumps(result,indent=2,allow_nan=False)+"\n")
    except (Exception,subprocess.TimeoutExpired) as exc:
        with log_path.open("a") as log:log.write(f"\nEXPERIMENT FAILURE: {exc}\n")
    with ledger.open("a",newline="") as handle:
        writer=csv.DictWriter(handle,fieldnames=COLUMNS,delimiter="\t")
        if not previous:writer.writeheader()
        writer.writerow(row)
    print(json.dumps(row))
    best=json.loads(best_path.read_text()) if best_path.exists() else None
    if best:print("best_commit:",best["commit"])
    return 1 if row["status"]=="crash" else 0

if __name__=="__main__":raise SystemExit(main())
