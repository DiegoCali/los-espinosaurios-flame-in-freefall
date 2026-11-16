import type {Metadata} from 'next';
import type {Locale} from '@/shared/i18n';
import {BassPage} from '@/_pages/bass';
export async function generateMetadata({params}:{params:Promise<{locale:Locale}>}):Promise<Metadata>{
 const {locale}=await params;
 return {title:'BASS-II / Flame Spread · Los Espinosaurios',description:locale==='es'?'Propagación de llama: mediciones de video, comparaciones publicadas y métricas históricas de siete pronosticadores.':'Flame spread: video measurements, published comparisons and historical metrics for seven forecasters.'};
}
export default async function Page({params}:{params:Promise<{locale:Locale}>}){const {locale}=await params;return <BassPage locale={locale}/>;}
