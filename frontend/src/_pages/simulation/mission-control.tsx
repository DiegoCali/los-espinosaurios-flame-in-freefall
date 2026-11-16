'use client';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import Link from 'next/link';
import { animate } from 'animejs';
import { asset } from '@/shared/config';
import type { Locale } from '@/shared/i18n';
import evidence from '@/entities/saffire/evidence.json';
import { saffireFlameAt, saffireMission, type SaffireMissionTest } from '@/entities/saffire/mission';
import { spacecraftCopy } from '@/widgets/measure/spacecraft-copy';
import type { MissionScene, Preset, ScenePart } from './scene';
import { simCopy } from './copy';
import { explorerCopy } from '@/_pages/explorer/copy';

type Point = [number, number];
const rows = evidence.rows, model = evidence.model;
const fill = (s: string, v: Record<string, string | number>) => s.replace(/\{(\w+)\}/g, (_, k) => String(v[k] ?? ''));
const sign = (v: number, d = 2) => `${v >= 0 ? '+' : '−'}${Math.abs(v).toFixed(d)}`;
const lastAt = (pts: Point[], t: number) => { if (t < pts[0][0]) return null; let lo = 0, hi = pts.length - 1; while (lo < hi) { const m = (lo + hi + 1) >> 1; if (pts[m][0] <= t) lo = m; else hi = m - 1; } return pts[lo][1]; };
const SPEEDS = [1, 5, 10, 30];

const INDICATORS: { key: string; get: (m: SaffireMissionTest, actual: number) => number; unit: string; d: number }[] = [
  { key: 'co2', get: (_, a) => a, unit: 'ppm', d: 2 }, { key: 'peak', get: m => m.co2Peak180Ppm, unit: 'ppm', d: 1 }, { key: 'end', get: m => m.co2EndChangePpm, unit: 'ppm', d: 1 },
  { key: 'o2', get: m => m.o2Change180Pp, unit: 'pp', d: 3 }, { key: 'pressure', get: m => m.pressureChange180KPa, unit: 'kPa', d: 4 }, { key: 'inlet', get: m => m.inletTempChange180C, unit: '°C', d: 3 },
  { key: 'plume', get: m => m.plumePeakC, unit: '°C', d: 1 }, { key: 'radiation', get: m => m.radiationPeak180KWm2, unit: 'kW/m²', d: 3 },
];

