import type { Metadata } from 'next';
import type { Locale } from '@/shared/i18n';
import { MethodologyPage } from '@/_pages/methodology';
export async function generateMetadata({params}:{params:Promise<{locale:Locale}>}):Promise<Metadata>{const {locale}=await params;return {title:locale==='es'?'Metodología · Los Espinosaurios':'Methodology · Los Espinosaurios',description:locale==='es'?'AutoResearch: iteraciones, evaluación protegida y protocolos de las cinco investigaciones.':'AutoResearch: iteration, protected evaluation and protocols for five investigations.',alternates:{canonical:`/los-espinosaurios-flame-in-freefall/${locale}/methodology/`,languages:{en:'/los-espinosaurios-flame-in-freefall/en/methodology/',es:'/los-espinosaurios-flame-in-freefall/es/methodology/'}}};}
export default async function Page({params}:{params:Promise<{locale:Locale}>}){const {locale}=await params;return <MethodologyPage locale={locale}/>;}
