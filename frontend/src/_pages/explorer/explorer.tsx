'use client';
import { useEffect, useMemo, useRef, useState } from 'react';
import Link from 'next/link';
import { animate } from 'animejs';
import { asset } from '@/shared/config';
import type { Locale } from '@/shared/i18n';
import evidence from '@/entities/saffire/evidence.json';
import { saffireFlameAt, saffireMission } from '@/entities/saffire/mission';
import { spacecraftCopy } from '@/widgets/measure/spacecraft-copy';
import type { Explorer, Part, View } from './engine';
import { explorerCopy } from './copy';

type Point = [number, number];
type Phase = 'idle' | 'running' | 'paused' | 'done';
const rows = evidence.rows;
const GOALS = ['approach', 'inspect', 'open', 'test', 'ignite', 'spread', 'measure'] as const;
const fill = (s: string, v: Record<string, string | number>) => s.replace(/\{(\w+)\}/g, (_, k) => String(v[k] ?? ''));
const sign = (v: number, d = 2) => `${v >= 0 ? '+' : '−'}${Math.abs(v).toFixed(d)}`;
const lastAt = (pts: Point[], t: number) => { if (t < pts[0][0]) return null; let lo = 0, hi = pts.length - 1; while (lo < hi) { const m = (lo + hi + 1) >> 1; if (pts[m][0] <= t) lo = m; else hi = m - 1; } return pts[lo][1]; };

