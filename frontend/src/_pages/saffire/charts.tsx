'use client';
import { useMemo } from 'react';
import { ScientificChart } from '@/shared/ui/scientific-chart';
import evidence from '@/entities/saffire/evidence.json';
import { evaluateSaffire, type MaterialGroup } from '@/entities/saffire/model';
import type { SaffireCopy } from './copy';
export type SensorSeries = {test_id:string;points:[number,number][];baseline_ppm:number;source_file:string};
export const materialColor=(material:string)=>material==='Silicone'?'#5c6873':material==='SIBAL'?'#228bdf':material==='PMMA_Nomex'?'#77c3ed':'#87b9a4';
const tickLabel=(value:number)=>[-20,0,40,80,120].includes(value)?String(value):'';
const gridColors=['#1b2632','#2c3a47','transparent','#1b2632','transparent','#1b2632','transparent','#1b2632'];
const axis={axisLine:{lineStyle:{color:'#2c3a47'}},axisLabel:{color:'#8c9eae',fontFamily:'monospace',fontSize:11},nameTextStyle:{color:'#8c9eae',fontSize:11},splitLine:{lineStyle:{color:'#1b2632'}}};
export function SaffireChart({kind,t,selected='II-7',onSelect,group='other',flow=20,sensor}:{kind:'bars'|'scatter'|'flow'|'sensor';t:SaffireCopy;selected?:string;onSelect?:(id:string)=>void;group?:MaterialGroup;flow?:number;sensor?:SensorSeries}){
 const option=useMemo(()=>{
  const base={backgroundColor:'transparent',textStyle:{color:'#8c9eae',fontFamily:'monospace'},aria:{enabled:true},grid:{left:65,right:30,top:35,bottom:85},tooltip:{trigger:'item' as const,backgroundColor:'#0f1720',borderColor:'#2c3a47',textStyle:{color:'#f2f3ed'},confine:true,renderMode:'richText' as const},xAxis:{...axis,nameLocation:'middle',nameGap:40},yAxis:{...axis,nameGap:20},legend:{bottom:0,textStyle:{color:'#8c9eae',fontSize:11}}};
  const rows=evidence.rows;
  if(kind==='bars')return {...base,xAxis:{...base.xAxis,type:'category',data:rows.map(r=>r.id),name:t.mission},grid:{...base.grid,top:52},yAxis:{...base.yAxis,type:'value',min:-20,max:120,interval:20,axisLabel:{...axis.axisLabel,formatter:tickLabel},splitLine:{lineStyle:{color:gridColors}},name:'ppm'},series:[{type:'bar',barMaxWidth:48,data:rows.map(r=>({id:r.id,value:r.actual,itemStyle:{color:materialColor(r.material),borderColor:r.id===selected?'#f2f3ed':undefined,borderWidth:r.id===selected?1:0}})),label:{show:true,position:'outside',fontSize:11,color:'#77c3ed',formatter:(p:{value:unknown})=>`${Number(p.value)>0?'+':''}${Number(p.value).toFixed(1)}`}}]};
  if(kind==='scatter')return {...base,grid:{left:96,right:130,top:38,bottom:94},xAxis:{...base.xAxis,type:'value',min:-20,max:120,interval:20,axisLabel:{...axis.axisLabel,formatter:tickLabel},splitLine:{lineStyle:{color:gridColors}},name:t.observed},yAxis:{...base.yAxis,type:'value',min:-20,max:120,interval:20,axisLabel:{...axis.axisLabel,formatter:tickLabel},splitLine:{lineStyle:{color:gridColors}},name:t.predicted},series:[{type:'line',data:[[-20,-20],[120,120]],symbol:'none',silent:true,lineStyle:{type:'dotted',color:'#5c6873'}},...['Silicone','SIBAL','PMMA_Nomex','PMMA'].map((m,i)=>({name:t.materialLabels[i],type:'scatter',symbolSize:m==='PMMA_Nomex'?16:12,itemStyle:{color:materialColor(m)},data:rows.filter(r=>r.material===m).map(r=>({id:r.id,name:r.id,value:[r.actual,r.predicted],itemStyle:{color:materialColor(m),borderColor:r.id===selected?'#f2f3ed':materialColor(m),borderWidth:2}}))}))]};
  if(kind==='flow'){
   const [min,max]=evidence.model.flowRange;
   const flows=Array.from({length:61},(_,i)=>min+(max-min)*i/60);
   return {...base,legend:{...base.legend,data:[t.other,t.silicone]},grid:{left:45,right:20,top:30,bottom:70},xAxis:{...base.xAxis,type:'value',min,max,name:t.airSpeed,axisLabel:{...axis.axisLabel,formatter:(v:number)=>v.toFixed(0)}},yAxis:{...base.yAxis,type:'value',min:-10,max:65,interval:10,axisLabel:{...axis.axisLabel,formatter:(v:number)=>[-10,0,20,40,60].includes(v)?String(v):''},name:'Δ CO₂ / ppm'},series:[...(['other','silicone'] as const).map(g=>({name:g==='other'?t.other:t.silicone,type:'line',showSymbol:false,data:flows.map(f=>[f,evaluateSaffire(evidence.model,g,f)]),lineStyle:{width:3,type:g==='other'?'solid':'dashed',color:g==='other'?'#228bdf':'#87b9a4'},itemStyle:{color:g==='other'?'#228bdf':'#87b9a4'}})),{type:'scatter',name:t.scenario,symbolSize:14,itemStyle:{color:'#77c3ed'},data:[[flow,evaluateSaffire(evidence.model,group,flow)]],markLine:{symbol:'none',label:{show:false},lineStyle:{color:'#77c3ed',type:'dashed'},data:[{xAxis:flow}]}}]};
  }
  return {...base,grid:{left:65,right:20,top:35,bottom:65},tooltip:{...base.tooltip,trigger:'axis'},xAxis:{...base.xAxis,type:'value',name:t.time,min:-60,max:240},yAxis:{...base.yAxis,type:'value',scale:true,name:t.absolute},series:[{name:sensor?.test_id,type:'line',showSymbol:false,connectNulls:false,data:sensor?.points??[],lineStyle:{color:'#77c3ed',width:1.5},markArea:{silent:true,label:{color:'#8c9eae',fontSize:10},data:[[{name:t.reference,xAxis:-30,itemStyle:{color:'#5c687333'}},{xAxis:0}],[{name:t.response,xAxis:150,itemStyle:{color:'#228bdf33'}},{xAxis:180}]]}}]};
 },[kind,t,selected,group,flow,sensor]);
 return <ScientificChart option={option} loading={t.loading} onSelect={onSelect} label={kind==='bars'?t.local:kind==='scatter'?t.comparison:kind==='flow'?t.flowChart:t.sensorTitle}/>;
}
