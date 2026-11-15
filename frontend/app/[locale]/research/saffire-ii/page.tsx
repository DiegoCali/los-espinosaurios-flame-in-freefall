import type { Metadata } from 'next';
import type { Locale } from '@/shared/i18n';
import { SaffirePage } from '@/_pages/saffire';
export async function generateMetadata({params}:{params:Promise<{locale:Locale}>}):Promise<Metadata>{const {locale}=await params;return {title:'SAFFIRE-II · Los Espinosaurios',description:locale==='es'?'Nueve ensayos de SAFFIRE-II: respuesta local de CO₂, validación cruzada y modelo exploratorio.':'Nine SAFFIRE-II tests: local CO₂ response, cross-validation and an exploratory model.',alternates:{languages:{en:'/los-espinosaurios-flame-in-freefall/en/research/saffire-ii/',es:'/los-espinosaurios-flame-in-freefall/es/research/saffire-ii/'}}};}
export default async function Page({params}:{params:Promise<{locale:Locale}>}){const {locale}=await params;return <SaffirePage locale={locale}/>;}
