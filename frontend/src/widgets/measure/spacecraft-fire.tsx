'use client';
import { useEffect, useMemo, useRef, useState } from 'react';
import Link from 'next/link';
import { animate, onScroll, stagger, type JSAnimation } from 'animejs';
import { prefersReducedMotion } from '@/shared/motion/anime';
import { asset } from '@/shared/config';
import evidence from '@/entities/saffire/evidence.json';
import { saffireFlameAt as flameAt, saffireLoocv, saffireMission } from '@/entities/saffire/mission';
import type { SpacecraftCopy } from './spacecraft-copy';
import { CargoCraft, CraftDefs, CRAFT_CARGO_CENTER_X } from './spacecraft-model';
import './measure.css';
import './spacecraft.css';

type Point = [number, number];
const model = evidence.model;
// Scroll milestones (0–1) of the pinned sequence.
const M = { launch: .12, orbit: .24, zoom: .34, setup: .42, base: .48, burn: .88 };
const SAMPLE = { x0: 300, x1: 900, y: 350, h: 40 }, PX_PER_CM = (SAMPLE.x1 - SAMPLE.x0) / 29, SENSOR_X = 1000;
const clamp = (v: number, a = 0, b = 1) => Math.min(b, Math.max(a, v));
const seg = (p: number, a: number, b: number) => clamp((p - a) / (b - a));
const ease = (x: number) => x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2;
function rng(seed: number) { return () => { seed |= 0; seed = seed + 0x6D2B79F5 | 0; let t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
const STARS = (() => { const r = rng(7); return Array.from({ length: 90 }, () => [r() * 1200, r() * 560, r() * 1.4 + .3] as const); })();
const SMOKE = 44;
const LEAD_PX = saffireMission['II-7'].burnLengthCm * ((900 - 300) / 29);
const CRAFT_START = .2, CRAFT_END = 1.25, ZX = 600 + CRAFT_CARGO_CENTER_X * CRAFT_END;

export function SpacecraftFire({ t, simulationHref }: { t: SpacecraftCopy; simulationHref?: string }) {
  const [id, setId] = useState('II-5'), [points, setPoints] = useState<Point[] | null>(null);
  const section = useRef<HTMLElement>(null), svgRef = useRef<SVGSVGElement>(null), hud = useRef<HTMLDivElement>(null), chart = useRef<SVGSVGElement>(null);
  const row = evidence.rows.find(r => r.id === id)!, c = row.conditions, mission = saffireMission[id];
  const opposed = c.flow_direction.value === 'opposed';
  const modelValue = row.material === 'Silicone' ? model.coefficients.silicone_location : model.coefficients.non_silicone_location * (20 / row.flow);
  const marker = new Date(c.ignition_epoch_ms.value as number).toISOString().replace('T', ' ').slice(0, 19);

  useEffect(() => {
    const ctrl = new AbortController();
    setPoints(null);
    fetch(asset(`/data/saffire/${id}.json`), { signal: ctrl.signal }).then(r => r.ok ? r.json() : Promise.reject()).then((d: { test_id?: string; points?: unknown }) => {
      if (d.test_id === id && Array.isArray(d.points) && d.points.every(p => Array.isArray(p) && p.length === 2 && p.every(Number.isFinite))) setPoints(d.points as Point[]);
    }).catch(() => undefined);
    return () => ctrl.abort();
  }, [id]);

  // Mini CO₂ chart geometry for [-30, 180] s from the real series.
  const mini = useMemo(() => {
    if (!points) return null;
    const view = points.filter(([x]) => x >= -30 && x <= 180), vs = view.map(p => p[1]);
    const lo = Math.min(...vs, row.baseline), hi = Math.max(...vs, row.baseline + row.actual), pad = (hi - lo) * .15 || 5;
    const X = (v: number) => 8 + ((v + 30) / 210) * 284, Y = (v: number) => 92 - ((v - (lo - pad)) / (hi - lo + 2 * pad)) * 80;
    return { d: view.map((p, i) => `${i ? 'L' : 'M'}${X(p[0]).toFixed(1)} ${Y(p[1]).toFixed(1)}`).join(''), X, Y };
  }, [points, row]);

  useEffect(() => {
    const el = section.current!, s = svgRef.current!, h = hud.current!;
    const reduced = prefersReducedMotion();
    const q = <T extends Element>(sel: string) => s.querySelector<T>(sel)!;
    const scA = q<SVGGElement>('.sc-a'), scB = q<SVGGElement>('.sc-b'), rocket = q<SVGGElement>('.sc-rocket'), craft = q<SVGGElement>('.sc-craft');
    const fairL = q<SVGGElement>('.sc-fair-l'), fairR = q<SVGGElement>('.sc-fair-r'), gores = [...s.querySelectorAll<SVGGElement>('.cr-gore')], callouts = q<SVGGElement>('.cr-callouts'), glints = [...s.querySelectorAll<SVGCircleElement>('.cr-array-glint')], earth = q<SVGGElement>('.sc-earth');
    const flame = q<SVGGElement>('.sc-flame'), burnt = q<SVGRectElement>('.sc-burnt'), regress = q<SVGRectElement>('.sc-regress'), ign = q<SVGGElement>('.sc-ign');
    const beads = [...s.querySelectorAll<SVGCircleElement>('.sc-bead')], smoke = [...s.querySelectorAll<SVGCircleElement>('.sc-smoke')], sensor = q<SVGRectElement>('.sc-co2-box');
    const stages = [...h.querySelectorAll<HTMLElement>('.sc-stage')], out = (k: string) => h.querySelector<HTMLElement>(`[data-o="${k}"]`)!;
    const clip = chart.current?.querySelector<SVGRectElement>('.sc-mini-clip'), cursor = chart.current?.querySelector<SVGLineElement>('.sc-mini-cursor');
    const calc = h.querySelector<HTMLElement>('.sc-calc')!, bar = el.querySelector<HTMLElement>('.sc-bar')!;
    const plumeK = clamp((mission.plumePeakC - 22) / (86 - 22));
    const intensity = clamp(Math.abs(row.actual) / 107, .35, 1);
    const live = { flameX: SAMPLE.x0, alive: 0, tSim: -999 };
    const reading = (time: number) => { if (!points) return null; let lo = 0, hi = points.length - 1; if (time < points[0][0]) return null; while (lo < hi) { const m = (lo + hi + 1) >> 1; if (points[m][0] <= time) lo = m; else hi = m - 1; } return points[lo][1]; };

    const render = (p: number) => {
      // Scene A: launch, separation, orbit.
      const up = ease(seg(p, 0, M.launch)), sep = ease(seg(p, .09, .15)), fall = ease(seg(p, .14, .22)), dep = ease(seg(p, .15, M.orbit)), zoom = ease(seg(p, M.orbit, M.zoom));
      rocket.setAttribute('transform', `translate(${600 - fall * 120} ${820 - up * 380 + fall * 520}) rotate(${-fall * 24})`);
      rocket.style.opacity = String(1 - seg(p, .14, .18));
      fairL.setAttribute('transform', `translate(${-sep * 70} ${sep * 30}) rotate(${-sep * 55} -22 -200)`); fairR.setAttribute('transform', `translate(${sep * 70} ${sep * 30}) rotate(${sep * 55} 22 -200)`);
      fairL.style.opacity = fairR.style.opacity = String(1 - seg(p, .13, .17));
      const cy = 440 - 250 + dep * (300 - 190);
      craft.setAttribute('transform', `translate(600 ${p < .1 ? 820 - up * 380 - 250 : cy}) scale(${CRAFT_START + dep * (CRAFT_END - CRAFT_START)})`);
      craft.style.opacity = String(seg(p, .1, .13));
      // Fan-type arrays open gore by gore.
      const fan = ease(seg(p, .16, .23));
      gores.forEach(g => { const i = Number(g.dataset.i); g.setAttribute('transform', `rotate(${i * 36 * fan})`); g.style.opacity = String(i === 0 ? Math.min(1, .3 + fan) : fan > 0 ? 1 : 0); });
      glints.forEach(g => { g.style.visibility = fan > .99 ? 'visible' : 'hidden'; });
      callouts.style.opacity = String(seg(p, .19, .215) * (1 - seg(p, M.orbit, M.orbit + .025)));
      earth.setAttribute('transform', `translate(0 ${180 - dep * 180})`);
      scA.setAttribute('transform', `translate(${ZX} 300) scale(${1 + zoom * 9}) translate(${-ZX} -300)`);
      scA.style.opacity = String(1 - seg(p, M.orbit + .05, M.zoom));
      scB.style.opacity = String(seg(p, M.orbit + .04, M.zoom));
      scB.setAttribute('transform', `translate(600 350) scale(${.55 + .45 * zoom}) translate(-600 -350)`);

      // Simulated time from ignition.
      const tSim = p < M.setup ? -999 : p < M.base ? -30 + 30 * seg(p, M.setup, M.base) : 180 * seg(p, M.base, M.burn);
      live.tSim = tSim;
      const f = flameAt(id, tSim), dir = opposed ? -1 : 1, x0 = opposed ? SAMPLE.x1 : SAMPLE.x0;
      const fx = x0 + dir * f.x * PX_PER_CM;
      live.flameX = fx; live.alive = f.alive;
      flame.setAttribute('transform', `translate(${fx} ${SAMPLE.y}) scale(${dir * 1.45} 1.45)`);
      flame.style.opacity = String(f.alive);
      const bw = f.burnt * PX_PER_CM;
      burnt.setAttribute('x', String(opposed ? SAMPLE.x1 - bw : SAMPLE.x0)); burnt.setAttribute('width', String(bw));
      regress.style.opacity = String(f.regress * .85);
      ign.style.opacity = String(.25 + .75 * f.pulse);
      beads.forEach(b => { const d = Math.abs(Number(b.dataset.x) - fx) / 600, heat = f.alive * plumeK * Math.max(0, 1 - d * 2.2); b.style.fill = `rgb(${Math.round(60 + 195 * heat)},${Math.round(80 + 100 * heat)},${Math.round(110 - 70 * heat)})`; });
      const sensed = clamp(seg(tSim, 0, 60) * intensity);
      sensor.style.stroke = `rgba(255,${Math.round(179 - 89 * sensed)},71,${.35 + .65 * sensed})`;

      // HUD
      const stage = p < M.launch ? 0 : p < M.orbit ? 1 : p < M.setup ? 2 : p < M.base ? 3 : p < .55 ? 4 : p < M.burn ? 5 : 6;
      stages.forEach((st, i) => st.classList.toggle('is-on', i === stage));
      const r = tSim > -999 ? reading(tSim) : null;
      out('time').textContent = tSim > -999 ? `${tSim >= 0 ? '+' : '−'}${Math.abs(tSim).toFixed(1)} s` : '—';
      out('co2').textContent = r !== null ? `${r.toFixed(1)} ppm` : '—';
      out('delta').textContent = r !== null ? `${r - row.baseline >= 0 ? '+' : '−'}${Math.abs(r - row.baseline).toFixed(1)} ppm` : '—';
      out('front').textContent = !mission.spreadRateMmS ? t.labels.none : tSim >= 0 ? `${(Math.min(29, mission.spreadRateMmS * tSim / 10)).toFixed(1)} / 29 cm` : '—';
      if (mini && clip && cursor) { const x = tSim > -999 ? mini.X(Math.min(180, tSim)) : 8; clip.setAttribute('width', String(Math.max(0, x - 8))); cursor.setAttribute('x1', String(x)); cursor.setAttribute('x2', String(x)); }
      calc.classList.toggle('is-on', p >= M.burn);
      bar.style.setProperty('--sc-p', p.toFixed(4));
    };

    const loops: JSAnimation[] = [];
    if (reduced) { render(.95); return; }
    render(0);
    const state = { p: 0 };
    loops.push(animate(state, { p: [0, 1], ease: 'linear', autoplay: onScroll({ target: el, enter: 'start start', leave: 'end end', sync: .12 }), onUpdate: () => render(state.p) }));
    loops.push(animate(s.querySelectorAll('.sc-exhaust'), { scaleY: [1, 1.25], scaleX: [1, .9], opacity: [.8, 1], duration: 120, loop: true, alternate: true, ease: 'inOut(2)' }));
    loops.push(animate(s.querySelectorAll('.sc-star'), { opacity: [.2, 1], duration: 1600, delay: stagger(40, { from: 'random' }), loop: true, alternate: true, ease: 'inOut(2)' }));
    // Spacecraft life: attitude drift, navigation lights, strobe, RCS puffs, sun glints.
    loops.push(animate(q('.cr-body'), { rotate: [-1.8, 1.8], translateY: [-4, 4], duration: 7000, loop: true, alternate: true, ease: 'inOut(2)' }));
    loops.push(animate(s.querySelectorAll('.cr-nav'), { opacity: [1, .15], duration: 900, delay: stagger(450), loop: true, alternate: true, ease: 'inOut(4)' }));
    loops.push(animate(q('.cr-strobe'), { opacity: [0, 1, 0], scale: [1, 2.4, 1], duration: 300, loopDelay: 1800, loop: true, ease: 'out(2)' }));
    loops.push(animate(s.querySelectorAll('.cr-puff'), { opacity: [0, .8, 0], scale: [.4, 2.2], duration: 650, delay: stagger(1700), loopDelay: 5200, loop: true, ease: 'out(3)' }));
    loops.push(animate(s.querySelectorAll('.cr-array-glint'), { opacity: [0, .55, 0], duration: 2600, delay: stagger(1300), loopDelay: 2400, loop: true, ease: 'inOut(2)' }));
    loops.push(animate(q('.cr-glint'), { opacity: [.25, .65], translateX: [-10, 14], duration: 5200, loop: true, alternate: true, ease: 'inOut(2)' }));
    loops.push(animate(q('.sc-fan'), { rotate: 360, duration: 900, loop: true, ease: 'linear' }));
    loops.push(animate(s.querySelectorAll('.sc-flow path'), { strokeDashoffset: [0, -60], duration: 900, loop: true, ease: 'linear' }));
    loops.push(animate(q('.sc-flame-body'), { scaleX: [1, 1.08, .96, 1.04, 1], scaleY: [1, .94, 1.05, .97, 1], duration: 900, loop: true, ease: 'inOut(2)' }));
    loops.push(animate(s.querySelectorAll('.sc-spark'), { translateX: [0, 46], translateY: () => [0, (Math.random() - .5) * 30], opacity: [1, 0], duration: 700, delay: stagger(120), loop: true, ease: 'out(2)' }));
    loops.push(animate(q('.sc-ign-glow'), { r: [10, 16], opacity: [.5, 1], duration: 300, loop: true, alternate: true }));
    // Combustion products: a continuous stream from the live flame position to the CO₂ sensor.
    const ph = { v: 0 };
    loops.push(animate(ph, { v: [0, 1], duration: 2800, loop: true, ease: 'linear', onUpdate: () => {
      const level = live.tSim > 0 ? Math.max(live.alive, .25 * clamp(live.tSim / 30)) * intensity : 0;
      smoke.forEach((dot, i) => {
        const jit = (Math.sin(i * 12.9898) * 43758.5453) % 1, k = (ph.v + jit + 1) % 1, sx = live.flameX, x = sx + (SENSOR_X - sx) * k, y = SAMPLE.y - 6 + (((Math.sin(i * 78.233) * 43758.5453) % 1)) * 46 * k + Math.sin(k * 9 + i) * 5;
        dot.setAttribute('cx', x.toFixed(1)); dot.setAttribute('cy', y.toFixed(1)); dot.setAttribute('r', (1.6 + k * 4.5).toFixed(2));
        dot.style.opacity = String(Math.min(1, level * Math.sin(Math.PI * k) * 1.1));
      });
    } }));
    return () => loops.forEach(a => a.revert());
  }, [id, points, mini, row, mission, opposed, t.labels.none]);

  const beadsX = [380, 480, 580, 680, 780, 880];
  return <section ref={section} className="sc-section" aria-labelledby="sc-title">
    <div className="sc-sticky">
      <div className="sc-stage-wrap">
        <header className="sc-head"><p className="eyebrow">{t.index}</p><h2 id="sc-title" data-fx-skip>{t.title}</h2><p className="sc-intro">{t.intro}</p>{simulationHref && <Link className="sc-sim-link" href={simulationHref}><i aria-hidden="true" /><span><b>{t.simulate}</b><small>{t.simulateNote}</small></span><em aria-hidden="true">→</em></Link>}</header>
        <svg ref={svgRef} className="sc-svg" viewBox="0 0 1200 700" role="img" aria-label={`${t.title} ${id}: ${t.outcomes[mission.outcome]}`}>
          <defs>
            <radialGradient id="scEarth" cx="50%" cy="20%" r="80%"><stop offset="0%" stopColor="#1d5f9a" /><stop offset="55%" stopColor="#0b2a4a" /><stop offset="100%" stopColor="#020305" /></radialGradient>
            <linearGradient id="scExhaust" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#fff3c4" /><stop offset="35%" stopColor="#ffb347" /><stop offset="100%" stopColor="#c81936" stopOpacity="0" /></linearGradient>
            <CraftDefs />
            <radialGradient id="scSun"><stop offset="0%" stopColor="#fff8e1" stopOpacity=".9" /><stop offset="18%" stopColor="#ffd27a" stopOpacity=".35" /><stop offset="100%" stopColor="#ffd27a" stopOpacity="0" /></radialGradient>
            <radialGradient id="scFlameO" cx="35%" cy="50%" r="65%"><stop offset="0%" stopColor="#fff3c4" /><stop offset="40%" stopColor="#ffb347" /><stop offset="80%" stopColor="#ff5a3d" stopOpacity=".7" /><stop offset="100%" stopColor="#c81936" stopOpacity="0" /></radialGradient>
            <linearGradient id="scRegress" x1="0" x2="1"><stop offset="0%" stopColor="#2a0a10" /><stop offset="100%" stopColor="#2a0a10" stopOpacity="0" /></linearGradient>
            <filter id="scGlow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="7" result="b" /><feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge></filter>
          </defs>

          <g className="sc-a">
            {STARS.map(([x, y, r], i) => <circle key={i} className="sc-star" cx={x} cy={y} r={r} />)}
            <circle cx="1060" cy="70" r="260" fill="url(#scSun)" />
            <path d="M-100 520 Q600 360 1300 520" fill="none" stroke="#77c3ed" strokeOpacity=".18" strokeDasharray="3 10" />
            <g className="sc-earth"><circle cx="600" cy="1500" r="980" fill="url(#scEarth)" /><circle cx="600" cy="1500" r="986" fill="none" stroke="#77c3ed" strokeOpacity=".55" strokeWidth="5" filter="url(#scGlow)" /></g>
            <g className="sc-rocket" transform="translate(600 820)">
              <g className="sc-exhaust" style={{ transformOrigin: '0px 0px' }}><path d="M-16 0 Q0 160 16 0 Z" fill="url(#scExhaust)" /></g>
              <path d="M-22 -40 L-46 6 L-22 0 Z M22 -40 L46 6 L22 0 Z" fill="#8c9eae" />
              <rect x="-22" y="-200" width="44" height="200" rx="5" fill="#d8dde3" /><rect x="-22" y="-120" width="44" height="6" fill="#228bdf" /><rect x="-22" y="-60" width="44" height="4" fill="#c81936" />
              <g className="sc-fair-l"><path d="M-22 -200 L-22 -250 Q-22 -300 0 -322 L0 -200 Z" fill="#eef1f4" stroke="#8c9eae" /></g>
              <g className="sc-fair-r"><path d="M22 -200 L22 -250 Q22 -300 0 -322 L0 -200 Z" fill="#e2e6ea" stroke="#8c9eae" /></g>
            </g>
            <g className="sc-craft" transform="translate(600 300)"><CargoCraft labels={t.craft} /></g>
            <text x="1180" y="684" textAnchor="end" className="sc-note">{t.scene.orbit}</text>
          </g>

          <g className="sc-b" style={{ opacity: 0 }}>
            <rect x="40" y="90" width="1120" height="540" rx="70" className="sc-hull" />
            {Array.from({ length: 11 }, (_, i) => <line key={i} x1={130 + i * 94} x2={130 + i * 94} y1="100" y2="620" className="sc-rib" />)}
            <rect x="150" y="200" width="900" height="300" rx="6" className="sc-duct" />
            <text x="160" y="190" className="sc-label">{t.scene.duct}</text>
            <g transform="translate(190 350)"><circle r="40" className="sc-fan-ring" /><g className="sc-fan">{[0, 1, 2, 3].map(i => <path key={i} d="M0 0 L34 -9 L34 9 Z" transform={`rotate(${i * 90})`} fill="#5c7183" />)}</g></g>
            <g className="sc-flow">{[230, 280, 420, 470].map(y => <path key={y} d={`M250 ${y} H1040`} />)}</g>
            <text x="250" y="222" className="sc-label sc-label-dim">{t.scene.flowWord} → {row.flow.toFixed(2)} cm/s</text>
            <rect x={SAMPLE.x0} y={SAMPLE.y - SAMPLE.h / 2} width={SAMPLE.x1 - SAMPLE.x0} height={SAMPLE.h} className={`sc-sample sc-mat-${row.material}`} />
            {row.material === 'PMMA_Nomex' && <><rect x={SAMPLE.x0 + LEAD_PX} y={SAMPLE.y - SAMPLE.h / 2} width={SAMPLE.x1 - SAMPLE.x0 - LEAD_PX} height={SAMPLE.h} className="sc-mat-nomex" /><text x={SAMPLE.x0 + 4} y={SAMPLE.y + 36} className="sc-label sc-label-dim">{t.scene.leadIn}</text><text x={SAMPLE.x0 + LEAD_PX + 6} y={SAMPLE.y + 36} className="sc-label sc-label-dim">{t.scene.nomex}</text></>}
            <rect className="sc-burnt" x={SAMPLE.x0} y={SAMPLE.y - SAMPLE.h / 2} width="0" height={SAMPLE.h} />
            <rect className="sc-regress" x={opposed ? SAMPLE.x1 - (mission.burnLengthCm * PX_PER_CM || 90) : SAMPLE.x0} y={SAMPLE.y - SAMPLE.h / 2} width={mission.burnLengthCm * PX_PER_CM || 90} height={SAMPLE.h} fill="url(#scRegress)" style={{ opacity: 0 }} transform={opposed ? `rotate(180 ${SAMPLE.x1 - 45} ${SAMPLE.y})` : undefined} />
            {Array.from({ length: 30 }, (_, i) => <line key={i} x1={SAMPLE.x0 + i * PX_PER_CM} x2={SAMPLE.x0 + i * PX_PER_CM} y1={SAMPLE.y + 24} y2={SAMPLE.y + (i % 5 ? 30 : 36)} className="sc-tick" />)}
            {[0, 5, 10, 15, 20, 25].map(v => <text key={v} x={SAMPLE.x0 + v * PX_PER_CM} y={SAMPLE.y + 50} textAnchor="middle" className="sc-note">{v}</text>)}
            <text x={SAMPLE.x1} y={SAMPLE.y + 50} textAnchor="end" className="sc-note">29 cm</text>
            <text x={(SAMPLE.x0 + SAMPLE.x1) / 2} y={SAMPLE.y - 34} textAnchor="middle" className="sc-label">{t.scene.sample}</text>
            <g className="sc-ign" transform={`translate(${opposed ? SAMPLE.x1 + 6 : SAMPLE.x0 - 6} ${SAMPLE.y})`}><circle className="sc-ign-glow" r="12" fill="#ff5a3d" opacity=".6" filter="url(#scGlow)" /><path d="M0 -18 L-5 -10 L5 -2 L-5 6 L5 14 L0 20" fill="none" stroke="#ffb347" strokeWidth="2.5" /><text y="-28" textAnchor="middle" className="sc-label">{t.scene.igniter}</text></g>
            {beadsX.map(x => <g key={x}><line x1={x} x2={x} y1="250" y2="300" className="sc-tc" /><circle className="sc-bead" data-x={x} cx={x} cy="302" r="5" /></g>)}
            <text x={beadsX[0] - 10} y="244" className="sc-label sc-label-dim">{t.scene.tc} ×6</text>
            <g transform="translate(600 470)"><rect x="-26" y="0" width="52" height="22" className="sc-box" /><path d="M-14 0 L0 -40 L14 0" className="sc-cone" /><text y="38" textAnchor="middle" className="sc-label sc-label-dim">{t.scene.radiometer}</text></g>
            <g className="sc-flame" filter="url(#scGlow)" style={{ opacity: 0 }}>
              <g className="sc-flame-body" style={{ transformOrigin: '0px 0px' }}>
                <ellipse cx="46" cy="-4" rx="86" ry="40" fill="#c81936" opacity=".22" />
                <ellipse cx="34" cy="-4" rx="62" ry="30" fill="url(#scFlameO)" />
                <ellipse cx="18" cy="-3" rx="34" ry="18" fill="#ffd27a" opacity=".75" />
                <ellipse cx="10" cy="-2" rx="16" ry="10" fill="#fff8e1" opacity=".9" />
                <path d="M-4 -26 Q-14 -2 -4 22" stroke="#77c3ed" strokeWidth="4" fill="none" />
                {[0, 1, 2, 3, 4].map(i => <circle key={i} className="sc-spark" cx={60 + i * 14} cy={-20 + (i % 3) * 16} r="1.8" fill="#ffd27a" />)}
              </g>
            </g>
            <g className="sc-smokes">{Array.from({ length: SMOKE }, (_, i) => <circle key={i} className="sc-smoke" cx="0" cy="0" r="2" style={{ opacity: 0 }} />)}</g>
            <rect x={SENSOR_X - 6} y={SAMPLE.y - 22} width="44" height="44" rx="4" className="sc-box sc-co2-box" /><text x={SENSOR_X + 16} y={SAMPLE.y + 5} textAnchor="middle" className="sc-label">{t.scene.co2}</text>
            <rect x={SENSOR_X - 6} y={SAMPLE.y - 92} width="44" height="36" rx="4" className="sc-box" /><text x={SENSOR_X + 16} y={SAMPLE.y - 69} textAnchor="middle" className="sc-label sc-label-dim">{t.scene.o2}</text>
            <text x="1140" y="618" textAnchor="end" className="sc-note">{t.scene.cutaway}</text>
          </g>
        </svg>
      </div>

      <aside ref={hud} className="sc-hud">
        <p className="eyebrow">{t.pick}</p>
        <div className="mx-chips sc-chips" role="radiogroup" aria-label="SAFFIRE-II">{evidence.rows.map(r => <button key={r.id} type="button" role="radio" aria-checked={r.id === id} onClick={() => setId(r.id)}>{r.id}</button>)}</div>
        <div className="sc-stages">{t.stages.map((st, i) => <article key={st.title} className={`sc-stage${i === 0 ? ' is-on' : ''}`}><p className="eyebrow">{String(i).padStart(2, '0')} · {st.tag}</p><h3>{st.title}</h3><p>{st.body}</p></article>)}</div>
        <div className="sc-live">
          <div><span>{t.labels.time}</span><b data-o="time">—</b></div>
          <div><span>{t.labels.co2}</span><b data-o="co2">—</b></div>
          <div className="mx-hot"><span>{t.labels.delta}</span><b data-o="delta">—</b></div>
          <div><span>{t.labels.front}</span><b data-o="front">—</b></div>
        </div>
        <svg ref={chart} className="sc-mini" viewBox="0 0 300 100" aria-hidden="true">
          <defs><clipPath id="scMiniClip"><rect className="sc-mini-clip" x="8" y="0" width="0" height="100" /></clipPath></defs>
          {mini && <>
            <rect x={mini.X(-30)} y="8" width={mini.X(0) - mini.X(-30)} height="86" className="sm-win-base" /><rect x={mini.X(150)} y="8" width={mini.X(180) - mini.X(150)} height="86" className="sm-win-resp" />
            <line x1="8" x2="292" y1={mini.Y(row.baseline)} y2={mini.Y(row.baseline)} className="sc-mini-base" />
            <path d={mini.d} clipPath="url(#scMiniClip)" className="sc-mini-line" />
            <line className="sc-mini-cursor" x1="8" x2="8" y1="6" y2="96" />
          </>}
        </svg>
        <dl className="sc-facts">
          <div><dt>{t.labels.material}</dt><dd>{t.materials[row.material] ?? row.material} · {c.thickness_nominal_mm.value as number} mm</dd></div>
          <div><dt>{t.labels.direction}</dt><dd>{t.directions[c.flow_direction.value as string]} · {row.flow.toFixed(2)} cm/s</dd></div>
          <div><dt>{t.labels.o2} · {t.labels.pressure}</dt><dd>{(c.o2_pre_sensor_pct.value as number).toFixed(2)} % · {(c.pressure_pre_kpa.value as number).toFixed(1)} kPa</dd></div>
          <div><dt>{t.labels.igniter}</dt><dd>{c.ignition_power_command_w.value as number} W × {c.ignition_duration_command_s.value as number} s</dd></div>
          <div><dt>{t.labels.marker}</dt><dd>{marker}</dd></div>
          <div><dt>{t.labels.outcome}</dt><dd>{t.outcomes[mission.outcome]}</dd></div>
          <div><dt>{t.labels.rate}</dt><dd>{mission.spreadRateMmS ? `${mission.spreadRateMmS} mm/s` : t.labels.none}</dd></div>
          <div><dt>{t.labels.plume}</dt><dd>{mission.plumePeakC.toFixed(1)} °C</dd></div>
        </dl>
        <div className="sc-calc">
          <p className="eyebrow">{t.calc.title} · {id}</p>
          <p className="sc-eq"><span>{t.calc.delta}</span> = <em>{t.calc.response}</em> − <em>{t.calc.baseline}</em></p>
          <p className="sc-eq sc-eq-num">= {(row.baseline + row.actual).toFixed(1)} − {row.baseline.toFixed(1)} = <b>{row.actual >= 0 ? '+' : ''}{row.actual.toFixed(2)} ppm</b></p>
          <p className="eyebrow sc-sub">{t.calc.model}</p>
          <p className="sc-eq">ΔCO₂ = {model.coefficients.silicone_location.toFixed(3)} <small>({t.calc.silicone})</small> · {model.coefficients.non_silicone_location.toFixed(3)} × (20 / flow) <small>({t.calc.other})</small></p>
          <p className="sc-eq sc-eq-num">{t.calc.thisTest}: <b>{modelValue.toFixed(2)} ppm</b></p>
          <p className="eyebrow sc-sub">{t.calc.heldOut}</p>
          <p className="sc-eq sc-eq-num"><b>{row.predicted.toFixed(2)} ppm</b> · {t.calc.residual} {row.residual >= 0 ? '+' : ''}{row.residual.toFixed(2)} ppm</p>
          <p className="sc-eq">{t.calc.rmse}: <b>{saffireLoocv.rmse.toFixed(2)} ppm</b> vs {saffireLoocv.baselineRmse.toFixed(2)} ppm ({t.calc.baselineRmse}) · −{saffireLoocv.reductionPct.toFixed(1)}%</p>
          <p className="sc-caveat">{t.calc.caveat}</p>
        </div>
        <p className="sc-motion">{t.motion}</p>
      </aside>
    </div>
    <i className="sc-bar" aria-hidden="true" />
    <p className="sc-source">{t.source}</p>
  </section>;
}
