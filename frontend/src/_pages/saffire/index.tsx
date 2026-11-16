import { SiteHeader } from '@/widgets/site-header';
import type { Locale } from '@/shared/i18n';
import { SaffireDashboard } from './dashboard';
import '@/_pages/home/home.css';
import './saffire.css';
export function SaffirePage({locale}:{locale:Locale}){return <div className="research-home saffire-page"><SiteHeader locale={locale}/><SaffireDashboard locale={locale}/></div>;}
