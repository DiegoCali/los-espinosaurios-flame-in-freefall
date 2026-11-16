export {default as acmeEvidence} from './evidence.json';
export {default as acmeModel} from './model.json';
export {default as validationRows} from '../../../public/data/acme/validation.json';
import type rows from '../../../public/data/acme/validation.json';
export type AcmeValidationRow = typeof rows[number];
export type AcmeExperiment = {test_id:string;flame_type:'Normal'|'Inverse';ambient_reactant_fraction_initial:number;tad_calculated_k:number;split:string;group_id:string};
