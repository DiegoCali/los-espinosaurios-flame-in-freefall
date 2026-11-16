import type {Metadata} from 'next';
import type {Locale} from '@/shared/i18n';
import {SamePage} from '@/_pages/same';
export async function generateMetadata({params}:{params:Promise<{locale:Locale}>}):Promise<Metadata> {
  const {locale}=await params;
  return {title:'SAME-R / Smoke Aerosols · Los Espinosaurios',description:locale==='es'?'Tamaños de partículas y respuestas proxy de detectores en SAME-R / PSI-101. Mediciones NASA/NIST y 90 escenarios guardados.':'Particle sizes and detector proxy responses in SAME-R / PSI-101. NASA/NIST measurements and 90 saved scenarios.'};
}
export default async function Page({params}:{params:Promise<{locale:Locale}>}) {
  const {locale}=await params;
  return <SamePage locale={locale}/>;
}
