'use client';
import { useEffect, useRef } from 'react';
import { createAnimatable, animate } from 'animejs';

/** Trailing targeting reticle for fine pointers. The native cursor is kept for accessibility. */
export function CursorReticle() {
  const ring = useRef<HTMLDivElement>(null), dot = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!window.matchMedia('(pointer: fine)').matches || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    const r = ring.current!, d = dot.current!;
    const ringA = createAnimatable(r, { x: 520, y: 520, ease: 'out(4)' });
    const dotA = createAnimatable(d, { x: 90, y: 90, ease: 'out(2)' });
    let hovering = false, shown = false;
    const move = (e: PointerEvent) => {
      if (!shown) { shown = true; ringA.x(e.clientX, 0); ringA.y(e.clientY, 0); dotA.x(e.clientX, 0); dotA.y(e.clientY, 0); r.style.opacity = '1'; d.style.opacity = '1'; }
      ringA.x(e.clientX); ringA.y(e.clientY); dotA.x(e.clientX); dotA.y(e.clientY);
      const interactive = (e.target as Element | null)?.closest?.('a,button,[role=button],input,select,summary,label') != null;
      if (interactive !== hovering) {
        hovering = interactive;
        animate(r, { scale: interactive ? 1.75 : 1, rotate: interactive ? 45 : 0, borderColor: interactive ? '#ff5a3d' : '#77c3ed', duration: 420, ease: 'out(3)' });
      }
    };
    const down = () => animate(r, { scale: [hovering ? 1.4 : .8, hovering ? 1.75 : 1], duration: 380, ease: 'out(3)' });
    const leave = () => { r.style.opacity = '0'; d.style.opacity = '0'; };
    const enter = () => { if (shown) { r.style.opacity = '1'; d.style.opacity = '1'; } };
    window.addEventListener('pointermove', move, { passive: true }); window.addEventListener('pointerdown', down);
    document.documentElement.addEventListener('pointerleave', leave); document.documentElement.addEventListener('pointerenter', enter);
    return () => { window.removeEventListener('pointermove', move); window.removeEventListener('pointerdown', down); document.documentElement.removeEventListener('pointerleave', leave); document.documentElement.removeEventListener('pointerenter', enter); ringA.revert(); dotA.revert(); };
  }, []);
  return <><div ref={ring} className="fx-reticle" aria-hidden="true"><i /><i /><i /><i /></div><div ref={dot} className="fx-reticle-dot" aria-hidden="true" /></>;
}
