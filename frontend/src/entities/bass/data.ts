import evidence from './evidence.json';

export const bassEvidence = evidence;
export type BassRecord = typeof evidence.rates[number];
export type BassComparison = typeof evidence.comparisons[number];
export type BassForecast = typeof evidence.forecast[number];
export type BassSeriesPoint = {time_s:number;leading_edge_mm:number|null;fit:number|null};
export const exampleIds = ['B1','B2','B3','B4','B5','B7','B12','M1'];
export const exampleComparisons = exampleIds.map(id=>evidence.comparisons.find(r=>r.test_id===id && r.set==='development')!);
export const forecastModels = ['kalman_conformal','persistence','physics_linear','drift','holt_damped','kalman_cv','kalman_mle'];

export function readBassSeries(value:unknown):BassSeriesPoint[] {
 if(!Array.isArray(value)||!value.length)throw Error('BASS_SERIES');
 let previous=-Infinity;
 for(const row of value){
  if(!row||typeof row!=='object'||typeof row.time_s!=='number'||!Number.isFinite(row.time_s)||row.time_s<=previous||
   !['leading_edge_mm','fit'].every(key=>row[key]===null||(typeof row[key]==='number'&&Number.isFinite(row[key]))))throw Error('BASS_SERIES');
  previous=row.time_s;
 }
 return value as BassSeriesPoint[];
}

export function forecastMetric(model:string,horizon:number):BassForecast {
 const row=evidence.forecast.find(r=>r.model===model && r.horizon_s===horizon);
 if(!row)throw RangeError('BASS_FORECAST_UNAVAILABLE');
 return row;
}
