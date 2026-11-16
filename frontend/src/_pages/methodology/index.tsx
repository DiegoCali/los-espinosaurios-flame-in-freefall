import Link from 'next/link';
import { SiteHeader } from '@/widgets/site-header';
import { Reveal } from '@/shared/ui/reveal';
import { dictionaries, type Locale } from '@/shared/i18n';
import { methodologyCopy } from './copy';
import evidence from './acme-evidence.json';
import { MethodSignal } from './signals';
import '@/_pages/home/home.css';
import './methodology.css';

const original='https://github.com/karpathy/autoresearch';
const repository='https://github.com/DiegoCali/los-espinosaurios-flame-in-freefall';
const files=['program.md','train.py','prepare.py'];
const studySlugs=['acme','bass-ii','saffire-ii','same-r','flex'];
export function MethodologyPage({locale}:{locale:Locale}){
 const t=methodologyCopy[locale], shared=dictionaries[locale];
 return <div className="research-home methodology-page"><SiteHeader locale={locale}/><main id="main">
  <Reveal className="methodology-hero" aria-labelledby="methodology-title">
   <p className="eyebrow compact-only methodology-index">03 / {shared.nav[2]} · <span className="mobile-label">{shared.mobile}</span><span className="tablet-label">{shared.tablet}</span></p>
   <p className="eyebrow"><span className="desktop-only">{t.eyebrow}</span><span className="compact-only">{t.compactEyebrow}</span></p>
   <h1 id="methodology-title">{t.title}</h1><h2 className="desktop-only">{t.subtitle}</h2><p className="methodology-intro">{t.intro}</p><h2 className="compact-only">{t.subtitle}</h2>
   <div className="methodology-origins desktop-only"><span>{t.origin}</span><span>{t.team}</span></div><p className="methodology-disclaimer desktop-only">{t.disclaimer}</p><div className="methodology-red compact-only"/>
  </Reveal>
  <Reveal className="methodology-flow" aria-labelledby="flow-title">
   <p className="eyebrow"><span className="desktop-only">{t.flowIndex}</span><span className="compact-only">{t.compactFlowIndex}</span></p><h2 id="flow-title">{t.flowTitle}</h2><p className="methodology-description"><span className="desktop-only">{t.flowIntro}</span><span className="compact-only">{t.disclaimer}</span></p>
   <div className="methodology-files">{files.map((file,i)=><article key={file}><MethodSignal/><p className="eyebrow desktop-only">{['H / 00','A / 01','F / 02'][i]}</p><h3 className="desktop-only">{t.roles[i]}</h3><p className="eyebrow compact-only">{t.fileLabel}</p><a className="methodology-file-name" href={`${original}/blob/master/${file}`}>{file}</a><p>{t.fileDescriptions[i]}</p>{i<2&&<span className="methodology-arrow desktop-only" aria-hidden="true">→</span>}</article>)}</div>
   <div className="methodology-cycle desktop-only"><p className="eyebrow">{t.cycleIndex}</p><ol>{t.steps.map((step,i)=><li key={step}><span>0{i+1}</span><h3>{step}</h3><p>{t.stepDescriptions[i]}</p></li>)}</ol><p className="eyebrow methodology-decision">{t.decision}</p><div className="methodology-outcomes">{[[t.keep,t.keepBody],[t.discard,t.discardBody]].map(([heading,body])=><article key={heading}><h3>{heading}</h3><p>{body}</p></article>)}</div><p className="methodology-repeat">{t.repeat}</p></div>
  </Reveal>
  <Reveal className="methodology-compact-cycle compact-only"><p className="eyebrow">{t.compactCycleIndex}</p><h2>{t.cycleTitle}</h2><p>{t.cycleIntro}</p></Reveal>
  <Reveal className="methodology-adaptation" aria-labelledby="adaptation-title"><p className="eyebrow"><span className="desktop-only">{t.adaptationIndex}</span><span className="compact-only">{t.compactAdaptationIndex}</span></p><h2 id="adaptation-title">{t.adaptationTitle}</h2><p className="methodology-description">{t.adaptationIntro}</p><div className="desktop-only"><table className="methodology-comparison"><thead><tr>{t.tableHeaders.map(h=><th key={h} scope="col">{h}</th>)}</tr></thead><tbody>{t.comparison.map(([label,a,b])=><tr key={label}><th scope="row">{label}</th><td>{a}</td><td>{b}</td></tr>)}</tbody></table><p className="methodology-source">{t.comparisonSource}</p></div></Reveal>
  <Reveal className="methodology-protocols desktop-only" aria-labelledby="protocols-title"><p className="eyebrow">{t.protocolsIndex}</p><h2 id="protocols-title">{t.protocolsTitle}</h2><p className="methodology-description">{t.protocolsIntro}</p><table><thead><tr>{t.protocolHeaders.map(h=><th scope="col" key={h}>{h}</th>)}</tr></thead><tbody>{t.protocols.map(([name,file,history,metric,constraint],i)=><tr key={name}><th scope="row"><Link href={`/${locale}/research/${studySlugs[i]}/`}>{name}</Link><code>{file}</code><small>{history}</small></th><td>{metric}</td><td>{constraint}</td></tr>)}</tbody></table><p className="methodology-description methodology-protocol-note">{t.protocolNote}</p></Reveal>
  <Reveal className="methodology-acme desktop-only" aria-labelledby="acme-title"><p className="eyebrow">{t.acmeIndex}</p><h2 id="acme-title">{t.acmeTitle}</h2><p className="methodology-description">{t.acmeIntro}</p><p className="eyebrow methodology-pilot">{t.pilot}</p><dl className="methodology-partitions">{evidence.partitions.map((n,i)=><div key={i}><dt>{t.partitions[i]}</dt><dd>{n}</dd></div>)}</dl><p className="eyebrow methodology-rmse-label">{t.rmse}</p><div className="methodology-error-bars">{[[t.baseline,evidence.baselineRmseK],[t.selected,evidence.selectedRmseK]].map(([label,value],i)=><div key={label}><span>{label}</span><div><i style={{width:`${Number(value)/evidence.baselineRmseK*100}%`}}/></div><b>{Number(value).toFixed(2)} K</b></div>)}</div><p className="methodology-description methodology-gain">{t.improvement}</p><p className="eyebrow methodology-holdout">{t.holdout}</p><p className="methodology-description methodology-holdout-note">{t.holdoutNote}</p></Reveal>
  <Reveal className="methodology-limits" aria-labelledby="limits-title"><p className="eyebrow desktop-only">{t.limitsIndex}</p><span className="methodology-red compact-only"/><h2 id="limits-title">{t.limitsTitle}</h2><p className="methodology-description"><span className="desktop-only">{t.limitsIntro}</span><span className="compact-only">{t.disclaimer}</span></p><div className="methodology-limits-grid desktop-only">{t.limits.map(([heading,body],i)=><article key={heading}><span>0{i+1}</span><h3>{heading}</h3><p>{body}</p></article>)}</div></Reveal>
  <Reveal className="methodology-references" aria-labelledby="references-title"><p className="eyebrow"><span className="desktop-only">{t.referencesIndex}</span><span className="compact-only">{t.compactReferencesIndex}</span></p><h2 id="references-title">{t.referencesTitle}</h2><p><a href={original}>{t.original} / github.com/karpathy/autoresearch</a></p><p><a href={repository}>{t.adaptation} / github.com/DiegoCali/los-espinosaurios-flame-in-freefall</a></p><p className="desktop-only methodology-source">{t.referenceNote}</p></Reveal>
 </main><footer className="methodology-footer compact-only"><p className="eyebrow">{t.footer}</p><p>{t.credits}</p></footer></div>;
}
