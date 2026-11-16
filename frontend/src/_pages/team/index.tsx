import Link from 'next/link';
import { SiteHeader } from '@/widgets/site-header';
import { Reveal } from '@/shared/ui/reveal';
import { asset } from '@/shared/config';
import { dictionaries, type Locale } from '@/shared/i18n';
import { members } from './members';
import { teamCopy } from './copy';
import '@/_pages/home/home.css';
import './team.css';

export function TeamPage({locale}:{locale:Locale}){
 const t=teamCopy[locale],shared=dictionaries[locale];
 return <div className="research-home team-page"><SiteHeader locale={locale}/><main id="main">
  <Reveal className="team-hero" aria-labelledby="team-title"><p className="eyebrow compact-only team-page-index">04 / {shared.nav[3]} · <span className="mobile-label">{shared.mobile}</span><span className="tablet-label">{shared.tablet}</span></p><p className="eyebrow"><span className="desktop-only">{t.eyebrow}</span><span className="compact-only">{t.compactEyebrow}</span></p><h1 id="team-title"><span className="desktop-only">{t.title.map(line=><span key={line}>{line}</span>)}</span><span className="compact-only">{t.title.join(' ')}</span></h1><p className="team-intro">{t.intro}</p><p className="team-credit-note desktop-only">{t.credits}</p><h2 className="compact-only">{t.projectCredits}</h2><div className="team-red"/><p className="eyebrow team-count desktop-only">{t.count}</p></Reveal>
  <section className="team-directory" aria-labelledby="directory-title"><p className="eyebrow"><span className="desktop-only" id="directory-title">{t.directoryIndex}</span><span className="compact-only">{t.compactDirectoryIndex}</span></p><h2 className="compact-only">{t.directoryTitle}</h2><p className="team-directory-intro"><span className="desktop-only">{t.directoryIntro}</span><span className="compact-only">{t.credits}</span></p>
   <div className="team-members">{members.map((member,i)=>{
    const profile=`https://github.com/${member.handle}`;
    const reference=`https://github.com/DiegoCali/los-espinosaurios-flame-in-freefall/commit/${member.commit}`;
    return <Reveal className={`team-member team-member-${i}`} key={member.handle} aria-labelledby={`member-${i}`}>
     <span className="team-member-index desktop-only">0{i+1}</span>
     <div className="team-portrait"><img src={asset(`/assets/team/${member.avatarFile}`)} alt={`${locale==='es'?'Avatar de GitHub de':'GitHub avatar for'} @${member.handle}`} width={220} height={220} loading="lazy" decoding="async"/><span className="team-portrait-calibration"/><a href={`https://avatars.githubusercontent.com/u/${member.avatarId}?v=4`} target="_blank" rel="noopener noreferrer">{t.photo}</a></div>
     <div className="team-member-copy"><a className="team-handle desktop-only" href={profile} target="_blank" rel="noopener noreferrer">@{member.handle}</a><h3 id={`member-${i}`}><a href={profile} target="_blank" rel="noopener noreferrer">{member.name}</a></h3><p className="team-study">{member.psi}{"  /  "}{member.study}{"   /   "}{t.subjects[i]}</p><p className="team-contribution">{t.contributions[i]}</p><p className="team-contract-label desktop-only">{t.contract}</p><p className="team-contract">{t.contracts[i]}</p><p className="team-history desktop-only">{t.histories[i]}</p><a className="team-profile-link" href={profile} target="_blank" rel="noopener noreferrer">github.com/{member.handle}</a></div>
     <a className="team-reference desktop-only" href={reference} target="_blank" rel="noopener noreferrer" title={i===3?t.identityNote:`${t.gitAuthor}: ${member.gitAuthor}`}>REF / {member.commit.slice(0,7)}</a>
    </Reveal>;
   })}</div>
  </section>
  <Reveal className="team-methodology desktop-only"><p className="eyebrow">{t.methodologyIndex}</p><h2>{t.methodologyTitle}</h2><div><article><h3>{t.git}</h3><p>ACME · SAFFIRE-II · FLEX</p></article><article><h3>{t.snapshots}</h3><p>BASS-II · SAME-R</p></article></div></Reveal>
  <Reveal className="team-provenance compact-only"><p className="eyebrow">{t.compactMethodologyIndex}</p><h2>{t.provenanceTitle}</h2><p>{t.attribution}</p></Reveal>
 </main><footer className="team-footer"><div className="desktop-only team-footer-top"><Link href={`/${locale}/`} className="brand">S//L / LOS ESPINOSAURIOS</Link><p>{t.footerSources}</p></div><p className="desktop-only">{t.attribution}</p><p className="eyebrow compact-only">{t.footer}</p><p className="compact-only">{t.footerCredits}</p></footer></div>;
}
