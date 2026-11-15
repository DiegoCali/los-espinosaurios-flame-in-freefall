import type { Metadata } from 'next';
import { ResearchPage } from '@/_pages/research';
import type { Locale } from '@/shared/i18n';
export async function generateMetadata({params}:{params:Promise<{locale:Locale}>}):Promise<Metadata>{const {locale}=await params;return {title:locale==='es'?'Investigaciones · Los Espinosaurios':'Research · Los Espinosaurios',description:locale==='es'?'Cinco investigaciones NASA: ACME, BASS-II, SAFFIRE-II, SAME-R y FLEX.':'Five NASA investigations: ACME, BASS-II, SAFFIRE-II, SAME-R and FLEX.',alternates:{canonical:`/los-espinosaurios-flame-in-freefall/${locale}/research/`,languages:{en:'/los-espinosaurios-flame-in-freefall/en/research/',es:'/los-espinosaurios-flame-in-freefall/es/research/'}}};}
export default async function Page({params}:{params:Promise<{locale:Locale}>}){const {locale}=await params;return <ResearchPage locale={locale}/>;}
