import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import ts from 'typescript';
const root=new URL('../',import.meta.url);
const read=file=>JSON.parse(readFileSync(new URL(file,root),'utf8'));
function module(file,require){
  const code=ts.transpileModule(readFileSync(new URL(file,root),'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,esModuleInterop:true}}).outputText;
  const exports={};new Function('exports','require',code)(exports,require);return exports;
}
const size=module('src/entities/same/size.ts');
const detection=module('src/entities/same/detection.ts');
const evidence=read('src/entities/same/evidence.json');
const data=module('src/entities/same/data.ts',name=>name.includes('size')?size:name.includes('detection')?detection:evidence);
const rows=read('public/data/same/validation.json');
assert.equal(data.validValidation(rows),true);
for(const bad of [null,[],rows.slice(1),rows.map((r,i)=>i? r : {...r,actual:{}}),rows.map((r,i)=>i? r : {...r,task:'unknown'})])assert.equal(data.validValidation(bad),false);
const fixtures=read('src/entities/same/physical-fixtures.json');
assert.equal(fixtures.length,520);
for(const f of fixtures)assert.ok(Math.abs(size.physicalSize(f.target,f.input)-f.expected)<=1e-12*Math.max(1,f.expected));
for(const target of size.sizeTargets){
  const subset=rows.filter(r=>r.task==='size');
  const rmse=Math.sqrt(subset.reduce((s,r)=>s+(r.actual[target]-r.predicted[target])**2,0)/subset.length);
  assert.ok(Math.abs(rmse-evidence.metrics[target].rmse)<1e-12);
}
for(const detector of detection.detectors){
  const subset=rows.filter(r=>r.task==='detection');
  const brier=subset.reduce((s,r)=>s+(r.actual[detector]-r.predicted[detector])**2,0)/subset.length;
  assert.ok(Math.abs(brier-evidence.metrics[detector].brier)<1e-12);
}
assert.equal(detection.modelAged(120),false);assert.equal(detection.telemetryAged(120),true);
assert.equal(detection.modelAged(120.001),true);assert.equal(detection.telemetryAged(119.999),false);
const expected=[.1599,.2094,.2982,.3128,.2637,.3455,.4920,.5161];
let i=0;
for(const material of ['Kapton','Lampwick'])for(const flow of ['flow_8cm_s','no_flow'])for(const age of [38,566])assert.equal(data.savedScenario(material,flow,age).dm_um,expected[i++]);
assert.throws(()=>data.savedScenario('Kapton','flow_8cm_s',121));
assert.equal(evidence.scenarios.length,90);
console.log('SAME-R: 520 Python/JS inverse transforms, five size RMSEs, two Brier scores, A–H scenarios, data contract and distinct 120 s boundaries pass.');
