"""Read-only SAFFIRE adapter: python3 frontend/scripts/export-saffire.py."""
import csv
import hashlib
import json
import math
from pathlib import Path
from statistics import median

FRONTEND = Path(__file__).resolve().parents[1]
SOURCE = FRONTEND.parent / 'investigations/SAFFIRE'
PUBLIC = FRONTEND / 'public/data/saffire'
ENTITY = FRONTEND / 'src/entities/saffire'
PUBLIC.mkdir(parents=True, exist_ok=True)
ENTITY.mkdir(parents=True, exist_ok=True)

def read(name):
    return json.loads((SOURCE / name).read_text())

def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, separators=(',', ':'), allow_nan=False) + '\n')

p = read('predictions.json')
a = read('analysis-saffire.json')
s = read('analysis-saffire-summary.json')
assert p['schema_version'] == 2 and p['model'] == 'group_huber20_inverse_flow'
assert p['residual_definition'] == 'actual_minus_predicted'
for ref in p['references']['source_files']:
    assert hashlib.sha256((SOURCE / ref['file']).read_bytes()).hexdigest() == ref['sha256'], ref['file']
target = 'co2_increase_180s_ppm'
series = {t['test_id']: [] for t in a['tests']}
with (SOURCE / 'data/processed/sensor_timeseries.csv').open() as f:
    for row in csv.DictReader(f):
        if row['co2_ppm']:
            point = [float(row['time_since_ignition_s']), float(row['co2_ppm'])]
            assert all(math.isfinite(x) for x in point)
            series[row['test_id']].append(point)
rows = []
for i, (t, prediction) in enumerate(zip(a['tests'], p['predictions'], strict=True)):
    assert t['test_id'] == prediction['test_id']
    values = series[t['test_id']]
    baseline = median(v for time, v in values if -30 <= time < 0)
    response = median(v for time, v in values if 150 <= time < 180) - baseline
    actual, predicted, residual = [prediction[k][target] for k in ['actual', 'predicted', 'residual']]
    assert abs(response - actual) < 1e-7, t['test_id']
    assert abs(actual - predicted - residual) < 1e-10
    c = t['conditions']
    rows.append(dict(id=t['test_id'], material=c['material']['value'], flow=c['flow_pre_cm_s']['value'], actual=actual, predicted=predicted, residual=residual, baseline=baseline, responseMetadata=t['results'][target], conditions=c, source=prediction['source_pointer'], sources=t['source_files']))
    write(PUBLIC / (t['test_id'] + '.json'), dict(test_id=t['test_id'], unit='ppm', time_unit='s', kind='absolute_sensor_reading', baseline_ppm=baseline, source_file=t['results'][target]['source_file'], source_channels=t['results'][target]['source_channels'], method='per_channel_1s_median; ignition_electrical_t0', points=values))
assert len(rows) == 9
metrics = p['metrics'][target]
assert abs(math.sqrt(sum(r['residual']**2 for r in rows)/9) - metrics['rmse']) < 1e-10
assert abs(sum(abs(r['residual']) for r in rows)/9 - metrics['mae']) < 1e-10
model = a['predictive_model']
write(ENTITY / 'evidence.json', dict(rows=rows, metrics=metrics, model=dict(name=model['model_name'], formula=model['formula'], coefficients=model['coefficients'], flowRange=model['validity_range']['inputs']['flow_pre_cm_s']), target=p['target_metadata'][target], validation=p['validation'], source=s['source'], provenance=p['references']['source_files']))
# Evaluate the exact exported Python expression, without fitting or changing models.
expression = model['formula'].split(' = ', 1)[1].replace('^', '**')
fixtures = []
for material in ['Silicone', 'SIBAL', 'PMMA', 'PMMA_Nomex']:
    for flow in [model['validity_range']['inputs']['flow_pre_cm_s'][0], 20, 22, 24.9, model['validity_range']['inputs']['flow_pre_cm_s'][1]]:
        expected = eval(expression, {'__builtins__': {}}, dict(model['coefficients'], material=material, Silicone='Silicone', flow_cm_s=flow))
        fixtures.append(dict(material=material, flow=flow, expected=expected))
write(ENTITY / 'formula-fixtures.json', fixtures)
for name in ['predictions.json', 'SAFFIRE_ANALYSIS_REPORT_EN.md']:
    (PUBLIC / name).write_bytes((SOURCE / name).read_bytes())
print('SAFFIRE: 9 responses, source hashes, residuals, MAE/RMSE and sensor windows verified; 20 Python formula fixtures exported.')
