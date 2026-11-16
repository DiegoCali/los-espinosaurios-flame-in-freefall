'use client';

import { useState } from 'react';
import Link from 'next/link';
import { motion, AnimatePresence, useReducedMotion } from 'motion/react';
import { SiteHeader } from '@/widgets/site-header';
import { dictionaries, pagePaths, type Locale } from '@/shared/i18n';
import { asset } from '@/shared/config';
import { categories, matchesCategory, type Category } from '@/entities/research/catalog';
import evidence from '@/entities/research/evidence.json';
import { researchCopy } from './copy';
import '@/_pages/home/home.css';
import './research.css';

function ScientificPanel({slug,locale}:{slug:string;locale:Locale}) {
 const t=researchCopy[locale];
 if(slug==='acme') return <aside className="catalog-visual"><p>{t.configurations}</p><div className="flame-configurations">{[0,1].map((n)=><figure key={n}><div><img src={asset(`/assets/research/diagram-${n*2}.svg`)} width={73} height={73} alt=""/><img className="reactant-marker" src={asset(`/assets/research/diagram-${n*2+1}.svg`)} width={20} height={20} alt=""/></div><figcaption>{n===0?t.normal:t.inverse}</figcaption></figure>)}</div><small>{t.flameNote}</small></aside>;
 if(slug==='bass-ii') return <aside className="catalog-visual"><p>{t.video}</p><div className="measurement-steps">{t.steps.map((s,i)=><div key={s}><b>0{i+1}</b><span>{s}</span></div>)}</div><small data-source="investigations/BASS-II/predictions.json#/discovery/study_summary/dataset/n_processed_tests">{evidence.values.processedTests} {t.analyzed}</small></aside>;
 if(slug==='saffire-ii') return <aside className="catalog-visual"><p>{t.co2}</p><div className="co2-number" data-source="investigations/SAFFIRE/predictions.json#/predictions/6/actual/co2_increase_180s_ppm">+{evidence.values.co2ResponsePpm.toFixed(0)} <span>ppm</span></div><small>{t.test}</small><small className="catalog-warning">{t.hazard}</small></aside>;
 if(slug==='same-r') return <aside className="catalog-visual"><p>{t.proxy}</p>{[[t.photo,evidence.values.photoRate],[t.ion,evidence.values.ionRate]].map(([label,rate],i)=><div className={`proxy-bar proxy-${i}`} key={label}><span>{label}</span><b>{(Number(rate)*100).toFixed(0)}%</b><div><i style={{width:`${Number(rate)*100}%`}}/></div></div>)}<small>{t.thresholds}</small></aside>;
 return <aside className="catalog-visual"><p>{t.drop}</p><div className="drop-stages">{[53,39,19].map((size,i)=><figure key={i}><div><img src={asset(`/assets/research/diagram-${i+4}.svg`)} width={size} height={size} alt=""/></div><figcaption>{t.dropStages[i]}</figcaption></figure>)}</div><small>{t.dropNote}</small></aside>;
}

