"""Read-only SAME-R web export. No fitting or changes to investigation files."""
import hashlib
import json
import math
from pathlib import Path
from shutil import copyfile

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'investigations/SAME'
FRONTEND = ROOT / 'frontend'
p = json.loads((SOURCE / 'predictions.json').read_text())
s = json.loads((SOURCE / 'analysis-same-summary.json').read_text())
a = json.loads((SOURCE / 'analysis-same.json').read_text())
assert p['schema_version'] == 2
for ref in p['references']['source_files']:
    assert hashlib.sha256((SOURCE / ref['file']).read_bytes()).hexdigest() == ref['sha256'], ref['file']
size = [r for r in p['predictions'] if r['task'] == 'size']
det = [r for r in p['predictions'] if r['task'] == 'detection']
assert len(size) == 52 and len({r['run'] for r in size}) == 35
assert len(det) == 65 and len({r['test'] for r in det}) == 36
scenarios = a['predictive_model']['scenario_curves']
assert len(scenarios) == 90
assert len({(r['material'], r['flow_regime'], r['aging_s']) for r in scenarios}) == 90
assert len([r for r in scenarios if r['material'] in ['Kapton', 'Lampwick'] and r['aging_s'] in [38, 566]]) == 8
assert all(0 <= r[k] <= 1 for r in scenarios for k in ['p_iss_detect', 'p_ion_detect'])
for material in s['scope']['materials']:
    for flow in ['flow_8cm_s', 'no_flow']:
        rows = [r for r in scenarios if r['material'] == material and r['flow_regime'] == flow]
        for branch in [False, True]:
            for key in ['p_iss_detect', 'p_ion_detect']:
                assert len({r[key] for r in rows if (r['aging_s'] > 120) == branch}) == 1

def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, separators=(',', ':'), allow_nan=False) + '\n')

# Do not export the misleading historical *_false_negative_risk aliases.
scenarios = [{k: v for k, v in r.items() if not k.endswith('_false_negative_risk')} for r in scenarios]
write(FRONTEND / 'src/entities/same/evidence.json', {
    'schema_version': 2, 'validation': p['validation'], 'metrics': p['metrics'],
    'scope': s['scope'], 'materials': s['material_summary'],
    'detectors': a['detectors']['overall'], 'scenarios': scenarios,
    'rt_r0': a['predictive_model']['rt_r0_used_for_scenarios'],
    'source_sha256': hashlib.sha256((SOURCE / 'predictions.json').read_bytes()).hexdigest(),
})
write(FRONTEND / 'public/data/same/validation.json', p['predictions'])
write(FRONTEND / 'src/entities/same/physical-fixtures.json', [
    {'target': key, 'input': r[kind][key], 'expected': math.exp(r[kind][key]) if key == 'ln_sigma_g' else 10 ** r[kind][key]}
    for r in size for kind in ['actual', 'predicted'] for key in r[kind]
])
for src, dest in [('predictions.json', 'predictions.json'), ('SAME_ANALYSIS_REPORT_EN.md', 'report-en.md'),
                  ('data/processed/VALIDATION.md', 'VALIDATION.md'),
                  ('data/processed/test_material_audit.csv', 'test_material_audit.csv')]:
    copyfile(SOURCE / src, FRONTEND / 'public/data/same' / dest)
print('SAME-R: 90 scenarios; 52 size rows / 35 runs; 65 detection rows / 36 tests. Source hashes verified.')
