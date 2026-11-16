import {Document} from '@/_app/document';
export default function Layout({children}:{children:React.ReactNode}){return <Document locale="en" fx={false}>{children}</Document>;}
