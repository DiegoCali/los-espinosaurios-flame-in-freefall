import {SiteHeader} from '@/widgets/site-header';
import type {Locale} from '@/shared/i18n';
import {FlexDashboard} from './dashboard';
import '@/_pages/home/home.css';
import './flex.css';
export function FlexPage({locale}:{locale:Locale}){return <div className="research-home flex-page"><SiteHeader locale={locale}/><FlexDashboard locale={locale}/></div>;}
