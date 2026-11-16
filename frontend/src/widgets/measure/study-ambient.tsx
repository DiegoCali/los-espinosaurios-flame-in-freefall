'use client';
import { useEffect, useRef } from 'react';
import './measure.css';

export type AmbientTheme = 'acme' | 'bass' | 'saffire' | 'same' | 'flex';
type P = { x: number; y: number; vx: number; vy: number; r: number; a: number; s: number; life: number };

/**
 * Per-record microgravity backdrop for the page hero. Every theme drifts without a gravity
 * term; motifs follow each study's subject. Decorative only (aria-hidden), no data.
 *  acme    – spherical diffusion-flame shells around a burner
 *  bass    – opposed-flow streaks and a blue leading edge crossing a sample
 *  saffire – CO₂ molecules drifting in forced air flow
 *  same    – smoke particles slowly coagulating into clusters
 *  flex    – floating droplets with flame halos that shrink
 */
export function StudyAmbient({ theme, label }: { theme: AmbientTheme; label: string }) {
  const canvas = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    const el = canvas.current!, ctx = el.getContext('2d');
    if (!ctx) return;
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const dpr = Math.min(window.devicePixelRatio || 1, 1.5);
    let w = 0, h = 0, raf = 0, ps: P[] = [], visible = true;
    const rnd = (a: number, b: number) => a + Math.random() * (b - a);
    const make = (): P => ({ x: rnd(0, w), y: rnd(0, h), vx: rnd(-.15, .15), vy: rnd(-.15, .15), r: rnd(1, 3), a: rnd(0, Math.PI * 2), s: rnd(-.01, .01), life: Math.random() });
    const resize = () => {
      const box = el.parentElement!.getBoundingClientRect();
      w = box.width; h = box.height; el.width = w * dpr; el.height = h * dpr; el.style.width = `${w}px`; el.style.height = `${h}px`;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      const count = { acme: 70, bass: 60, saffire: 34, same: 120, flex: 9 }[theme];
      ps = Array.from({ length: count }, make);
      if (theme === 'flex') ps.forEach(p => { p.r = rnd(10, 30); p.vx *= .6; p.vy *= .6; });
      if (theme === 'bass') ps.forEach(p => { p.vx = -rnd(.6, 1.6); p.vy = rnd(-.04, .04); });
    };
    const glow = (x: number, y: number, r: number, c0: string, c1: string) => { const g = ctx.createRadialGradient(x, y, 0, x, y, r); g.addColorStop(0, c0); g.addColorStop(1, c1); ctx.fillStyle = g; ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.fill(); };
    const frame = (time: number) => {
      ctx.clearRect(0, 0, w, h);
      const T = time / 1000;
      if (theme === 'acme') {
        const cx = w * .78, cy = h * .5;
        for (let k = 0; k < 4; k++) {
          const rr = ((T * 22 + k * 60) % 240) + 30, alpha = Math.max(0, 1 - rr / 270);
          ctx.strokeStyle = `rgba(119,195,237,${alpha * .45})`; ctx.lineWidth = 1.2; ctx.beginPath(); ctx.arc(cx, cy, rr, 0, Math.PI * 2); ctx.stroke();
        }
        glow(cx, cy, 120 + Math.sin(T * 1.6) * 6, 'rgba(255,179,71,.18)', 'rgba(255,179,71,0)');
        ctx.strokeStyle = 'rgba(200,25,54,.7)'; ctx.lineWidth = 2; ctx.beginPath(); ctx.arc(cx, cy, 90 + Math.sin(T * 1.6) * 4, 0, Math.PI * 2); ctx.stroke();
        ctx.fillStyle = '#0f1720'; ctx.strokeStyle = '#228bdf'; ctx.beginPath(); ctx.arc(cx, cy, 24, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
        for (const p of ps) { // reactants diffusing radially toward the flame sheet
          const d = Math.hypot(p.x - cx, p.y - cy) || 1; p.vx += ((cx - p.x) / d) * .004; p.vy += ((cy - p.y) / d) * .004;
          p.vx *= .99; p.vy *= .99; p.x += p.vx; p.y += p.vy;
          if (d < 95) { Object.assign(p, make()); }
          ctx.fillStyle = 'rgba(119,195,237,.6)'; ctx.beginPath(); ctx.arc(p.x, p.y, p.r * .7, 0, Math.PI * 2); ctx.fill();
        }
      } else if (theme === 'bass') {
        for (const p of ps) { p.x += p.vx; p.y += p.vy; if (p.x < -40) { p.x = w + 40; p.y = rnd(0, h); }
          ctx.strokeStyle = `rgba(140,158,174,${.18 + p.r * .05})`; ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(p.x, p.y); ctx.lineTo(p.x + 26 * p.r, p.y); ctx.stroke(); }
        const sy = h * .72, front = (T * 38) % (w + 200) - 100;
        ctx.fillStyle = '#16222e'; ctx.fillRect(0, sy, w, 10);
        ctx.fillStyle = '#05080d'; ctx.fillRect(0, sy, Math.max(0, front), 10);
        glow(front - 10, sy + 5, 70, 'rgba(255,90,61,.45)', 'rgba(255,90,61,0)');
        glow(front, sy + 5, 34, 'rgba(255,214,150,.6)', 'rgba(255,214,150,0)');
        ctx.strokeStyle = '#77c3ed'; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(front + 18, sy - 26); ctx.quadraticCurveTo(front + 30, sy + 5, front + 18, sy + 36); ctx.stroke();
      } else if (theme === 'saffire') {
        for (const p of ps) { p.vx = p.vx * .995 + .004; p.vy += rnd(-.01, .01); p.vy *= .99; p.x += p.vx; p.y += p.vy; p.a += p.s;
          if (p.x > w + 40) { p.x = -40; p.y = rnd(0, h); } if (p.y < -20) p.y = h + 20; if (p.y > h + 20) p.y = -20;
          const len = 9 + p.r * 2, dx = Math.cos(p.a) * len, dy = Math.sin(p.a) * len;
          ctx.strokeStyle = 'rgba(140,158,174,.35)'; ctx.lineWidth = 1.2; ctx.beginPath(); ctx.moveTo(p.x - dx, p.y - dy); ctx.lineTo(p.x + dx, p.y + dy); ctx.stroke();
          ctx.fillStyle = 'rgba(242,243,237,.55)'; ctx.beginPath(); ctx.arc(p.x, p.y, 2.6, 0, Math.PI * 2); ctx.fill();
          ctx.fillStyle = 'rgba(255,90,61,.6)'; [-1, 1].forEach(sg => { ctx.beginPath(); ctx.arc(p.x + sg * dx, p.y + sg * dy, 2.2, 0, Math.PI * 2); ctx.fill(); });
        }
      } else if (theme === 'same') {
        const centers = [[w * .65, h * .35], [w * .82, h * .62], [w * .55, h * .7]];
        for (const [i, p] of ps.entries()) { const [cx, cy] = centers[i % 3], phase = (Math.sin(T * .35 + i) + 1) / 2;
          p.vx += (cx - p.x) * .00004 * phase + rnd(-.02, .02); p.vy += (cy - p.y) * .00004 * phase + rnd(-.02, .02); p.vx *= .985; p.vy *= .985; p.x += p.vx; p.y += p.vy;
          ctx.fillStyle = `rgba(157,175,190,${.25 + phase * .4})`; ctx.beginPath(); ctx.arc(p.x, p.y, p.r * (.6 + phase * .9), 0, Math.PI * 2); ctx.fill(); }
      } else {
        for (const p of ps) { p.x += p.vx; p.y += p.vy; p.life += .0012; if (p.life > 1) { Object.assign(p, make(), { r: rnd(10, 30), life: 0 }); }
          if (p.x < -60) p.x = w + 60; if (p.x > w + 60) p.x = -60; if (p.y < -60) p.y = h + 60; if (p.y > h + 60) p.y = -60;
          const r = p.r * Math.sqrt(Math.max(.05, 1 - p.life)); // D² shrinks roughly linearly in time
          ctx.strokeStyle = `rgba(119,195,237,${.5 * (1 - p.life)})`; ctx.lineWidth = 1.5; ctx.beginPath(); ctx.arc(p.x, p.y, r * 2.2, 0, Math.PI * 2); ctx.stroke();
          ctx.fillStyle = '#0f1720'; ctx.strokeStyle = 'rgba(242,243,237,.7)'; ctx.lineWidth = 1; ctx.beginPath(); ctx.arc(p.x, p.y, r, 0, Math.PI * 2); ctx.fill(); ctx.stroke(); }
      }
      if (!reduced && visible) raf = requestAnimationFrame(frame);
    };
    const io = new IntersectionObserver(([e]) => { visible = e.isIntersecting; cancelAnimationFrame(raf); if (visible && !reduced) raf = requestAnimationFrame(frame); });
    resize(); frame(0); io.observe(el);
    const ro = new ResizeObserver(resize); ro.observe(el.parentElement!);
    return () => { cancelAnimationFrame(raf); io.disconnect(); ro.disconnect(); };
  }, [theme]);
  return <div className={`sa sa-${theme}`} aria-hidden="true"><canvas ref={canvas} /><span className="sa-label">{label}</span></div>;
}
