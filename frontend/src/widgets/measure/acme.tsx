'use client';
import { useEffect, useRef, useState } from 'react';
import { animate, createTimeline, onScroll, stagger, svg, utils, type JSAnimation, type Timeline } from 'animejs';
import { prefersReducedMotion } from '@/shared/motion/anime';
import evidence from '@/entities/acme/evidence.json';
import type { MeasureCopy } from './copy';
import './measure.css';

const BURNER = 30, SHEET = 92, OUTER = 150, N = 30;
const holdout = evidence.metrics.holdout;
const partitions = [holdout.n_train, evidence.metrics.validation.n_validation, holdout.n_holdout];
const byType = [['Normal', holdout.by_flame_type.Normal.rmse_k], ['Inverse', holdout.by_flame_type.Inverse.rmse_k]] as const;

/** Normal vs inverse diffusion flame (conceptual) and the real model contract behind Tad. */
export function AcmeMeasure({ t }: { t: MeasureCopy['acme'] }) {
  const [config, setConfig] = useState(0);
  const stage = useRef<SVGSVGElement>(null), pipe = useRef<HTMLDivElement>(null);
  const burnerSpecies = config === 0 ? t.fuel : t.oxygen, ambientSpecies = config === 0 ? t.oxygen : t.ethylene;
  const burnerColor = config === 0 ? '#ffb347' : '#77c3ed', ambientColor = config === 0 ? '#77c3ed' : '#ffb347';

  useEffect(() => {
    const el = stage.current!, reduced = prefersReducedMotion();
    if (reduced) return;
    const loops: JSAnimation[] = [];
    el.querySelectorAll<SVGCircleElement>('.ax-out').forEach((p, i) => {
      const a = (i / N) * Math.PI * 2;
      loops.push(animate(p, { cx: [Math.cos(a) * BURNER, Math.cos(a) * (SHEET - 4)], cy: [Math.sin(a) * BURNER, Math.sin(a) * (SHEET - 4)], opacity: [0, 1, 0], duration: utils.random(1600, 2400), delay: i * 60, ease: 'out(2)', loop: true }));
    });
    el.querySelectorAll<SVGCircleElement>('.ax-in').forEach((p, i) => {
      const a = (i / N) * Math.PI * 2 + .1;
      loops.push(animate(p, { cx: [Math.cos(a) * OUTER, Math.cos(a) * (SHEET + 4)], cy: [Math.sin(a) * OUTER, Math.sin(a) * (SHEET + 4)], opacity: [0, 1, 0], duration: utils.random(2400, 3400), delay: i * 70, ease: 'in(1.5)', loop: true }));
    });
    loops.push(animate(el.querySelector('.ax-sheet')!, { r: [SHEET - 3, SHEET + 3], opacity: [.65, 1], duration: 1800, ease: 'inOut(2)', loop: true, alternate: true }));
    loops.push(animate(el.querySelector('.ax-sheet-dash')!, { rotate: 360, duration: 24000, ease: 'linear', loop: true }));
    return () => loops.forEach(a => a.revert());
  }, [config]);

  useEffect(() => {
    const el = pipe.current!, reduced = prefersReducedMotion();
    const bars = el.querySelectorAll<HTMLElement>('[data-w]');
    if (reduced) { bars.forEach(b => { b.style.transform = `scaleX(${b.dataset.w})`; }); return; }
    const flows = el.querySelectorAll<SVGPathElement>('.ax-wire');
    const pulses: JSAnimation[] = [];
    el.querySelectorAll<SVGCircleElement>('.ax-pulse').forEach((p, i) => pulses.push(animate(p, { ...svg.createMotionPath(flows[i % flows.length]), opacity: [0, 1, 1, 0], duration: 1800, delay: i * 260, ease: 'inOut(2)', loop: true })));
    utils.set(el.querySelectorAll('.ax-chip, .ax-model, .ax-output'), { opacity: 0 });
    utils.set(bars, { scaleX: 0 });
    const tl: Timeline = createTimeline({ autoplay: onScroll({ target: el }) })
      .add(el.querySelectorAll('.ax-chip'), { opacity: [0, 1], translateX: [-16, 0], duration: 500, delay: stagger(70), ease: 'out(3)' })
      .add(svg.createDrawable(flows), { draw: ['0 0', '0 1'], duration: 900, delay: stagger(50), ease: 'inOut(2)' }, 300)
      .add(el.querySelector('.ax-model')!, { scale: [.8, 1], opacity: [0, 1], duration: 700, ease: 'out(4)' }, 700)
      .add(el.querySelector('.ax-output')!, { scale: [.8, 1], opacity: [0, 1], duration: 700, ease: 'out(4)' }, 1000);
    bars.forEach((b, i) => tl.add(b, { scaleX: [0, Number(b.dataset.w)], duration: 1200, ease: 'inOut(3)' }, 1200 + i * 120));
    return () => { tl.revert(); pulses.forEach(p => p.revert()); };
  }, []);

  const maxRmse = Math.max(...byType.map(b => b[1]));
  const total = partitions.reduce((a, b) => a + b, 0);
  return <section className="mx-section ax" aria-labelledby="ax-title">
    <div className="mx-copy">
      <p className="eyebrow">{t.index}</p>
      <h2 id="ax-title">{t.title}</h2>
      <p className="section-intro">{t.intro}</p>
      <div className="mx-chips" role="radiogroup" aria-label="ACME">{t.configs.map((c, i) => <button key={c} type="button" role="radio" aria-checked={config === i} onClick={() => setConfig(i)}>{c}</button>)}</div>
      <dl className="ax-roles"><div><dt>{t.burner}</dt><dd style={{ color: burnerColor }}>{burnerSpecies}</dd></div><div><dt>{t.ambient}</dt><dd style={{ color: ambientColor }}>{ambientSpecies}</dd></div></dl>
      <p className="mx-micro"><i aria-hidden="true" />{t.micro}</p>
    </div>
    <figure className="mx-figure">
      <svg ref={stage} className="mx-chart ax-stage" viewBox="-180 -180 360 360" role="img" aria-label={`${t.configs[config]}: ${t.burner} ${burnerSpecies}, ${t.ambient} ${ambientSpecies}`}>
        <defs><radialGradient id="axGlow"><stop offset="80%" stopColor="#228bdf" stopOpacity="0" /><stop offset="94%" stopColor={config === 0 ? '#ffb347' : '#77c3ed'} stopOpacity=".9" /><stop offset="100%" stopColor="#c81936" stopOpacity="0" /></radialGradient></defs>
        <circle r={OUTER + 10} className="ax-ambient-ring" />
        <circle className="ax-sheet" r={SHEET} fill="url(#axGlow)" />
        <circle className="ax-sheet-dash" r={SHEET + 14} fill="none" stroke="#c81936" strokeDasharray="2 8" style={{ transformOrigin: '0 0' }} />
        {Array.from({ length: N }, (_, i) => <circle key={`o${i}`} className="ax-out" r="2.2" fill={burnerColor} opacity="0" />)}
        {Array.from({ length: N }, (_, i) => <circle key={`i${i}`} className="ax-in" r="1.8" fill={ambientColor} opacity="0" />)}
        <circle r={BURNER} className="ax-burner" stroke={burnerColor} />
        <rect x="-7" y={BURNER} width="14" height="60" className="ax-tube" />
        <text y="-166" textAnchor="middle" className="ax-label">{t.ambient}: {ambientSpecies}</text>
        <text y="5" textAnchor="middle" className="ax-label ax-label-burner">{t.burner}</text>
        <text y="172" textAnchor="middle" className="ax-note">{t.diagram}</text>
      </svg>
      <div ref={pipe} className="ax-pipe">
        <div className="ax-flow">
          <ul className="ax-chips">{t.inputs.map(name => <li key={name} className="ax-chip">{name}</li>)}</ul>
          <svg className="ax-wires" viewBox="0 0 120 210" preserveAspectRatio="none" aria-hidden="true">
            {t.inputs.map((_, i) => <path key={i} className="ax-wire" d={`M0 ${15 + i * 30} C 60 ${15 + i * 30} 60 105 120 105`} />)}
            {Array.from({ length: 7 }, (_, i) => <circle key={i} className="ax-pulse" r="2.4" opacity="0" />)}
          </svg>
          <div className="ax-model"><b>{t.model}</b><small>α = 0.001 · n = {holdout.n_train}</small></div>
          <div className="ax-output"><b>Tad</b><small>{t.output}</small></div>
        </div>
        <div className="ax-part">{partitions.map((n, i) => <div key={i} style={{ flex: n / total }}><i data-w="1" /><span>{t.partitions[i]} · {n}</span></div>)}</div>
        <p className="eyebrow">{t.holdout}</p>
        <div className="ax-rmse">{byType.map(([name, v], i) => <div key={name}><span>{t.configs[i]}</span><div><i data-w={(v / maxRmse).toFixed(4)} /></div><b>{v.toFixed(2)} K</b></div>)}<div className="ax-total"><span>ALL · n = {holdout.n_holdout}</span><b>{holdout.rmse.toFixed(2)} K</b></div></div>
        <p className="mx-caption">{t.notMeasured}</p>
      </div>
    </figure>
  </section>;
}
