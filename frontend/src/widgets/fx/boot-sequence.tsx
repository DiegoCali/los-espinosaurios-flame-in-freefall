'use client';
import { useEffect, useRef } from 'react';
import { animate, createTimeline, stagger } from 'animejs';
import { scrambleFrame } from '@/shared/motion/anime';
import { asset } from '@/shared/config';
import { pauseScroll, resumeScroll } from '@/shared/motion/smooth-scroll';
import { BOOT_KEY } from './boot-key';

const LINES = [
  'S//L · LOS ESPINOSAURIOS',
  'NASA PHYSICAL SCIENCES INFORMATICS / PSI',
  'PSI-10 ACME · PSI-25 BASS-II · PSI-99 SAFFIRE-II',
  'PSI-101 SAME-R · PSI-69 FLEX',
  'MICROGRAVITY COMBUSTION ARCHIVE / 2026',
];

/**
 * First-visit ignition sequence (once per browser session). It is server-rendered so it
 * covers the first paint, hidden by an inline head script on later loads, and protected by
 * a CSS failsafe so the archive is never blocked if scripts fail.
 */
export function BootSequence({ skip }: { skip: string }) {
  const root = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const el = root.current!;
    const done = () => {
      try { sessionStorage.setItem(BOOT_KEY, '1'); } catch { /* storage may be blocked */ }
      document.documentElement.dataset.booted = '1'; resumeScroll();
    };
    if (document.documentElement.dataset.booted || window.matchMedia('(prefers-reduced-motion: reduce)').matches) { done(); return; }
    pauseScroll();
    const lines = [...el.querySelectorAll<HTMLElement>('.boot-line')];
    const proxies = lines.map(() => ({ p: 0 }));
    const tl = createTimeline({ defaults: { ease: 'out(3)' } })
      .add(el.querySelectorAll('.boot-ring')[0], { rotate: 160, scale: [.6, 1], opacity: [0, 1], duration: 1500, ease: 'out(4)' }, 0)
      .add(el.querySelectorAll('.boot-ring')[1], { rotate: -200, scale: [.6, 1], opacity: [0, 1], duration: 1500, ease: 'out(4)' }, 0)
      .add(el.querySelector('.boot-emblem')!, { opacity: [0, 1], scale: [.85, 1], filter: ['blur(10px)', 'blur(0px)'], duration: 900 }, 120)
      .add(el.querySelector('.boot-bar i')!, { scaleX: [0, 1], duration: 2100, ease: 'inOut(2)' }, 100);
    lines.forEach((line, i) => {
      const text = line.dataset.text!;
      tl.add(proxies[i], { p: 1, duration: 520, ease: 'linear', onBegin: () => { line.style.opacity = '1'; }, onUpdate: () => { line.textContent = scrambleFrame(text, proxies[i].p); } }, 180 + i * 300);
    });
    tl.add(el.querySelector('.boot-flare')!, { scale: [0, 38], opacity: [1, 1], duration: 900, ease: 'in(3)' }, 2150)
      .add(el, { opacity: 0, duration: 520, ease: 'out(2)', onComplete: () => { el.style.display = 'none'; done(); } }, 2850);
    const pulse = animate(el.querySelectorAll('.boot-tick'), { opacity: [.15, 1], duration: 600, delay: stagger(60), loop: true, alternate: true });
    const skipNow = () => { tl.pause(); pulse.pause(); animate(el, { opacity: 0, duration: 260, onComplete: () => { el.style.display = 'none'; done(); } }); };
    const key = (e: KeyboardEvent) => { if (e.key === 'Escape' || e.key === 'Enter' || e.key === ' ') skipNow(); };
    el.querySelector('.boot-skip')?.addEventListener('click', skipNow); window.addEventListener('keydown', key);
    return () => { tl.revert(); pulse.revert(); window.removeEventListener('keydown', key); resumeScroll(); };
  }, []);
  return <div ref={root} className="boot" aria-hidden="true">
    <div className="boot-grid" />
    <div className="boot-stage">
      <div className="boot-orbit"><img className="boot-ring" src={asset('/assets/outer-ring.svg')} alt="" width="320" height="320" /><img className="boot-ring" src={asset('/assets/inner-ring.svg')} alt="" width="272" height="272" /><img className="boot-emblem" src={asset('/assets/emblem.svg')} alt="" width="250" height="250" /></div>
      <div className="boot-log">{LINES.map((line, i) => <p key={line} className="boot-line" data-text={line} style={{ opacity: 0 }}>{i === 0 ? line : ''}</p>)}</div>
      <div className="boot-bar"><i /></div>
      <div className="boot-ticks">{Array.from({ length: 12 }, (_, i) => <i key={i} className="boot-tick" />)}</div>
    </div>
    <i className="boot-flare" />
    <button type="button" className="boot-skip" tabIndex={-1}>{skip} ›</button>
  </div>;
}
