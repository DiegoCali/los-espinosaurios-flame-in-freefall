import type { Locale } from '@/shared/i18n';
import { SiteHeader } from '@/widgets/site-header';
import { MissionControl } from './mission-control';
import '@/_pages/home/home.css';
import '@/widgets/measure/measure.css';
import '@/widgets/measure/spacecraft.css';
import './simulation.css';

export function SimulationPage({ locale }: { locale: Locale }) {
  return <div className="research-home ms-page"><SiteHeader locale={locale} /><MissionControl locale={locale} /></div>;
}
