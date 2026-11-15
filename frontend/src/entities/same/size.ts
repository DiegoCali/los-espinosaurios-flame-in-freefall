export const sizeTargets = ['log10_dm_um', 'log10_dg_um', 'log10_amd_um', 'ln_sigma_g', 'log10_m0_per_cc'] as const;
export type SizeTarget = typeof sizeTargets[number];
export type SizeValues = Record<SizeTarget, number>;
export type SizeRow = { task: 'size'; run: number; source_row: number; material: string; aged_state: string; actual: SizeValues; predicted: SizeValues; residual: SizeValues; source_pointer: string };
export const sizeLabels: Record<SizeTarget, string> = {log10_dm_um: 'D_m / μm', log10_dg_um: 'D_g / μm', log10_amd_um: 'AMD / μm', ln_sigma_g: 'σg / 1', log10_m0_per_cc: 'M₀ / cm⁻³'};
export function physicalSize(target: SizeTarget, value: number): number {
  return target === 'ln_sigma_g' ? Math.exp(value) : 10 ** value;
}
