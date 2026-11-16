'use client';
import { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { animate, onScroll, svg, utils, type JSAnimation } from 'animejs';
import { prefersReducedMotion, useAnimeScope } from '@/shared/motion/anime';
import { asset } from '@/shared/config';
import { dictionaries, type Locale } from '@/shared/i18n';
import researchEvidence from '@/entities/research/evidence.json';
import acmeEvidence from '@/entities/acme/evidence.json';
import type { FxCopy } from '@/widgets/measure/fx-copy';

type Point = [number, number];

// Real values from exported evidence (see entities/*/evidence.json).
const realValue: Record<string, (string | null)[]> = {
  acme: [null, null, acmeEvidence.metrics.holdout.rmse.toFixed(2)],
  'bass-ii': [null, null, null],
  'saffire-ii': [null, `+${researchEvidence.values.co2ResponsePpm.toFixed(0)}`, null],
  'same-r': [(researchEvidence.values.photoRate * 100).toFixed(0), (researchEvidence.values.ionRate * 100).toFixed(0), null],
  flex: [null, null, null],
};

function AcmeVisual() {
  return <svg viewBox="0 0 320 180" className="mr-visual" aria-hidden="true">
    {[0, 1].map(k => <g key={k} transform={`translate(${k ? 230 : 90} 120)`}>
      <circle className="mr-acme-halo" r="44" fill="none" stroke={k ? '#c81936' : '#228bdf'} strokeOpacity=".7" strokeDasharray="4 6" />
      <circle r="30" fill={k ? '#2a0a10' : '#0a2033'} stroke={k ? '#c81936' : '#228bdf'} strokeWidth="2" />
      {Array.from({ length: 10 }, (_, i) => <circle key={i} className={`mr-acme-p mr-acme-p${k}`} r="2" fill={k ? '#77c3ed' : '#ffb347'} />)}
      <rect x="-9" y="30" width="18" height="40" fill="#16222e" stroke="#2c3a47" />
      <text y="-58" textAnchor="middle" className="mr-svg-label">{k ? 'INVERSE' : 'NORMAL'}</text>
    </g>)}
  </svg>;
}
function BassVisual() {
  return <svg viewBox="0 0 320 180" className="mr-visual" aria-hidden="true">
    <rect x="20" y="78" width="280" height="24" fill="#0f1720" stroke="#2c3a47" />
    <rect className="mr-bass-burnt" x="20" y="78" width="0" height="24" fill="#05080d" />
    <g className="mr-bass-front" transform="translate(20 0)">
      <ellipse cx="0" cy="90" rx="26" ry="34" fill="#ff5a3d" opacity=".35" />
      <ellipse cx="4" cy="90" rx="14" ry="24" fill="#ffb347" opacity=".7" />
      <path d="M14 62 C 22 76 22 104 14 118" stroke="#77c3ed" strokeWidth="3" fill="none" />
      <line x1="14" x2="14" y1="40" y2="140" stroke="#77c3ed" strokeDasharray="2 4" />
    </g>
    {Array.from({ length: 15 }, (_, i) => <line key={i} x1={20 + i * 20} x2={20 + i * 20} y1="108" y2={i % 5 ? 113 : 118} stroke="#5c7183" />)}
    <text x="20" y="34" className="mr-svg-label">FLOW →</text><text x="300" y="34" textAnchor="end" className="mr-svg-label">← SPREAD</text>
  </svg>;
}
function SaffireVisual({ points }: { points: Point[] | null }) {
  const W = 280, H = 120, x0 = 20, y0 = 30;
  let d = '', t180: number | null = null, tz: number | null = null;
  if (points?.length) {
    const tMin = points[0][0], tMax = points[points.length - 1][0];
    const vs = points.map(p => p[1]), vMin = Math.min(...vs), vMax = Math.max(...vs);
    const X = (t: number) => x0 + ((t - tMin) / (tMax - tMin)) * W, Y = (v: number) => y0 + H - ((v - vMin) / (vMax - vMin)) * H;
    d = points.filter((_, i) => i % 2 === 0).map((p, i) => `${i ? 'L' : 'M'}${X(p[0]).toFixed(1)} ${Y(p[1]).toFixed(1)}`).join(' ');
    t180 = X(180); tz = X(0);
  }
  return <svg viewBox="0 0 320 180" className="mr-visual" aria-hidden="true">
    {[0, 1, 2, 3].map(i => <line key={i} x1={x0} x2={x0 + W} y1={y0 + i * 40} y2={y0 + i * 40} stroke="#16222e" />)}
    {tz !== null && <><line x1={tz} x2={tz} y1={y0 - 6} y2={y0 + H} stroke="#c81936" strokeDasharray="3 4" /><text x={tz + 4} y={y0 - 10} className="mr-svg-label">t₀</text></>}
    {t180 !== null && <><line x1={t180} x2={t180} y1={y0 - 6} y2={y0 + H} stroke="#77c3ed" strokeDasharray="3 4" /><text x={t180 + 4} y={y0 - 10} className="mr-svg-label">180 s</text></>}
    {d && <path className="mr-saff-line" d={d} fill="none" stroke="#ffb347" strokeWidth="1.6" />}
    <text x={x0} y="172" className="mr-svg-label">II-7 · CO₂ ppm</text>
  </svg>;
}
function SameVisual() {
  return <svg viewBox="0 0 320 180" className="mr-visual" aria-hidden="true">
    <rect x="10" y="20" width="300" height="140" fill="none" stroke="#16222e" />
    {Array.from({ length: 36 }, (_, i) => <circle key={i} className="mr-same-p" cx="160" cy="90" r="2" fill="#8c9eae" />)}
    <text x="20" y="38" className="mr-svg-label">FRESH → AGED</text>
  </svg>;
}
function FlexVisual() {
  return <svg viewBox="0 0 320 180" className="mr-visual" aria-hidden="true">
    <defs><radialGradient id="mrHalo"><stop offset="60%" stopColor="#228bdf" stopOpacity="0" /><stop offset="85%" stopColor="#77c3ed" stopOpacity=".8" /><stop offset="100%" stopColor="#77c3ed" stopOpacity="0" /></radialGradient></defs>
    <circle className="mr-flex-halo" cx="160" cy="92" r="70" fill="url(#mrHalo)" />
    <circle className="mr-flex-drop" cx="160" cy="92" r="26" fill="#0f1720" stroke="#f2f3ed" strokeWidth="1.5" />
    <line x1="60" x2="260" y1="92" y2="92" stroke="#2c3a47" strokeDasharray="2 5" />
    <text x="160" y="176" textAnchor="middle" className="mr-svg-label">D(t) ↓</text>
  </svg>;
}

export function MissionRail({ locale, t }: { locale: Locale; t: FxCopy['rail'] }) {
  const outer = useRef<HTMLElement>(null), track = useRef<HTMLDivElement>(null);
  const shared = dictionaries[locale];
  const [co2, setCo2] = useState<Point[] | null>(null);
  useEffect(() => {
    const controller = new AbortController();
    fetch(asset('/data/saffire/II-7.json'), { signal: controller.signal }).then(r => r.ok ? r.json() : Promise.reject()).then((data: { test_id?: string; points?: unknown }) => {
      if (data.test_id === 'II-7' && Array.isArray(data.points) && data.points.every(p => Array.isArray(p) && p.length === 2 && p.every(Number.isFinite))) setCo2(data.points as Point[]);
    }).catch(() => undefined);
    return () => controller.abort();
  }, []);

  // Horizontal travel while the section is pinned (desktop only).
  useAnimeScope(outer, reduced => {
    const el = outer.current!, rail = track.current!;
    const desktop = window.matchMedia('(min-width: 1200px)').matches;
    if (reduced || !desktop) return;
    el.classList.add('is-pinned');
    const state = { p: 0 };
    const distance = () => Math.max(0, rail.scrollWidth - rail.parentElement!.clientWidth);
    const anim = animate(state, { p: [0, 1], ease: 'linear', autoplay: onScroll({ target: el, enter: 'start start', leave: 'end end', sync: .12 }), onUpdate: () => {
      rail.style.transform = `translate3d(${-state.p * distance()}px,0,0)`;
      el.style.setProperty('--mr-progress', state.p.toFixed(4));
    } });
    return () => { anim.revert(); el.classList.remove('is-pinned'); rail.style.transform = ''; };
  });

  // Mini illustrations: one looping animation per record.
  useEffect(() => {
    const root = track.current!;
    if (prefersReducedMotion()) return;
    const loops: JSAnimation[] = [];
    root.querySelectorAll<SVGCircleElement>('.mr-acme-p').forEach((p, i) => {
      const inverse = p.classList.contains('mr-acme-p1'), a = utils.random(0, Math.PI * 2);
      // Normal: fuel leaves the burner outward. Inverse: oxidizer leaves the burner into fuel.
      loops.push(animate(p, { cx: [0, Math.cos(a) * 44], cy: [0, Math.sin(a) * 44], opacity: [1, 0], duration: utils.random(1400, 2400), delay: i * 140, ease: inverse ? 'out(2)' : 'out(3)', loop: true }));
    });
    loops.push(animate(root.querySelectorAll('.mr-acme-halo'), { rotate: 360, duration: 16000, ease: 'linear', loop: true }));
    loops.push(animate(root.querySelector('.mr-bass-front')!, { translateX: [20, 290], duration: 6000, ease: 'linear', loop: true }));
    loops.push(animate(root.querySelector('.mr-bass-burnt')!, { width: [0, 270], duration: 6000, ease: 'linear', loop: true }));
    root.querySelectorAll<SVGCircleElement>('.mr-same-p').forEach((p, i) => {
      const cluster = i % 9, cx = 50 + (cluster % 3) * 110 + utils.random(-8, 8), cy = 50 + Math.floor(cluster / 3) * 40 + utils.random(-6, 6);
      loops.push(animate(p, { cx: [utils.random(20, 300), cx], cy: [utils.random(30, 150), cy], r: [1.6, 3.4], fill: ['#8c9eae', '#ffb347'], duration: 4200, delay: i * 30, ease: 'inOut(3)', loop: true, alternate: true }));
    });
    loops.push(animate(root.querySelector('.mr-flex-drop')!, { r: [26, 10, 10], opacity: [1, 1, 0], duration: 5200, ease: 'inOut(2)', loop: true }));
    loops.push(animate(root.querySelector('.mr-flex-halo')!, { r: [70, 34, 34], opacity: [1, .8, 0], duration: 5200, ease: 'inOut(2)', loop: true }));
    return () => loops.forEach(a => a.revert());
  }, []);

  // Draw the real CO₂ trace whenever it is loaded.
  useEffect(() => {
    if (!co2 || prefersReducedMotion()) return;
    const line = track.current!.querySelector<SVGPathElement>('.mr-saff-line');
    if (!line) return;
    const a = animate(svg.createDrawable(line), { draw: ['0 0', '0 1', '1 1'], duration: 5200, ease: 'inOut(2)', loop: true, loopDelay: 400 });
    return () => { a.revert(); };
  }, [co2]);

  const visuals: Record<string, React.ReactNode> = { acme: <AcmeVisual />, 'bass-ii': <BassVisual />, 'saffire-ii': <SaffireVisual points={co2} />, 'same-r': <SameVisual />, flex: <FlexVisual /> };
  return <section ref={outer} className="mr-section" aria-labelledby="mr-title">
    <div className="mr-sticky">
      <header className="mr-head">
        <p className="eyebrow">{t.index}</p>
        <h2 id="mr-title">{t.title}</h2>
        <p className="section-intro">{t.intro}</p>
        <span className="mr-hint eyebrow" aria-hidden="true">{t.drag}</span>
      </header>
      <div className="mr-viewport">
        <div ref={track} className="mr-track">
          {shared.studiesList.map((study, i) => <article className="mr-card" key={study.slug} data-study={study.slug}>
            <div className="mr-card-top"><span className="mr-num">0{i + 1}</span><p className="eyebrow">{study.psi}</p></div>
            <div className="mr-visual-wrap">{visuals[study.slug]}</div>
            <h3>{study.title}</h3>
            <p className="mr-question">{study.question}</p>
            <dl className="mr-facts">{t.facts[study.slug].map(([label, unit], k) => {
              const real = realValue[study.slug][k];
              return <div key={label}><dt>{label}</dt><dd data-count="">{real ? `${real}${unit === 'K' ? ' K' : unit === 'ppm' ? ' ppm' : unit}` : unit}</dd></div>;
            })}</dl>
            <p className="mr-note">{t.notes[study.slug]}</p>
            <Link className="mr-open" href={`/${locale}/research/${study.slug}/`}>{t.open} <span aria-hidden="true">→</span></Link>
          </article>)}
        </div>
      </div>
      <div className="mr-progress" aria-hidden="true"><i /></div>
    </div>
  </section>;
}