export function ResearchPage({locale}:{locale:Locale}) {
 const t=researchCopy[locale], shared=dictionaries[locale];
 const [category,setCategory]=useState<Category>('all');
 const reduced=useReducedMotion();
 const studies=shared.studiesList.filter(study=>matchesCategory(study.slug,category));
 return <div className="research-home catalog-page">
  <SiteHeader locale={locale}/>
  <main id="main">
   <motion.section className="catalog-hero" initial={false} whileInView={{opacity:[.85,1],y:reduced?0:[8,0]}} viewport={{once:true}} transition={{duration:reduced?.1:.22}}>
    <p className="eyebrow compact-only catalog-page-index">02 / {shared.nav[1]} · <span className="mobile-label">{shared.mobile}</span><span className="tablet-label">{shared.tablet}</span></p>
    <p className="eyebrow"><span className="desktop-only">{t.eyebrow}</span><span className="compact-only">{shared.micro} / NASA PSI</span></p>
    <span className="catalog-edition desktop-only">▪ &nbsp; {t.edition}</span>
    <h1>{t.title}</h1><p className="catalog-choice desktop-only">{t.choice}</p><p className="catalog-intro">{t.intro}</p>
    <div className="catalog-summary desktop-only"><div><b>05</b><span>{t.records}</span></div><div><b>{t.data}</b><span>{t.types}</span></div><div><b>NASA PSI</b><span>{t.source}</span></div></div>
    <div className="catalog-red compact-only"/>
   </motion.section>
   <section className="catalog-filters" aria-labelledby="filter-heading">
    <p className="eyebrow" id="filter-heading">{t.filterIndex}</p><h2 className="compact-only">{t.filterTitle}</h2><p>{t.filterIntro}</p>
    <div className="catalog-filter-buttons" role="group" aria-label={t.filterTitle}>{categories.map((value,i)=><motion.button key={value} type="button" tabIndex={0} aria-pressed={category===value} onClick={()=>setCategory(value)} whileTap={reduced?undefined:{scale:.98}}>{t.filters[i]}</motion.button>)}</div>
    <p className="catalog-filter-status desktop-only" aria-live="polite">{t.active} / {category==='all'?t.allStudies:t.filters[categories.indexOf(category)]} · {String(studies.length).padStart(2,'0')} {t.results}<span>{t.filterStatus}</span></p>
    <span className="sr-only" aria-live="polite">{studies.length} {t.results}</span>
   </section>
   <section className="catalog-records" data-filtered={category!=='all'} aria-labelledby="catalog-heading">
    <p className="eyebrow"><span className="desktop-only">{t.listIndex}</span><span className="compact-only">{t.compactListIndex}</span></p><span className="catalog-record-source desktop-only">{t.recordsSource}</span>
    <h2 id="catalog-heading">{t.listTitle}</h2><p className="catalog-record-intro">{t.listIntro}</p>
    <div className="catalog-rows"><AnimatePresence initial={false} mode="popLayout">{studies.map((study,index)=>{
     const originalIndex=shared.studiesList.findIndex(s=>s.slug===study.slug);
     return <motion.article className="catalog-record" data-study={study.slug} key={study.slug} layout={!reduced} initial={{opacity:.85}} animate={{opacity:1}} exit={{opacity:0}} whileInView={{opacity:[.85,1]}} viewport={{once:true}} transition={{duration:reduced?.1:.22,delay:Math.min(index*.035,.14)}}>
      <span className="catalog-number desktop-only">0{originalIndex+1}</span>
      <div className="catalog-record-copy"><p className="eyebrow">{study.psi}</p><h3><Link href={`/${locale}/research/${study.slug}/`}>{study.title}</Link></h3><p>{study.question}</p><p className="catalog-tags">{study.tags}</p><Link className="catalog-open" href={`/${locale}/research/${study.slug}/`}>{shared.open}<span className="desktop-only"> / 0{originalIndex+1} &gt;</span><span className="compact-only"> →</span></Link></div>
      <ScientificPanel slug={study.slug} locale={locale}/>
     </motion.article>;
    })}</AnimatePresence></div>
   </section>
   <section className="catalog-comparison" aria-labelledby="comparison-heading"><p className="eyebrow"><span className="desktop-only">{t.compareIndex}</span><span className="compact-only">{t.compactCompareIndex}</span></p><h2 id="comparison-heading">{t.compareTitle}</h2><p>{t.compareIntro}</p>
    <div className="desktop-only"><table><thead><tr>{t.columns.map(col=><th key={col} scope="col">{col}</th>)}</tr></thead><tbody>{shared.studiesList.map((study,i)=><tr key={study.slug}><th scope="row"><Link href={`/${locale}/research/${study.slug}/`}>{study.psi.split(' / ')[1]}</Link><small>{study.psi.split(' / ')[0]}</small></th>{t.rows[i].map((value,j)=><td key={j}>{value}</td>)}</tr>)}</tbody></table><p className="catalog-units">{t.units}</p></div><p className="catalog-compare-note compact-only">{t.compareNote}</p>
   </section>
   <section className="catalog-provenance desktop-only"><p className="eyebrow">{t.provenanceIndex}</p><h2>{t.provenanceTitle}</h2><p>{t.provenanceIntro}</p><div>{t.provenance.map(([label,description])=><article key={label}><h3>{label}</h3><p>{description}</p></article>)}</div><p className="catalog-psi-list">PSI-10 / PSI-25 / PSI-99 / PSI-101 / PSI-69</p></section>
  </main>
  <footer className="home-footer catalog-footer"><div className="footer-top desktop-only"><Link className="brand" href={`/${locale}/`}>S//L / LOS ESPINOSAURIOS</Link><nav aria-label={shared.pages}>{shared.nav.map((label,i)=><Link key={label} href={`/${locale}/${pagePaths[i]}`}>{label}</Link>)}</nav></div><p className="desktop-only footer-description">{t.footer}</p><p className="desktop-only footer-edition">{t.footerEdition}</p><p className="footer-source compact-only">S//L · NASA PSI · {shared.archive}</p><p className="compact-only compact-footer-description">{shared.compactFooter}</p></footer>
 </div>;
}
