import { notFound } from 'next/navigation';
import { Document } from '@/_app/document';
export const metadata={metadataBase:new URL('https://diegocali.github.io/los-espinosaurios-flame-in-freefall/'),title:'Los Espinosaurios · Research Hub'};
export const dynamicParams = false;
export function generateStaticParams() { return [{locale:'en'},{locale:'es'}]; }
export default async function LocaleLayout({children,params}:{children:React.ReactNode;params:Promise<{locale:string}>}) { const {locale}=await params; if(locale!=='en'&&locale!=='es')notFound(); return <Document locale={locale}>{children}</Document>; }
