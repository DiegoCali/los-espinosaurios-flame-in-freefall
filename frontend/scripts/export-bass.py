"""Export existing BASS-II evidence; no extraction, fitting or source writes."""
import csv
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'investigations/BASS-II'
FRONT = ROOT / 'frontend'


def read_csv(name):
    return list(csv.DictReader((SOURCE / name).open()))


def number(value):
    if value in ('', None):
        return None
    value = float(value)
    return value if math.isfinite(value) else None


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(',', ':')) + '\n')


ensemble = 'reports/figures/_ensemble/'
rates = []
for row in read_csv(ensemble + 'steady_rates.csv'):
    rates.append({key: number(row[key]) if key in {'rate', 'lo', 'hi', 't0', 't1', 'thickness_mm', 'flow_initial_cm_s', 'o2_initial_pct'} else row[key]
                  for key in ['test_id', 'rate', 'lo', 'hi', 'unit', 'status', 'qc', 'geometry', 'material_class', 'thickness_mm', 'flow_initial_cm_s', 'o2_initial_pct', 't0', 't1']})
comparisons = []
for row in read_csv(ensemble + 'G6_parity_published.csv'):
    comparisons.append({key: number(row[key]) if key in {'vf_measured_mm_s', 'vf_published_mm_s', 'published_step', 'rel_error'} else row[key]
                        for key in ['test_id', 'vf_measured_mm_s', 'vf_published_mm_s', 'published_step', 'rel_error', 'set', 'qc_status', 'source']})
original = json.loads((SOURCE / 'predictions.json').read_text())
assert not original['predictions'], 'Revisit trajectory availability when upstream exports change'
assert len(rates) == 83 and sum(r['status'] == 'steady_spread' for r in rates) == 54
assert len(comparisons) == 25
assert original['validation']['holdout_accounting']['n_processed'] == 13
assert sum(r['set'] == 'holdout' for r in comparisons) == 14
files = ['predictions.json', 'reports/REPORT.md', 'reports/physics_review.md', 'reports/validation_summary.json',
         'src/bass2/forecast.py', 'src/bass2/forecast_ensemble.py', 'src/bass2/pipeline.py', 'src/bass2/metrics.py',
         'configs/pipeline.yaml', 'configs/qc.yaml', 'configs/holdout_tests.yaml', 'research/best/result.json',
         ensemble + 'steady_rates.csv', ensemble + 'G6_parity_published.csv', ensemble + 'forecast_summary.csv', ensemble + 'forecast_summary_all_tests.csv']
series_ids = []
for test in ['B1', 'M1', 'B4']:
    name = f'reports/figures/{test}/G3_edge_fit.csv'
    rows = [{key: number(value) for key, value in row.items()} for row in read_csv(name)]
    assert len(rows) > 100 and all(r['time_s'] is not None for r in rows)
    write(FRONT / f'public/data/bass/series/{test}.json', rows)
    series_ids.append(test)
    files.append(name)
manifest = []
for name in files:
    data = (SOURCE / name).read_bytes()
    destination = FRONT / 'public/data/bass/sources' / name
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(data)
    manifest.append({'file': name, 'sha256': hashlib.sha256(data).hexdigest()})
write(FRONT / 'src/entities/bass/evidence.json', {
    'rates': rates, 'comparisons': comparisons,
    'forecast': [r for r in original['metrics']['forecast_qc_trusted'] if r['target'] == 'leading_edge'],
    'validation': original['validation'], 'seriesIds': series_ids, 'sources': manifest,
})
print('BASS-II: 83 records, 25 comparisons, 21 physical forecast aggregates, 3 measured series; sources unchanged.')
