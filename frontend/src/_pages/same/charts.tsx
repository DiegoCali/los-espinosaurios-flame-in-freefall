'use client';
import {useMemo, type ReactNode} from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import {ScientificChart} from '@/shared/ui/scientific-chart';
import {sameEvidence, type Scenario, type ValidationRow} from '@/entities/same/data';
import {physicalSize, sizeLabels, type SizeTarget} from '@/entities/same/size';
import type {Detector} from '@/entities/same/detection';
import type {SameCopy} from './copy';

export type ChartKind = 'sizes' | 'detectors' | 'parity' | 'residuals' | 'aging' | 'proxy' | 'detection-validation';
const axis = {axisLine:{lineStyle:{color:'#2c3a47'}},axisTick:{show:false},axisLabel:{color:'#8c9eae',fontFamily:'monospace',fontSize:11},nameTextStyle:{color:'#8c9eae',fontSize:11},splitLine:{lineStyle:{color:'#1b2632'}}};
const materials = ['Kapton', 'Teflon', 'Lampwick', 'Pyrell', 'Silicone'];
const colors = ['#228bdf', '#77c3ed', '#87b9a4', '#b0a0cc', '#c4b994'];
export function SameChart({kind,t,rows=[],scenario,target='log10_dm_um',detector='iss_detect'}:{kind:ChartKind;t:SameCopy;rows?:ValidationRow[];scenario?:Scenario;target?:SizeTarget;detector?:Detector}) {
  const option = useMemo(() => {
    const base = {textStyle:{color:'#8c9eae',fontFamily:'monospace'},grid:{left:64,right:32,top:60,bottom:70},tooltip:{trigger:'item' as const,renderMode:'richText' as const,confine:true,backgroundColor:'#0f1720',borderColor:'#2c3a47',textStyle:{color:'#f2f3ed'}},legend:{bottom:0,textStyle:{color:'#8c9eae',fontSize:11}},xAxis:{...axis,type:'value',nameLocation:'middle',nameGap:35},yAxis:{...axis,type:'value',nameGap:23}};
    if (kind === 'sizes') return {...base,grid:{left:60,right:20,top:100,bottom:100},xAxis:{...axis,type:'category',data:materials},yAxis:{...base.yAxis,name:'D_m / μm',min:0,max:.6,interval:.2},series:['unaged','aged'].map((state,i)=>({type:'bar',name:i?t.aged:t.fresh,barMaxWidth:36,itemStyle:{color:colors[i]},label:{show:true,position:'top',color:'#77c3ed',fontSize:10},data:materials.map(m=>sameEvidence.materials.find(r=>r.material===m&&r.aged_state===state)?.dm_um??null)}))};
    if (kind === 'detectors') return {...base,grid:{left:'28%',right:'12%',top:85,bottom:80},xAxis:{...axis,type:'value',min:0,max:100,name:'%',splitLine:{show:false}},yAxis:{...axis,type:'category',inverse:true,data:[`${t.flow}\n45 ${t.pushes}`,`${t.noFlow}\n20 ${t.pushes}`],axisLabel:{...axis.axisLabel,lineHeight:22,fontSize:10,width:100,overflow:'break'}},series:['iss_rate','ion_rate'].map((key,i)=>({name:i?t.ion:t.iss,type:'bar',barWidth:22,barGap:'160%',showBackground:true,backgroundStyle:{color:'#0f1720'},itemStyle:{color:i?'#87b9a4':'#228bdf'},label:{show:true,position:'right',color:'#f2f3ed',formatter:({value}:{value:number})=>`${value.toFixed(1)}%`},data:[sameEvidence.detectors.flow_8cm_s[key as 'iss_rate'],sameEvidence.detectors.no_flow[key as 'iss_rate']].map(v=>v*100)}))};
    if (kind === 'aging') {
      const series = sameEvidence.scenarios.filter(r=>r.material===scenario?.material&&r.flow_regime===scenario?.flow_regime&&r.aging_s>=38&&r.aging_s<=Math.max(566,scenario?.aging_s??566));
      if(scenario && !series.includes(scenario))series.push(scenario);
      series.sort((a,b)=>a.aging_s-b.aging_s);
      return {...base,legend:{show:false},xAxis:{...base.xAxis,name:t.ageAxis,min:Math.min(38,scenario?.aging_s??38),max:Math.max(566,scenario?.aging_s??566)},yAxis:{...base.yAxis,name:'D_m / μm',min:0,max:Math.max(.6,Math.ceil(Math.max(...series.map(r=>r.dm_um))/.1)*.1)},series:[{type:'line',name:'D_m / μm',smooth:false,symbolSize:6,itemStyle:{color:'#77c3ed'},lineStyle:{width:2},data:series.map(r=>({name:`${r.material} · ${r.aging_s} s · ${r.extrapolated?t.extrapolated:t.supported}`,value:[r.aging_s,r.dm_um],symbolSize:r===scenario?13:6}))}]};
    }
    if(kind==='proxy')return {...base,grid:{left:5,right:65,top:10,bottom:15},legend:{show:false},xAxis:{...axis,type:'value',min:0,max:100,show:false},yAxis:{...axis,type:'category',data:[t.ion,t.iss],show:false},series:[{type:'bar',name:t.proxyResponses,barWidth:24,showBackground:true,backgroundStyle:{color:'#0f1720'},label:{show:true,position:'right',color:'#77c3ed',formatter:({value}:{value:number})=>`${value.toFixed(1)}%`},data:[{value:(scenario?.p_ion_detect??0)*100,itemStyle:{color:'#87b9a4'}},{value:(scenario?.p_iss_detect??0)*100,itemStyle:{color:'#228bdf'}}]}]};
    if(kind==='detection-validation')return {...base,xAxis:{...base.xAxis,name:t.probability,min:0,max:1},yAxis:{...base.yAxis,name:t.observed,min:0,max:1,interval:1},series:[{type:'scatter',name:detector==='iss_detect'?t.iss:t.ion,symbolSize:7,itemStyle:{color:detector==='iss_detect'?'#228bdf':'#87b9a4'},data:rows.filter(r=>r.task==='detection').map(r=>({name:`R-${r.test} / ${r.push_index} · ${r.material}`,value:[r.predicted[detector],r.actual[detector]]}))}]};
    const size = rows.filter(r=>r.task==='size');
    const rawMax = Math.max(.8,...size.flatMap(r=>[physicalSize(target,r.actual[target]),physicalSize(target,r.predicted[target])]));
    const tick = 10 ** Math.ceil(Math.log10(rawMax)) / 5;
    const max = Math.ceil(rawMax/tick)*tick;
    const series=materials.map((m,i)=>({type:'scatter',name:m,symbolSize:6,itemStyle:{color:kind==='parity'?'#77c3ed':colors[i],opacity:.9},data:size.filter(r=>r.material===m).map(r=>({name:`R-${r.run} / ${r.source_row} · ${r.material}`,value:[physicalSize(target,r.actual[target]),kind==='residuals'?r.residual[target]:physicalSize(target,r.predicted[target])]}))}));
    return {...base,legend:{...base.legend,show:kind==='residuals'},xAxis:{...base.xAxis,name:`${t.reference} · ${sizeLabels[target]}`,min:0,max},yAxis:{...base.yAxis,name:kind==='residuals'?`${t.residual} / ${target==='ln_sigma_g'?'ln':'log10'}`:`${t.predicted} · ${sizeLabels[target]}`,...(kind==='parity'?{min:0,max}:{})},series:[{type:'line',name:kind==='parity'?t.reference:'0',showSymbol:false,silent:true,lineStyle:{color:'#5c6873',type:'dotted'},data:kind==='parity'?[[0,0],[max,max]]:[[0,0],[max,0]]},...series]};
  },[kind,t,rows,scenario,target,detector]);
  return <ScientificChart option={option} label={kind==='sizes'?t.sizes:kind==='detectors'?t.responses:kind==='aging'?t.curve:kind==='proxy'?t.proxyResponses:kind==='residuals'?`${t.residual} · ${sizeLabels[target]}`:kind==='detection-validation'?`${t.probability} · ${detector==='iss_detect'?t.iss:t.ion}`:t.parity} loading={t.loading}/>;
}

