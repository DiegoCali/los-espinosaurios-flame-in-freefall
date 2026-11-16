import evidence from './evidence.json';
import {sizeTargets, type SizeRow} from './size';
import {detectors, type DetectionRow} from './detection';
export const sameEvidence = evidence;
export type Scenario = typeof evidence.scenarios[number];
export type ValidationRow = SizeRow | DetectionRow;
export function savedScenario(material: string, flow: string, age: number): Scenario {
  const row = evidence.scenarios.find(r => r.material === material && r.flow_regime === flow && r.aging_s === age);
  if (!row) throw new Error('SAME_SCENARIO');
  return row;
}
export function validValidation(value: unknown): value is ValidationRow[] {
  if (!Array.isArray(value) || value.length !== 117) return false;
  const valid = value.every(r => {
    if (!r || typeof r !== 'object' || !['size', 'detection'].includes(r.task) || typeof r.material !== 'string' || typeof r.source_pointer !== 'string') return false;
    const targets = r.task === 'size' ? sizeTargets : detectors;
    if (!['actual', 'predicted', 'residual'].every(k => r[k] && targets.every(t => typeof r[k][t] === 'number' && Number.isFinite(r[k][t])))) return false;
    return r.task === 'size' ? Number.isInteger(r.run) && Number.isInteger(r.source_row)
      : Number.isInteger(r.test) && Number.isInteger(r.push_index) && Number.isFinite(r.aging_s) && Number.isFinite(r.flow_velocity_cm_s) && detectors.every(t => [0,1].includes(r.actual[t]) && r.predicted[t] >= 0 && r.predicted[t] <= 1);
  });
  const size = value.filter(r => r.task === 'size'), det = value.filter(r => r.task === 'detection');
  return valid && size.length === 52 && det.length === 65 && new Set(size.map(r => r.run)).size === 35 && new Set(det.map(r => r.test)).size === 36;
}
