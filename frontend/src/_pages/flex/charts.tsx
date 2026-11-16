'use client';
import type {EChartsCoreOption} from 'echarts/core';
import {ScientificChart} from '@/shared/ui/scientific-chart';
import {flexRecords, type FlexHistory, type FlexTarget} from '@/entities/flex/data';
import type {FlexCopy} from './copy';

const colors=['#77c3ed','#ff667a','#8abbaa'];
const axis={type:'value',axisLabel:{color:'#8c9eae',fontFamily:'monospace',fontSize:11},nameTextStyle:{color:'#8c9eae',fontFamily:'monospace',fontSize:10},axisLine:{show:true,lineStyle:{color:'#2c3a47'}},splitLine:{lineStyle:{color:'#1b2632'}}};
const base={backgroundColor:'transparent',color:colors,textStyle:{fontFamily:'monospace'},tooltip:{trigger:'item',renderMode:'richText',backgroundColor:'#0f1720',borderColor:'#294050',textStyle:{color:'#f2f3ed',fontSize:11}},grid:{left:58,right:30,top:45,bottom:70},legend:{bottom:0,textStyle:{color:'#8c9eae',fontSize:10}}};
export function FlexTrajectory({histories,t,mode,selected}:{histories:FlexHistory[];t:FlexCopy;mode:'normalized'|'diameter'|'squared';selected:string}) {
 const visible=histories.filter(h=>selected==='all'||h.id===selected);
 const ylabel=mode==='normalized'?'D²(t) / D²(t≈0.3 s)':mode==='diameter'?t.measured:t.squared;
 const option:EChartsCoreOption={...base,tooltip:{...base.tooltip,trigger:'axis'},xAxis:{...axis,name:t.time,nameLocation:'middle',nameGap:35,min:0},yAxis:{...axis,name:ylabel,nameLocation:'middle',nameGap:42,min:mode==='normalized'?.2:0},series:visible.map(h=>({type:'line',name:h.id,symbol:'circle',symbolSize:3,showSymbol:false,connectNulls:false,smooth:false,lineStyle:{width:1.5},data:h.points.filter(p=>mode!=='normalized'||p[0]>=h.reference_time_s).map(([time,d])=>[time,mode==='normalized'?d*d/(h.reference_diameter_mm*h.reference_diameter_mm):mode==='diameter'?d:d*d])}))};
 return <ScientificChart option={option} label={`${t.trajectory}: ${ylabel}; ${t.time}`} loading={t.loading}/>;
}
export function FlexValidation({t,target,residual=false,onSelect}:{t:FlexCopy;target:FlexTarget;residual?:boolean;onSelect?:(id:string)=>void}) {
 const rate=target==='burning_rate_m2_s',scale=rate?1e7:1,unit=rate?'×10⁻⁷ m²/s':'s',label=rate?t.rate:t.duration;
 const paired=flexRecords.filter(r=>r.actual[target]!==null&&r.predicted[target]!==null);
 const option:EChartsCoreOption={...base,legend:{show:false},xAxis:{...axis,name:`${t.observed} (${unit})`,nameLocation:'middle',nameGap:35,min:0,max:rate?12:40},yAxis:{...axis,name:`${residual?t.residual:t.predicted} (${unit})`,nameLocation:'middle',nameGap:42,...(residual?{}:{min:0,max:rate?12:40})},series:[{type:'scatter',symbolSize:6,itemStyle:{color:'#77c3ed',opacity:.85},data:paired.map(r=>({id:String(r.row_index),name:`${r.id} / #${r.test}`,value:[r.actual[target]!*scale,(residual?r.residual[target]!:r.predicted[target]!)*scale]})),tooltip:{formatter:'{b}\n{c}'}},...(residual?[{type:'line',data:[[0,0],[rate?12:40,0]],symbol:'none',lineStyle:{color:'#8c9eae',type:'dashed'}}]:[{type:'line',data:[[0,0],[rate?12:40,rate?12:40]],symbol:'none',lineStyle:{color:'#8c9eae',type:'dashed'},silent:true}])]};
 return <ScientificChart option={option} label={`${label}: ${residual?t.residualPlot:t.parity} (${unit})`} loading={t.loading} onSelect={onSelect}/>;
}
export function FlexOutcomes({t}:{t:FlexCopy}) {
 const option:EChartsCoreOption={...base,grid:{left:85,right:25,top:30,bottom:65},tooltip:{...base.tooltip,trigger:'axis',axisPointer:{type:'shadow'}},xAxis:{...axis,max:160,min:0,name:t.tests},yAxis:{type:'category',data:[t.fuelNames.Heptane,t.fuelNames.Methanol],axisLabel:{color:'#f2f3ed',fontSize:12},axisLine:{show:false},axisTick:{show:false}},series:t.outcomeNames.map((name,i)=>({name,type:'bar',stack:'outcomes',barWidth:45,itemStyle:{color:['#228bdf','#a7b2ba','#8abbaa'][i]},data:[[60,126],[38,23],[19,8]][i]}))};
 return <ScientificChart option={option} label={`${t.outcomes}: 126/23/8 ${t.fuelNames.Methanol}; 60/38/19 ${t.fuelNames.Heptane}`} loading={t.loading}/>;
}
