'use client';
import { useRef } from 'react';
import { animate, createAnimatable, createTimeline, onScroll, splitText, stagger, svg, utils } from 'animejs';
import { useAnimeScope } from '@/shared/motion/anime';

const ORBIT = 'M 242 -6 A 248 248 0 1 1 241.9 -6';
const ORBIT_INNER = 'M 242 34 A 208 208 0 1 0 242.1 34';

/**
 * Hero choreography (desktop). Server markup stays intact; this component only animates
 * what is already rendered: title ignition, orbiting rings, a satellite on a motion path,
 * scroll parallax and pointer tilt of the emblem.
 */
export function HeroFx() {
  const anchor = useRef<HTMLSpanElement>(null);
  const root = useRef<HTMLElement | null>(null);
  useAnimeScope(anchor, reduced => {
    const hero = anchor.current!.closest<HTMLElement>('.home-hero');
    if (!hero) return;
    root.current = hero;
    const emblem = hero.querySelector<HTMLElement>('.hero-emblem');
    const lines = [...hero.querySelectorAll<HTMLElement>('.hero-line')];
    const booted = document.documentElement.dataset.booted;
    const start = booted ? 150 : 3050;
    if (reduced) return;

    const splits = lines.map(line => splitText(line, { chars: { class: 'fx-char hero-char' }, accessible: true }));
    const chars = splits.flatMap(s => s.chars);
    utils.set(chars, { opacity: 0 });
    utils.set(hero.querySelectorAll('.hero-intro, .hero-actions .action-button, .hero-metadata span, .hero-emblem img, .hero-emblem .reticle'), { opacity: 0 });
    const tl = createTimeline({ delay: start, defaults: { ease: 'out(4)' }, onComplete: () => splits.forEach(s => s.revert()) })
      .add(chars, { opacity: [0, 1], translateY: ['0.9em', '0em'], rotateX: [-90, 0], color: ['#ffb347', '#f2f3ed'], textShadow: ['0 0 28px #ff5a3d', '0 0 0px #ff5a3d00'], duration: 1100, delay: stagger(22) }, 0)
      .add(hero.querySelector('.hero-marker')!, { scaleX: [0, 1], duration: 900, ease: 'inOut(3)' }, 500)
      .add(hero.querySelector('.hero-intro')!, { opacity: [0, 1], translateY: [24, 0], filter: ['blur(6px)', 'blur(0px)'], duration: 1000 }, 700)
      .add(hero.querySelectorAll('.hero-actions .action-button'), { opacity: [0, 1], translateX: [-30, 0], duration: 800, delay: stagger(120) }, 900)
      .add(hero.querySelectorAll('.hero-metadata span'), { opacity: [0, 1], translateY: [12, 0], duration: 700, delay: stagger(90) }, 1100);

    if (!emblem) return () => tl.revert();
    tl.add(emblem.querySelectorAll('img'), { opacity: [0, 1], scale: [.7, 1], duration: 1600, delay: stagger(160) }, 200)
      .add(emblem.querySelectorAll('.reticle'), { scale: [0, 1], opacity: [0, 1], duration: 600, delay: stagger(80) }, 900);
    const orbits = emblem.querySelectorAll<SVGPathElement>('.hero-orbit-path');
    tl.add(svg.createDrawable(orbits), { draw: ['0 0', '0 1'], duration: 2200, ease: 'inOut(3)', delay: stagger(300) }, 400);

    const spinOuter = animate(emblem.querySelector('.outer-ring')!, { rotate: 360, duration: 90000, ease: 'linear', loop: true });
    const spinInner = animate(emblem.querySelector('.inner-ring')!, { rotate: -360, duration: 140000, ease: 'linear', loop: true });
    const sat = emblem.querySelector('.hero-satellite');
    const sat2 = emblem.querySelector('.hero-satellite.alt');
    const satAnim = sat ? animate(sat, { ...svg.createMotionPath(orbits[0]), duration: 14000, ease: 'linear', loop: true }) : null;
    const satAnim2 = sat2 && orbits[1] ? animate(sat2, { ...svg.createMotionPath(orbits[1]), duration: 21000, ease: 'linear', loop: true }) : null;
    const pulse = animate(emblem.querySelector('.hero-core')!, { scale: [.94, 1.06], opacity: [.55, .9], duration: 2600, ease: 'inOut(2)', loop: true, alternate: true });
    const blink = animate(emblem.querySelector('.red-calibration')!, { opacity: [1, .15], duration: 700, ease: 'inOut(2)', loop: true, alternate: true });

    // Parallax: the emblem floats up slower than the page while the hero scrolls out.
    const parallax = animate(emblem, { translateY: [0, 160], ease: 'linear', autoplay: onScroll({ target: hero, enter: 'start start', leave: 'start end', sync: .4 }) });
    const copy = hero.querySelector('.hero-copy');
    const copyParallax = copy ? animate(copy, { translateY: [0, -60], opacity: [1, .25], ease: 'linear', autoplay: onScroll({ target: hero, enter: 'start start', leave: 'start end', sync: .4 }) }) : null;

    // Pointer tilt
    const tilt = createAnimatable(emblem, { rotateX: 900, rotateY: 900, ease: 'out(3)' });
    const move = (e: PointerEvent) => {
      const r = hero.getBoundingClientRect();
      tilt.rotateY(((e.clientX - r.left) / r.width - .5) * 14);
      tilt.rotateX(-((e.clientY - r.top) / r.height - .5) * 10);
    };
    hero.addEventListener('pointermove', move);
    return () => { hero.removeEventListener('pointermove', move); [tl, spinOuter, spinInner, satAnim, satAnim2, pulse, blink, parallax, copyParallax].forEach(a => a?.revert()); tilt.revert(); splits.forEach(s => s.revert()); };
  });
  return <span ref={anchor} hidden />;
}

/** SVG overlay for the emblem: orbit traces, satellites and a microgravity flame core. */
export function HeroOrbits() {
  return <svg className="hero-orbits" viewBox="-20 -20 524 524" aria-hidden="true">
    <defs>
      <radialGradient id="heroCore" cx="50%" cy="50%" r="50%"><stop offset="0%" stopColor="#d9f1ff" stopOpacity=".9" /><stop offset="28%" stopColor="#77c3ed" stopOpacity=".55" /><stop offset="60%" stopColor="#228bdf" stopOpacity=".18" /><stop offset="100%" stopColor="#020305" stopOpacity="0" /></radialGradient>
    </defs>
    <circle className="hero-core" cx="242" cy="242" r="230" fill="url(#heroCore)" />
    <path className="hero-orbit-path" d={ORBIT} fill="none" stroke="#228bdf" strokeWidth="1" strokeDasharray="2 6" />
    <path className="hero-orbit-path" d={ORBIT_INNER} fill="none" stroke="#c81936" strokeWidth="1" opacity=".6" />
    <g className="hero-satellite"><circle r="5" fill="#77c3ed" /><circle r="12" fill="none" stroke="#77c3ed" strokeOpacity=".4" /></g>
    <g className="hero-satellite alt"><circle r="3.5" fill="#ff5a3d" /><circle r="9" fill="none" stroke="#ff5a3d" strokeOpacity=".4" /></g>
  </svg>;
}
