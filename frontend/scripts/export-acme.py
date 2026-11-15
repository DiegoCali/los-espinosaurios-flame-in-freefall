"""Offline export of the frozen ACME Ridge; requires NumPy from ACME requirements.

Run: /path/to/python-with-numpy frontend/scripts/export-acme.py
Writes frontend artifacts only. Never runs the holdout evaluator or a new search.
"""
import csv
import hashlib
import importlib.util
import io
import json
import math
import sys
from collections import Counter
from pathlib import Path

import numpy as np

sys.dont_write_bytecode = True
FRONTEND = Path(__file__).resolve().parents[1]
SOURCE = FRONTEND.parent / 'investigations/ACME'
ENTITY = FRONTEND / 'src/entities/acme'
PUBLIC = FRONTEND / 'public/data/acme'


def read(name):
    return json.loads((SOURCE / name).read_text())


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, separators=(',', ':'), allow_nan=False) + '\n')


p = read('predictions.json')
validation = read('runs/pilot-01/validation_predictions.json')
selected = read('runs/pilot-01/latest_validation.json')
holdout = read('runs/holdout-final-v1/final_holdout_metrics.json')
refs = {r['file']: r['sha256'] for r in p['references']['source_files']}
for name, digest in refs.items():
    if (SOURCE / name).exists():
        assert hashlib.sha256((SOURCE / name).read_bytes()).hexdigest() == digest, name
assert p['model'] == validation['model'] == selected['model_name'] == holdout['model_name']
assert p['residual_definition'] == validation['residual_definition'] == 'actual_minus_predicted'
assert selected['train_sha256'] == holdout['train_sha256'] == refs['train.py']
assert validation['predictions'] == p['predictions']
with (SOURCE / 'data/processed/acme_tad_pilot.csv').open(newline='') as f:
    reader = csv.DictReader(f)
    fields = reader.fieldnames
    partitions = {'train': [], 'validation': []}
    counts = Counter()
    for row in reader:
        counts[row['split']] += 1
        if row['split'] in partitions:
            partitions[row['split']].append(row)
assert dict(counts) == p['validation']['partitions'] == {'train': 134, 'validation': 52, 'holdout': 50}
# Recover absent split files in memory, verifying their original hashes; no protected files are written.
for name, rows in partitions.items():
    memory = io.StringIO(newline='')
    writer = csv.DictWriter(memory, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)
    assert hashlib.sha256(memory.getvalue().encode()).hexdigest() == refs[f'data/processed/acme_tad_{name}.csv'], name
    assert set(r['group_id'] for r in rows) == set(p['validation']['groups'][name])
assert not set(p['validation']['groups']['train']) & set(p['validation']['groups']['validation'])
order = validation['feature_order']
assert order == selected['features']


def inputs(row):
    return [float(row['flame_type'] == 'Inverse')] + [float(row[f]) for f in order[1:]]


X = np.array([inputs(r) for r in partitions['train']])
y = np.array([float(r['tad_calculated_k']) for r in partitions['train']])
V = np.array([inputs(r) for r in partitions['validation']])
assert np.isfinite(X).all() and np.isfinite(y).all() and np.isfinite(V).all()
spec = importlib.util.spec_from_file_location('frozen_acme_train', SOURCE / 'train.py')
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)
captured = {}


def capture(frame, event, arg):
    if event == 'return' and frame.f_code is model.fit_predict.__code__:
        for key in ['means', 'scales', 'fitted']:
            captured[key] = frame.f_locals[key].tolist()
    return capture


# Execute the selected original algorithm on the original 134 rows only.
try:
    sys.settrace(capture)
    estimates = model.fit_predict(X.copy(), y.copy(), V.copy(), validation['seed'])
finally:
    sys.settrace(None)
actuals = np.array([r['actual']['tad_calculated_k'] for r in p['predictions']])
saved = np.array([r['predicted']['tad_calculated_k'] for r in p['predictions']])
assert max(abs(estimates - saved)) < 1e-6
residuals = actuals - saved
metrics = p['metrics']['tad_calculated_k']
assert abs(math.sqrt(np.mean(residuals**2)) - metrics['validation']['rmse']) < 1e-9
assert abs(np.mean(abs(residuals)) - metrics['validation']['mae']) < 1e-9
for record, prediction in zip(partitions['validation'], p['predictions'], strict=True):
    assert record['test_id'] == prediction['test_id']
    assert float(record['tad_calculated_k']) == prediction['actual']['tad_calculated_k']
    assert abs(prediction['residual']['tad_calculated_k'] - prediction['actual']['tad_calculated_k'] + prediction['predicted']['tad_calculated_k']) < 1e-9
model_export = dict(name=p['model'], featureOrder=order, alpha=model.RIDGE_ALPHA,
                    means=captured['means'], scales=captured['scales'], coefficients=captured['fitted'],
                    n_train=134, unit='K', train_sha256=refs['train.py'],
                    trainingDomains={name: dict(min=X[X[:, 0] == flag].min(axis=0).tolist(), max=X[X[:, 0] == flag].max(axis=0).tolist()) for flag, name in [(0, 'Normal'), (1, 'Inverse')]},
                    provenance=dict(p['validation'], recovered_split_hashes={name: refs[f'data/processed/acme_tad_{name}.csv'] for name in partitions}))
write(ENTITY / 'model.json', model_export)
fixtures = [dict(id=r['test_id'], inputs=inputs(r), expected=float(value)) for r, value in zip(partitions['validation'], estimates, strict=True)]
write(ENTITY / 'python-fixtures.json', fixtures)
write(ENTITY / 'evidence.json', dict(model=p['model'], metrics=metrics, validation=p['validation'], target=p['target_metadata'], source_files=p['references']['source_files']))
rows = []
for record, prediction in zip(partitions['validation'], p['predictions'], strict=True):
    rows.append(dict(prediction, inputs=inputs(record), ambientReactant=record['ambient_reactant'], burnerReactant=record['burner_reactant']))
write(PUBLIC / 'validation.json', rows)
write(PUBLIC / 'experimental.json', p['discovery']['experimental_data']['pilot'])
for name in ['predictions.json', 'analysis/FINAL_TAD_PILOT.md', 'runs/holdout-final-v1/final_holdout_metrics.json']:
    dest = PUBLIC / Path(name).name
    dest.write_bytes((SOURCE / name).read_bytes())
print(f'ACME: verified 134/52/50 partitions, original hashes and 52 Python predictions; max difference {max(abs(estimates-saved)):.3g} K. No holdout predictions generated.')
