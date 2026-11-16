'use client';
import { useEffect, useMemo, useRef, useState } from 'react';
import Link from 'next/link';
import { animate, stagger } from 'animejs';
import { asset } from '@/shared/config';
import type { Locale } from '@/shared/i18n';
import evidence from '@/entities/saffire/evidence.json';
import { saffireFlameAt, saffireLoocv, saffireMission } from '@/entities/saffire/mission';
import { spacecraftCopy } from '@/widgets/measure/spacecraft-copy';
import type { Explorer, Part, View } from './engine';
import { explorerCopy, type ExplorerCopy } from './copy';

type Point = [number, number];
type Phase = 'idle' | 'running' | 'paused' | 'done';
type Toast = { id: number; text: string; kind: 'event' | 'hot' | 'goal' | 'verdict' };
const rows = evidence.rows;
const coef = evidence.model.coefficients;
const GOALS = ['approach', 'inspect', 'open', 'test', 'ignite', 'spread', 'measure'] as const;
const STEPS = ['forecast', 'baseline', 'burn', 'response', 'verdict'] as const;
const RMSE = saffireLoocv.rmse;
const fill = (s: string, v: Record<string, string | number>) => s.replace(/\{(\w+)\}/g, (_, k) => String(v[k] ?? ''));
const sign = (v: number, d = 2) => `${v >= 0 ? '+' : '−'}${Math.abs(v).toFixed(d)}`;
const lastAt = (pts: Point[], t: number) => { if (t < pts[0][0]) return null; let lo = 0, hi = pts.length - 1; while (lo < hi) { const m = (lo + hi + 1) >> 1; if (pts[m][0] <= t) lo = m; else hi = m - 1; } return pts[lo][1]; };
const reduced = () => typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
const stepAt = (phase: Phase, time: number) => (phase === 'idle' ? 0 : time < 0 ? 1 : time < 150 ? 2 : time < 180 ? 3 : 4);

/** Decoding text effect for HUD titles. */
function useScramble(text: string) {
  const [out, setOut] = useState(text);
  useEffect(() => {
    if (reduced()) { setOut(text); return; }
    const glyphs = '▓▒░<>/#01Δ'; let f = 0, raf = 0;
    const tick = () => { f++; const n = Math.floor(f * 1.4); setOut(text.split('').map((ch, i) => (i < n || ch === ' ' ? ch : glyphs[(i + f) % glyphs.length])).join('')); if (n < text.length) raf = requestAnimationFrame(tick); };
    raf = requestAnimationFrame(tick); return () => cancelAnimationFrame(raf);
  }, [text]);
  return out;
}

