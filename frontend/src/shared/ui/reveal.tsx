'use client';
import { motion, useReducedMotion } from 'motion/react';
import type { ReactNode } from 'react';

/**
 * Section entrance used across the archive: content rises out of a soft blur while a
 * thin scan line crosses it. Reduced motion falls back to a short fade.
 */
export function Reveal({ children, className, id, ...props }: { children: ReactNode; className?: string; id?: string; 'aria-labelledby'?: string }) {
  const reduced = useReducedMotion();
  return <motion.section {...props} id={id} className={`${className ?? ''} fx-reveal`} initial={reduced ? { opacity: .9 } : { opacity: 0, y: 56, filter: 'blur(8px)' }} whileInView={{ opacity: 1, y: 0, filter: 'blur(0px)' }} viewport={{ once: true, amount: .08 }} transition={{ duration: reduced ? .12 : 1.1, ease: [.16, 1, .3, 1] }}>
    {!reduced && <motion.i aria-hidden="true" className="fx-reveal-scan" initial={{ scaleX: 0, opacity: 1 }} whileInView={{ scaleX: [0, 1, 1], opacity: [1, 1, 0] }} viewport={{ once: true, amount: .08 }} transition={{ duration: 1.4, ease: [.65, 0, .35, 1], times: [0, .6, 1] }} />}
    {children}
  </motion.section>;
}
