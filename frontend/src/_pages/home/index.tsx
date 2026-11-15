import Link from 'next/link';
import { asset } from '@/shared/config';
import { dictionaries, pagePaths, type Locale } from '@/shared/i18n';
import { SiteHeader } from '@/widgets/site-header';
import { Reveal } from './reveal';
import './home.css';

function Action({ href, children, secondary = false }: { href: string; children: React.ReactNode; secondary?: boolean }) {
  return <Link className={`action-button ${secondary ? 'secondary' : ''}`} href={href}><span aria-hidden="true" className="action-signal" /><span aria-hidden="true" className="action-number">{secondary ? '02' : '01'}</span><span>{children}</span><span aria-hidden="true" className="action-arrow">&gt;</span></Link>;
}

export function HomePage({ locale }: { locale: Locale }) {
  const t = dictionaries[locale];
  return <div className="research-home">
    <SiteHeader locale={locale} />
    <main id="main">
      <Reveal className="home-hero" aria-labelledby="hero-title">
        <p className="compact-page-index eyebrow compact-only">01 / {t.nav[0]} · <span className="mobile-label">{t.mobile}</span><span className="tablet-label">{t.tablet}</span></p>
        <div className="hero-copy">
          <p className="eyebrow hero-eyebrow"><span className="desktop-only">{t.desktopEyebrow}</span><span className="compact-only">{t.micro} / NASA PSI</span></p>
          <h1 id="hero-title"><span className="desktop-only">{t.heroLines.map(line => <span className="hero-line" key={line}>{line}</span>)}</span><span className="compact-only">{t.hero}</span></h1>
          <div className="hero-marker desktop-only" />
          <p className="hero-intro">{t.intro}</p>
          <div className="hero-actions desktop-only"><Action href={`/${locale}/research/`}>{t.view}</Action><Action href={`/${locale}/methodology/`} secondary>{t.read}</Action></div>
        </div>
        <figure className="hero-emblem desktop-only" aria-label={t.emblem}>
          <span className="emblem-code eyebrow">SL // EMBLEM-001</span>
          <img className="outer-ring" src={asset('/assets/outer-ring.svg')} width="485" height="485" alt="" />
          <img className="inner-ring" src={asset('/assets/inner-ring.svg')} width="412" height="412" alt="" />
          <img className="dinosaur" src={asset('/assets/emblem.svg')} width="408" height="408" alt="Los Espinosaurios" />
          <i className="reticle north" /><i className="reticle south" /><i className="reticle west" /><i className="reticle east" /><i className="red-calibration" />
          <figcaption>{t.emblem}</figcaption>
        </figure>
        <div className="hero-metadata desktop-only"><span>{t.five}</span><span>NASA PSI / {t.micro}</span><span>{t.archive} / 2026</span></div>
        <div className="compact-red-marker compact-only" />
      </Reveal>
      <Reveal className="archive-section">
        <p className="eyebrow"><span className="desktop-only">{t.archiveIndex}</span><span className="compact-only">{t.files}</span></p>
        <span className="archive-count desktop-only">{t.studies}</span>
        <h2>{t.archiveTitle}</h2>
        <p className="section-intro"><span className="desktop-only">{t.archiveIntro}</span><span className="compact-only">{t.compactArchiveIntro}</span></p>
        <div className="archive-access desktop-only"><Action href={`/${locale}/research/`}>{t.view}</Action><p>ACME / BASS-II / SAFFIRE-II / SAME-R / FLEX</p></div>
        <div className="study-grid compact-only">{t.studiesList.map(study => <Link className="study-card" key={study.slug} href={`/${locale}/research/${study.slug}/`}><p className="eyebrow">{study.psi}</p><h3>{study.title}</h3><p>{study.question}</p><p className="study-tags">{study.tags}</p><span className="study-open">{t.open} →</span></Link>)}</div>
      </Reveal>
      <Reveal className="reading-section" id="reading">
        <p className="eyebrow"><span className="desktop-only">{t.guideIndex}</span><span className="compact-only">{t.interpretation}</span></p>
        <div className="reading-layout">
          <div className="reading-copy"><h2><span className="desktop-only">{t.guideLines.map(line => <span key={line}>{line}</span>)}</span><span className="compact-only">{t.guideTitle}</span></h2><p className="section-intro">{t.guideIntro}</p><div className="reading-marker desktop-only" /><p className="eyebrow reading-units desktop-only">{t.units}</p></div>
          <div className="evidence-list">{t.evidence.map((item, i) => <article className="evidence-item" key={item.title}><span className="evidence-number desktop-only">0{i + 1}</span><div><h3>{item.title}</h3><p><span className="desktop-only">{item.body}</span><span className="compact-only">{item.compact}</span></p><span className={`evidence-badge desktop-only badge-${i}`}><b>{['SRC', 'CAL', '?'][i]}</b>{item.badge}</span></div></article>)}</div>
        </div>
      </Reveal>
      <Reveal className="impact-section desktop-only">
        <p className="eyebrow">{t.impactIndex}</p><h2>{t.impactTitle}</h2><p className="section-intro">{t.impactIntro}</p>
        <div className="impact-grid">{t.impacts.map(item => <article key={item.label}><p className="eyebrow">{item.label}</p><h3>{item.title}</h3><p>{item.body}</p></article>)}</div><p className="impact-status">{t.impactStatus}</p>
      </Reveal>
      <Reveal className="method-section desktop-only"><p className="eyebrow">{t.methodIndex}</p><h2>{t.methodTitle}</h2><p>{t.methodIntro}</p><p className="method-steps eyebrow">{t.methodSteps}</p><Action href={`/${locale}/methodology/`} secondary>{t.methodAction}</Action></Reveal>
    </main>
    <footer className="home-footer">
      <div className="footer-top desktop-only"><Link className="brand" href={`/${locale}/`}>S//L / LOS ESPINOSAURIOS</Link><nav aria-label={t.pages}>{t.nav.slice(1).map((label, i) => <Link key={label} href={`/${locale}/${pagePaths[i + 1]}`}>{label}</Link>)}</nav></div>
      <p className="desktop-only footer-description">{t.footerIntro}</p>
      <p className="footer-source"><span className="desktop-only">{t.footerData} · ACME / BASS-II / SAFFIRE-II / SAME-R / FLEX</span><span className="compact-only">S//L · NASA PSI · {t.archive}</span></p>
      <p className="desktop-only footer-edition">{t.edition}</p><p className="compact-only compact-footer-description">{t.compactFooter}</p>
    </footer>
  </div>;
}
