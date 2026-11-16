import type { Metadata } from 'next';
import type { Locale } from '@/shared/i18n';
import { ExplorerPage } from '@/_pages/explorer';
import { explorerCopy } from '@/_pages/explorer/copy';
export async function generateMetadata({ params }: { params: Promise<{ locale: Locale }> }): Promise<Metadata> { const { locale } = await params; return explorerCopy[locale].meta; }
export default async function Page({ params }: { params: Promise<{ locale: Locale }> }) { const { locale } = await params; return <ExplorerPage locale={locale} />; }
