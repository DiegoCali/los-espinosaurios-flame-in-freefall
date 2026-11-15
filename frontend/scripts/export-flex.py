"""Export read-only FLEX sources; never import or execute the training pipeline."""
import csv
import hashlib
import json
import math
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'investigations/flex'
PUBLIC = ROOT / 'frontend/public/data/flex'
ENTITY = ROOT / 'frontend/src/entities/flex'
PUBLIC.mkdir(parents=True, exist_ok=True)
ENTITY.mkdir(parents=True, exist_ok=True)
saved = json.loads((SOURCE / 'predictions.json').read_text())
assert saved['schema_version'] == 2 and len(saved['predictions']) == 50
assert saved['residual_definition'] == 'actual_minus_predicted'
assert saved['validation_campaign'] == 'NaT'
table = SOURCE / saved['data_source']['file']
assert hashlib.sha256(table.read_bytes()).hexdigest() == saved['data_source']['sha256']

def number(value):
    try:
        result = float(value)
        return result if math.isfinite(result) else None
    except (ValueError, TypeError):
        return None

with table.open(encoding='cp1252', newline='') as source:
    original = list(csv.DictReader(source))
assert len(original) == 274
records = []
for prediction in saved['predictions']:
    row = original[prediction['row_index']]
    for target in saved['target_metadata']:
        actual = prediction['actual'][target]
        predicted = prediction['predicted'][target]
        residual = prediction['residual'][target]
        assert (actual is None and residual is None) or math.isclose(actual - predicted, residual, abs_tol=1e-14)
        source_actual = number(row['Burn time; s'] if target == 'burn_time_s' else row['Burning rate; mm'])
        if source_actual is not None and target == 'burning_rate_m2_s':
            source_actual /= 1e6
        assert source_actual == actual or (source_actual is not None and actual is not None and math.isclose(source_actual, actual))
    records.append({**prediction, 'id': row['FLEX Identifier'], 'test': int(row['FLEX Test #']),
                    'fuel': row['Fuel'], 'oxygen': number(row['O initial ambient composition; mole fraction']),
                    'pressure_mmhg': number(row['Ambient pressure; mmHg']),
                    'diameter_mm': number(row['Droplet initial diameter; mm']),
                    'outcome': row['Test end'], 'source_date': row['Test Date'], 'parsed_date': None})

for target, metric in saved['metrics'].items():
    if target == 'objective':
        continue
    residuals = [r['residual'][target] for r in records if r['residual'][target] is not None]
    assert len(residuals) == metric['n_validation'] == 49
    assert math.isclose(math.sqrt(sum(r*r for r in residuals)/len(residuals)), metric['rmse'], rel_tol=1e-12)

histories = []
for identifier, filename in [('20CAL13', 'Heptane_FLEX-007_DropletData.txt'), ('20CAL08', 'MeOH_Air_FLEX-001_DropletData.txt'), ('256F002', 'MeOH_FLEX-010_DropletData.txt')]:
    with (SOURCE / 'data' / filename).open(encoding='utf-8-sig', newline='') as source:
        points = [[number(r['DropletTime_sec']), number(r['DropletDiameter_mm'])] for r in csv.DictReader(source, delimiter='\t')]
    points = [p for p in points if all(v is not None for v in p)]
    reference = min(points, key=lambda p: abs(p[0] - .3))
    assert reference[1] > 0 and abs(reference[0] - .3) < .04
    # Keep every measured point, including the pre-reference segment; the UI chooses the displayed interval.
    histories.append({'id': identifier, 'file': filename, 'reference_time_s': reference[0],
                      'reference_diameter_mm': reference[1], 'points': points})
    shutil.copyfile(SOURCE / 'data' / filename, PUBLIC / filename)
assert [len(h['points']) for h in histories] == [141, 170, 229]
payload = {'metrics': saved['metrics'], 'dataset': saved['discovery']['study_summary']['dataset'],
           'validation': saved['validation'], 'records': records, 'sources': saved['references']['source_files']}
(ENTITY / 'evidence.json').write_text(json.dumps(payload, allow_nan=False, indent=2) + '\n')
(PUBLIC / 'histories.json').write_text(json.dumps(histories, allow_nan=False) + '\n')
shutil.copyfile(SOURCE / 'predictions.json', PUBLIC / 'predictions.json')
shutil.copyfile(table, PUBLIC / table.name)
print('FLEX verified: 274 source rows, 50 predictions, 49 observations per target, 540 measured trajectory points; original sources unchanged.')
