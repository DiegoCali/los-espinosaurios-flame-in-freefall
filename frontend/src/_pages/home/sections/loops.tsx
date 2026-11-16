'use client';
import { useRef } from 'react';
import { animate, createTimeline, onScroll, stagger, svg } from 'animejs';
import { useAnimeScope } from '@/shared/motion/anime';
import acmeEvidence from '@/entities/acme/evidence.json';
import type { FxCopy } from '@/widgets/measure/fx-copy';

/** Data provenance as a pipeline: pulses travel from the NASA record to a proposal to validate. */
export function ProvenanceFlow({ t }: { t: FxCopy['pipeline'] }) {
  const root = useRef<HTMLDivElement>(null);
  useAnimeScope(root, reduced => {
    const el = root.current!;
    const nodes = el.querySelectorAll('.pf-node'), line = el.querySelector<SVGPathElement>('.pf-line')!;
    if (reduced) return;
    const draw = animate(svg.createDrawable(line), { draw: ['0 0', '0 1'], duration: 1800, ease: 'inOut(3)', autoplay: onScroll({ target: el }) });
    const pulses = [...el.querySelectorAll('.pf-pulse')].map((p, i) => animate(p, { ...svg.createMotionPath(line), opacity: [0, 1, 1, 0], duration: 4200, delay: i * 1400, ease: 'inOut(1.4)', loop: true }));
    const lights = createTimeline({ loop: true, autoplay: onScroll({ target: el }) })
      .add(nodes, { borderColor: ['#2c3a47', '#77c3ed', '#2c3a47'], boxShadow: ['0 0 0 #0000', '0 0 28px #228bdf88', '0 0 0 #0000'], duration: 1200, delay: stagger(900), ease: 'inOut(2)' });
    return () => { draw.revert(); pulses.forEach(p => p.revert()); lights.revert(); };
  });
  return <div ref={root} className="pf" aria-label={t.index} role="group">
    <p className="eyebrow">{t.index}</p>
    <div className="pf-stage">
      <svg className="pf-svg" viewBox="0 0 1000 60" preserveAspectRatio="none" aria-hidden="true">
        <path className="pf-line" d="M60 30 L940 30" stroke="url(#pfGrad)" strokeWidth="2" fill="none" />
        <defs><linearGradient id="pfGrad" x1="0" x2="1"><stop offset="0" stopColor="#77c3ed" /><stop offset=".66" stopColor="#228bdf" /><stop offset="1" stopColor="#5c6873" /></linearGradient></defs>
        {[0, 1, 2].map(i => <circle key={i} className="pf-pulse" r="5" fill="#ffb347" opacity="0" />)}
      </svg>
      <ol className="pf-nodes">{t.nodes.map((n, i) => <li key={n} className="pf-node"><b>0{i + 1}</b><span>{n}</span><small>{t.notes[i]}</small></li>)}</ol>
    </div>
  </div>;
}

const CYCLE = 'M 200 40 A 160 160 0 1 1 199.9 40';