export function ChartDialog({title,t,children,onOpen,compact=false}:{title:string;t:SameCopy;children:ReactNode;onOpen?:()=>void;compact?:boolean}) {
  return <div className={compact?'same-expand same-panel compact-only':'same-chart-action'}>
    {compact&&<><p className="eyebrow">{t.expanded}</p><h3>{title}</h3><p>{t.expandNote}</p></>}
    <Dialog.Root onOpenChange={open=>{if(open)onOpen?.();}}><Dialog.Trigger className="same-text-button">{t.expand}</Dialog.Trigger>
      <Dialog.Portal><Dialog.Overlay className="same-dialog-overlay"/><Dialog.Content className="same-dialog"><div className="same-dialog-heading"><Dialog.Title>{title}</Dialog.Title><Dialog.Close>{t.close} ×</Dialog.Close></div><Dialog.Description>{t.expandNote}</Dialog.Description>{children}</Dialog.Content></Dialog.Portal>
    </Dialog.Root>
  </div>;
}

export function ChartTable({headers,rows,t}:{headers:string[];rows:(string|number)[][];t:SameCopy}) {
  return <details className="same-table-details"><summary>{t.table}</summary><div className="same-table-scroll"><table><caption className="sr-only">{t.table}</caption><thead><tr>{headers.map(h=><th scope="col" key={h}>{h}</th>)}</tr></thead><tbody>{rows.map((row,i)=><tr key={i}>{row.map((v,j)=>j===0?<th scope="row" key={j}>{v}</th>:<td key={j}>{v}</td>)}</tr>)}</tbody></table></div></details>;
}
