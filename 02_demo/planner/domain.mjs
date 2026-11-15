export const VERSION = 1;
export const AREA_FACTOR = 2.4710538147;
export const defaults = () => ({version:VERSION,lang:'en',step:1,name:'',area:'',unit:'ac',lastCrop:'unknown',use:'grain',water:'unknown',waterBudget:'',establishment:'unknown',termination:'unknown',oatsMarket:'unknown',budget:'',priorities:['cover','water','income','cost'],selected:['S0','S1','S2'],notes:'',reviewed:[]});
export const enums = {lang:['en','zh'],unit:['ac','ha'],lastCrop:['unknown','corn','soy'],use:['grain','other','unknown'],water:['unknown','rainfed','irrigated'],establishment:['unknown','owned','custom','unavailable'],termination:['unknown','owned','custom','unavailable'],oatsMarket:['unknown','buyer','feed','exploring','none']};
export const priorities = ['cover','water','income','cost'];
export const esc = x => String(x ?? '').replace(/[&<>"']/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export function sanitize(raw) {
  if (!raw || typeof raw!=='object' || raw.version!==VERSION) throw Error('Unsupported draft format');
  const d=defaults();
  for (const [k,values] of Object.entries(enums)) if(values.includes(raw[k])) d[k]=raw[k];
  for(const k of ['name','notes']) if(typeof raw[k]==='string') d[k]=raw[k].slice(0,k==='notes'?4000:100);
  for(const k of ['area','waterBudget','budget']) if(raw[k]==='' || (['string','number'].includes(typeof raw[k]) && String(raw[k]).trim()!=='' && Number.isFinite(Number(raw[k])) && Number(raw[k])>=0 && Number(raw[k])<=1e8)) d[k]=String(raw[k]);
  for(const [k,allowed] of Object.entries({priorities,selected:['S0','S1','S2'],reviewed:['timing','water','costs','market','soil','risk']})) if(Array.isArray(raw[k])) d[k]=[...new Set(raw[k].filter(x=>allowed.includes(x)))];
  if(!d.priorities.length) d.priorities=defaults().priorities;
  d.priorities=[...d.priorities,...priorities.filter(x=>!d.priorities.includes(x))];
  d.step=Number.isInteger(raw.step)&&raw.step>=1&&raw.step<=4?raw.step:1;
  return d;
}
export function convertArea(value,from,to){ return value===''?'':String(Number((Number(value)*(from===to?1:from==='ac'?1/AREA_FACTOR:AREA_FACTOR)).toFixed(4))); }
export function evaluate(d,id){
  const blocked=[], gaps=[];
  if(d.lastCrop==='unknown') gaps.push('history');
  if(d.use!=='grain') gaps.push('endUse');
  if(d.water==='unknown') gaps.push('waterUnknown');
  if(d.water==='irrigated') gaps.push('irrigated');
  if(id!=='S0'){
    if(d.establishment==='unavailable') blocked.push('establishment');
    else if(d.establishment==='unknown') gaps.push('establishment');
    else if(d.establishment==='custom') gaps.push('customEstablishment');
    if(d.termination==='unavailable') blocked.push('termination');
    else if(d.termination==='unknown') gaps.push('termination');
    else if(d.termination==='custom') gaps.push('customTermination');
    gaps.push('timing','costs');
  }
  if(id==='S2'){
    if(d.oatsMarket==='none') blocked.push('market');
    else if(['unknown','exploring'].includes(d.oatsMarket)) gaps.push('market');
    else gaps.push(d.oatsMarket==='buyer'?'buyerTerms':'feedTerms');
  }
  gaps.push('fieldValidation');
  return {status:blocked.length?'blocked':'review',blocked,gaps:[...new Set(gaps)]};
}
export function validateField(d){
  if(d.area!=='' && (!Number.isFinite(Number(d.area)) || Number(d.area)<=0 || Number(d.area)>1000000)) return 'area';
  return null;
}
export function validateLimits(d){
  for(const k of ['budget',...(d.water==='irrigated'?['waterBudget']:[])]) if(d[k]!==''&&(!Number.isFinite(Number(d[k]))||Number(d[k])<0||Number(d[k])>1e8)) return k;
  return null;
}
