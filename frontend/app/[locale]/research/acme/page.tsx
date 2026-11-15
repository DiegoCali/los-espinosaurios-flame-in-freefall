import type {Metadata} from 'next';
import type {Locale} from '@/shared/i18n';
import {AcmePage} from '@/_pages/acme';
export async function generateMetadata({params}:{params:Promise<{locale:Locale}>}):Promise<Metadata>{const {locale}=await params;return {title:'ACME / Flame Design · Los Espinosaurios',description:locale==='es'?'Tad calculada en llamas normales e inversas: 52 predicciones de validación, métricas agregadas de holdout y laboratorio Ridge.':'Calculated Tad in normal and inverse flames: 52 validation predictions, aggregate holdout metrics and a Ridge laboratory.',alternates:{languages:{en:'/los-espinosaurios-flame-in-freefall/en/research/acme/',es:'/los-espinosaurios-flame-in-freefall/es/research/acme/'}}};}
export default async function Page({params}:{params:Promise<{locale:Locale}>}){const {locale}=await params;return <AcmePage locale={locale}/>;}
