import {SiteHeader} from '@/widgets/site-header';
import type {Locale} from '@/shared/i18n';
import {BassDashboard} from './dashboard';
import '@/_pages/home/home.css';
import './bass.css';
export function BassPage({locale}:{locale:Locale}){return <div className="research-home bass-page"><SiteHeader locale={locale}/><BassDashboard locale={locale}/></div>;}