export function ExplorerApp({ locale }: { locale: Locale }) {
  const t = explorerCopy[locale], sc = spacecraftCopy[locale];
  const [id, setId] = useState('II-5'), [points, setPoints] = useState<Point[] | null>(null);
  const [phase, setPhase] = useState<Phase>('idle'), [speed, setSpeed] = useState(8);
  const [cut, setCut] = useState(0), [explode, setExplode] = useState(0), [sun, setSun] = useState(28), [orbit, setOrbit] = useState(1), [beacons, setBeacons] = useState(true), [autoRot, setAutoRot] = useState(false);
  const [done, setDone] = useState<Set<string>>(new Set()), [picked, setPicked] = useState<Part | null>(null), [hover, setHover] = useState<{ p: Part; x: number; y: number } | null>(null);
  const [hud, setHud] = useState({ time: -40, reading: null as number | null, alive: 0, pulse: 0, sensed: 0, theta: 0 });
  const [status3d, setStatus3d] = useState<'loading' | 'ok' | 'fail'>('loading');
  const stage = useRef<HTMLElement>(null), canvas = useRef<HTMLCanvasElement>(null), pip = useRef<HTMLCanvasElement>(null), overlay = useRef<HTMLDivElement>(null), engine = useRef<Explorer | null>(null);
  const simT = useRef(-40), phaseRef = useRef(phase), speedRef = useRef(speed), cursor = useRef<SVGLineElement>(null), clock = useRef<HTMLElement>(null);
  phaseRef.current = phase; speedRef.current = speed;

  const row = rows.find(r => r.id === id)!, c = row.conditions, mission = saffireMission[id];
  const D = c.ignition_duration_command_s.value as number, P = c.ignition_power_command_w.value as number;
  const utc = new Date(c.ignition_epoch_ms.value as number).toISOString().replace('T', ' ').slice(0, 19);
  const tEnd = points?.[points.length - 1][0] ?? 300, tMin = points?.[0][0] ?? -60;
  const achieve = (g: string) => setDone(s => (s.has(g) ? s : new Set(s).add(g)));

  useEffect(() => {
    const ctrl = new AbortController(); setPoints(null);
    fetch(asset(`/data/saffire/${id}.json`), { signal: ctrl.signal }).then(r => r.ok ? r.json() : Promise.reject()).then((d: { test_id?: string; points?: unknown }) => {
      if (d.test_id === id && Array.isArray(d.points) && d.points.every(p => Array.isArray(p) && p.length === 2 && p.every(Number.isFinite))) setPoints(d.points as Point[]);
    }).catch(() => undefined);
    simT.current = -40; setPhase('idle');
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
        onPick: p => { setPicked(p); achieve('inspect'); }, onHover: (p, x, y) => setHover(p ? { p, x, y } : null),
        onCamera: d => { if (d < 16) achieve('approach'); },
      });
      e.onCutAuto(v => setCut(v)); engine.current = e; setSun(e.initialSun); setStatus3d('ok');
    }).catch(() => setStatus3d('fail'));
    return () => { alive = false; engine.current?.dispose(); engine.current = null; };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => { engine.current?.setSample({ material: row.material, opposed: c.flow_direction.value === 'opposed', leadInCm: row.material === 'PMMA_Nomex' ? mission.burnLengthCm : null, regressCm: mission.outcome === 'anchored_flame_slow_regression' ? mission.burnLengthCm : 0 }); }, [row, c, mission, status3d]);
  useEffect(() => { engine.current?.setCut(cut); if (cut > .3) achieve('open'); }, [cut, status3d]);
  useEffect(() => { engine.current?.setExplode(explode); if (explode > .3) achieve('open'); }, [explode, status3d]);
  useEffect(() => { engine.current?.setSun(sun); }, [sun, status3d]);
  useEffect(() => { engine.current?.setOrbitSpeed(orbit); }, [orbit, status3d]);
  useEffect(() => { engine.current?.setBeacons(beacons); }, [beacons, status3d]);
  useEffect(() => { engine.current?.setAutoRotate(autoRot); }, [autoRot, status3d]);

  const chart = useMemo(() => {
    if (!points) return null;
    const vs = points.map(p => p[1]), lo = Math.min(...vs), hi = Math.max(...vs), pad = (hi - lo) * .1 || 5;
    const X = (v: number) => 4 + ((v - tMin) / (tEnd - tMin)) * 292, Y = (v: number) => 86 - ((v - lo + pad) / (hi - lo + 2 * pad)) * 78;
    const step = Math.max(1, Math.floor(points.length / 500));
    return { X, Y, d: points.filter((_, i) => i % step === 0).map((p, i) => `${i ? 'L' : 'M'}${X(p[0]).toFixed(1)} ${Y(p[1]).toFixed(1)}`).join('') };
  }, [points, tMin, tEnd]);

  // Simulation clock
  useEffect(() => {
    let raf = 0, last = performance.now(), lastHud = 0;
    const intensity = Math.min(1, Math.max(.35, Math.abs(row.actual) / 107)), heat = Math.min(1, Math.max(0, (mission.plumePeakC - 22) / 64));
    const loop = (now: number) => {
      const dt = Math.min(.1, (now - last) / 1000); last = now;
      if (phaseRef.current === 'running' && points) { simT.current += dt * speedRef.current; if (simT.current >= tEnd) { simT.current = tEnd; setPhase('done'); } }
      const time = simT.current, running = phaseRef.current !== 'idle';
      const f = running ? saffireFlameAt(id, time) : { x: 0, alive: 0, burnt: 0, regress: 0, pulse: 0 };
      const reading = points ? lastAt(points, time) : null;
      const sensed = reading === null || !running ? 0 : Math.min(1, Math.max(0, (reading - row.baseline) / Math.max(30, Math.abs(row.actual) * 1.3)));
      engine.current?.update({ flame: f, sensed, heat, intensity, reading, burning: running });
      if (chart && cursor.current) { const x = chart.X(Math.max(tMin, Math.min(tEnd, time))).toFixed(1); cursor.current.setAttribute('x1', x); cursor.current.setAttribute('x2', x); }
      if (clock.current) clock.current.textContent = `T${time >= 0 ? '+' : '−'}${Math.abs(time).toFixed(1).padStart(5, '0')}`;
      if (running && f.alive > .3 && time > 20) achieve('spread');
      if (running && time >= 180) achieve('measure');
      if (now - lastHud > 120) { lastHud = now; setHud({ time, reading, alive: f.alive, pulse: f.pulse, sensed, theta: engine.current?.theta() ?? 0 }); }
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id, points, chart, row, mission, tEnd, tMin]);

  const ignite = () => { simT.current = -30; setPhase('running'); achieve('ignite'); engine.current?.focus('flame', 1800); };
  const togglePlay = () => { if (phase === 'idle' || phase === 'done') ignite(); else setPhase(p => (p === 'running' ? 'paused' : 'running')); };
  const reset = () => { simT.current = -40; setPhase('idle'); };
  const chooseTest = (r: string) => { setId(r); achieve('test'); };
  const view = (v: View) => engine.current?.focus(v);

  // Keyboard shortcuts handled by the UI (camera keys live in the engine)
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement)?.tagName; if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT' || tag === 'BUTTON') return;
      const k = e.key.toLowerCase();
      if (k === ' ') { e.preventDefault(); togglePlay(); }
      if (k === 'c') setCut(v => (v > .3 ? 0 : .8));
      if (k === 'x') { const o = { v: explode }; animate(o, { v: explode > .5 ? 0 : 1, duration: 900, ease: 'inOut(3)', onUpdate: () => setExplode(o.v) }); }
    };
    window.addEventListener('keydown', onKey); return () => window.removeEventListener('keydown', onKey);
  });

  const statusText = phase === 'idle' ? t.status.idle : phase === 'paused' ? t.status.paused : phase === 'done' ? t.status.done : hud.time < 0 ? `${t.status.armed}${Math.abs(hud.time).toFixed(0)} s` : t.status.burning;
  const events = useMemo(() => {
    const ev: { t: number; text: string; hot?: boolean }[] = [
      { t: -30, text: t.events.armed }, { t: 0, text: fill(t.events.ignition, { utc }), hot: true }, { t: D, text: fill(t.events.igniterOff, { power: P, duration: D }) },
      { t: 150, text: t.events.response }, { t: 180, text: fill(t.events.delta, { delta: sign(row.actual) }), hot: true },
    ];
    if (mission.spreadRateMmS) ev.push({ t: 290 / mission.spreadRateMmS, text: fill(t.events.front, { rate: mission.spreadRateMmS }) });
    ev.push(mission.burnDurationS ? { t: mission.burnDurationS, text: fill(t.events.burnEnd, { duration: mission.burnDurationS, length: mission.burnLengthCm }) } : { t: D + 14, text: t.events.noSpread });
    return ev.sort((a, b) => a.t - b.t);
  }, [t, utc, D, P, row.actual, mission]);
  const partInfo = (p: Part) => fill(t.parts[p][1], {
    flow: row.flow.toFixed(2), dir: sc.directions[c.flow_direction.value as string], o2: (c.o2_pre_sensor_pct.value as number).toFixed(2), p: (c.pressure_pre_kpa.value as number).toFixed(1),
    material: sc.materials[row.material] ?? row.material, thickness: c.thickness_nominal_mm.value as number, outcome: sc.outcomes[mission.outcome], power: P, duration: D, plume: mission.plumePeakC.toFixed(1), delta: sign(row.actual),
  });
  const progress = done.size / GOALS.length;
  const rx = 60 + Math.cos(hud.theta) * 44, ry = 60 + Math.sin(hud.theta) * 44 * .55;

  return <main id="main" className="xp">
    <header className="xp-head">
      <div><p className="eyebrow">{t.eyebrow}</p><h1 data-fx-skip>{t.title}</h1><p className="xp-intro">{t.intro}</p></div>
      <Link className="xp-back" href={`/${locale}/simulation/`}>{t.back}</Link>
    </header>

    <section ref={stage} className="xp-stage" data-lenis-prevent aria-label={t.title}>
      <canvas ref={canvas} className="xp-canvas" />
      <div ref={overlay} className="xp-overlay" />
      {status3d !== 'ok' && <p className="xp-boot">{status3d === 'fail' ? t.webgl : t.loading}</p>}

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

      <aside className="xp-right">
        <figure className="xp-panel xp-pip">
          <figcaption><span className="xp-rec" />{t.pip}</figcaption>
          <canvas ref={pip} />
          <p>{t.pipNote}</p>
        </figure>
        <div className="xp-panel xp-co2">
          <p className="eyebrow">{t.co2} · {id}</p>
          <div className="xp-read"><div><span>{t.reading}</span><b>{hud.reading !== null ? hud.reading.toFixed(1) : '—'}</b></div><div className="xp-hot"><span>{t.delta}</span><b>{hud.reading !== null && phase !== 'idle' ? sign(hud.reading - row.baseline, 1) : '—'}</b></div><div><span>{t.final}</span><b>{sign(row.actual)}</b></div></div>
          {chart && <svg viewBox="0 0 300 92" className="xp-chart" aria-hidden="true">
            <rect x={chart.X(-30)} y="6" width={chart.X(0) - chart.X(-30)} height="82" className="sm-win-base" /><rect x={chart.X(150)} y="6" width={chart.X(180) - chart.X(150)} height="82" className="sm-win-resp" />
            <line x1="4" x2="296" y1={chart.Y(row.baseline)} y2={chart.Y(row.baseline)} className="sc-mini-base" />
            <path d={chart.d} className="xp-line" /><line ref={cursor} y1="4" y2="90" className="xp-cursor" />
          </svg>}
          <p className="xp-outcome"><span>{t.outcome}</span>{sc.outcomes[mission.outcome]} · {t.burn}: {mission.burnDurationS ? `${mission.burnDurationS} s · ${mission.burnLengthCm} cm` : t.insignificant} · {t.rate}: {mission.spreadRateMmS ? `${mission.spreadRateMmS} mm/s` : t.none}</p>
        </div>
      </aside>

      {picked && <div className="xp-panel xp-card" role="dialog" aria-label={t.parts[picked][0]}>
        <button type="button" className="xp-x" onClick={() => setPicked(null)} aria-label="×">×</button>
        <p className="eyebrow">{t.parts[picked][0]}</p><p>{partInfo(picked)}</p>
      </div>}
      {hover && <div className="xp-tip" style={{ left: hover.x, top: hover.y }}>{t.parts[hover.p][0]}</div>}

      <div className="xp-panel xp-radar" aria-label={t.radar}>
        <p className="eyebrow">{t.radar}</p>
        <svg viewBox="0 0 120 120" aria-hidden="true"><circle cx="60" cy="60" r="20" className="xp-r-earth" /><ellipse cx="60" cy="60" rx="44" ry="24" className="xp-r-orbit" /><circle cx={rx} cy={ry} r="4" className="xp-r-craft" /><circle cx={rx} cy={ry} r="9" className="xp-r-ping" /></svg>
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
    </section>

    <section className="xp-below">
      <div className="xp-log"><p className="eyebrow">{t.log}</p><ol>{events.filter(e => phase !== 'idle' && e.t <= hud.time).reverse().map(e => <li key={e.text} className={e.hot ? 'is-hot' : ''}><b>T{e.t >= 0 ? '+' : '−'}{Math.abs(e.t).toFixed(1)} s</b>{e.text}</li>)}</ol></div>
      <p className="xp-disclaimer">{t.disclaimer}</p>
    </section>
  </main>;
}
