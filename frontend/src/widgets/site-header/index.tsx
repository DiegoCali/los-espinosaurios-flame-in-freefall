'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import * as Dialog from '@radix-ui/react-dialog';
import { AnimatePresence, motion, useReducedMotion } from 'motion/react';
import { asset } from '@/shared/config';
import { dictionaries, pagePaths, type Locale } from '@/shared/i18n';

export function SiteHeader({ locale }: { locale: Locale }) {
  const [open, setOpen] = useState(false);
  const pathname = usePathname();
  const reduced = useReducedMotion();
  const isResearch = pathname.replace(/\/$/, '') === `/${locale}/research`;
  const isActive = (index: number) => (index === 1 && pathname.startsWith(`/${locale}/research/`)) || pathname.replace(/\/$/, '') === `/${locale}/${pagePaths[index]}`.replace(/\/$/, '');
  const t = dictionaries[locale];
  const languageLinks = <div className="language-links" aria-label={t.language}>{(['en', 'es'] as const).map(lang => <a key={lang} href={asset(pathname.replace(/^\/(en|es)(?=\/|$)/, `/${lang}`))} hrefLang={lang} lang={lang} aria-current={locale === lang ? 'true' : undefined} onClick={event => { event.currentTarget.href += window.location.search + window.location.hash; }}>{lang.toUpperCase()}</a>)}</div>;
  return <>
    <a href="#main" className="skip-link">{t.skip}</a>
    <header className="site-header">
      <Link href={`/${locale}/`} className="brand">S//L&nbsp; LOS ESPINOSAURIOS</Link>
      <div className="desktop-language">{languageLinks}</div>
      <nav className="desktop-nav" aria-label={t.pages}>{t.nav.map((label, i) => <Link key={label} href={`/${locale}/${pagePaths[i]}`} aria-current={isActive(i) ? 'page' : undefined}>{label}</Link>)}</nav>
      <Dialog.Root open={open} onOpenChange={setOpen}>
        <Dialog.Trigger className="menu-trigger">{t.menu}&nbsp; ☰</Dialog.Trigger>
        <AnimatePresence>{open && <Dialog.Portal forceMount>
          <Dialog.Overlay forceMount asChild><motion.div className="menu-overlay" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: .17 }} /></Dialog.Overlay>
          <Dialog.Content forceMount asChild aria-describedby="menu-description">
            <motion.div className="menu-content" initial={{ opacity: 0, y: reduced ? 0 : -12 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: reduced ? 0 : -12 }} transition={{ duration: reduced ? .1 : .22, ease: [.22, 1, .36, 1] }}>
              <p className="eyebrow">S//L / {t.navigation}</p>
              <div className="menu-heading"><Dialog.Title>{t.explore}</Dialog.Title><Dialog.Close>{t.close} ×</Dialog.Close></div>
              <Dialog.Description id="menu-description" className="sr-only">{t.pages} / NASA PSI</Dialog.Description>
              <p className="eyebrow">{t.pages}</p>
              <nav aria-label={t.pages}>{t.nav.map((label, i) => <Dialog.Close asChild key={label}><Link href={`/${locale}/${pagePaths[i]}`}>{label}<span>{t.pageLabel} 0{i + 1}</span></Link></Dialog.Close>)}</nav>
              <p className="eyebrow">{t.menuResearch}</p>
              <nav aria-label="NASA PSI">{['saffire-ii', 'acme', 'bass-ii', 'same-r', 'flex'].map(slug => t.studiesList.find(study => study.slug === slug)!).map(study => <Dialog.Close asChild key={study.slug}><Link href={`/${locale}/research/${study.slug}/`}>{study.psi.split(' / ')[1]}<span>{study.psi.split(' / ')[0]}</span></Link></Dialog.Close>)}</nav>
              <div className="menu-language">{languageLinks}</div>
            </motion.div>
          </Dialog.Content>
        </Dialog.Portal>}</AnimatePresence>
      </Dialog.Root>
    </header>
    <nav className="quick-nav" aria-label={t.pages}>
      <Link className="mobile-quick" href={isResearch ? `/${locale}/` : `/${locale}/research/`}>{isResearch ? (locale === 'es' ? 'VOLVER A INICIO' : 'BACK TO HOME') : t.view} →</Link>
      {t.nav.map((label, i) => <Link className="tablet-quick" key={label} href={`/${locale}/${pagePaths[i]}`} aria-current={isActive(i) ? 'page' : undefined}>{label}</Link>)}
    </nav>
  </>;
}
