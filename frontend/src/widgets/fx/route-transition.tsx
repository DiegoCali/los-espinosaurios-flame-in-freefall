'use client';
import { useLayoutEffect, useRef } from 'react';
import { usePathname } from 'next/navigation';
import { createTimeline, stagger } from 'animejs';
import { scrambleFrame } from '@/shared/motion/anime';
import { getLenis } from '@/shared/motion/smooth-scroll';

const BARS = 9;

/**
 * "Ignition wipe" between archive pages: a column of flame-coloured shutters covers the
 * freshly rendered route before paint and burns away from the centre outwards.
 */
export function RouteTransition() {
  const pathname = usePathname();
  const root = useRef<HTMLDivElement>(null), label = useRef<HTMLSpanElement>(null);
  const first = useRef(true);
  useLayoutEffect(() => {
    if (first.current) { first.current = false; return; }
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    const el = root.current!, bars = el.querySelectorAll('.fx-wipe-bar');
    getLenis()?.scrollTo(0, { immediate: true });
    const text = `> ${pathname.split('/').filter(Boolean).slice(1).join(' / ').toUpperCase() || 'HOME'}`;
    el.style.visibility = 'visible';
    const proxy = { p: 0 };
    const tl = createTimeline({ onComplete: () => { el.style.visibility = 'hidden'; } })
      .set(bars, { scaleY: 1, opacity: 1 })
      .set(el.querySelector('.fx-wipe-core')!, { opacity: 1, scale: 1 })
      .add(proxy, { p: 1, duration: 420, ease: 'linear', onUpdate: () => { if (label.current) label.current.textContent = scrambleFrame(text, proxy.p); } }, 0)
      .add(el.querySelector('.fx-wipe-scan')!, { translateY: ['-10vh', '110vh'], duration: 520, ease: 'inOut(2)' }, 0)
      .add(el.querySelector('.fx-wipe-core')!, { opacity: 0, scale: 1.6, duration: 380, ease: 'out(3)' }, 420)
      .add(bars, { scaleY: 0, duration: 620, ease: 'inOut(4)', delay: stagger(42, { from: 'center' }) }, 440);
    return () => { tl.revert(); el.style.visibility = 'hidden'; };
  }, [pathname]);
  return <div ref={root} className="fx-wipe" aria-hidden="true">
    {Array.from({ length: BARS }, (_, i) => <i key={i} className="fx-wipe-bar" />)}
    <i className="fx-wipe-scan" />
    <div className="fx-wipe-core"><b>S//L</b><span ref={label} /></div>
  </div>;
}
