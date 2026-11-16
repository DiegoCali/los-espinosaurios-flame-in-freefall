'use client';
import { useEffect, useRef, useState } from 'react';
import { useReducedMotion } from 'motion/react';
import type { EChartsCoreOption, EChartsType } from 'echarts/core';

// Only visible scientific panels load the chart engine; other pages never import it.
export function ScientificChart({option,label,loading,onSelect}:{option:EChartsCoreOption;label:string;loading:string;onSelect?:(id:string)=>void}) {
 const node=useRef<HTMLDivElement>(null), chart=useRef<EChartsType|null>(null), latest=useRef(option), select=useRef(onSelect);
 const reduced=useReducedMotion();
 const [ready,setReady]=useState(false),[failed,setFailed]=useState(false),[attempt,setAttempt]=useState(0);
 useEffect(()=>{latest.current={...option,aria:{enabled:true,label:{description:label}},animation:!reduced,animationDuration:220,animationDurationUpdate:170};select.current=onSelect;chart.current?.setOption(latest.current,{notMerge:true});},[option,reduced,onSelect,label]);
 useEffect(()=>{
  const element=node.current!;let stopped=false;let resize:ResizeObserver|undefined;
  const observer=new IntersectionObserver(async entries=>{
   if(!entries.some(e=>e.isIntersecting))return;
   observer.disconnect();
   try {
    const [ec,charts,components,renderers]=await Promise.all([import('echarts/core'),import('echarts/charts'),import('echarts/components'),import('echarts/renderers')]);
    if(stopped)return;
    ec.use([charts.BarChart,charts.LineChart,charts.ScatterChart,components.GridComponent,components.TooltipComponent,components.LegendComponent,components.MarkAreaComponent,components.MarkLineComponent,components.AriaComponent,renderers.SVGRenderer]);
    chart.current=ec.init(element,null,{renderer:'svg'});chart.current.setOption(latest.current);
    chart.current.on('click',event=>{const point=event.data as {id?:string}|undefined;if(point?.id)select.current?.(point.id);});
    resize=new ResizeObserver(()=>chart.current?.resize());resize.observe(element);setReady(true);
   }catch{if(!stopped)setFailed(true);}
  },{rootMargin:'120px'});
  observer.observe(element);
  return()=>{stopped=true;observer.disconnect();resize?.disconnect();chart.current?.dispose();chart.current=null;};
 },[attempt]);
 return <div className="scientific-chart" aria-busy={!ready&&!failed}><div ref={node} className="scientific-chart-canvas" role="img" aria-label={label}/>{!ready&&!failed&&<p className="chart-status" role="status">{loading}</p>}{failed&&<button className="chart-status" onClick={()=>{setFailed(false);setAttempt(v=>v+1);}}>{loading.includes('CARGANDO')?'ERROR · REINTENTAR':'ERROR · RETRY'}</button>}</div>;
}
