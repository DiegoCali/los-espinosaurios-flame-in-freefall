'use client';
import { motion, useReducedMotion } from 'motion/react';
export function MethodSignal(){const reduced=useReducedMotion();return <motion.span aria-hidden="true" className="method-signal" initial={false} whileInView={{scaleX:reduced?1:[0,1]}} viewport={{once:true}} transition={{duration:.5,ease:'easeOut'}}/>;}