export function ExplorerApp({ locale }: { locale: Locale }) {
  const t = explorerCopy[locale], sc = spacecraftCopy[locale];
  const [id, setId] = useState('II-5'), [points, setPoints] = useState<Point[] | null>(null);
  const [phase, setPhase] = useState<Phase>('idle'), [speed, setSpeed] = useState(8);
  const [cut, setCut] = useState(0), [explode, setExplode] = useState(0), [sun, setSun] = useState(28), [orbit, setOrbit] = useState(1), [beacons, setBeacons] = useState(true), [autoRot, setAutoRot] = useState(false);
  const [done, setDone] = useState<Set<string>>(new Set()), [picked, setPicked] = useState<Part | null>(null), [hover, setHover] = useState<{ p: Part; x: number; y: number } | null>(null);
  const [hud, setHud] = useState({ time: -40, reading: null as number | null, alive: 0, pulse: 0, sensed: 0, theta: 0, slow: false });
  const [status3d, setStatus3d] = useState<'loading' | 'ok' | 'fail'>('loading'), [ready, setReady] = useState(false);
  const [toasts, setToasts] = useState<Toast[]>([]), [flash, setFlash] = useState(0), [debrief, setDebrief] = useState(false);
  const stage = useRef<HTMLElement>(null), canvas = useRef<HTMLCanvasElement>(null), pip = useRef<HTMLCanvasElement>(null), overlay = useRef<HTMLDivElement>(null), engine = useRef<Explorer | null>(null);
  const simT = useRef(-40), prevT = useRef(-40), phaseRef = useRef(phase), speedRef = useRef(speed), cursor = useRef<SVGLineElement>(null), clipRect = useRef<SVGRectElement>(null), dot = useRef<SVGCircleElement>(null), clock = useRef<HTMLElement>(null);
  const doneRef = useRef<Set<string>>(new Set()), toastSeq = useRef(0), pendingIgnite = useRef(false);
  phaseRef.current = phase; speedRef.current = speed;

  const row = rows.find(r => r.id === id)!, c = row.conditions, mission = saffireMission[id];
  const D = c.ignition_duration_command_s.value as number, P = c.ignition_power_command_w.value as number;
  const utc = new Date(c.ignition_epoch_ms.value as number).toISOString().replace('T', ' ').slice(0, 19);
  const tEnd = points?.[points.length - 1][0] ?? 300, tMin = points?.[0][0] ?? -60;
  const within = Math.abs(row.residual) <= RMSE;

  const pushToast = (text: string, kind: Toast['kind'] = 'event') => {
    const tid = ++toastSeq.current; setToasts(ts => [...ts.slice(-3), { id: tid, text, kind }]);
    setTimeout(() => setToasts(ts => ts.filter(x => x.id !== tid)), kind === 'verdict' ? 6000 : 3800);
  };
  const toastRef = useRef(pushToast); toastRef.current = pushToast;
  const achieve = (g: string) => {
    if (doneRef.current.has(g)) return;
    doneRef.current = new Set(doneRef.current).add(g); setDone(doneRef.current);
    toastRef.current(`✓ ${t.toastGoal} · ${t.goals[g]}`, 'goal');
  };
  const achieveRef = useRef(achieve); achieveRef.current = achieve;

  useEffect(() => {
    const ctrl = new AbortController(); setPoints(null);
    fetch(asset(`/data/saffire/${id}.json`), { signal: ctrl.signal }).then(r => r.ok ? r.json() : Promise.reject()).then((d: { test_id?: string; points?: unknown }) => {
      if (d.test_id === id && Array.isArray(d.points) && d.points.every(p => Array.isArray(p) && p.length === 2 && p.every(Number.isFinite))) setPoints(d.points as Point[]);
    }).catch(() => undefined);
    simT.current = -40; prevT.current = -40; setPhase('idle');
    return () => ctrl.abort();
  }, [id]);

  // Engine lifecycle
  useEffect(() => {
    let alive = true;
    const probe = document.createElement('canvas');
    if (!(probe.getContext('webgl2') || probe.getContext('webgl'))) { setStatus3d('fail'); return; }
    import('./engine').then(({ createExplorer }) => {
      if (!alive || !canvas.current || !pip.current || !overlay.current) return;
      const beaconText = Object.fromEntries(Object.entries(t.parts).map(([k, v]) => [k, v[0]])) as Record<Part, string>;
      const e = createExplorer({
        canvas: canvas.current, pip: pip.current, overlay: overlay.current, beacons: beaconText,
        onPick: p => { setPicked(p); achieveRef.current('inspect'); }, onHover: (p, x, y) => setHover(p ? { p, x, y } : null),
        onCamera: d => { if (d < 7) achieveRef.current('approach'); },
      });
      e.onCutAuto(v => setCut(v)); engine.current = e; setSun(e.initialSun); setStatus3d('ok');
    }).catch(() => setStatus3d('fail'));
    return () => { alive = false; engine.current?.dispose(); engine.current = null; };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // HUD entrance: panels assemble once the spacecraft is on screen.
  useEffect(() => {
    if (status3d === 'loading') return;
    const timer = setTimeout(() => setReady(true), status3d === 'ok' ? 900 : 0);
    return () => clearTimeout(timer);
  }, [status3d]);
  useEffect(() => {
    if (!ready || !stage.current) return;
    if (reduced()) return;
    const panels = stage.current.querySelectorAll<HTMLElement>('.xp-panel:not(.xp-card):not(.xp-debrief), .xp-right');
    const a = animate(panels, { opacity: [0, 1], y: [18, 0], filter: ['blur(6px)', 'blur(0px)'], duration: 900, delay: stagger(110), ease: 'out(4)' });
    return () => { a.revert(); };
  }, [ready]);

  useEffect(() => { engine.current?.setSample({ material: row.material, opposed: c.flow_direction.value === 'opposed', leadInCm: row.material === 'PMMA_Nomex' ? mission.burnLengthCm : null, regressCm: mission.outcome === 'anchored_flame_slow_regression' ? mission.burnLengthCm : 0 }); }, [row, c, mission, status3d]);
  useEffect(() => { engine.current?.setCut(cut); if (cut > .3) achieveRef.current('open'); }, [cut, status3d]);
  useEffect(() => { engine.current?.setExplode(explode); if (explode > .3) achieveRef.current('open'); }, [explode, status3d]);
  useEffect(() => { engine.current?.setSun(sun); }, [sun, status3d]);
  useEffect(() => { engine.current?.setOrbitSpeed(orbit); }, [orbit, status3d]);
  useEffect(() => { engine.current?.setBeacons(beacons); }, [beacons, status3d]);
  useEffect(() => { engine.current?.setAutoRotate(autoRot); }, [autoRot, status3d]);

  // CO₂ chart with the team forecast band (baseline + Δ̂ ± RMSE) over the response window.
  const forecastLevel = row.baseline + row.predicted;
  const chart = useMemo(() => {
    if (!points) return null;
    const vs = points.map(p => p[1]).concat([forecastLevel + RMSE, forecastLevel - RMSE, row.baseline + row.actual]);
    const lo = Math.min(...vs), hi = Math.max(...vs), pad = (hi - lo) * .1 || 5;
    const X = (v: number) => 4 + ((v - tMin) / (tEnd - tMin)) * 292, Y = (v: number) => 86 - ((v - lo + pad) / (hi - lo + 2 * pad)) * 78;
    const step = Math.max(1, Math.floor(points.length / 500));
    return { X, Y, d: points.filter((_, i) => i % step === 0).map((p, i) => `${i ? 'L' : 'M'}${X(p[0]).toFixed(1)} ${Y(p[1]).toFixed(1)}`).join('') };
  }, [points, tMin, tEnd, forecastLevel, row]);

  const events = useMemo(() => {
    const ev: { t: number; text: string; hot?: boolean }[] = [
      { t: -30, text: t.events.armed }, { t: 0, text: fill(t.events.ignition, { utc }), hot: true }, { t: D, text: fill(t.events.igniterOff, { power: P, duration: D }) },
      { t: 150, text: t.events.response }, { t: 180, text: fill(t.events.delta, { delta: sign(row.actual) }), hot: true },
    ];
    if (mission.spreadRateMmS) ev.push({ t: 290 / mission.spreadRateMmS, text: fill(t.events.front, { rate: mission.spreadRateMmS }) });
    ev.push(mission.burnDurationS ? { t: mission.burnDurationS, text: fill(t.events.burnEnd, { duration: mission.burnDurationS, length: mission.burnLengthCm }) } : { t: D + 14, text: t.events.noSpread });
    return ev.sort((a, b) => a.t - b.t);
  }, [t, utc, D, P, row.actual, mission]);
  const eventsRef = useRef(events); eventsRef.current = events;
  const verdictText = fill(t.solution.captions.verdict, { actual: sign(row.actual), pred: sign(row.predicted), res: sign(row.residual), within: within ? t.solution.within : t.solution.outside });
  const verdictRef = useRef(verdictText); verdictRef.current = verdictText;

  // Simulation clock
  useEffect(() => {
    let raf = 0, last = performance.now(), lastHud = 0;
    const intensity = Math.min(1, Math.max(.35, Math.abs(row.actual) / 107)), heat = Math.min(1, Math.max(0, (mission.plumePeakC - 22) / 64));
    const loop = (now: number) => {
      const dt = Math.min(.1, (now - last) / 1000); last = now;
      // Automatic slow motion around ignition so the igniter and the first flame are always visible.
      const slow = simT.current > -3.2 && simT.current < 3 && speedRef.current > 1;
      if (phaseRef.current === 'running' && points) {
        simT.current += dt * (slow ? 1 : speedRef.current);
        if (simT.current >= tEnd) { simT.current = tEnd; setPhase('done'); setDebrief(true); }
      }
      const time = simT.current, running = phaseRef.current !== 'idle', prev = prevT.current; prevT.current = time;
      if (running && time > prev) {
        for (const e of eventsRef.current) if (prev < e.t && e.t <= time) toastRef.current(e.text, e.hot ? 'hot' : 'event');
        if (prev < 0 && time >= 0) { engine.current?.ignitionFx(); setFlash(k => k + 1); }
        if (prev < 180 && time >= 180) toastRef.current(verdictRef.current, 'verdict');
      }
      const f = running ? saffireFlameAt(id, time) : { x: 0, alive: 0, burnt: 0, regress: 0, pulse: 0 };
      const reading = points ? lastAt(points, time) : null;
      const sensed = reading === null || !running ? 0 : Math.min(1, Math.max(0, (reading - row.baseline) / Math.max(30, Math.abs(row.actual) * 1.3)));
      const frontLabel = f.alive > .05 && mission.outcome !== 'no_sustained_spread' && mission.outcome !== 'anchored_flame_slow_regression' ? fill(mission.spreadRateMmS ? t.front : t.frontInterp, { x: f.x.toFixed(1) }) : null;
      engine.current?.update({ flame: f, sensed, heat, intensity, reading, burning: running, frontLabel });
      if (chart) {
        const x = chart.X(Math.max(tMin, Math.min(tEnd, running ? time : tMin))).toFixed(1);
        cursor.current?.setAttribute('x1', x); cursor.current?.setAttribute('x2', x);
        clipRect.current?.setAttribute('width', String(Math.max(0, Number(x) - 4)));
        if (dot.current) { dot.current.setAttribute('cx', x); dot.current.setAttribute('cy', reading !== null && running ? chart.Y(reading).toFixed(1) : '-20'); }
      }
      if (clock.current) clock.current.textContent = `T${time >= 0 ? '+' : '−'}${Math.abs(time).toFixed(1).padStart(5, '0')}`;
      if (running && f.alive > .3 && time > 20) achieveRef.current('spread');
      if (running && time >= 180) achieveRef.current('measure');
      if (now - lastHud > 120) { lastHud = now; setHud({ time, reading, alive: f.alive, pulse: f.pulse, sensed, theta: engine.current?.theta() ?? 0, slow: slow && phaseRef.current === 'running' }); }
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id, points, chart, row, mission, tEnd, tMin]);

  const ignite = () => { simT.current = -30; prevT.current = -31; setDebrief(false); setPhase('running'); achieveRef.current('ignite'); engine.current?.focus('flame', 1800); };
  const togglePlay = () => { if (phase === 'idle' || phase === 'done') ignite(); else setPhase(p => (p === 'running' ? 'paused' : 'running')); };
  const reset = () => { simT.current = -40; prevT.current = -40; setPhase('idle'); setDebrief(false); };
  const chooseTest = (r: string) => { setId(r); setDebrief(false); achieveRef.current('test'); };
  const nextTest = () => { const i = rows.findIndex(r => r.id === id); pendingIgnite.current = true; chooseTest(rows[(i + 1) % rows.length].id); };
  useEffect(() => { if (points && pendingIgnite.current) { pendingIgnite.current = false; ignite(); } // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [points]);
  const view = (v: View) => engine.current?.focus(v);

  // Keyboard shortcuts handled by the UI (camera keys live in the engine)
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement)?.tagName; if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT' || tag === 'BUTTON') return;
      const k = e.key.toLowerCase();
      if (k === ' ') { e.preventDefault(); togglePlay(); }
      if (k === 'escape') { setDebrief(false); setPicked(null); }
      if (k === 'c') { const o = { v: cut }; animate(o, { v: cut > .3 ? 0 : .8, duration: 900, ease: 'inOut(3)', onUpdate: () => setCut(o.v) }); }
      if (k === 'x') { const o = { v: explode }; animate(o, { v: explode > .5 ? 0 : 1, duration: 900, ease: 'inOut(3)', onUpdate: () => setExplode(o.v) }); }
    };
    window.addEventListener('keydown', onKey); return () => window.removeEventListener('keydown', onKey);
  });

  const statusText = phase === 'idle' ? t.status.idle : phase === 'paused' ? t.status.paused : phase === 'done' ? t.status.done : hud.time < 0 ? `${t.status.armed}${Math.abs(hud.time).toFixed(0)} s` : t.status.burning;
  const partInfo = (p: Part) => fill(t.parts[p][1], {
    flow: row.flow.toFixed(2), dir: sc.directions[c.flow_direction.value as string], o2: (c.o2_pre_sensor_pct.value as number).toFixed(2), p: (c.pressure_pre_kpa.value as number).toFixed(1),
    material: sc.materials[row.material] ?? row.material, thickness: c.thickness_nominal_mm.value as number, outcome: sc.outcomes[mission.outcome], power: P, duration: D, plume: mission.plumePeakC.toFixed(1), delta: sign(row.actual),
  });
  const progress = done.size / GOALS.length;
  const rx = 60 + Math.cos(hud.theta) * 44, ry = 60 + Math.sin(hud.theta) * 44 * .55;
  const step = stepAt(phase, hud.time), measuredShown = phase !== 'idle' && hud.time >= 180;
  const caption = fill(t.solution.captions[STEPS[step]], { pred: sign(row.predicted), rmse: RMSE.toFixed(1), base: row.baseline.toFixed(1), power: P, duration: D, actual: sign(row.actual), res: sign(row.residual), within: within ? t.solution.within : t.solution.outside });
  const cardTitle = useScramble(picked ? t.parts[picked][0] : '');
  const countdown = phase === 'running' && hud.time > -3 && hud.time < 0 ? Math.ceil(-hud.time) : null;

  return <main id="main" className="xp">
    <header className="xp-head">
      <div><p className="eyebrow">{t.eyebrow}</p><h1 data-fx-skip>{t.title}</h1><p className="xp-intro">{t.intro}</p></div>
      <Link className="xp-back" href={`/${locale}/simulation/`}>{t.back}</Link>
    </header>

    <section ref={stage} className={`xp-stage${ready ? ' is-ready' : ''}${phase === 'running' && hud.alive > .05 ? ' is-burning' : ''}`} data-lenis-prevent aria-label={t.title} style={{ '--heat': (hud.alive * .9).toFixed(2) } as React.CSSProperties}>
      <canvas ref={canvas} className="xp-canvas" />
      <div ref={overlay} className="xp-overlay" />
      <div className="xp-fx" aria-hidden="true"><i className="xp-heat" /><i className="xp-scan" />
        {flash > 0 && <i key={flash} className="xp-flash" />}
        {flash > 0 && <b key={`w${flash}`} className="xp-ign-word">{t.ignition}</b>}
        {countdown !== null && <b key={countdown} className="xp-count">{countdown}</b>}
        {hud.slow && <em className="xp-slow">◉ {t.slowmo}</em>}
      </div>
      {(!ready || status3d === 'fail') && <div className={`xp-boot${status3d === 'ok' ? ' is-locked' : ''}`}>
        <i className="xp-boot-ring" /><p>{status3d === 'fail' ? t.webgl : status3d === 'ok' ? t.signalOk : t.signal}</p><i className="xp-boot-bar" />
      </div>}

      <aside className="xp-panel xp-goals">
        <div className="xp-goals-head"><p className="eyebrow">{t.objectives}</p><b>{done.size}/{GOALS.length}</b></div>
        <div className="xp-goals-bar"><i style={{ transform: `scaleX(${progress})` }} /></div>
        <ol>{GOALS.map(g => <li key={g} className={done.has(g) ? 'is-done' : ''}><i />{t.goals[g]}</li>)}</ol>
        {progress === 1 && <p className="xp-complete">★ {t.complete}</p>}
      </aside>

      <div className="xp-panel xp-clock">
        <span>{t.clock}</span><b ref={clock}>T−0040.0</b>
        <em className={`xp-phase xp-phase-${phase}`}>{statusText}</em>
        <small>{t.utc} · {utc} UTC</small>
      </div>

      <div className="xp-panel xp-pipeline" aria-live="polite">
        <p className="eyebrow">{t.solution.title}</p>
        <ol>{STEPS.map((s, i) => <li key={s} className={i < step ? 'is-past' : i === step ? 'is-now' : ''}><button type="button" onClick={() => { if (s === 'verdict' && measuredShown) setDebrief(true); }}>{t.solution.steps[s]}</button></li>)}</ol>
        <p key={`${step}-${id}`} className="xp-caption">{caption}</p>
      </div>

      <aside className="xp-right">
        <figure className="xp-panel xp-pip">
          <figcaption><span className="xp-rec" />{t.pip}</figcaption>
          <canvas ref={pip} />
          <p>{t.pipNote}</p>
        </figure>
        <div className="xp-panel xp-co2">
          <p className="eyebrow">{t.co2} · {id}</p>
          <div className="xp-read">
            <div><span>{t.reading}</span><b>{hud.reading !== null && phase !== 'idle' ? hud.reading.toFixed(1) : '—'}</b></div>
            <div className="xp-hot"><span>{t.solution.live}</span><b>{hud.reading !== null && phase !== 'idle' ? sign(hud.reading - row.baseline, 1) : '—'}</b></div>
            <div className="xp-fc"><span>{t.solution.forecast}</span><b>{sign(row.predicted, 1)}</b></div>
          </div>
          {chart && <svg viewBox="0 0 300 92" className="xp-chart" aria-hidden="true">
            <defs><clipPath id="xp-rec-clip"><rect ref={clipRect} x="4" y="0" width="0" height="92" /></clipPath></defs>
            <rect x={chart.X(-30)} y="6" width={chart.X(0) - chart.X(-30)} height="82" className="sm-win-base" /><rect x={chart.X(150)} y="6" width={chart.X(180) - chart.X(150)} height="82" className="sm-win-resp" />
            <rect x={chart.X(0)} width={chart.X(tEnd) - chart.X(0)} y={chart.Y(forecastLevel + RMSE)} height={chart.Y(forecastLevel - RMSE) - chart.Y(forecastLevel + RMSE)} className="xp-band" />
            <line x1={chart.X(0)} x2="296" y1={chart.Y(forecastLevel)} y2={chart.Y(forecastLevel)} className="xp-fline" />
            <line x1="4" x2="296" y1={chart.Y(row.baseline)} y2={chart.Y(row.baseline)} className="sc-mini-base" />
            <g clipPath="url(#xp-rec-clip)"><path d={chart.d} className="xp-line" /></g>
            {measuredShown && <circle cx={chart.X(165)} cy={chart.Y(row.baseline + row.actual)} r="4" className={`xp-mpt${within ? ' is-in' : ''}`} />}
            <line ref={cursor} y1="4" y2="90" className="xp-cursor" /><circle ref={dot} r="3" cx="-20" cy="-20" className="xp-dot" />
          </svg>}
          <p className="xp-legend"><i className="lg-line" />{t.co2.split('·')[0]}<i className="lg-band" />{t.solution.forecast} ±{RMSE.toFixed(1)}<i className="lg-base" />{t.solution.steps.baseline.replace(/^\d · /, '')}</p>
          <div className={`xp-verdict${measuredShown ? ' is-on' : ''}${within ? ' is-in' : ' is-out'}`}>
            <div><span>{t.solution.forecast}</span><b>{sign(row.predicted)}</b></div>
            <div><span>{t.solution.measured}</span><b>{measuredShown ? sign(row.actual) : t.solution.pending}</b></div>
            <div><span>{t.debrief.residual.split('(')[0]}</span><b>{measuredShown ? sign(row.residual) : '—'}</b></div>
          </div>
          {measuredShown && <button type="button" className="xp-report-btn" onClick={() => setDebrief(true)}>▤ {t.solution.report}</button>}
          <p className="xp-outcome"><span>{t.outcome}</span>{sc.outcomes[mission.outcome]} · {t.burn}: {mission.burnDurationS ? `${mission.burnDurationS} s · ${mission.burnLengthCm} cm` : t.insignificant} · {t.rate}: {mission.spreadRateMmS ? `${mission.spreadRateMmS} mm/s` : t.none}</p>
        </div>
      </aside>

      {picked && <div className="xp-panel xp-card" role="dialog" aria-label={t.parts[picked][0]} key={picked}>
        <button type="button" className="xp-x" onClick={() => setPicked(null)} aria-label="×">×</button>
        <p className="eyebrow">{cardTitle}</p><p>{partInfo(picked)}</p>
      </div>}
      {hover && <div className="xp-tip" style={{ left: hover.x, top: hover.y }}>{t.parts[hover.p][0]}</div>}

      <div className="xp-toasts" aria-live="polite">{toasts.map(x => <p key={x.id} className={`xp-toast xp-toast-${x.kind}`}>{x.text}</p>)}</div>

      <div className="xp-panel xp-radar" aria-label={t.radar}>
        <p className="eyebrow">{t.radar}</p>
        <svg viewBox="0 0 120 120" aria-hidden="true">
          <defs><linearGradient id="xp-sweep" x1="0" x2="1"><stop offset="0" stopColor="#77c3ed" stopOpacity="0" /><stop offset="1" stopColor="#77c3ed" stopOpacity=".45" /></linearGradient></defs>
          <circle cx="60" cy="60" r="56" className="xp-r-grid" /><circle cx="60" cy="60" r="36" className="xp-r-grid" />
          <g className="xp-r-sweep"><path d="M60 60 L116 60 A56 56 0 0 0 108 31 Z" fill="url(#xp-sweep)" /></g>
          <circle cx="60" cy="60" r="20" className="xp-r-earth" /><ellipse cx="60" cy="60" rx="44" ry="24" className="xp-r-orbit" /><circle cx={rx} cy={ry} r="4" className="xp-r-craft" /><circle cx={rx} cy={ry} r="9" className="xp-r-ping" />
        </svg>
        <div className="xp-views">{(['orbit', 'craft', 'rack', 'flame'] as View[]).map(v => <button key={v} type="button" onClick={() => view(v)}>{t.controls.views[v]}</button>)}</div>
      </div>

      <div className="xp-panel xp-dock">
        <div className="xp-tests"><span>{t.controls.test}</span>{rows.map(r => <button key={r.id} type="button" aria-pressed={r.id === id} onClick={() => chooseTest(r.id)}>{r.id}</button>)}</div>
        <div className="xp-main-ctl">
          <button type="button" className={`xp-ignite${phase === 'running' ? ' is-live' : ''}`} onClick={togglePlay}>{phase === 'idle' || phase === 'done' ? `🔥 ${t.controls.ignite}` : phase === 'running' ? `❚❚ ${t.controls.pause}` : `▶ ${t.controls.resume}`}</button>
          <button type="button" onClick={reset}>↺ {t.controls.reset}</button>
          <div className="xp-speed"><span>{t.controls.speed}</span>{[1, 4, 8, 20].map(s => <button key={s} type="button" aria-pressed={speed === s} onClick={() => setSpeed(s)}>{s}×</button>)}</div>
        </div>
        <div className="xp-sliders">
          <label><span>{t.controls.cut} <b>{Math.round(cut * 100)}%</b></span><input type="range" min="0" max="1" step=".01" value={cut} onChange={e => setCut(Number(e.target.value))} /></label>
          <label><span>{t.controls.explode} <b>{Math.round(explode * 100)}%</b></span><input type="range" min="0" max="1" step=".01" value={explode} onChange={e => setExplode(Number(e.target.value))} /></label>
          <label><span>{t.controls.sun} <b>{sun}°</b></span><input type="range" min="0" max="360" step="1" value={sun} onChange={e => setSun(Number(e.target.value))} /></label>
          <label><span>{t.controls.orbit} <b>{orbit.toFixed(1)}×</b></span><input type="range" min="0" max="6" step=".1" value={orbit} onChange={e => setOrbit(Number(e.target.value))} /></label>
        </div>
        <div className="xp-toggles"><button type="button" aria-pressed={beacons} onClick={() => setBeacons(v => !v)}>{t.controls.labels}</button><button type="button" aria-pressed={autoRot} onClick={() => setAutoRot(v => !v)}>{t.controls.autorotate}</button></div>
      </div>
      <p className="xp-keys">{t.keys}</p>

      {debrief && <Debrief t={t} id={id} caveat={sc.calc.caveat} onClose={() => setDebrief(false)} onNext={nextTest} onReplay={ignite} />}
    </section>

    <section className="xp-below">
      <div className="xp-log"><p className="eyebrow">{t.log}</p><ol>{events.filter(e => phase !== 'idle' && e.t <= hud.time).reverse().map(e => <li key={e.text} className={e.hot ? 'is-hot' : ''}><b>T{e.t >= 0 ? '+' : '−'}{Math.abs(e.t).toFixed(1)} s</b>{e.text}</li>)}</ol></div>
      <p className="xp-disclaimer">{t.disclaimer}</p>
    </section>
  </main>;
}

/** End-of-run report: the team's held-out forecast against the measurement, across all nine tests. */
function Debrief({ t, id, caveat, onClose, onNext, onReplay }: { t: ExplorerCopy; id: string; caveat: string; onClose: () => void; onNext: () => void; onReplay: () => void }) {
  const d = t.debrief, row = rows.find(r => r.id === id)!, m = saffireMission[id], within = Math.abs(row.residual) <= RMSE;
  const root = useRef<HTMLDivElement>(null);
  const vals = [...rows.map(r => r.predicted), ...rows.map(r => r.actual)], lo = Math.floor(Math.min(...vals) / 10) * 10 - 10, hi = Math.ceil(Math.max(...vals) / 10) * 10 + 10;
  const S = (v: number) => 30 + ((v - lo) / (hi - lo)) * 220, Sy = (v: number) => 230 - ((v - lo) / (hi - lo)) * 220;
  const band = `${S(lo)},${Sy(lo + RMSE)} ${S(hi - RMSE)},${Sy(hi)} ${S(hi)},${Sy(hi)} ${S(hi)},${Sy(hi - RMSE)} ${S(lo + RMSE)},${Sy(lo)} ${S(lo)},${Sy(lo)}`;
  const t0 = Math.ceil(lo / 20) * 20, ticks = Array.from({ length: Math.floor((hi - t0) / 20) + 1 }, (_, i) => t0 + i * 20);
  useEffect(() => {
    const el = root.current; if (!el) return;
    const counters = [...el.querySelectorAll<HTMLElement>('[data-to]')];
    if (reduced()) { counters.forEach(c => { c.textContent = c.dataset.final!; }); return; }
    const anims = counters.map(c => { const o = { v: 0 }, to = Number(c.dataset.to), dec = Number(c.dataset.dec ?? 2); return animate(o, { v: to, duration: 1400, ease: 'out(4)', onUpdate: () => { c.textContent = `${o.v >= 0 && c.dataset.sign ? '+' : o.v < 0 ? '−' : ''}${Math.abs(o.v).toFixed(dec)}`; }, onComplete: () => { c.textContent = c.dataset.final!; } }); });
    anims.push(animate(el.querySelectorAll('.xp-db-pt:not(.is-cur)'), { r: [0, 3.6], opacity: [0, 1], delay: stagger(70, { start: 300 }), duration: 600, ease: 'out(3)' }));
    anims.push(animate(el.querySelectorAll('.xp-db-pt.is-cur'), { r: [0, 9, 6], opacity: [0, 1], delay: 1000, duration: 900, ease: 'out(3)' }));
    anims.push(animate(el.querySelectorAll('.xp-db-bar i'), { scaleX: [0, 1], delay: stagger(200, { start: 400 }), duration: 1100, ease: 'out(4)' }));
    anims.push(animate(el.querySelectorAll('.xp-db-block'), { opacity: [0, 1], y: [16, 0], delay: stagger(90), duration: 700, ease: 'out(3)' }));
    return () => anims.forEach(a => a.revert());
  }, [id]);
  const num = (v: number, dec = 2, signed = true) => ({ 'data-to': v, 'data-dec': dec, 'data-sign': signed ? '1' : undefined, 'data-final': signed ? sign(v, dec) : v.toFixed(dec) });
  return <div className="xp-debrief-wrap" onClick={e => { if (e.target === e.currentTarget) onClose(); }}>
    <div ref={root} className="xp-panel xp-debrief" role="dialog" aria-label={fill(d.title, { id })}>
      <button type="button" className="xp-x" onClick={onClose} aria-label={d.close}>×</button>
      <p className="eyebrow">{t.solution.title}</p>
      <h2>{fill(d.title, { id })}</h2>
      <div className="xp-db-grid">
        <div className="xp-db-block xp-db-kpis">
          <div><span>{d.forecast}</span><b {...num(row.predicted)}>{sign(row.predicted)}</b><small>ppm · LOOCV</small></div>
          <div className="is-hot"><span>{d.measured}</span><b {...num(row.actual)}>{sign(row.actual)}</b><small>ppm</small></div>
          <div className={within ? 'is-in' : 'is-out'}><span>{d.residual}</span><b {...num(row.residual)}>{sign(row.residual)}</b><small>{within ? t.solution.within : t.solution.outside} (±{RMSE.toFixed(2)})</small></div>
        </div>
        <figure className="xp-db-block xp-db-scatter">
          <figcaption>{d.scatter}</figcaption>
          <svg viewBox="0 0 260 260" role="img" aria-label={d.scatter}>
            {ticks.map(v => <g key={v}><line x1={S(v)} x2={S(v)} y1="10" y2="230" className="xp-db-gl" /><line x1="30" x2="250" y1={Sy(v)} y2={Sy(v)} className="xp-db-gl" /><text x={S(v)} y="244" textAnchor="middle">{v}</text><text x="25" y={Sy(v) + 3} textAnchor="end">{v}</text></g>)}
            <polygon points={band} className="xp-db-band" />
            <line x1={S(lo)} y1={Sy(lo)} x2={S(hi)} y2={Sy(hi)} className="xp-db-ideal" />
            {rows.map(r => <g key={r.id}><circle className={`xp-db-pt${r.id === id ? ' is-cur' : ''}${r.material === 'Silicone' ? ' is-sil' : ''}`} cx={S(r.predicted)} cy={Sy(r.actual)} r={r.id === id ? 6 : 3.6} />{r.id === id && <text x={S(r.predicted) + 9} y={Sy(r.actual) + 4} className="xp-db-lbl">{r.id}</text>}</g>)}
            <text x="140" y="258" textAnchor="middle" className="xp-db-ax">{d.axisX} →</text>
            <text x="8" y="120" textAnchor="middle" className="xp-db-ax" transform="rotate(-90 8 120)">{d.axisY} →</text>
          </svg>
          <p className="xp-db-key"><i className="k-ideal" />{d.ideal}<i className="k-band" />{d.band}<i className="k-sil" />{explorerSil(t)}<i className="k-oth" />{explorerOther(t)}</p>
        </figure>
        <div className="xp-db-block xp-db-rmse">
          <p className="eyebrow">{d.rmse}</p>
          <div className="xp-db-bar is-model"><span>{d.model}</span><i style={{ width: `${(saffireLoocv.rmse / saffireLoocv.baselineRmse) * 100}%` }} /><b>{saffireLoocv.rmse.toFixed(2)} ppm</b></div>
          <div className="xp-db-bar"><span>{d.baseline}</span><i style={{ width: '100%' }} /><b>{saffireLoocv.baselineRmse.toFixed(2)} ppm</b></div>
          <p className="xp-db-better">▼ {fill(d.better, { pct: saffireLoocv.reductionPct.toFixed(1) })}</p>
          <p className="xp-db-formula">{fill(d.formula, { sil: coef.silicone_location.toFixed(3), k: coef.non_silicone_location.toFixed(3) })}</p>
        </div>
        <div className="xp-db-block xp-db-facts">
          <p className="eyebrow">{d.facts}</p>
          <dl>
            <div><dt>{d.plume}</dt><dd>{m.plumePeakC.toFixed(1)} °C</dd></div>
            <div><dt>{d.o2}</dt><dd>{sign(m.o2Change180Pp, 3)} pp</dd></div>
            <div><dt>{d.press}</dt><dd>{sign(m.pressureChange180KPa, 4)} kPa</dd></div>
            <div><dt>{d.rad}</dt><dd>{m.radiationPeak180KWm2.toFixed(3)} kW/m²</dd></div>
            <div><dt>{d.burnLen}</dt><dd>{m.burnDurationS ? `${m.burnLengthCm} cm · ${m.burnDurationS} s` : t.insignificant}</dd></div>
            <div><dt>{d.rate}</dt><dd>{m.spreadRateMmS ? `${m.spreadRateMmS} mm/s` : t.none}</dd></div>
          </dl>
        </div>
      </div>
      <p className="xp-db-caveat">{caveat}</p>
      <div className="xp-db-actions"><button type="button" onClick={onReplay}>{d.replay}</button><button type="button" className="is-primary" onClick={onNext}>{d.next}</button><button type="button" onClick={onClose}>{d.close}</button></div>
    </div>
  </div>;
}
const explorerSil = (t: ExplorerCopy) => t.solution.branchSilicone.split('·')[0].trim();
const explorerOther = (t: ExplorerCopy) => t.solution.branchOther.split('·')[0].trim();
