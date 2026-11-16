'use client';
import { useEffect, useMemo, useRef, useState } from 'react';
import { animate, onScroll, type JSAnimation } from 'animejs';
import { prefersReducedMotion } from '@/shared/motion/anime';
import { asset } from '@/shared/config';
import { isFlexHistory, type FlexHistory } from '@/entities/flex/data';
import type { FxCopy } from './fx-copy';
import './measure.css';

const COLORS = ['#77c3ed', '#ff667a', '#8abbaa'];
const W = 520, H = 260, PAD = { l: 44, r: 12, t: 26, b: 30 };

/** Last measured diameter at or before time t (no interpolation, matching the dashboard's rule). */
function diameterAt(h: FlexHistory, t: number) {
  let lo = 0, hi = h.points.length - 1;
  if (t <= h.points[0][0]) return h.points[0][1];
  while (lo < hi) { const mid = (lo + hi + 1) >> 1; if (h.points[mid][0] <= t) lo = mid; else hi = mid - 1; }
  return h.points[lo][1];
}

export function DropletLab({ t }: { t: FxCopy['droplet'] }) {
  const section = useRef<HTMLElement>(null);
  const [data, setData] = useState<FlexHistory[] | null>(null), [failed, setFailed] = useState(false), [playing, setPlaying] = useState(true);
  const anim = useRef<JSAnimation | null>(null), state = useRef({ time: 0.3 });
  const drops = useRef<(SVGCircleElement | null)[]>([]), halos = useRef<(SVGCircleElement | null)[]>([]), labels = useRef<(HTMLElement | null)[]>([]), ended = useRef<(HTMLElement | null)[]>([]);
  const clip = useRef<SVGRectElement>(null), clock = useRef<HTMLElement>(null), range = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const controller = new AbortController();
    fetch(asset('/data/flex/histories.json'), { signal: controller.signal }).then(r => r.ok ? r.json() : Promise.reject()).then(v => { if (!isFlexHistory(v)) throw Error('FLEX'); setData(v); }).catch(e => { if (e?.name !== 'AbortError') setFailed(true); });
    return () => controller.abort();
  }, []);

  const geo = useMemo(() => {
    if (!data) return null;
    const t0 = data[0].reference_time_s, tEnd = Math.max(...data.map(h => h.points[h.points.length - 1][0]));
    const norm = data.map(h => h.points.filter(p => p[0] >= h.reference_time_s).map(([x, d]) => [x, (d * d) / (h.reference_diameter_mm ** 2)] as [number, number]));
    const yMax = Math.max(1.2, ...norm.flat().map(p => p[1]));
    const X = (v: number) => PAD.l + ((v - t0) / (tEnd - t0)) * (W - PAD.l - PAD.r), Y = (v: number) => H - PAD.b - (v / yMax) * (H - PAD.t - PAD.b);
    const paths = norm.map(s => s.map((p, i) => `${i ? 'L' : 'M'}${X(p[0]).toFixed(1)} ${Y(p[1]).toFixed(1)}`).join(''));
    const dMax = Math.max(...data.flatMap(h => h.points.map(p => p[1])));
    return { t0, tEnd, X, Y, yMax, paths, dMax };
  }, [data]);

  useEffect(() => {
    if (!data || !geo) return;
    const render = (time: number) => {
      data.forEach((h, i) => {
        const d = diameterAt(h, time), r = (d / geo.dMax) * 34, done = time > h.points[h.points.length - 1][0];
        drops.current[i]?.setAttribute('r', r.toFixed(2));
        halos.current[i]?.setAttribute('r', (r * 2.1 + 6).toFixed(2));
        halos.current[i]?.setAttribute('opacity', done ? '0.15' : String(.55 + .25 * Math.sin(time * 9 + i)));
        if (labels.current[i]) labels.current[i]!.textContent = `${d.toFixed(3)} mm`;
        ended.current[i]?.classList.toggle('is-visible', done);
      });
      clip.current?.setAttribute('width', String(Math.max(0, geo.X(time) - PAD.l)));
      if (clock.current) clock.current.textContent = `t = ${time.toFixed(2)} s`;
      if (range.current) range.current.value = String(time);
    };
    state.current.time = geo.t0;
    if (prefersReducedMotion()) { render(geo.tEnd); setPlaying(false); return; }
    render(geo.t0);
    anim.current = animate(state.current, { time: [geo.t0, geo.tEnd], duration: (geo.tEnd - geo.t0) * 1400, ease: 'linear', loop: true, loopDelay: 1200, autoplay: onScroll({ target: section.current!, enter: 'end start', leave: 'start end' }), onUpdate: () => render(state.current.time) });
    return () => { anim.current?.revert(); anim.current = null; };
  }, [data, geo]);

  const toggle = () => { const a = anim.current; if (!a) return; if (playing) a.pause(); else a.play(); setPlaying(!playing); };
  const scrub = (v: number) => {
    const a = anim.current; if (!a || !geo) return;
    a.pause(); setPlaying(false);
    a.seek(((v - geo.t0) / (geo.tEnd - geo.t0)) * a.iterationDuration);
  };

  return <section ref={section} className="dl-section" aria-labelledby="dl-title">
    <div className="dl-copy">
      <p className="eyebrow">{t.index}</p>
      <h2 id="dl-title">{t.title}</h2>
      <p className="section-intro">{t.intro}</p>
      <p className="dl-formula">{t.formula}</p>
      <p className="dl-note">{t.note}</p>
    </div>
    {failed ? <p role="alert" className="ff-status">{t.error}</p> : !data || !geo ? <p role="status" className="ff-status">{t.loading}</p> : <div className="dl-lab">
      <div className="dl-drops">{data.map((h, i) => <figure key={h.id} className="dl-drop">
        <svg viewBox="-80 -80 160 160" aria-hidden="true">
          <defs><radialGradient id={`dlHalo${i}`}><stop offset="55%" stopColor="#228bdf" stopOpacity="0" /><stop offset="82%" stopColor={COLORS[i]} stopOpacity=".85" /><stop offset="100%" stopColor={COLORS[i]} stopOpacity="0" /></radialGradient></defs>
          <circle r="76" fill="none" stroke="#16222e" strokeDasharray="2 5" />
          <circle ref={el => { halos.current[i] = el; }} r="40" fill={`url(#dlHalo${i})`} />
          <circle ref={el => { drops.current[i] = el; }} r="20" fill="#0f1720" stroke="#f2f3ed" strokeWidth="1.2" />
        </svg>
        <figcaption><b style={{ color: COLORS[i] }}>{h.id}</b><span>{t.fuels[h.id]}</span><span>{t.diameter}: <em ref={el => { labels.current[i] = el; }}>—</em></span><span ref={el => { ended.current[i] = el; }} className="dl-ended">END OF FILE</span></figcaption>
      </figure>)}</div>
      <div className="dl-chart-wrap">
        <div className="dl-controls">
          <button type="button" onClick={toggle} aria-pressed={!playing}>{playing ? `❚❚ ${t.pause}` : `▶ ${t.play}`}</button>
          <input ref={range} type="range" aria-label={t.scrub} min={geo.t0} max={geo.tEnd} step="0.01" defaultValue={geo.t0} onChange={e => scrub(Number(e.target.value))} />
          <b ref={clock} className="dl-clock">t = {geo.t0.toFixed(2)} s</b>
        </div>
        <svg className="dl-chart" viewBox={`0 0 ${W} ${H}`} role="img" aria-label={`${t.norm} vs ${t.time}: ${data.map(h => h.id).join(', ')}`}>
          <defs><clipPath id="dlClip"><rect ref={clip} x={PAD.l} y="0" width="0" height={H} /></clipPath></defs>
          {Array.from({ length: Math.floor(geo.yMax / .5) + 1 }, (_, k) => k * .5).map(v => <g key={v}><line x1={PAD.l} x2={W - PAD.r} y1={geo.Y(v)} y2={geo.Y(v)} className="ff-grid" /><text x={PAD.l - 6} y={geo.Y(v) + 3} textAnchor="end" className="ff-tick">{v.toFixed(2)}</text></g>)}
          {[0, 1, 2, 3, 4, 5].filter(v => v <= geo.tEnd).map(v => <text key={v} x={geo.X(v)} y={H - 10} textAnchor="middle" className="ff-tick">{v}</text>)}
          <g clipPath="url(#dlClip)">{geo.paths.map((d, i) => <path key={i} d={d} fill="none" stroke={COLORS[i]} strokeWidth="1.6" />)}</g>
          <text x={W - PAD.r} y={H - PAD.b - 6} textAnchor="end" className="ff-axis">s</text><text x={PAD.l} y={12} className="ff-axis">{t.norm}</text>
        </svg>
        <p className="dl-halo-note">{t.halo}</p>
      </div>
    </div>}
  </section>;
}
