'use client';
import { useEffect, useRef, useState } from 'react';
import { animate, stagger, svg, utils, type JSAnimation, type Timeline } from 'animejs';
import { prefersReducedMotion, scrambleFrame } from '@/shared/motion/anime';
import type { FxCopy } from '@/widgets/measure/fx-copy';

// Conceptual flame outlines (outer, inner) for each regime. Source point at (200, 262).
const SHAPES = [
  ['M200 305 C150 305 142 262 158 222 C175 178 194 132 200 50 C206 132 225 178 242 222 C258 262 250 305 200 305 Z', 'M200 300 C170 300 166 270 176 240 C186 210 196 180 200 120 C204 180 214 210 224 240 C234 270 230 300 200 300 Z'],
  ['M200 330 C125 330 108 292 112 258 C116 222 152 196 200 196 C248 196 284 222 288 258 C292 292 275 330 200 330 Z', 'M200 312 C150 312 140 288 142 262 C144 236 168 220 200 220 C232 220 256 236 258 262 C260 288 250 312 200 312 Z'],
  ['M200 290 C178 290 168 278 168 262 C168 246 180 234 200 234 C220 234 232 246 232 262 C232 278 222 290 200 290 Z', 'M200 280 C186 280 180 272 180 262 C180 252 188 244 200 244 C212 244 220 252 220 262 C220 272 214 280 200 280 Z'],
] as const;
const PARTICLES = 28;
const CX = 200, CY = 262;

