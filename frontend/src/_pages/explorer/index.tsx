import type { Locale } from '@/shared/i18n';
import { SiteHeader } from '@/widgets/site-header';
import { ExplorerApp } from './explorer';
import '@/_pages/home/home.css';
import '@/widgets/measure/measure.css';
import '@/widgets/measure/spacecraft.css';
import './explorer.css';

export function ExplorerPage({ locale }: { locale: Locale }) {
  return <div className="research-home xp-page"><SiteHeader locale={locale} /><ExplorerApp locale={locale} /></div>;
}
