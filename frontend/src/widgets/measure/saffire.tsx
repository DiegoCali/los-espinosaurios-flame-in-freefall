'use client';
import { useEffect, useMemo, useRef, useState } from 'react';
import { createTimeline, svg, utils, type Timeline } from 'animejs';
import { prefersReducedMotion } from '@/shared/motion/anime';
import { asset } from '@/shared/config';
import evidence from '@/entities/saffire/evidence.json';
import type { MeasureCopy } from './copy';
import './measure.css';

type Point = [number, number];
const W = 620, H = 310, PAD = { l: 58, r: 16, t: 30, b: 44 };
const median = (v: number[]) => { const s = [...v].sort((a, b) => a - b), m = s.length >> 1; return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2; };

/** Recomputes the SAFFIRE-II CO₂ response from a real sensor series and animates the method. */
export function SaffireMeasure({ t }: { t: MeasureCopy['saffire'] }) {
  const rows = evidence.rows;
  const [id, setId] = useState('II-7'), [points, setPoints] = useState<Point[] | null>(null), [failed, setFailed] = useState(false);
  const root = useRef<HTMLElement>(null), deltaOut = useRef<HTMLElement>(null), seen = useRef(false);
  const row = rows.find(r => r.id === id)!;

  useEffect(() => {
    const c = new AbortController();
    setPoints(null); setFailed(false);
    fetch(asset(`/data/saffire/${id}.json`), { signal: c.signal }).then(r => r.ok ? r.json() : Promise.reject()).then((d: { test_id?: string; points?: unknown }) => {
      if (d.test_id !== id || !Array.isArray(d.points) || !d.points.every(p => Array.isArray(p) && p.length === 2 && p.every(Number.isFinite))) throw Error('SAFFIRE');
      setPoints(d.points as Point[]);
    }).catch(e => { if (e?.name !== 'AbortError') setFailed(true); });
    return () => c.abort();
  }, [id]);

  const geo = useMemo(() => {
    if (!points) return null;
    const base = median(points.filter(([x]) => x >= -30 && x < 0).map(p => p[1]));
    const resp = median(points.filter(([x]) => x >= 150 && x < 180).map(p => p[1]));
    const view = points.filter(([x]) => x <= 300);
    const vs = view.map(p => p[1]), lo = Math.min(...vs), hi = Math.max(...vs), pad = (hi - lo) * .12 || 5;
    const tMin = view[0][0], tMax = view[view.length - 1][0], vMin = lo - pad, vMax = hi + pad;
    const X = (v: number) => PAD.l + ((v - tMin) / (tMax - tMin)) * (W - PAD.l - PAD.r), Y = (v: number) => H - PAD.b - ((v - vMin) / (vMax - vMin)) * (H - PAD.t - PAD.b);
    const d = view.map((p, i) => `${i ? 'L' : 'M'}${X(p[0]).toFixed(1)} ${Y(p[1]).toFixed(1)}`).join('');
    const yTicks = Array.from({ length: 5 }, (_, i) => vMin + (i / 4) * (vMax - vMin));
    return { base, resp, delta: resp - base, X, Y, d, tMin, tMax, yTicks };
  }, [points]);

  useEffect(() => {
    if (!geo) return;
    const el = root.current!;
    const reduced = prefersReducedMotion();
    let tl: Timeline | null = null;
    const show = () => {
      const steps = el.querySelectorAll('.sm-steps li');
      const out = { v: 0 };
      if (reduced) { if (deltaOut.current) deltaOut.current.textContent = `${geo.delta >= 0 ? '+' : ''}${geo.delta.toFixed(2)}`; return; }
      utils.set(steps, { opacity: .35 });
      utils.set(el.querySelectorAll('.sm-t0, .sm-win-base, .sm-win-resp, .sm-base-line, .sm-resp-line, .sm-bracket'), { opacity: 0 });
      tl = createTimeline({ defaults: { ease: 'inOut(3)' } })
        .add(svg.createDrawable(el.querySelector<SVGPathElement>('.sm-line')!), { draw: ['0 0', '0 1'], duration: 2200 }, 0)
        .add(el.querySelector('.sm-t0')!, { opacity: [0, 1], scaleY: [0, 1], duration: 500 }, 300)
        .add(steps[0], { opacity: [.35, 1], duration: 300 }, 300)
        .add(el.querySelector('.sm-win-base')!, { opacity: [0, 1], scaleX: [0, 1], duration: 600 }, 900)
        .add(el.querySelector('.sm-base-line')!, { opacity: [0, 1], translateX: [-40, 0], duration: 600 }, 1100)
        .add(steps[1], { opacity: [.35, 1], duration: 300 }, 900)
        .add(el.querySelector('.sm-win-resp')!, { opacity: [0, 1], scaleX: [0, 1], duration: 600 }, 1700)
        .add(el.querySelector('.sm-resp-line')!, { opacity: [0, 1], translateX: [-40, 0], duration: 600 }, 1900)
        .add(steps[2], { opacity: [.35, 1], duration: 300 }, 1700)
        .add(el.querySelector('.sm-bracket')!, { opacity: [0, 1], scaleY: [0, 1], duration: 700, ease: 'out(3)' }, 2500)
        .add(steps[3], { opacity: [.35, 1], duration: 300 }, 2500)
        .add(out, { v: geo.delta, duration: 1200, ease: 'out(4)', onUpdate: () => { if (deltaOut.current) deltaOut.current.textContent = `${out.v >= 0 ? '+' : ''}${out.v.toFixed(2)}`; } }, 2500);
    };
    if (seen.current) { show(); return () => { tl?.revert(); }; }
    const io = new IntersectionObserver(([e]) => { if (e.isIntersecting) { io.disconnect(); seen.current = true; show(); } }, { threshold: .35 });
    io.observe(el);
    return () => { io.disconnect(); tl?.revert(); };
  }, [geo]);

  return <section ref={root} className="mx-section sm" aria-labelledby="sm-title">
    <div className="mx-copy">
      <p className="eyebrow">{t.index}</p>
      <h2 id="sm-title">{t.title}</h2>
      <p className="section-intro">{t.intro}</p>
      <div className="mx-chips" role="radiogroup" aria-label="SAFFIRE-II">{rows.map(r => <button key={r.id} type="button" role="radio" aria-checked={r.id === id} onClick={() => setId(r.id)}>{r.id}</button>)}</div>
      <ol className="sm-steps mx-steps">{t.steps.map(([a, b]) => <li key={a}><b>{a}</b><span>{b}</span></li>)}</ol>
      <p className="mx-micro"><i aria-hidden="true" />{t.micro}</p>
    </div>
    <figure className="mx-figure">
      <div className="mx-readouts">
        <div><span>{t.material}</span><b>{row.material.replace('_', ' / ')}</b></div>
        <div><span>{t.flow}</span><b>{row.flow.toFixed(1)} cm/s</b></div>
        <div className="mx-hot"><span>{t.delta} · {t.recomputed}</span><b><em ref={deltaOut}>—</em> <small>ppm</small></b></div>
        <div><span>{t.exported}</span><b>{row.actual >= 0 ? '+' : ''}{row.actual.toFixed(2)} <small>ppm</small></b></div>
      </div>
      {failed ? <p role="alert" className="ff-status">{t.error}</p> : !geo ? <p role="status" className="ff-status">{t.loading}</p> :
        <svg className="mx-chart" viewBox={`0 0 ${W} ${H}`} role="img" aria-label={`${id}: ${t.ppm} vs ${t.time}. ${t.baseline} ${geo.base.toFixed(1)} ppm; ${t.window} ${geo.resp.toFixed(1)} ppm; Δ ${geo.delta.toFixed(2)} ppm.`}>
          {geo.yTicks.map(v => <g key={v}><line x1={PAD.l} x2={W - PAD.r} y1={geo.Y(v)} y2={geo.Y(v)} className="ff-grid" /><text x={PAD.l - 8} y={geo.Y(v) + 3} textAnchor="end" className="ff-tick">{v.toFixed(0)}</text></g>)}
          {[-60, 0, 60, 120, 180, 240, 300].filter(v => v >= geo.tMin && v <= geo.tMax).map(v => <text key={v} x={geo.X(v)} y={H - 24} textAnchor="middle" className="ff-tick">{v}</text>)}
          <rect className="sm-win-base" x={geo.X(-30)} y={PAD.t} width={geo.X(0) - geo.X(-30)} height={H - PAD.t - PAD.b} style={{ transformBox: 'fill-box', transformOrigin: 'left' }} />
          <rect className="sm-win-resp" x={geo.X(150)} y={PAD.t} width={geo.X(180) - geo.X(150)} height={H - PAD.t - PAD.b} style={{ transformBox: 'fill-box', transformOrigin: 'left' }} />
          <line className="sm-t0" x1={geo.X(0)} x2={geo.X(0)} y1={PAD.t} y2={H - PAD.b} style={{ transformBox: 'fill-box', transformOrigin: 'bottom' }} />
          <text x={geo.X(0) + 4} y={PAD.t + 10} className="ff-tick sm-t0-label">t₀</text>
          <path className="sm-line" d={geo.d} fill="none" stroke="#ffb347" strokeWidth="1.5" />
          <g className="sm-base-line"><line x1={geo.X(-30)} x2={W - PAD.r} y1={geo.Y(geo.base)} y2={geo.Y(geo.base)} /><text x={W - PAD.r} y={geo.Y(geo.base) + 14} textAnchor="end">{t.baseline} · {geo.base.toFixed(1)}</text></g>
          <g className="sm-resp-line"><line x1={geo.X(150)} x2={W - PAD.r} y1={geo.Y(geo.resp)} y2={geo.Y(geo.resp)} /><text x={W - PAD.r} y={geo.Y(geo.resp) - 6} textAnchor="end">{t.window} · {geo.resp.toFixed(1)}</text></g>
          <g className="sm-bracket" style={{ transformBox: 'fill-box', transformOrigin: 'bottom' }}><line x1={geo.X(195)} x2={geo.X(195)} y1={geo.Y(geo.base)} y2={geo.Y(geo.resp)} /><path d={`M${geo.X(190)} ${geo.Y(geo.base)} H${geo.X(200)} M${geo.X(190)} ${geo.Y(geo.resp)} H${geo.X(200)}`} /><text x={geo.X(203)} y={(geo.Y(geo.base) + geo.Y(geo.resp)) / 2 + 4}>Δ</text></g>
          <text x={W - PAD.r} y={H - 2} textAnchor="end" className="ff-axis">{t.time}</text><text x={PAD.l - 8} y={14} textAnchor="end" className="ff-axis">ppm</text>
        </svg>}
      <figcaption>{t.warning} · {row.responseMetadata.method}</figcaption>
    </figure>
  </section>;
}
