export const detectors = ['iss_detect', 'ion_detect'] as const;
export type Detector = typeof detectors[number];
export type DetectionRow = { task: 'detection'; test: number; push_index: number; material: string; aging_s: number; flow_velocity_cm_s: number; actual: Record<Detector, number>; predicted: Record<Detector, number>; residual: Record<Detector, number>; source_pointer: string };
export const modelAged = (seconds: number) => seconds > 120;
export const telemetryAged = (seconds: number) => seconds >= 120;
