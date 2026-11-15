import Link from 'next/link';
import { notFound } from 'next/navigation';
import { SiteHeader } from '@/widgets/site-header';
import '@/_pages/home/home.css';
const sections=['research/acme','research/bass-ii','research/same-r','research/flex'];
export const dynamicParams=false;
export function generateStaticParams(){return sections.map(section=>({section:section.split('/')}));}
export default async function Page({params}:{params:Promise<{locale:'en'|'es';section:string[]}>}){const {locale,section}=await params;const route=section.join('/');if(!sections.includes(route))notFound();const titles:Record<string,string[]>={research:['RESEARCH ARCHIVE','ARCHIVO DE INVESTIGACIONES'],methodology:['METHODOLOGY','METODOLOGÍA'],team:['THE TEAM','EL EQUIPO']};const title=titles[route]?.[locale==='es'?1:0]??section.at(-1)!.toUpperCase();return <div className="research-home"><SiteHeader locale={locale}/><main id="main" style={{padding:'80px 0',minHeight:'70vh'}}><p className="eyebrow">S//L / NASA PSI</p><h1 style={{fontSize:'clamp(28px,5vw,60px)',margin:'24px 0'}}>{title}</h1><p>{locale==='es'?'Esta página se implementará en la próxima entrega.':'This page is scheduled for the next delivery.'}</p><Link href={`/${locale}/`} style={{display:'inline-block',marginTop:32,color:'#77c3ed'}}>← {locale==='es'?'VOLVER AL INICIO':'BACK TO HOME'}</Link></main></div>;}
