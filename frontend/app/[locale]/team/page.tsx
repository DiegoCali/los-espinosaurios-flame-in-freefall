import type { Metadata } from 'next';
import type { Locale } from '@/shared/i18n';
import { TeamPage } from '@/_pages/team';
export async function generateMetadata({params}:{params:Promise<{locale:Locale}>}):Promise<Metadata>{const {locale}=await params;return {title:locale==='es'?'Equipo · Los Espinosaurios':'Team · Los Espinosaurios',description:locale==='es'?'Integrantes, contribuciones y créditos del proyecto Los Espinosaurios.':'Contributors, code contributions and credits for the Los Espinosaurios project.',alternates:{canonical:`/los-espinosaurios-flame-in-freefall/${locale}/team/`,languages:{en:'/los-espinosaurios-flame-in-freefall/en/team/',es:'/los-espinosaurios-flame-in-freefall/es/team/'}}};}
export default async function Page({params}:{params:Promise<{locale:Locale}>}){const {locale}=await params;return <TeamPage locale={locale}/>;}
