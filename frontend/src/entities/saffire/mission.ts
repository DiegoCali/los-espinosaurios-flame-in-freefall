import evidence from './evidence.json';

// Per-test documented outcomes and derived indicators for SAFFIRE-II, transcribed from
// investigations/SAFFIRE/analysis-saffire.json (tests/*/results). Burn length and duration are
// published values (null duration = "published as insignificant, not a measured zero").
// Only SIBAL has published spread rates.
export type SaffireOutcome = 'no_sustained_spread' | 'complete_fabric_spread' | 'PMMA_consumed_Nomex_not_ignited' | 'anchored_flame_slow_regression';
export type SaffireMissionTest = {
  outcome: SaffireOutcome; spreadRateMmS: number | null; plumePeakC: number;
  burnLengthCm: number; burnDurationS: number | null;
  o2Change180Pp: number; pressureChange180KPa: number; inletTempChange180C: number; radiationPeak180KWm2: number; co2Peak180Ppm: number; co2EndChangePpm: number;
};

export const saffireMission: Record<string, SaffireMissionTest> = {
  'II-1': { outcome: 'no_sustained_spread', spreadRateMmS: null, plumePeakC: 22.624760321, burnLengthCm: 0, burnDurationS: null, o2Change180Pp: 0.0366, pressureChange180KPa: 0.0016, inletTempChange180C: 0.0957, radiationPeak180KWm2: 0.255, co2Peak180Ppm: 3356.3828, co2EndChangePpm: 9.1523 },
  'II-2': { outcome: 'no_sustained_spread', spreadRateMmS: null, plumePeakC: 61.931387547, burnLengthCm: 0, burnDurationS: null, o2Change180Pp: -0.0238, pressureChange180KPa: 0.0096, inletTempChange180C: 0.0431, radiationPeak180KWm2: 0.3035, co2Peak180Ppm: 3362.2671, co2EndChangePpm: 24.7417 },
  'II-3': { outcome: 'no_sustained_spread', spreadRateMmS: null, plumePeakC: 22.882547952, burnLengthCm: 0, burnDurationS: null, o2Change180Pp: 0.019, pressureChange180KPa: 0.0064, inletTempChange180C: 0.0432, radiationPeak180KWm2: 0.1336, co2Peak180Ppm: 3350.2912, co2EndChangePpm: -11.4033 },
  'II-4': { outcome: 'no_sustained_spread', spreadRateMmS: null, plumePeakC: 22.923204145, burnLengthCm: 0, burnDurationS: null, o2Change180Pp: -0.0238, pressureChange180KPa: 0.0112, inletTempChange180C: 0.0323, radiationPeak180KWm2: 0.2993, co2Peak180Ppm: 3357.7453, co2EndChangePpm: 5.7609 },
  'II-5': { outcome: 'complete_fabric_spread', spreadRateMmS: 2.1, plumePeakC: 51.505485919, burnLengthCm: 29, burnDurationS: 145, o2Change180Pp: -0.0213, pressureChange180KPa: 0.0257, inletTempChange180C: 0.0533, radiationPeak180KWm2: 0.5622, co2Peak180Ppm: 3402.0356, co2EndChangePpm: 82.247 },
  'II-6': { outcome: 'complete_fabric_spread', spreadRateMmS: 2.6, plumePeakC: 23.118480878, burnLengthCm: 29, burnDurationS: 115, o2Change180Pp: -0.2246, pressureChange180KPa: 0.0193, inletTempChange180C: 0.093, radiationPeak180KWm2: 0.3228, co2Peak180Ppm: 3476.162, co2EndChangePpm: 74.9114 },
  'II-7': { outcome: 'PMMA_consumed_Nomex_not_ignited', spreadRateMmS: null, plumePeakC: 25.09585856, burnLengthCm: 5, burnDurationS: 140, o2Change180Pp: -0.2235, pressureChange180KPa: 0.0208, inletTempChange180C: 0.2084, radiationPeak180KWm2: 0.0538, co2Peak180Ppm: 3587.5591, co2EndChangePpm: 139.9942 },
  'II-8': { outcome: 'anchored_flame_slow_regression', spreadRateMmS: null, plumePeakC: 85.851441232, burnLengthCm: 10, burnDurationS: 600, o2Change180Pp: 0.0142, pressureChange180KPa: 0.0383, inletTempChange180C: 0.0733, radiationPeak180KWm2: 0.0666, co2Peak180Ppm: 3710.9518, co2EndChangePpm: 699.6253 },
  'II-9': { outcome: 'anchored_flame_slow_regression', spreadRateMmS: null, plumePeakC: 32.524423526, burnLengthCm: 10, burnDurationS: 900, o2Change180Pp: -0.0956, pressureChange180KPa: 0.0048, inletTempChange180C: 0.1975, radiationPeak180KWm2: 0.0505, co2Peak180Ppm: 4397.2337, co2EndChangePpm: 749.01 },
};

/** Leave-one-test-out evaluation reported in SAFFIRE_ANALYSIS_REPORT_EN.md. */
export const saffireLoocv = { rmse: 23.451, baselineRmse: 41.416, reductionPct: 43.38 };

export type FlameState = { x: number; alive: number; burnt: number; regress: number; pulse: number };
const clamp = (v: number, a = 0, b = 1) => Math.min(b, Math.max(a, v));

/**
 * Visual flame state at time t (s from the electrical ignition marker), driven by the published
 * outcome, burn length and burn duration. Front positions are interpolated linearly between
 * ignition and the published end, so they are illustrative except where a spread rate exists.
 */
export function saffireFlameAt(id: string, t: number): FlameState {
  const m = saffireMission[id], row = evidence.rows.find(r => r.id === id)!;
  const D = row.conditions.ignition_duration_command_s.value as number;
  const pulse = t < 0 ? 0 : t <= D ? 1 : Math.max(0, 1 - (t - D) / 6);
  if (t < 0) return { x: 0, alive: 0, burnt: 0, regress: 0, pulse };
  const dur = m.burnDurationS ?? D, fade = (end: number, k = 8) => (t <= end ? clamp(t / 4) : Math.max(0, 1 - (t - end) / k));
  switch (m.outcome) {
    case 'complete_fabric_spread': { const x = Math.min(m.burnLengthCm, (m.spreadRateMmS! * t) / 10); return { x, alive: fade(dur), burnt: x, regress: 0, pulse }; }
    case 'PMMA_consumed_Nomex_not_ignited': { const x = Math.min(m.burnLengthCm, (m.burnLengthCm * t) / dur); return { x, alive: fade(dur), burnt: x, regress: 0, pulse }; }
    case 'anchored_flame_slow_regression': return { x: 1, alive: fade(dur, 20), burnt: 1, regress: clamp(t / dur), pulse };
    default: return { x: 1.2, alive: t <= D ? clamp(t / 3) : Math.max(0, 1 - (t - D) / 14), burnt: 1.2, regress: 0, pulse };
  }
}