/** AutoResearch cycle: a comet orbits PROPOSE → MODIFY → RUN → RECORD, lighting each stage. */
export function ResearchLoop({ t }: { t: FxCopy['loop'] }) {
  const root = useRef<HTMLElement>(null);
  useAnimeScope(root, reduced => {
    const el = root.current!;
    const path = el.querySelector<SVGPathElement>('.rl-path')!;
    if (reduced) return;
    const ring = animate(svg.createDrawable(path), { draw: ['0 0', '0 1'], duration: 2000, ease: 'inOut(3)', autoplay: onScroll({ target: el }) });
    const comet = animate(el.querySelector('.rl-comet')!, { ...svg.createMotionPath(path), duration: 8000, ease: 'linear', loop: true });
    const trail = animate(el.querySelectorAll('.rl-trail'), { ...svg.createMotionPath(path), duration: 8000, ease: 'linear', loop: true, delay: stagger(-90) });
    const stages = createTimeline({ loop: true, loopDelay: 100 })
      .add(el.querySelectorAll('.rl-stage'), { scale: [1, 1.12, 1], fill: ['#0f1720', '#0a2033', '#0f1720'], stroke: ['#2c3a47', '#77c3ed', '#2c3a47'], duration: 900, delay: stagger(2000), ease: 'inOut(2)' })
      .add(el.querySelectorAll('.rl-branch'), { opacity: [.25, 1, .25], duration: 1000, delay: stagger(600), ease: 'inOut(2)' }, '-=600');
    return () => { ring.revert(); comet.revert(); trail.revert(); stages.revert(); };
  });
  const angles = [-90, 0, 90, 180];
  return <section ref={root} className="rl-section" aria-labelledby="rl-title">
    <div className="rl-copy">
      <p className="eyebrow">{t.index}</p>
      <h2 id="rl-title">{t.title}</h2>
      <p className="section-intro">{t.intro}</p>
      <div className="rl-example"><p className="eyebrow">{t.example}</p><dl>{t.exampleFacts.map(([label, value], i) => <div key={label}><dt>{label}</dt><dd data-count="">{i === 2 ? `${acmeEvidence.metrics.holdout.rmse.toFixed(2)} ${value}` : value}</dd></div>)}</dl></div>
      <p className="rl-disclaimer">{t.disclaimer}</p>
    </div>
    <svg className="rl-svg" viewBox="0 0 400 400" role="img" aria-label={`${t.steps.join(' → ')} · ${t.decision} ${t.keep} / ${t.discard}`}>
      <circle cx="200" cy="200" r="160" fill="none" stroke="#16222e" strokeWidth="10" />
      <path className="rl-path" d={CYCLE} fill="none" stroke="#228bdf" strokeWidth="1.5" strokeDasharray="1 0" />
      {Array.from({ length: 6 }, (_, i) => <circle key={i} className="rl-trail" r={4 - i * .55} fill="#ff5a3d" opacity={.6 - i * .09} />)}
      <g className="rl-comet"><circle r="6" fill="#ffb347" /><circle r="14" fill="#ff5a3d" opacity=".25" /></g>
      {t.steps.map((s, i) => {
        const a = (angles[i] * Math.PI) / 180, x = 200 + Math.cos(a) * 160, y = 200 + Math.sin(a) * 160;
        return <g key={s} transform={`translate(${x} ${y})`}><rect className="rl-stage" x="-52" y="-17" width="104" height="34" rx="2" fill="#0f1720" stroke="#2c3a47" style={{ transformBox: 'fill-box', transformOrigin: 'center' }} /><text textAnchor="middle" y="4" className="rl-stage-label">{s}</text><title>{t.stepNotes[i]}</title></g>;
      })}
      <g transform="translate(200 200)">
        <path d="M0 -46 L58 0 L0 46 L-58 0 Z" fill="#05080d" stroke="#c81936" />
        <text textAnchor="middle" y="-4" className="rl-decision">{t.decision.split(' ').slice(0, 2).join(' ')}</text>
        <text textAnchor="middle" y="10" className="rl-decision">{t.decision.split(' ').slice(2).join(' ')}</text>
        <text className="rl-branch rl-keep" x="-92" y="70" textAnchor="middle">✓ {t.keep}</text>
        <text className="rl-branch rl-discard" x="92" y="70" textAnchor="middle">↺ {t.discard}</text>
      </g>
    </svg>
  </section>;
}

/** Fire fuse between sections: a burning line scrubbed by scroll position. */
export function FlameFuse({ label }: { label: string }) {
  const root = useRef<HTMLDivElement>(null);
  useAnimeScope(root, reduced => {
    const el = root.current!;
    if (reduced) { el.style.setProperty('--fuse', '1'); return; }
    const state = { p: 0 };
    const a = animate(state, { p: [0, 1], ease: 'linear', autoplay: onScroll({ target: el, enter: 'end start', leave: 'center center', sync: .3 }), onUpdate: () => el.style.setProperty('--fuse', state.p.toFixed(4)) });
    const sparks = animate(el.querySelectorAll('.fuse-spark'), { translateY: () => [0, -(Math.random() * 26 + 6)], translateX: () => [0, (Math.random() - .5) * 40], opacity: [1, 0], scale: [1, .2], duration: () => 500 + Math.random() * 600, delay: stagger(70), loop: true, ease: 'out(2)' });
    return () => { a.revert(); sparks.revert(); };
  });
  return <div ref={root} className="fuse" aria-hidden="true">
    <span className="fuse-label">{label}</span>
    <div className="fuse-track"><i className="fuse-burn" /><span className="fuse-head">{Array.from({ length: 8 }, (_, i) => <i key={i} className="fuse-spark" />)}</span></div>
  </div>;
}
