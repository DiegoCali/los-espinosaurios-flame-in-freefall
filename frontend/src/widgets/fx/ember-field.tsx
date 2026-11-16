'use client';
import { useEffect, useRef } from 'react';
import { getLenis } from '@/shared/motion/smooth-scroll';

type Ember = { x: number; y: number; vx: number; vy: number; r: number; hue: 'blue' | 'soot'; life: number; phase: number };

/**
 * Decorative background layer: slow isotropic drift (no upward buoyant bias) to evoke
 * microgravity. Blue points echo chemiluminescent edges, warm points echo incandescent soot.
 * It is purely illustrative and carries no data.
 */
export function EmberField() {
  const canvas = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    const el = canvas.current!;
    const ctx = el.getContext('2d');
    if (!ctx) return;
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    let w = 0, h = 0, raf = 0, embers: Ember[] = [], pointer = { x: -9999, y: -9999 };
    const dpr = Math.min(window.devicePixelRatio || 1, 1.5);
    const spawn = (anywhere = true): Ember => ({
      x: Math.random() * w, y: anywhere ? Math.random() * h : h + 10,
      vx: (Math.random() - .5) * .16, vy: (Math.random() - .5) * .16,
      r: Math.random() * 1.6 + .4, hue: Math.random() < .72 ? 'blue' : 'soot', life: Math.random(), phase: Math.random() * Math.PI * 2,
    });
    const resize = () => {
      w = window.innerWidth; h = window.innerHeight;
      el.width = w * dpr; el.height = h * dpr; el.style.width = `${w}px`; el.style.height = `${h}px`;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      const target = Math.min(110, Math.round((w * h) / 16000));
      embers = Array.from({ length: target }, () => spawn());
    };
    const draw = (t: number) => {
      ctx.clearRect(0, 0, w, h);
      const velocity = getLenis()?.velocity ?? 0;
      for (const e of embers) {
        // Brownian-like drift: tiny random accelerations, damped, no gravity term.
        e.vx = (e.vx + (Math.random() - .5) * .012) * .995;
        e.vy = (e.vy + (Math.random() - .5) * .012) * .995;
        const dx = e.x - pointer.x, dy = e.y - pointer.y, d2 = dx * dx + dy * dy;
        if (d2 < 14000) { const f = (1 - d2 / 14000) * .06; e.vx += dx * f * .02; e.vy += dy * f * .02; }
        e.x += e.vx; e.y += e.vy - velocity * e.r * .18;
        if (e.x < -20) e.x = w + 20; if (e.x > w + 20) e.x = -20;
        if (e.y < -20) e.y = h + 20; if (e.y > h + 20) e.y = -20;
        const flicker = .55 + .45 * Math.sin(t * .0016 + e.phase);
        const g = ctx.createRadialGradient(e.x, e.y, 0, e.x, e.y, e.r * 7);
        if (e.hue === 'blue') { g.addColorStop(0, `rgba(160,220,255,${.75 * flicker})`); g.addColorStop(.35, `rgba(34,139,223,${.28 * flicker})`); }
        else { g.addColorStop(0, `rgba(255,214,150,${.7 * flicker})`); g.addColorStop(.35, `rgba(255,110,40,${.22 * flicker})`); }
        g.addColorStop(1, 'rgba(0,0,0,0)');
        ctx.fillStyle = g; ctx.beginPath(); ctx.arc(e.x, e.y, e.r * 7, 0, Math.PI * 2); ctx.fill();
      }
      if (!reduced) raf = requestAnimationFrame(draw);
    };
    const move = (ev: PointerEvent) => { pointer = { x: ev.clientX, y: ev.clientY }; };
    const visibility = () => { cancelAnimationFrame(raf); if (!document.hidden && !reduced) raf = requestAnimationFrame(draw); };
    resize(); draw(0);
    window.addEventListener('resize', resize); window.addEventListener('pointermove', move, { passive: true }); document.addEventListener('visibilitychange', visibility);
    return () => { cancelAnimationFrame(raf); window.removeEventListener('resize', resize); window.removeEventListener('pointermove', move); document.removeEventListener('visibilitychange', visibility); };
  }, []);
  return <canvas ref={canvas} className="fx-embers" aria-hidden="true" />;
}