export function MissionControl({ locale }: { locale: Locale }) {
  const t = simCopy[locale], sc = spacecraftCopy[locale];
  const [id, setId] = useState('II-5'), [points, setPoints] = useState<Point[] | null>(null);
  const [playing, setPlaying] = useState(true), [speed, setSpeed] = useState(10);
  const [toggles, setToggles] = useState({ cutaway: false, labels: true, orbit: true, flow: true });
  const [picked, setPicked] = useState<ScenePart | null>(null), [webgl, setWebgl] = useState<'loading' | 'ok' | 'fail'>('loading');
  const [hud, setHud] = useState({ time: -40, reading: null as number | null, alive: 0, pulse: 0, sensed: 0 });
  const [sandbox, setSandbox] = useState({ silicone: false, flow: 20 });
  const canvas = useRef<HTMLCanvasElement>(null), layer = useRef<HTMLDivElement>(null), scene = useRef<MissionScene | null>(null);
  const simT = useRef(-40), playRef = useRef(playing), speedRef = useRef(speed);
  const cursors = useRef<SVGLineElement[]>([]), frontDot = useRef<SVGCircleElement>(null), scrub = useRef<HTMLInputElement>(null), clock = useRef<HTMLElement>(null);
  playRef.current = playing; speedRef.current = speed;

  const row = rows.find(r => r.id === id)!, c = row.conditions, mission = saffireMission[id];
  const opposed = c.flow_direction.value === 'opposed';
  const D = c.ignition_duration_command_s.value as number, P = c.ignition_power_command_w.value as number;
  const utc = new Date(c.ignition_epoch_ms.value as number).toISOString().replace('T', ' ').slice(0, 19);
  const tMin = points?.[0][0] ?? -60, tEnd = points?.[points.length - 1][0] ?? 300;

  // Real CO₂ series for the selected test.
  useEffect(() => {
    const ctrl = new AbortController(); setPoints(null);
    fetch(asset(`/data/saffire/${id}.json`), { signal: ctrl.signal }).then(r => r.ok ? r.json() : Promise.reject()).then((d: { test_id?: string; points?: unknown }) => {
      if (d.test_id === id && Array.isArray(d.points) && d.points.every(p => Array.isArray(p) && p.length === 2 && p.every(Number.isFinite))) setPoints(d.points as Point[]);
    }).catch(() => undefined);
    simT.current = -40;
    return () => ctrl.abort();
  }, [id]);

  // 3D scene lifecycle (three.js loaded on demand).
  useEffect(() => {
    let alive = true;
    const probe = document.createElement('canvas');
    if (!(probe.getContext('webgl2') || probe.getContext('webgl'))) { setWebgl('fail'); return; }
    import('./scene').then(({ createMissionScene }) => {
      if (!alive || !canvas.current || !layer.current) return;
      const labelSpecs = (['cargo', 'service', 'array', 'earth', 'duct', 'sample', 'igniter', 'tc', 'co2', 'fan'] as const).map(part => ({ part, text: t.labels[part], inside: !['cargo', 'service', 'array', 'earth'].includes(part) }));
      const s = createMissionScene(canvas.current, layer.current, labelSpecs);
      s.onPick(setPicked); scene.current = s; setWebgl('ok');
    }).catch(() => setWebgl('fail'));
    return () => { alive = false; scene.current?.dispose(); scene.current = null; };
  }, [t.labels]);

  useEffect(() => { scene.current?.setSample({ material: row.material, opposed, leadInCm: row.material === 'PMMA_Nomex' ? mission.burnLengthCm : null }); }, [row, opposed, mission, webgl]);
  useEffect(() => { const s = scene.current; if (!s) return; s.setCutaway(toggles.cutaway); s.setLabels(toggles.labels); s.setOrbit(toggles.orbit); s.setFlowVectors(toggles.flow); }, [toggles, webgl]);

  // Geometry of the charts.
  const geo = useMemo(() => {
    if (!points) return null;
    const W = 640, H = 210, L = 132, R = 12, T = 14, B = 26;
    const vs = points.map(p => p[1]), lo = Math.min(...vs), hi = Math.max(...vs), pad = (hi - lo) * .08 || 5;
    const X = (v: number) => L + ((v - tMin) / (tEnd - tMin)) * (W - L - R), Y = (v: number) => H - B - ((v - (lo - pad)) / (hi - lo + 2 * pad)) * (H - T - B);
    const step = Math.max(1, Math.floor(points.length / 900));
    const d = points.filter((_, i) => i % step === 0).map((p, i) => `${i ? 'L' : 'M'}${X(p[0]).toFixed(1)} ${Y(p[1]).toFixed(1)}`).join('');
    const ticks = Array.from({ length: 6 }, (_, i) => Math.round((tMin + (i / 5) * (tEnd - tMin)) / 10) * 10);
    const yTicks = Array.from({ length: 4 }, (_, i) => lo - pad + (i / 3) * (hi - lo + 2 * pad));
    return { W, H, L, R, T, B, X, Y, d, ticks, yTicks };
  }, [points, tMin, tEnd]);

  const events = useMemo(() => {
    const list: { t: number; text: string; tone?: string }[] = [
      { t: tMin, text: t.events.record }, { t: -30, text: t.events.baseline }, { t: 0, text: fill(t.events.ignition, { utc }), tone: 'hot' },
      { t: D, text: fill(t.events.igniterOff, { power: P, duration: D }) },
      { t: 150, text: t.events.response }, { t: 180, text: fill(t.events.delta, { delta: sign(row.actual) }), tone: 'hot' }, { t: tEnd, text: t.events.end },
    ];
    if (mission.spreadRateMmS) list.push({ t: 290 / mission.spreadRateMmS, text: fill(t.events.front, { rate: mission.spreadRateMmS }) });
    if (mission.burnDurationS) list.push({ t: mission.burnDurationS, text: fill(t.events.burnEnd, { duration: mission.burnDurationS, length: mission.burnLengthCm }) });
    else list.push({ t: D + 14, text: t.events.noSpread });
    return list.sort((a, b) => a.t - b.t);
  }, [t, tMin, tEnd, utc, D, P, row.actual, mission]);

  // Simulation clock: drives the 3D scene every frame and the HUD at ~8 Hz.
  useEffect(() => {
    let raf = 0, last = performance.now(), lastHud = 0;
    const intensity = Math.min(1, Math.max(.35, Math.abs(row.actual) / 107)), heat = Math.min(1, Math.max(0, (mission.plumePeakC - 22) / 64));
    const loop = (now: number) => {
      const dt = Math.min(.1, (now - last) / 1000); last = now;
      if (playRef.current && points) { simT.current += dt * speedRef.current; if (simT.current > tEnd) simT.current = -40; }
      const time = simT.current, f = saffireFlameAt(id, time), reading = points ? lastAt(points, time) : null;
      const sensed = reading === null ? 0 : Math.min(1, Math.max(0, (reading - row.baseline) / Math.max(30, Math.abs(row.actual) * 1.3)));
      scene.current?.update({ flame: f, sensed, heat, intensity });
      if (geo) { const x = geo.X(Math.min(tEnd, Math.max(tMin, time))).toFixed(1); cursors.current.forEach(l => { l?.setAttribute('x1', x); l?.setAttribute('x2', x); }); }
      if (frontDot.current && geo) { frontDot.current.setAttribute('cx', geo.X(Math.min(tEnd, Math.max(tMin, time))).toFixed(1)); frontDot.current.setAttribute('cy', String(118 - (f.burnt / 29) * 96)); }
      if (clock.current) clock.current.textContent = `T${time >= 0 ? '+' : '−'}${Math.abs(time).toFixed(1).padStart(5, '0')} s`;
      if (now - lastHud > 120) { lastHud = now; setHud({ time, reading, alive: f.alive, pulse: f.pulse, sensed }); if (scrub.current && document.activeElement !== scrub.current) scrub.current.value = String(time); }
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);
  }, [id, points, geo, row, mission, tEnd, tMin]);

  const fly = useCallback((p: Preset) => { scene.current?.fly(p); if (p === 'inside' || p === 'flame') setToggles(v => ({ ...v, cutaway: true })); }, []);
  const jump = (to: number) => { const o = { v: simT.current }; animate(o, { v: to, duration: 700, ease: 'inOut(3)', onUpdate: () => { simT.current = o.v; } }); };

  const status = [
    { k: 'flow', on: true }, { k: 'igniter', on: hud.pulse > .05 }, { k: 'flame', on: hud.alive > .05 }, { k: 'sensor', on: hud.sensed > .15 }, { k: 'record', on: !!points && hud.time >= tMin && hud.time <= tEnd },
  ];
  const partText = picked ? fill(t.parts[picked] ?? '', {
    flow: row.flow.toFixed(2), dir: sc.directions[c.flow_direction.value as string], material: sc.materials[row.material] ?? row.material, thickness: c.thickness_nominal_mm.value as number,
    outcome: sc.outcomes[mission.outcome], power: P, duration: D, plume: mission.plumePeakC.toFixed(1),
  }) : t.pickHint;
  const sandboxOut = sandbox.silicone ? model.coefficients.silicone_location : model.coefficients.non_silicone_location * (20 / sandbox.flow);
  const [fMin, fMax] = model.flowRange;

  return <main id="main" className="ms">
    <header className="ms-head">
      <div><p className="eyebrow">{t.eyebrow}</p><h1>{t.title}</h1><p className="ms-intro">{t.intro}</p></div>
      <Link className="sc-sim-link ms-explorer-link" href={`/${locale}/simulation/explorer/`}><i aria-hidden="true" /><span><b>{explorerCopy[locale].open3d}</b><small>{explorerCopy[locale].open3dNote}</small></span><em aria-hidden="true">→</em></Link>
      <div className="ms-clockbox"><span>{t.clock}</span><b ref={clock}>T−0040.0 s</b><small>{t.utc} · {utc}</small></div>
    </header>
    <div className="ms-status" role="status" aria-live="off">{status.map(s => <span key={s.k} className={s.on ? 'is-on' : ''}><i />{t.status[s.k as keyof typeof t.status]}</span>)}<Link className="ms-back" href={`/${locale}/research/saffire-ii/`}>{t.back}</Link></div>

    <div className="ms-grid">
      <section className="ms-viewport" data-lenis-prevent aria-label={t.view.title}>
        <canvas ref={canvas} className="ms-canvas" />
        <div ref={layer} className="ms-labels" aria-hidden="true" />
        {webgl !== 'ok' && <p className="ms-boot">{webgl === 'fail' ? t.view.webgl : t.view.loading}</p>}
        <div className="ms-toolbar">
          <div className="ms-tool-group">{(['orbit', 'craft', 'inside', 'flame'] as Preset[]).map(p => <button key={p} type="button" onClick={() => fly(p)}>{t.view.presets[p]}</button>)}</div>
          <div className="ms-tool-group">{(Object.keys(toggles) as (keyof typeof toggles)[]).map(k => <button key={k} type="button" aria-pressed={toggles[k]} onClick={() => setToggles(v => ({ ...v, [k]: !v[k] }))}>{t.view.toggles[k]}</button>)}</div>
          <div className="ms-tool-group"><button type="button" aria-label={t.view.zoomIn} onClick={() => scene.current?.zoom(.7)}>＋</button><button type="button" aria-label={t.view.zoomOut} onClick={() => scene.current?.zoom(1.4)}>－</button></div>
        </div>
        <p className="ms-hint">{t.view.hint}</p>
        <div className="ms-pick"><p className="eyebrow">{t.picked}{picked ? ` · ${t.labels[picked]}` : ''}</p><p>{partText}</p></div>
      </section>

      <aside className="ms-side">
        <p className="eyebrow">{t.test}</p>
        <div className="mx-chips ms-tests" role="radiogroup" aria-label={t.test}>{rows.map(r => <button key={r.id} type="button" role="radio" aria-checked={r.id === id} onClick={() => setId(r.id)}>{r.id}</button>)}</div>
        <p className="eyebrow">{t.conditions}</p>
        <dl className="ms-cond">
          <div><dt>{t.cond.material}</dt><dd>{sc.materials[row.material] ?? row.material}</dd></div>
          <div><dt>{t.cond.thickness}</dt><dd>{c.thickness_nominal_mm.value as number} mm</dd></div>
          <div><dt>{t.cond.flow}</dt><dd>{row.flow.toFixed(2)} cm/s · {sc.directions[c.flow_direction.value as string]}</dd></div>
          <div><dt>{t.cond.o2} · {t.cond.pressure}</dt><dd>{(c.o2_pre_sensor_pct.value as number).toFixed(2)} % · {(c.pressure_pre_kpa.value as number).toFixed(1)} kPa</dd></div>
          <div><dt>{t.cond.igniter}</dt><dd>{P} W × {D} s</dd></div>
          <div><dt>{t.cond.outcome}</dt><dd>{sc.outcomes[mission.outcome]}</dd></div>
          <div><dt>{t.cond.length}</dt><dd>{mission.burnDurationS ? `${mission.burnLengthCm} cm` : t.cond.insignificant}</dd></div>
          <div><dt>{t.cond.duration}</dt><dd>{mission.burnDurationS ? `${mission.burnDurationS} s` : t.cond.insignificant}</dd></div>
          <div><dt>{t.cond.rate}</dt><dd>{mission.spreadRateMmS ? `${mission.spreadRateMmS} mm/s` : t.cond.none}</dd></div>
        </dl>
        <p className="eyebrow">{t.indicators}</p>
        <div className="ms-ind">{INDICATORS.map(ind => {
          const vals = rows.map(r => ind.get(saffireMission[r.id], r.actual)), v = ind.get(mission, row.actual), lo = Math.min(...vals), hi = Math.max(...vals);
          const rank = [...vals].sort((a, b) => b - a).indexOf(v) + 1;
          return <div key={ind.key}><span>{t.ind[ind.key as keyof typeof t.ind]}</span><b>{ind.key === 'peak' || ind.key === 'plume' || ind.key === 'radiation' ? v.toFixed(ind.d) : sign(v, ind.d)} <small>{ind.unit}</small></b><em>#{rank}/9</em><i><u style={{ left: `${((v - lo) / (hi - lo || 1)) * 100}%` }} /></i></div>;
        })}</div>
      </aside>
    </div>

    <section className="ms-transport" aria-label={t.timeline.scrub}>
      <button type="button" className="ms-play" onClick={() => setPlaying(p => !p)}>{playing ? `❚❚ ${t.timeline.pause}` : `▶ ${t.timeline.play}`}</button>
      <button type="button" onClick={() => { simT.current = -40; setPlaying(true); }}>↺ {t.timeline.restart}</button>
      <div className="ms-speed" role="radiogroup" aria-label={t.timeline.speed}>{SPEEDS.map(s => <button key={s} type="button" role="radio" aria-checked={speed === s} onClick={() => setSpeed(s)}>{s}×</button>)}</div>
      <input ref={scrub} type="range" min={tMin} max={tEnd} step=".1" defaultValue={-40} aria-label={t.timeline.scrub} onChange={e => { simT.current = Number(e.target.value); setPlaying(false); }} />
      <div className="ms-jumps">{[['ignition', 0], ['response', 180], ['end', tEnd]].map(([k, v]) => <button key={k as string} type="button" onClick={() => jump(v as number)}>{t.timeline.jump[k as string]}</button>)}</div>
    </section>

    <div className="ms-charts">
      <figure className="ms-card ms-co2">
        <figcaption><p className="eyebrow">{t.charts.co2} · {id}</p><p className="ms-note">{t.charts.co2Note}</p></figcaption>
        <div className="ms-readouts">
          <div><span>{t.charts.reading}</span><b>{hud.reading !== null ? `${hud.reading.toFixed(1)} ppm` : '—'}</b></div>
          <div className="mx-hot"><span>{t.charts.delta}</span><b>{hud.reading !== null ? `${sign(hud.reading - row.baseline, 1)} ppm` : '—'}</b></div>
          <div><span>{t.charts.final}</span><b>{sign(row.actual)} ppm</b></div>
        </div>
        {geo ? <svg viewBox={`0 0 ${geo.W} ${geo.H}`} className="ms-svg" role="img" aria-label={`${t.charts.co2} ${id}`}>
          {geo.yTicks.map(v => <g key={v}><line x1={geo.L} x2={geo.W - geo.R} y1={geo.Y(v)} y2={geo.Y(v)} className="ff-grid" /><text x={geo.L - 6} y={geo.Y(v) + 3} textAnchor="end" className="ff-tick">{v.toFixed(0)}</text></g>)}
          {geo.ticks.map(v => <text key={v} x={geo.X(v)} y={geo.H - 8} textAnchor="middle" className="ff-tick">{v}</text>)}
          <rect x={geo.X(-30)} y={geo.T} width={geo.X(0) - geo.X(-30)} height={geo.H - geo.T - geo.B} className="sm-win-base" />
          <rect x={geo.X(150)} y={geo.T} width={geo.X(180) - geo.X(150)} height={geo.H - geo.T - geo.B} className="sm-win-resp" />
          <line x1={geo.X(0)} x2={geo.X(0)} y1={geo.T} y2={geo.H - geo.B} className="sm-t0" />
          <line x1={geo.L} x2={geo.W - geo.R} y1={geo.Y(row.baseline)} y2={geo.Y(row.baseline)} className="sc-mini-base" />
          <path d={geo.d} className="ms-line" />
          <line ref={el => { if (el) cursors.current[0] = el; }} y1={geo.T - 4} y2={geo.H - geo.B} className="ms-cursor" />
        </svg> : <p className="ff-status">…</p>}
      </figure>

      <figure className="ms-card">
        <figcaption><p className="eyebrow">{t.charts.events}</p></figcaption>
        {geo && <svg viewBox={`0 0 ${geo.W} 150`} className="ms-svg ms-svg-sm">
          {([['record', tMin, tEnd], ['baseline', -30, 0], ['igniter', 0, D], ['flame', 0, mission.burnDurationS ?? 0], ['response', 150, 180]] as [string, number, number][]).map(([k, a, b], i) => <g key={k}>
            <text x="4" y={24 + i * 26} className="ff-tick">{t.charts.rows[k]}</text>
            <rect x={geo.X(a)} y={14 + i * 26} width={Math.max(2, geo.X(b) - geo.X(a))} height="14" className={`ms-bar ms-bar-${k}`} />
          </g>)}
          <line ref={el => { if (el) cursors.current[1] = el; }} y1="8" y2="142" className="ms-cursor" />
        </svg>}
        <figcaption><p className="eyebrow ms-sub">{t.charts.front}</p><p className="ms-note">{mission.spreadRateMmS ? t.charts.frontRate : mission.outcome === 'anchored_flame_slow_regression' ? t.charts.frontAnchored : mission.burnDurationS ? t.charts.frontInterp : t.charts.frontNone}</p></figcaption>
        {geo && <svg viewBox={`0 0 ${geo.W} 130`} className="ms-svg ms-svg-sm">
          <line x1={geo.L} x2={geo.W - geo.R} y1="118" y2="118" className="ff-grid" /><line x1={geo.L} x2={geo.W - geo.R} y1="22" y2="22" className="ff-grid" />
          <text x={geo.L - 6} y="121" textAnchor="end" className="ff-tick">0</text><text x={geo.L - 6} y="25" textAnchor="end" className="ff-tick">29 cm</text>
          {mission.burnDurationS && mission.outcome !== 'anchored_flame_slow_regression' && <path d={`M${geo.X(0)} 118 L${geo.X(mission.spreadRateMmS ? 290 / mission.spreadRateMmS : mission.burnDurationS)} ${118 - (mission.burnLengthCm / 29) * 96} H${geo.X(tEnd)}`} className={mission.spreadRateMmS ? 'ms-front' : 'ms-front ms-front-dash'} />}
          <circle ref={frontDot} r="5" className="ms-front-dot" cx={geo.L} cy="118" />
          <line ref={el => { if (el) cursors.current[2] = el; }} y1="12" y2="122" className="ms-cursor" />
        </svg>}
      </figure>

      <section className="ms-card ms-console" aria-label={t.console}>
        <p className="eyebrow">{t.console}</p>
        <ol>{events.filter(e => e.t <= hud.time).reverse().map(e => <li key={`${e.t}-${e.text}`} className={e.tone === 'hot' ? 'is-hot' : ''}><b>T{e.t >= 0 ? '+' : '−'}{Math.abs(e.t).toFixed(1)} s</b><span>{e.text}</span></li>)}</ol>
      </section>
    </div>

    <div className="ms-bottom">
      <section className="ms-card ms-sandbox" aria-labelledby="ms-sandbox">
        <p className="eyebrow" id="ms-sandbox">{t.sandbox.title}</p><p className="ms-note">{t.sandbox.intro}</p>
        <div className="mx-chips" role="radiogroup" aria-label={t.sandbox.group}>{[false, true].map(si => <button key={String(si)} type="button" role="radio" aria-checked={sandbox.silicone === si} onClick={() => setSandbox(v => ({ ...v, silicone: si }))}>{si ? t.sandbox.silicone : t.sandbox.other}</button>)}</div>
        <label className="ms-flow"><span>{t.sandbox.flow}: <b>{sandbox.flow.toFixed(2)} cm/s</b></span><input type="range" min={fMin} max={fMax} step=".01" value={sandbox.flow} onChange={e => setSandbox(v => ({ ...v, flow: Number(e.target.value) }))} /></label>
        <div className="ms-out"><span>{t.sandbox.output}</span><b>{sign(sandboxOut)} ppm</b><code>{sandbox.silicone ? `${model.coefficients.silicone_location.toFixed(3)}` : `${model.coefficients.non_silicone_location.toFixed(3)} × (20 / ${sandbox.flow.toFixed(2)})`}</code></div>
        <svg viewBox="0 0 320 150" className="ms-svg ms-sandbox-chart">
          {(() => { const X = (f: number) => 40 + ((f - 19.5) / 6) * 270, Y = (v: number) => 130 - ((v + 30) / 150) * 120; return <>
            {[0, 50, 100].map(v => <g key={v}><line x1="40" x2="310" y1={Y(v)} y2={Y(v)} className="ff-grid" /><text x="34" y={Y(v) + 3} textAnchor="end" className="ff-tick">{v}</text></g>)}
            {[20, 22, 24].map(f => <text key={f} x={X(f)} y="146" textAnchor="middle" className="ff-tick">{f}</text>)}
            <path d={Array.from({ length: 30 }, (_, i) => { const f = fMin + (i / 29) * (fMax - fMin); return `${i ? 'L' : 'M'}${X(f).toFixed(1)} ${Y(model.coefficients.non_silicone_location * 20 / f).toFixed(1)}`; }).join('')} className="ms-model" />
            <line x1={X(fMin)} x2={X(fMax)} y1={Y(model.coefficients.silicone_location)} y2={Y(model.coefficients.silicone_location)} className="ms-model ms-model-si" />
            {rows.map(r => <circle key={r.id} cx={X(r.flow)} cy={Y(r.actual)} r={r.id === id ? 6 : 4} className={`ms-obs${r.material === 'Silicone' ? ' is-si' : ''}${r.id === id ? ' is-sel' : ''}`}><title>{`${r.id} · ${r.flow.toFixed(2)} cm/s · ${sign(r.actual)} ppm`}</title></circle>)}
            <circle cx={X(sandbox.flow)} cy={Y(sandboxOut)} r="6" className="ms-pred" />
          </>; })()}
        </svg>
        <p className="ms-note">{t.sandbox.note}</p>
      </section>
      <section className="ms-card ms-explosion" aria-labelledby="ms-exp">
        <p className="eyebrow" id="ms-exp">{t.explosion.title}</p>
        <b className="ms-exp-status"><i />{t.explosion.status}</b>
        <p>{fill(t.explosion.body, { p: sign(mission.pressureChange180KPa, 4) })}</p>
        <p className="ms-note">{t.disclaimer}</p>
      </section>
    </div>
  </main>;
}
