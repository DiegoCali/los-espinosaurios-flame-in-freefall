'use client';
import {useMemo} from 'react';
import {ScientificChart} from '@/shared/ui/scientific-chart';
import {validationRows,type AcmeExperiment} from '@/entities/acme/data';
import {acmeScenario,acmePresets,type FlameType} from '@/features/acme-exploration/scenario';
import type {AcmeCopy} from './copy';
const colors={Normal:'#77c3ed',Inverse:'#87b9a4'};
const axis={axisLine:{lineStyle:{color:'#2c3a47'}},axisTick:{show:false},axisLabel:{color:'#8c9eae',fontSize:11,fontFamily:'monospace',formatter:(v:number)=>String(v)},nameTextStyle:{color:'#8c9eae',fontSize:11},splitLine:{lineStyle:{color:'#1b2632'}}};
export function AcmeChart({kind,t,experimental=[],flame='Normal',fraction=.21,selected,onSelect}:{kind:'composition'|'parity'|'response'|'residuals';t:AcmeCopy;experimental?:AcmeExperiment[];flame?:FlameType;fraction?:number;selected?:string;onSelect?:(id:string)=>void}){
 const option=useMemo(()=>{
  const tooltip={trigger:'item' as const,renderMode:'richText' as const,confine:true,backgroundColor:'#0f1720',borderColor:'#2c3a47',textStyle:{color:'#f2f3ed'}};
  const base={textStyle:{fontFamily:'monospace',color:'#8c9eae'},grid:{left:58,right:24,top:56,bottom:80},tooltip,legend:{bottom:0,textStyle:{color:'#8c9eae',fontSize:11}},xAxis:{...axis,type:'value',nameLocation:'middle',nameGap:43},yAxis:{...axis,type:'value',nameLocation:'end',nameGap:20}};
  if(kind==='response'){
   const [min,,max]=acmePresets[flame];
   const curve=Array.from({length:61},(_,i)=>{const x=min+(max-min)*i/60;return [x,acmeScenario(flame,x).value];});
   const value=acmeScenario(flame,fraction).value;
   return {...base,legend:{show:false},grid:{left:55,right:25,top:60,bottom:80},xAxis:{...base.xAxis,min:flame==='Normal'?.1:.08,max:.4,name:t.ambientAxis,axisLabel:{...axis.axisLabel,formatter:(v:number)=>`${Math.round(v*100)}%`}},yAxis:{...base.yAxis,name:'Tad / K',min:Math.min(1800,Math.floor(Math.min(...curve.map(p=>p[1]))/200)*200),max:Math.max(2700,Math.ceil(Math.max(...curve.map(p=>p[1]))/200)*200),interval:200,axisLabel:{...axis.axisLabel,showMaxLabel:false}},series:[{type:'line',name:t.response,showSymbol:false,data:curve,lineStyle:{color:'#77c3ed',width:3},itemStyle:{color:'#77c3ed'}},{type:'scatter',name:t.scenario,symbolSize:20,itemStyle:{color:'#77c3ed'},data:[[fraction,value]]}]};
  }
  if(kind==='composition')return {...base,legend:{show:false},xAxis:{...base.xAxis,name:t.ambientAxis,min:0,max:.72,interval:.1,axisLabel:{...axis.axisLabel,formatter:(v:number)=>`${Math.round(v*100)}%`,showMaxLabel:false}},yAxis:{...base.yAxis,name:'Tad / K',min:1600,max:3100,interval:100,axisLabel:{...axis.axisLabel,formatter:(v:number)=>[1700,2000,2300,2600,2900].includes(v)?String(v):''},splitLine:{lineStyle:{color:Array.from({length:16},(_,i)=>i%3===1?'#1b2632':'transparent')}}},series:(['Normal','Inverse'] as const).map(type=>({name:type==='Normal'?t.normalLegend:t.inverseLegend,type:'scatter',symbolSize:6,itemStyle:{color:colors[type],opacity:.8},data:experimental.filter(r=>r.flame_type===type).map(r=>({id:r.test_id,name:`${r.test_id} · ${r.group_id}`,value:[r.ambient_reactant_fraction_initial,r.tad_calculated_k]}))}))};
  const series=(['Normal','Inverse'] as const).map(type=>({type:'scatter',name:type==='Normal'?t.normal:t.inverse,itemStyle:{color:colors[type]},symbolSize:8,data:validationRows.filter(r=>r.flame_type===type).map(r=>({id:r.test_id,name:`${r.test_id} · ${r.group_id}`,value:[r.actual.tad_calculated_k,kind==='parity'?r.predicted.tad_calculated_k:r.residual.tad_calculated_k],symbolSize:r.test_id===selected?12:8,itemStyle:{borderColor:r.test_id===selected?'#f2f3ed':colors[type],borderWidth:r.test_id===selected?2:0}}))}));
  if(kind==='residuals')return {...base,xAxis:{...base.xAxis,name:t.calculatedAxis,min:1600,max:3100,interval:300},yAxis:{...base.yAxis,name:t.residualAxis},series:[...series,{type:'line',name:'0 K',showSymbol:false,silent:true,data:[[1600,0],[3100,0]],lineStyle:{color:'#5c6873',type:'dashed'}}]};
  return {...base,grid:{left:80,right:65,top:60,bottom:85},legend:{show:false},xAxis:{...base.xAxis,name:t.calculatedAxis,min:1600,max:3100,interval:300},yAxis:{...base.yAxis,name:t.predictedAxis,min:1600,max:3100,interval:300},series:[{type:'line',name:t.referenceLine,showSymbol:false,silent:true,data:[[1600,1600],[3100,3100]],lineStyle:{type:'dotted',color:'#5c6873',width:3}},...series]};
 },[kind,t,experimental,flame,fraction,selected]);
 return <ScientificChart option={option} label={kind==='composition'?t.composition:kind==='parity'?t.parity:kind==='residuals'?t.residuals:t.response} loading={t.loading} onSelect={onSelect}/>;
}
