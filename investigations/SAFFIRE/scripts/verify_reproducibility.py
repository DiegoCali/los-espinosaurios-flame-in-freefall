#!/usr/bin/env python3
"""Run the complete extraction/export twice and compare the scientific payload."""
from __future__ import annotations
import hashlib
import json
import subprocess
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from extraction.common import ROOT,PROCESSED,write_json
from extraction.inventory import verify_integrity

def scientific_payload():
    doc=json.loads((ROOT/"analysis-saffire.json").read_text());doc.pop("generated_at")
    return doc

def processed_hashes():
    return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(PROCESSED.rglob("*")) if p.is_file()}

def main():
    verification=ROOT/"runs/verification"
    write_json(verification/"raw_integrity_final.json",verify_integrity(full=True))
    saved=None;hashes=None
    for iteration in (1,2):
        print(f"Full reproducibility pass {iteration}/2",flush=True)
        subprocess.run([sys.executable,str(ROOT/"extraction/run_all.py")],cwd=ROOT,check=True)
        subprocess.run([sys.executable,str(ROOT/"analysis/build_analysis_json.py")],cwd=ROOT,check=True)
        current=scientific_payload();current_hashes=processed_hashes()
        if saved is not None:
            if saved!=current:raise RuntimeError("Analysis JSON changed beyond generated_at")
            if hashes!=current_hashes:raise RuntimeError("Processed files changed across identical runs")
        saved=current;hashes=current_hashes
    # Metadata check after both read-only passes; full byte hashes were checked before.
    verify_integrity()
    digest=hashlib.sha256(json.dumps(saved,sort_keys=True,ensure_ascii=False,allow_nan=False).encode()).hexdigest()
    result={"n_full_passes":2,"json_identical_except_generated_at":True,"all_processed_files_byte_identical":True,"scientific_json_sha256":digest,"processed_file_hashes":hashes,"raw_integrity":"Full SHA256 verified against initial manifest, then size/mtime after both passes"}
    write_json(verification/"reproducibility.json",result)
    print(json.dumps({k:v for k,v in result.items() if k!="processed_file_hashes"}))

if __name__=="__main__":main()
