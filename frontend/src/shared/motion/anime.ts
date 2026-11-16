'use client';
import { useEffect, type DependencyList, type RefObject } from 'react';
import { createScope, type Scope } from 'animejs';

export const prefersReducedMotion = () => typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

/**
 * Runs anime.js code inside a scope bound to a React root. Every animation, timer and
 * scroll observer created in `setup` is reverted when the component unmounts.
 * `setup` receives `reduced` so each effect can choose a static end state.
 */
export function useAnimeScope(root: RefObject<HTMLElement | SVGElement | null>, setup: (reduced: boolean, scope: Scope) => void | (() => void), deps: DependencyList = []) {
  useEffect(() => {
    if (!root.current) return;
    const reduced = prefersReducedMotion();
    let cleanup: void | (() => void);
    const scope = createScope({ root: root as { current: HTMLElement } }).add(self => { cleanup = setup(reduced, self!); });
    return () => { cleanup?.(); scope.revert(); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
}

const GLYPHS = '01<>/\\[]{}#%&*+=-_ABCDEFGHIJKLMNOPQRSTUVWXYZ';

/** Deterministic-length decode effect: characters resolve left to right into the final text. */
export function scrambleFrame(finalText: string, progress: number) {
  const settled = Math.floor(finalText.length * progress);
  let out = finalText.slice(0, settled);
  for (let i = settled; i < finalText.length; i++) {
    const ch = finalText[i];
    out += ch === ' ' || ch === '\n' ? ch : GLYPHS[(Math.random() * GLYPHS.length) | 0];
  }
  return out;
}
