import {acmeModel,validationRows} from '@/entities/acme/data';
import {predictAcme,outsideAcmeTrainingDomain} from '@/entities/acme/model';
export type FlameType = 'Normal' | 'Inverse';
export const acmePresets = {Normal:[.21,.30,.39],Inverse:[.10,.20,.27]} as const;
export function acmeScenario(type:FlameType,fraction:number){
 const presets=acmePresets[type];
 if(!Number.isFinite(fraction)||fraction<presets[0]||fraction>presets[2])throw new RangeError('ACME_SCENARIO_OUT_OF_RANGE');
 const anchor=validationRows.find(r=>r.test_id===(type==='Normal'?'19150N1':'21361D1'))!;
 const inputs=[...anchor.inputs];inputs[2]=fraction;
 const referenceInputs=[...anchor.inputs];referenceInputs[2]=presets[1];
 const value=predictAcme(acmeModel,inputs),reference=predictAcme(acmeModel,referenceInputs);
 return {anchor,inputs,value,reference,delta:value-reference,outsideDomain:outsideAcmeTrainingDomain(acmeModel,inputs)};
}
