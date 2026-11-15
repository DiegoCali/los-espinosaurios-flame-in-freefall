import evidence from './evidence.json';

export type FlexTarget = 'burn_time_s' | 'burning_rate_m2_s';
export type FlexFuel = 'Methanol' | 'Heptane';
export type FlexValues = Record<FlexTarget, number | null>;
export type FlexRecord = {row_index:number; id:string; test:number; fuel:FlexFuel; oxygen:number|null; pressure_mmhg:number|null; diameter_mm:number|null; outcome:string; source_date:string; parsed_date:null; actual:FlexValues; predicted:FlexValues; residual:FlexValues};
export type FlexHistory = {id:string; file:string; reference_time_s:number; reference_diameter_mm:number; points:[number,number][]};
export const flexEvidence = evidence;
export const flexRecords = evidence.records as FlexRecord[];
export const caseIds = ['192F001','178F001','177F001','196F002','182F001','181F001'];
export const flexCases = caseIds.map(id=>flexRecords.find(row=>row.id===id)!);
export const flexUnit = (target:FlexTarget) => target==='burn_time_s'?'s':'m²/s';
export function flexNumber(value:number|null, target:FlexTarget, signed=false) {
  if(value===null)return '—';
  const shown=target==='burn_time_s'?value:value/1e-7;
  return `${signed&&shown>0?'+':''}${shown.toFixed(2)}`;
}
export function isFlexHistory(value:unknown):value is FlexHistory[] {
  if(!Array.isArray(value)||value.length!==3)return false;
  return value.every(h=>h&&['20CAL13','20CAL08','256F002'].includes(h.id)&&typeof h.file==='string'&&Number.isFinite(h.reference_time_s)&&h.reference_diameter_mm>0&&Array.isArray(h.points)&&h.points.length>0&&h.points.every((p:unknown)=>Array.isArray(p)&&p.length===2&&p.every(v=>typeof v==='number'&&Number.isFinite(v))));
}
