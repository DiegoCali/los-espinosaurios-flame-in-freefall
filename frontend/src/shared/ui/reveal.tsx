'use client';
import { motion, useReducedMotion } from 'motion/react';
import type { ReactNode } from 'react';

export function Reveal({ children, className, id, ...props }: { children: ReactNode; className?: string; id?: string; 'aria-labelledby'?: string }) {
  const reduced = useReducedMotion();
  return <motion.section {...props} id={id} className={className} initial={false} whileInView={{ opacity: [0.85, 1], y: reduced ? 0 : [8, 0] }} viewport={{ once: true, amount: .08 }} transition={{ duration: reduced ? .1 : .22, ease: [.22, 1, .36, 1] }}>{children}</motion.section>;
}
