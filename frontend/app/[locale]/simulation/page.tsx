import type { Metadata } from 'next';
import type { Locale } from '@/shared/i18n';
import { SimulationPage } from '@/_pages/simulation';
import { simCopy } from '@/_pages/simulation/copy';
export async function generateMetadata({ params }: { params: Promise<{ locale: Locale }> }): Promise<Metadata> { const { locale } = await params; return simCopy[locale].meta; }
export default async function Page({ params }: { params: Promise<{ locale: Locale }> }) { const { locale } = await params; return <SimulationPage locale={locale} />; }