export function GravityExplainer({ t }: { t: FxCopy['gravity'] }) {
  const [mode, setMode] = useState(0);
  const stage = useRef<SVGSVGElement>(null), readouts = useRef<HTMLDListElement>(null), section = useRef<HTMLElement>(null);
  const touched = useRef(false), firstRun = useRef(true);

  // Auto-demonstrate once: when the section is first seen, gravity "switches off".
  useEffect(() => {
    const el = section.current!;
    const io = new IntersectionObserver(([entry]) => {
      if (!entry.isIntersecting) return;
      io.disconnect();
      const timer = window.setTimeout(() => { if (!touched.current) setMode(1); }, 2400);
      return () => clearTimeout(timer);
    }, { threshold: .45 });
    io.observe(el);
    return () => io.disconnect();
  }, []);

  useEffect(() => {
    const root = stage.current!;
    const reduced = prefersReducedMotion();
    // Transitions are paused on change (so the next morph starts from the current shape);
    // looping ambience is reverted.
    const running: (JSAnimation | Timeline)[] = [], loops: (JSAnimation | Timeline)[] = [];
    const [outerTarget, innerTarget] = [root.querySelector<SVGPathElement>(`#shape-${mode}-0`)!, root.querySelector<SVGPathElement>(`#shape-${mode}-1`)!];
    const outers = root.querySelectorAll<SVGPathElement>('.gx-outer'), inners = root.querySelectorAll<SVGPathElement>('.gx-inner');
    const warm = root.querySelectorAll('.gx-warm'), cool = root.querySelectorAll('.gx-cool');
    const duration = reduced || firstRun.current ? 0 : 1400;
    firstRun.current = false;

    running.push(animate(outers, { d: svg.morphTo(outerTarget), duration, ease: 'inOut(3)' }));
    running.push(animate(inners, { d: svg.morphTo(innerTarget), duration, ease: 'inOut(3)' }));
    running.push(animate(warm, { opacity: mode === 0 ? 1 : 0, duration, ease: 'inOut(2)' }));
    running.push(animate(cool, { opacity: mode === 0 ? 0 : 1, duration, ease: 'inOut(2)' }));
    running.push(animate(root.querySelector('.gx-flame')!, { opacity: mode === 2 ? [1, .12] : 1, duration: mode === 2 ? 3600 : duration, delay: mode === 2 ? 900 : 0, ease: 'in(2)' }));
    running.push(animate(root.querySelectorAll('.gx-plume'), { opacity: mode === 0 ? 1 : 0, duration: duration || 1, ease: 'out(2)' }));
    running.push(animate(root.querySelector('.gx-g-arrow')!, { scaleY: mode === 0 ? 1 : 0.001, opacity: mode === 0 ? 1 : .2, duration, ease: 'inOut(3)' }));

    // Readouts decode to the new regime text.
    readouts.current?.querySelectorAll<HTMLElement>('dd').forEach(dd => {
      const final = dd.dataset[`m${mode}`] ?? '';
      if (reduced) { dd.textContent = final; return; }
      const p = { v: 0 };
      running.push(animate(p, { v: 1, duration: 700, ease: 'out(2)', onUpdate: () => { dd.textContent = scrambleFrame(final, p.v); } }));
    });

    if (!reduced) {
      // Flame motion: buoyant flicker in 1 g, slow breathing in μg.
      loops.push(animate(root.querySelector('.gx-flame-body')!, mode === 0
        ? { scaleY: [1, 1.06, .97, 1.04, 1], scaleX: [1, .97, 1.02, .98, 1], duration: 1300, ease: 'inOut(2)', loop: true }
        : { scale: [1, mode === 1 ? 1.025 : .96, 1], duration: mode === 1 ? 3800 : 2400, ease: 'inOut(2)', loop: true }));
      loops.push(animate(root.querySelectorAll('.gx-plume path'), { strokeDashoffset: [0, -64], duration: 1400, ease: 'linear', loop: true }));

      // Oxygen / air particles: drawn upward by the plume, or diffusing radially inward.
      const dots = root.querySelectorAll<SVGCircleElement>('.gx-dot');
      dots.forEach((dot, i) => {
        if (mode === 0) {
          const x0 = utils.random(90, 310), drift = (CX - x0) * utils.random(.3, .7);
          loops.push(animate(dot, { cx: [x0, x0 + drift], cy: [395, utils.random(-10, 60)], opacity: [0, .9, 0], r: [2.2, 1.2], duration: utils.random(2600, 4200), delay: i * 110, ease: 'in(1.4)', loop: true }));
        } else {
          const a = (i / PARTICLES) * Math.PI * 2 + utils.random(-.15, .15), r0 = mode === 1 ? 175 : 160, r1 = mode === 1 ? 82 : 42;
          loops.push(animate(dot, { cx: [CX + Math.cos(a) * r0, CX + Math.cos(a) * r1], cy: [CY + Math.sin(a) * r0, CY + Math.sin(a) * r1], opacity: [0, mode === 1 ? .85 : .45, 0], r: [1.6, 2.4], duration: utils.random(mode === 1 ? 3200 : 5200, mode === 1 ? 4800 : 7600), delay: i * 90, ease: 'out(1.6)', loop: true }));
        }
      });
      loops.push(animate(root.querySelectorAll('.gx-ring'), { scale: [.92, 1.04], opacity: [0, mode === 0 ? 0 : .5, 0], duration: 3200, delay: stagger(700), ease: 'out(2)', loop: true }));
    }
    return () => { running.forEach(a => a.pause()); loops.forEach(a => a.revert()); };
  }, [mode]);

  const choose = (m: number) => { touched.current = true; setMode(m); };
  return <section ref={section} className="gx-section" aria-labelledby="gx-title">
    <div className="gx-copy">
      <p className="eyebrow">{t.index}</p>
      <h2 id="gx-title">{t.title}</h2>
      <p className="section-intro">{t.intro}</p>
      <div className="gx-modes" role="radiogroup" aria-label={t.mode}>{t.modes.map((label, i) => <button key={label} type="button" role="radio" aria-checked={mode === i} onClick={() => choose(i)}><i />{label}</button>)}</div>
      <article className="gx-panel" aria-live="polite"><p className="eyebrow">{t.panels[mode].tag}</p><h3>{t.panels[mode].title}</h3><p>{t.panels[mode].body}</p></article>
      <dl ref={readouts} className="gx-readouts">
        <div><dt>{t.shape}</dt><dd data-m0={t.shapeModes[0]} data-m1={t.shapeModes[1]} data-m2={t.shapeModes[2]}>{t.shapeModes[0]}</dd></div>
        <div><dt>{t.oxygen}</dt><dd data-m0={t.oxygenModes[0]} data-m1={t.oxygenModes[1]} data-m2={t.oxygenModes[2]}>{t.oxygenModes[0]}</dd></div>
      </dl>
      <p className="gx-colour"><b>{t.colour}</b>{t.colourNote}</p>
    </div>
    <figure className="gx-stage">
      <span className="gx-diagram eyebrow">{t.diagram}</span>
      <svg ref={stage} viewBox="0 0 400 400" role="img" aria-label={`${t.title} — ${t.modes[mode]}`}>
        <defs>
          <radialGradient id="gxWarmO" cx="50%" cy="78%" r="70%"><stop offset="0%" stopColor="#fff3c4" /><stop offset="35%" stopColor="#ffb347" /><stop offset="70%" stopColor="#ff5a3d" /><stop offset="100%" stopColor="#c81936" stopOpacity=".2" /></radialGradient>
          <radialGradient id="gxCoolO" cx="50%" cy="60%" r="60%"><stop offset="0%" stopColor="#0a2033" stopOpacity="0" /><stop offset="55%" stopColor="#228bdf" stopOpacity=".35" /><stop offset="82%" stopColor="#77c3ed" stopOpacity=".9" /><stop offset="100%" stopColor="#d9f1ff" stopOpacity=".2" /></radialGradient>
          <radialGradient id="gxWarmI" cx="50%" cy="80%" r="70%"><stop offset="0%" stopColor="#3a7bd5" /><stop offset="40%" stopColor="#fff7d6" /><stop offset="100%" stopColor="#ffd27a" stopOpacity=".1" /></radialGradient>
          <radialGradient id="gxCoolI" cx="50%" cy="50%" r="55%"><stop offset="0%" stopColor="#020305" stopOpacity="0" /><stop offset="70%" stopColor="#77c3ed" stopOpacity=".25" /><stop offset="100%" stopColor="#bfe6ff" stopOpacity=".7" /></radialGradient>
          <filter id="gxGlow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="9" result="b" /><feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge></filter>
          {SHAPES.map((pair, m) => pair.map((d, k) => <path key={`${m}-${k}`} id={`shape-${m}-${k}`} d={d} />))}
        </defs>
        <g className="gx-grid">{Array.from({ length: 9 }, (_, i) => <line key={`h${i}`} x1="0" x2="400" y1={i * 50} y2={i * 50} />)}{Array.from({ length: 9 }, (_, i) => <line key={`v${i}`} y1="0" y2="400" x1={i * 50} x2={i * 50} />)}</g>
        <g className="gx-plume">{[150, 200, 250].map((x, i) => <path key={x} d={`M${x} 390 C${x + (CX - x) * .3} 300 ${x + (CX - x) * .6} 160 ${x + (CX - x) * .4} 0`} fill="none" stroke="#8c9eae" strokeOpacity=".35" strokeWidth="1.2" strokeDasharray={`${8 + i * 2} 24`} />)}</g>
        {[0, 1, 2].map(i => <circle key={i} className="gx-ring" cx={CX} cy={CY} r={120 + i * 28} fill="none" stroke="#228bdf" strokeOpacity=".5" strokeDasharray="3 7" style={{ transformOrigin: `${CX}px ${CY}px`, opacity: 0 }} />)}
        <g className="gx-dots">{Array.from({ length: PARTICLES }, (_, i) => <circle key={i} className="gx-dot" cx={CX} cy={CY} r="1.6" fill={i % 4 ? '#77c3ed' : '#f2f3ed'} opacity="0" />)}</g>
        <g className="gx-flame" filter="url(#gxGlow)">
          <g className="gx-flame-body" style={{ transformOrigin: `${CX}px ${CY + 40}px` }}>
            <path className="gx-outer gx-warm" d={SHAPES[0][0]} fill="url(#gxWarmO)" />
            <path className="gx-outer gx-cool" d={SHAPES[0][0]} fill="url(#gxCoolO)" opacity="0" />
            <path className="gx-inner gx-warm" d={SHAPES[0][1]} fill="url(#gxWarmI)" opacity=".85" />
            <path className="gx-inner gx-cool" d={SHAPES[0][1]} fill="url(#gxCoolI)" opacity="0" />
          </g>
        </g>
        <circle cx={CX} cy={CY} r="9" fill="#1b2632" stroke="#8c9eae" strokeWidth="1" />
        <g className="gx-g" transform="translate(360 70)"><text x="0" y="-12" textAnchor="middle">{mode === 0 ? 'g' : 'g ≈ 0'}</text><g className="gx-g-arrow" style={{ transformOrigin: '0px 0px' }}><line x1="0" y1="0" x2="0" y2="60" /><path d="M-6 52 L0 64 L6 52" /></g></g>
      </svg>
      <figcaption>{t.source}</figcaption>
    </figure>
  </section>;
}
