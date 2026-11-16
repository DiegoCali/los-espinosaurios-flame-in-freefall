import {SiteHeader} from '@/widgets/site-header';
import type {Locale} from '@/shared/i18n';
import {AcmeDashboard} from './dashboard';
import '@/_pages/home/home.css';
import './acme.css';
export function AcmePage({locale}:{locale:Locale}){return <div className="research-home acme-page"><SiteHeader locale={locale}/><AcmeDashboard locale={locale}/></div>;}
