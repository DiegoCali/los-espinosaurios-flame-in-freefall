export type MaterialGroup = 'other' | 'silicone';
export type SaffireModel = {coefficients:{silicone_location:number;non_silicone_location:number};flowRange:number[]};

export function evaluateSaffire(model:SaffireModel, group:MaterialGroup, flow:number):number {
 if ((group !== 'other' && group !== 'silicone') || !Number.isFinite(flow) || flow < model.flowRange[0] || flow > model.flowRange[1]) throw new RangeError('SAFFIRE_INPUT_OUT_OF_DOMAIN');
 return group === 'silicone' ? model.coefficients.silicone_location : model.coefficients.non_silicone_location * (20 / flow);
}
