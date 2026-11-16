'use client';
import { useEffect, useMemo, useRef, useState } from 'react';
import { animate, onScroll } from 'animejs';
import { prefersReducedMotion } from '@/shared/motion/anime';
import { asset } from '@/shared/config';
import { bassEvidence, readBassSeries, type BassSeriesPoint } from '@/entities/bass/data';
import type { FxCopy } from './fx-copy';
import './measure.css';

const W = 560, H = 310, PAD = { l: 48, r: 16, t: 28, b: 34 };
const record = (id: string) => {
  const rate = bassEvidence.rates.find(r => r.test_id === id)!;
  const comparison = bassEvidence.comparisons.find(c => c.test_id === id && c.set === 'development')!;
  // Exported tests with series all have a steady-spread interval; fall back to an empty one.
  return { rate, comparison, T0: (rate.t0 ?? 0) as number, T1: (rate.t1 ?? 0) as number };
};

/**
 * Scroll-scrubbed replay of a real BASS-II leading-edge series (only tests whose series are
 * exported: B1, B4, M1). `materialName` localises the material class from the evidence.
 */
export function FlameFrontLab({ t, tests = ['B1'], materialName = m => m }: { t: FxCopy['front']; tests?: string[]; materialName?: (m: string) => string }) {
  const section = useRef<HTMLElement>(null);
  const [test, setTest] = useState(tests[0]);
  const { rate, comparison, T0, T1 } = record(test);
  const [series, setSeries] = useState<BassSeriesPoint[] | null>(null), [failed, setFailed] = useState(false);
  const refs = { clip: useRef<SVGRectElement>(null), dot: useRef<SVGGElement>(null), time: useRef<HTMLElement>(null), edge: useRef<HTMLElement>(null), front: useRef<SVGGElement>(null), burnt: useRef<SVGRectElement>(null), steps: useRef<HTMLOListElement>(null), result: useRef<HTMLDivElement>(null), bar: useRef<HTMLElement>(null) };

  useEffect(() => {
    const controller = new AbortController();
    setSeries(null); setFailed(false);
    fetch(asset(`/data/bass/series/${test}.json`), { signal: controller.signal }).then(r => r.ok ? r.json() : Promise.reject()).then(v => setSeries(readBassSeries(v))).catch(e => { if (e?.name !== 'AbortError') setFailed(true); });
    return () => controller.abort();
  }, [test]);

  const geo = useMemo(() => {
    if (!series) return null;
    const tMin = series[0].time_s, tMax = series[series.length - 1].time_s;
    const eMax = Math.max(...series.map(p => p.leading_edge_mm ?? 0));
    const tick = eMax > 60 ? 20 : eMax > 25 ? 10 : 5, yMax = Math.ceil(eMax / tick) * tick;
    const X = (v: number) => PAD.l + ((v - tMin) / (tMax - tMin)) * (W - PAD.l - PAD.r);
    const Y = (v: number) => H - PAD.b - (v / yMax) * (H - PAD.t - PAD.b);
    let d = '', pen = false;
    series.forEach(p => { if (p.leading_edge_mm === null) { pen = false; return; } d += `${pen ? 'L' : 'M'}${X(p.time_s).toFixed(1)} ${Y(p.leading_edge_mm).toFixed(1)}`; pen = true; });
    const inFit = series.filter(p => p.fit !== null && p.time_s >= T0 && p.time_s <= T1);
    const fit = inFit.length > 1 ? `M${X(inFit[0].time_s)} ${Y(inFit[0].fit!)} L${X(inFit[inFit.length - 1].time_s)} ${Y(inFit[inFit.length - 1].fit!)}` : '';
    const xTicks = Array.from({ length: 6 }, (_, i) => tMin + (i / 5) * (tMax - tMin));
    const yTicks = Array.from({ length: yMax / tick + 1 }, (_, i) => i * tick);
    return { tMin, tMax, yMax, X, Y, d, fit, xTicks, yTicks };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [series]);

  useEffect(() => {
    if (!series || !geo) return;
    const el = section.current!, desktop = window.matchMedia('(min-width: 1200px)').matches;
    const n = series.length;
    const render = (p: number) => {
      const i = Math.min(n - 1, Math.max(0, Math.round(p * (n - 1))));
      // Last valid measurement up to this frame.
      let j = i; while (j > 0 && series[j].leading_edge_mm === null) j--;
      const pt = series[j], edge = pt.leading_edge_mm ?? 0, x = geo.X(series[i].time_s);
      refs.clip.current?.setAttribute('width', String(Math.max(0, x - PAD.l + 2)));
      refs.dot.current?.setAttribute('transform', `translate(${geo.X(pt.time_s)} ${geo.Y(edge)})`);
      if (refs.time.current) refs.time.current.textContent = `${series[i].time_s.toFixed(2)} s`;
      if (refs.edge.current) refs.edge.current.textContent = `${edge.toFixed(2)} mm`;
      const frac = edge / geo.yMax;
      refs.front.current?.setAttribute('transform', `translate(${20 + frac * 500} 0)`);
      refs.burnt.current?.setAttribute('width', String(frac * 500));
      const step = series[i].time_s < T0 ? (p < .12 ? 0 : 1) : series[i].time_s < T1 ? 2 : 3;
      refs.steps.current?.querySelectorAll('li').forEach((li, k) => li.classList.toggle('is-active', k === step));
      refs.result.current?.classList.toggle('is-visible', series[i].time_s >= T1);
      refs.bar.current?.style.setProperty('--ff-p', p.toFixed(4));
    };
    if (prefersReducedMotion()) { render(1); return; }
    const state = { p: 0 };
    render(0);
    const anim = desktop
      ? animate(state, { p: [0, 1], ease: 'linear', autoplay: onScroll({ target: el, enter: 'start start', leave: 'end end', sync: .15 }), onUpdate: () => render(state.p) })
      : animate(state, { p: [0, 1], duration: 9000, ease: 'linear', loop: true, loopDelay: 1500, autoplay: onScroll({ target: el }), onUpdate: () => render(state.p) });
    return () => { anim.revert(); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [series, geo]);

  return <section ref={section} className="ff-section" aria-labelledby="ff-title">
    <div className="ff-sticky">
      <div className="ff-copy">
        <p className="eyebrow">{t.index}</p>
        <h2 id="ff-title">{t.title}</h2>
        <p className="section-intro">{tests.length > 1 ? t.introMulti : t.intro}</p>
        {tests.length > 1 && <div className="ff-tests" role="radiogroup" aria-label="BASS-II">{tests.map(id => <button key={id} type="button" role="radio" aria-checked={test === id} onClick={() => setTest(id)}><b>{id}</b><span>{materialName(record(id).rate.material_class)}</span></button>)}</div>}
        <ol ref={refs.steps} className="ff-steps">{t.steps.map(([title, body], i) => <li key={title} className={i === 0 ? 'is-active' : ''}><b>{title}</b><span>{i === 3 && test !== 'B1' ? t.compareGeneric : body}</span></li>)}</ol>
        <dl className="ff-conditions">
          <div><dt>{t.thickness}</dt><dd>{rate.thickness_mm} mm</dd></div>
          <div><dt>{t.flow}</dt><dd>{rate.flow_initial_cm_s.toFixed(2)} cm/s</dd></div>
          <div><dt>{t.oxygen}</dt><dd>{rate.o2_initial_pct}%</dd></div>
        </dl>
      </div>
      <figure className="ff-figure">
        <div className="ff-readouts" aria-hidden="true">
          <div><span>{t.time}</span><b ref={refs.time}>—</b></div>
          <div><span>{t.edge}</span><b ref={refs.edge}>—</b></div>
          <div><span>{t.test}</span><b>{test} · {materialName(rate.material_class)}</b></div>
        </div>
        {failed ? <p role="alert" className="ff-status">{t.error}</p> : !geo ? <p role="status" className="ff-status">{t.loading}</p> :
          <svg className="ff-chart" viewBox={`0 0 ${W} ${H}`} role="img" aria-label={`${test}: ${t.edge} (mm) vs ${t.time} (s). ${t.measured} ${comparison.vf_measured_mm_s.toFixed(2)} mm/s; ${t.published} ${comparison.vf_published_mm_s.toFixed(2)} mm/s.`}>
            <defs><clipPath id="ffClip"><rect ref={refs.clip} x={PAD.l} y="0" width="0" height={H} /></clipPath>
              <linearGradient id="ffLine" x1="0" x2="1"><stop offset="0" stopColor="#228bdf" /><stop offset="1" stopColor="#77c3ed" /></linearGradient></defs>
            {geo.yTicks.map(v => <g key={v}><line x1={PAD.l} x2={W - PAD.r} y1={geo.Y(v)} y2={geo.Y(v)} className="ff-grid" /><text x={PAD.l - 8} y={geo.Y(v) + 3} textAnchor="end" className="ff-tick">{v}</text></g>)}
            {geo.xTicks.map(v => <text key={v} x={geo.X(v)} y={H - 12} textAnchor="middle" className="ff-tick">{v.toFixed(0)}</text>)}
            <rect x={geo.X(T0)} y={PAD.t} width={geo.X(T1) - geo.X(T0)} height={H - PAD.t - PAD.b} className="ff-interval" />
            <text x={geo.X(T0) + 6} y={PAD.t + 12} className="ff-tick ff-interval-label">{t.interval}</text>
            <g clipPath="url(#ffClip)">
              <path d={geo.d} fill="none" stroke="url(#ffLine)" strokeWidth="1.6" />
              {geo.fit && <path d={geo.fit} fill="none" stroke="#ff5a3d" strokeWidth="2" strokeDasharray="6 5" />}
            </g>
            <g ref={refs.dot}><circle r="10" className="ff-dot-halo" /><circle r="3.5" fill="#f2f3ed" /></g>
            <text x={W - PAD.r} y={H - PAD.b - 6} textAnchor="end" className="ff-axis">s</text><text x={PAD.l - 8} y={12} textAnchor="end" className="ff-axis">mm</text>
          </svg>}
        <svg className="ff-strip" viewBox="0 0 540 90" aria-hidden="true">
          <rect x="20" y="34" width="500" height="22" className="ff-strip-sample" />
          <rect ref={refs.burnt} x="20" y="34" width="0" height="22" className="ff-strip-burnt" />
          <g ref={refs.front} transform="translate(20 0)">
            <ellipse cx="-4" cy="45" rx="20" ry="30" fill="#ff5a3d" opacity=".35" /><ellipse cx="0" cy="45" rx="10" ry="20" fill="#ffb347" opacity=".75" />
            <path d="M8 22 C 15 34 15 56 8 68" stroke="#77c3ed" strokeWidth="3" fill="none" />
          </g>
          <text x="20" y="84" className="ff-tick">{t.strip}</text>
        </svg>
        <div ref={refs.result} className="ff-result">
          <div><span>{t.measured}</span><b>{comparison.vf_measured_mm_s.toFixed(2)} <small>mm/s</small></b></div>
          <div><span>{t.published}</span><b>{comparison.vf_published_mm_s.toFixed(2)} <small>mm/s</small></b></div>
          <div><span>{t.relative}</span><b>{(comparison.rel_error * 100).toFixed(2)} <small>%</small></b></div>
        </div>
        <figcaption><span>{t.warning}</span><span>{`${t.dataLabel}: public/data/bass/series/${test}.json · ${series?.length ?? '—'} ${t.frames} · ${t.comparisonSource}: ${comparison.source}`}</span></figcaption>
        <i ref={refs.bar} className="ff-bar" aria-hidden="true" />
      </figure>
    </div>
  </section>;
}
