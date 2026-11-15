import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import ts from 'typescript';
const root=new URL('../',import.meta.url);
const read=path=>JSON.parse(readFileSync(new URL(path,root),'utf8'));
const evidence=read('src/entities/bass/evidence.json');
const original=read('../investigations/BASS-II/predictions.json');
assert.equal(evidence.rates.length,83);
assert.equal(evidence.rates.filter(r=>r.status==='steady_spread').length,54);
assert.equal(evidence.rates.filter(r=>r.status==='no_steady_spread').length,29);
assert.equal(evidence.comparisons.length,25);
const holdout=evidence.comparisons.filter(r=>r.set==='holdout');
assert.equal(holdout.length,14);
assert.equal(new Set(holdout.map(r=>r.test_id.split('.')[0])).size,12);
assert.equal(evidence.validation.holdout_accounting.n_processed,13);
assert.deepEqual(evidence.forecast,original.metrics.forecast_qc_trusted.filter(r=>r.target==='leading_edge'));
assert.equal(new Set(evidence.forecast.map(r=>r.model)).size,7);
assert.equal(original.predictions.length,0);
for(const s of evidence.sources){
 const raw=readFileSync(new URL('../investigations/BASS-II/'+s.file,root));
 assert.equal(createHash('sha256').update(raw).digest('hex'),s.sha256);
 assert.deepEqual(readFileSync(new URL('public/data/bass/sources/'+s.file,root)),raw);
}
const compiled=ts.transpileModule(readFileSync(new URL('src/entities/bass/data.ts',root),'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,esModuleInterop:true}}).outputText;
const exports={};new Function('exports','require',compiled)(exports,()=>evidence);
for(const id of evidence.seriesIds){
 const rows=read('public/data/bass/series/'+id+'.json');
 assert.equal(exports.readBassSeries(rows),rows);
 const csv=readFileSync(new URL('../investigations/BASS-II/reports/figures/'+id+'/G3_edge_fit.csv',root),'utf8').trim().split('\n');
 const keys=csv.shift().trim().split(',');
 assert.deepEqual(rows,csv.map(line=>Object.fromEntries(line.trim().split(',').map((v,i)=>[keys[i],v===''||!Number.isFinite(Number(v))?null:Number(v)]))));
}
for(const value of [null,[],[{}],[{time_s:0,leading_edge_mm:Infinity,fit:0}],[{time_s:0,leading_edge_mm:0,fit:0},{time_s:0,leading_edge_mm:0,fit:0}]])assert.throws(()=>exports.readBassSeries(value));
assert.deepEqual(exports.readBassSeries([{time_s:1,leading_edge_mm:null,fit:null}]),[{time_s:1,leading_edge_mm:null,fit:null}]);
for(const model of exports.forecastModels)for(const horizon of [1,5,10])assert.equal(exports.forecastMetric(model,horizon).horizon_s,horizon);
assert.throws(()=>exports.forecastMetric('unknown',1),RangeError);
assert.throws(()=>exports.forecastMetric('persistence',2),RangeError);
console.log('BASS-II: original hashes, 83 records, 13/12/14 holdout accounting, seven model aggregates, exact measured series and load validation pass.');
