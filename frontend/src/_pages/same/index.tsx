import {SiteHeader} from '@/widgets/site-header';
import type {Locale} from '@/shared/i18n';
import {SameDashboard} from './dashboard';
import '@/_pages/home/home.css';
import './same.css';
export function SamePage({locale}:{locale:Locale}) {
  return <div className="research-home same-page"><SiteHeader locale={locale}/><SameDashboard locale={locale}/></div>;
}
