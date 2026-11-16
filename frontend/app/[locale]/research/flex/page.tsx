import type {Metadata} from 'next';
import type {Locale} from '@/shared/i18n';
import {FlexPage} from '@/_pages/flex';
export async function generateMetadata({params}:{params:Promise<{locale:Locale}>}):Promise<Metadata>{const {locale}=await params;return {title:'FLEX / Flame Extinguishment · Los Espinosaurios',description:locale==='es'?'Gotas en microgravedad: trayectorias medidas, duración y tasa de combustión, y 50 predicciones Random Forest guardadas.':'Droplets in microgravity: measured trajectories, burning duration and rate, and 50 saved Random Forest predictions.'};}
export default async function Page({params}:{params:Promise<{locale:Locale}>}){const {locale}=await params;return <FlexPage locale={locale}/>;}
