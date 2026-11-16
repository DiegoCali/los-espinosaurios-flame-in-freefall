import localFont from 'next/font/local';
import type { Locale } from '@/shared/i18n';
import { GlobalFx, bootScript } from '@/widgets/fx';
import './global.css';
const oxanium=localFont({src:[{path:'./fonts/oxanium-latin-700-normal.woff2',weight:'700'},{path:'./fonts/oxanium-latin-800-normal.woff2',weight:'800'}],variable:'--font-oxanium',display:'swap'});
const chakra=localFont({src:[{path:'./fonts/chakra-petch-latin-400-normal.woff2',weight:'400'},{path:'./fonts/chakra-petch-latin-500-normal.woff2',weight:'500'}],variable:'--font-chakra',display:'swap'});
const mono=localFont({src:[{path:'./fonts/ibm-plex-mono-latin-400-normal.woff2',weight:'400'},{path:'./fonts/ibm-plex-mono-latin-500-normal.woff2',weight:'500'},{path:'./fonts/ibm-plex-mono-latin-700-normal.woff2',weight:'700'}],variable:'--font-mono',display:'swap'});
export function Document({children,locale,fx=true}:{children:React.ReactNode;locale:string;fx?:boolean}){
 return <html lang={locale} className={`${oxanium.variable} ${chakra.variable} ${mono.variable}`} suppressHydrationWarning>
  <head>{fx&&<script dangerouslySetInnerHTML={{__html:bootScript}}/>}</head>
  <body>{children}{fx&&<GlobalFx locale={(locale==='es'?'es':'en') as Locale}/>}</body>
 </html>;
}
