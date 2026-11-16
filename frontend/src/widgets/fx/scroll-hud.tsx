'use client';
import { useEffect, useRef } from 'react';
import { motion, useMotionValueEvent, useScroll, useSpring } from 'motion/react';
import { usePathname } from 'next/navigation';

/** Fixed telemetry rail: scroll progress and the current archive path. */
export function ScrollHud() {
  const { scrollYProgress } = useScroll();
  const progress = useSpring(scrollYProgress, { stiffness: 90, damping: 24, mass: .4 });
  const readout = useRef<HTMLSpanElement>(null);
  const pathname = usePathname();
  useMotionValueEvent(progress, 'change', v => { if (readout.current) readout.current.textContent = String(Math.round(Math.min(1, Math.max(0, v)) * 100)).padStart(3, '0'); });
  useEffect(() => { if (readout.current) readout.current.textContent = '000'; }, [pathname]);
  const segments = pathname.split('/').filter(Boolean).slice(1);
  const label = segments.length ? segments.join(' / ').toUpperCase() : 'HOME';
  return <div className="fx-hud" aria-hidden="true">
    <motion.div className="fx-progress" style={{ scaleX: progress }} />
    <div className="fx-rail">
      <span className="fx-rail-label">S//L · {label}</span>
      <div className="fx-rail-track"><motion.i style={{ scaleY: progress }} /></div>
      <span className="fx-rail-value"><span ref={readout}>000</span>%</span>
    </div>
  </div>;
}
