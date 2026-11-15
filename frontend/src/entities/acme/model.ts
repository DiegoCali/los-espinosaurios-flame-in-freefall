export type AcmeModel = {
 means:number[];scales:number[];coefficients:number[];
 trainingDomains:Record<'Normal'|'Inverse',{min:number[];max:number[]}>;
};

/** Exact frozen Ridge feature order; returns calculated Tad in K, never measured flame temperature. */
export function predictAcme(model:AcmeModel, x:readonly number[]):number {
 if (x.length !== 7 || !x.every(Number.isFinite) || (x[0] !== 0 && x[0] !== 1)
   || x[1] < 0 || x[1] > 1 || x[2] < 0 || x[2] > 1
   || x.slice(3,6).some(v=>v<0) || x[6] <= 0
   || Math.abs(x[3]+x[4]-x[5]) > 1e-6) throw new RangeError('ACME_INVALID_PHYSICAL_INPUTS');
 if (model.means.length !== 9 || model.scales.length !== 9 || model.coefficients.length !== 11
   || ![...model.means,...model.scales,...model.coefficients].every(Number.isFinite)
   || model.scales.some(v=>v<=0)) throw new RangeError('ACME_INVALID_FROZEN_MODEL');
 const features=[...x.slice(1),x[1]**2,x[1]*x[2],x[2]**2];
 let result=model.coefficients[0]+x[0]*model.coefficients[1];
 for(let i=0;i<features.length;i++) result+=(features[i]-model.means[i])/model.scales[i]*model.coefficients[i+2];
 return result;
}

/** A domain warning is separate from mathematical evaluation; marginal bounds do not prove joint support. */
export function outsideAcmeTrainingDomain(model:AcmeModel,x:readonly number[]):boolean {
 predictAcme(model,x);
 const domain=model.trainingDomains[x[0]===1?'Inverse':'Normal'];
 return x.some((v,i)=>v<domain.min[i] || v>domain.max[i]);
}
