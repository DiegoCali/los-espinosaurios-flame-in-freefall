'use client';
import { useEffect, useRef, useState } from 'react';
import { animate, stagger, utils, type JSAnimation } from 'animejs';
import { prefersReducedMotion } from '@/shared/motion/anime';
import evidence from '@/entities/same/evidence.json';
import type { MeasureCopy } from './copy';
import './measure.css';

const N = 46;
const regimes = [evidence.detectors.flow_8cm_s, evidence.detectors.no_flow];

/** Smoke push → two detectors. Particle motion is conceptual; response fractions are real. */
export function SameMeasure({ t }: { t: MeasureCopy['same'] }) {
  const [regime, setRegime] = useState(0);
  const stage = useRef<SVGSVGElement>(null), bars = useRef<HTMLDivElement>(null);
  const data = regimes[regime];

  useEffect(() => {
    const svgEl = stage.current!, reduced = prefersReducedMotion();
    const loops: JSAnimation[] = [];
    const dots = svgEl.querySelectorAll<SVGCircleElement>('.sx-p');
    // Bars and counters move to the real fractions of the selected regime.
    bars.current?.querySelectorAll<HTMLElement>('[data-rate]').forEach(bar => {
      const rate = Number(bar.dataset.rate);
      const fill = bar.querySelector<HTMLElement>('i')!, out = bar.querySelector<HTMLElement>('b')!;
      if (reduced) { fill.style.transform = `scaleX(${rate})`; out.textContent = `${(rate * 100).toFixed(1)}%`; return; }
      const p = { v: Number(out.dataset.v ?? 0) };
      loops.push(animate(fill, { scaleX: rate, duration: 1200, ease: 'inOut(3)' }));
      loops.push(animate(p, { v: rate, duration: 1200, ease: 'inOut(3)', onUpdate: () => { out.textContent = `${(p.v * 100).toFixed(1)}%`; out.dataset.v = String(p.v); } }));
    });
    if (reduced) return;
    dots.forEach((dot, i) => {
      if (regime === 0) {
        // Forced flow carries many small particles past both detectors.
        const y = utils.random(120, 220);
        loops.push(animate(dot, { cx: [70, 640], cy: [y, y + utils.random(-30, 30)], r: [1.6, 2], opacity: [0, .9, .9, 0], duration: utils.random(2400, 3200), delay: i * 70, ease: 'linear', loop: true }));
      } else {
        // No flow: smoke lingers near the source and coagulates into fewer, larger particles.
        const a = utils.random(0, Math.PI * 2), r = utils.random(8, 70), clusterA = Math.floor(i / 6) * 0.8;
        loops.push(animate(dot, { cx: [92 + Math.cos(a) * r, 110 + Math.cos(clusterA) * 46], cy: [170 + Math.sin(a) * r, 170 + Math.sin(clusterA) * 46], r: [1.4, i % 6 ? 1.2 : 5.2], opacity: [.2, i % 6 ? .25 : .95], duration: 5200, delay: i * 40, ease: 'inOut(2)', loop: true, alternate: true }));
      }
    });
    // Conceptual signals: photoelectric drops, ionization rises.
    loops.push(animate(svgEl.querySelector('.sx-beam')!, { opacity: [.35, .9], duration: 900, ease: 'inOut(2)', loop: true, alternate: true }));
    loops.push(animate(svgEl.querySelectorAll('.sx-ion'), { opacity: [.2, 1], r: [1.2, 2.2], duration: 700, delay: stagger(60), ease: 'inOut(2)', loop: true, alternate: true }));
    return () => loops.forEach(a => a.pause());
  }, [regime]);

  return <section className="mx-section sx" aria-labelledby="sx-title">
    <div className="mx-copy">
      <p className="eyebrow">{t.index}</p>
      <h2 id="sx-title">{t.title}</h2>
      <p className="section-intro">{t.intro}</p>
      <div className="mx-chips" role="radiogroup" aria-label={t.regime}>{t.regimes.map((r, i) => <button key={r} type="button" role="radio" aria-checked={regime === i} onClick={() => setRegime(i)}>{r}</button>)}</div>
      <div ref={bars} className="sx-bars" aria-live="polite">
        <p className="eyebrow">{t.rate} · n = {data.n_pushes} {t.pushes}</p>
        {[data.iss_rate, data.ion_rate].map((rate, i) => <div key={i} className={`sx-bar sx-bar-${i}`} data-rate={rate}><span>{t.detectors[i]} <small>{t.rules[i]}</small></span><b>{(rate * 100).toFixed(1)}%</b><div><i /></div></div>)}
      </div>
      <p className="mx-micro"><i aria-hidden="true" />{t.why}</p>
    </div>
    <figure className="mx-figure">
      <svg ref={stage} className="mx-chart sx-stage" viewBox="0 0 680 340" role="img" aria-label={`${t.title} ${t.regimes[regime]}: ${t.detectors[0]} ${(data.iss_rate * 100).toFixed(1)}%, ${t.detectors[1]} ${(data.ion_rate * 100).toFixed(1)}%`}>
        <rect x="20" y="70" width="640" height="200" className="sx-duct" />
        <g className="sx-source"><circle cx="92" cy="170" r="14" /><text x="92" y="300" textAnchor="middle">{t.source}</text></g>
        {regime === 0 && <g className="sx-flow">{[110, 170, 230].map(y => <path key={y} d={`M140 ${y} H620`} />)}</g>}
        <g className="sx-photo" transform="translate(330 0)">
          <rect x="-60" y="82" width="120" height="176" />
          <line className="sx-beam" x1="-56" y1="170" x2="56" y2="170" />
          <circle cx="-56" cy="170" r="5" className="sx-led" /><rect x="34" y="96" width="14" height="14" className="sx-diode" />
          <text y="60" textAnchor="middle">{t.detectors[0]}</text><text y="78" textAnchor="middle" className="sx-sub">{t.beam} → {t.sensor}</text>
        </g>
        <g className="sx-ionc" transform="translate(520 0)">
          <rect x="-60" y="82" width="120" height="176" />
          {Array.from({ length: 14 }, (_, i) => <circle key={i} className="sx-ion" cx={-40 + (i % 7) * 13} cy={150 + Math.floor(i / 7) * 36} r="1.6" />)}
          <path d="M-50 132 H50 M-50 214 H50" className="sx-plates" />
          <text y="60" textAnchor="middle">{t.detectors[1]}</text><text y="78" textAnchor="middle" className="sx-sub">{t.chamber}</text>
        </g>
        <g className="sx-dots">{Array.from({ length: N }, (_, i) => <circle key={i} className="sx-p" cx="92" cy="170" r="1.6" />)}</g>
        <text x="660" y="330" textAnchor="end" className="sx-sub">{t.signal}</text>
      </svg>
      <figcaption>{t.proxy}</figcaption>
    </figure>
  </section>;
}
