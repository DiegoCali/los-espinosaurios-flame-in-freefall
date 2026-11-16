'use client';
import { useEffect } from 'react';
import { usePathname } from 'next/navigation';
import { animate, splitText, stagger } from 'animejs';
import { scrambleFrame } from '@/shared/motion/anime';

/**
 * Route-level motion layer for every archive page, applied to static markup only:
 *  - the page title assembles character by character,
 *  - section titles decode when they enter the viewport,
 *  - KPI figures count up to their exact published string.
 * Every mutation restores the original text, so values shown at rest are untouched.
 */
export function PageEnhancer() {
  const pathname = usePathname();
  useEffect(() => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    const cleanups: (() => void)[] = [];
    const main = document.querySelector('main');
    if (!main) return;
    const wait = document.documentElement.dataset.booted ? 120 : 3000;

    const title = main.querySelector<HTMLElement>('h1:not([data-fx-skip])');
    if (title && title.offsetParent !== null) {
      const timer = window.setTimeout(() => {
        const split = splitText(title, { chars: { class: 'fx-char' }, accessible: true });
        const anim = animate(split.chars, { opacity: [0, 1], translateY: ['0.7em', '0em'], rotateX: [-80, 0], filter: ['blur(6px)', 'blur(0px)'], duration: 900, delay: stagger(16), ease: 'out(4)', onComplete: () => split.revert() });
        cleanups.push(() => { anim.revert(); split.revert(); });
      }, wait);
      cleanups.push(() => clearTimeout(timer));
    }

    const observer = new IntersectionObserver(entries => {
      for (const entry of entries) {
        if (!entry.isIntersecting) continue;
        observer.unobserve(entry.target);
        const el = entry.target as HTMLElement, original = el.textContent ?? '';
        if (el.matches('h2')) {
          const p = { v: 0 };
          const a = animate(p, { v: 1, duration: 760, ease: 'out(2)', onUpdate: () => { el.textContent = scrambleFrame(original, p.v); }, onComplete: () => { el.textContent = original; } });
          cleanups.push(() => { a.pause(); el.textContent = original; });
        } else {
          const match = original.match(/^([+−-]?)(\d+(?:[.,]\d+)?)([^]*)$/);
          if (!match) continue;
          const [, sign, num, rest] = match, decimals = (num.split(/[.,]/)[1] ?? '').length, width = num.split(/[.,]/)[0].length, target = parseFloat(num.replace(',', '.'));
          const p = { v: 0 };
          const a = animate(p, { v: target, duration: 1600, ease: 'out(4)', onUpdate: () => { el.textContent = `${sign}${p.v.toFixed(decimals).padStart(width + (decimals ? decimals + 1 : 0), '0')}${rest}`; }, onComplete: () => { el.textContent = original; } });
          cleanups.push(() => { a.pause(); el.textContent = original; });
        }
      }
    }, { threshold: .4 });
    // Only leaf headings (no nested responsive spans) are decoded, so markup is never lost.
    main.querySelectorAll<HTMLElement>('h2').forEach(h => { if (!h.childElementCount && !h.dataset.fxSkip) observer.observe(h); });
    main.querySelectorAll<HTMLElement>('[class$="-kpis"] strong, [data-count]').forEach(s => { if (!s.childElementCount) observer.observe(s); });
    cleanups.push(() => observer.disconnect());
    return () => cleanups.forEach(fn => fn());
  }, [pathname]);
  return null;
}
