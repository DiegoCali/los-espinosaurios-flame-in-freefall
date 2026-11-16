'use client';
import { useEffect } from 'react';
import Lenis from 'lenis';
import 'lenis/dist/lenis.css';

// One Lenis instance per document. Other widgets (menu dialog) pause it through these helpers.
let instance: Lenis | null = null;
export const getLenis = () => instance;
export const pauseScroll = () => instance?.stop();
export const resumeScroll = () => instance?.start();

/**
 * Slow, weighted scrolling for the whole archive. A low lerp gives the "floating in
 * microgravity" feel; it is disabled entirely for people who prefer reduced motion.
 */
export function SmoothScroll() {
  useEffect(() => {
    const media = window.matchMedia('(prefers-reduced-motion: reduce)');
    if (media.matches) return;
    const lenis = new Lenis({ lerp: 0.075, wheelMultiplier: 0.85, touchMultiplier: 1.2, smoothWheel: true, anchors: { offset: -24 }, autoRaf: true, prevent: node => node.closest?.('[data-lenis-prevent]') != null });
    instance = lenis;
    document.documentElement.dataset.smooth = 'on';
    return () => { lenis.destroy(); instance = null; delete document.documentElement.dataset.smooth; };
  }, []);
  return null;
}
