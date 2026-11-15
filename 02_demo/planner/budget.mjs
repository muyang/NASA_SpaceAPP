export function breakEven(inputs){
 const fields=['seedFreight','establishment','termination','other','payment','price'];
 for(const key of fields){const v=inputs[key];if(v===null||v===undefined||String(v).trim()===''||!Number.isFinite(Number(v))||Number(v)<0||Number(v)>1e9)return {ok:false,reason:'missing_or_invalid'};}
 if(Number(inputs.price)<=0)return {ok:false,reason:'price'};
 if(inputs.complete!==true)return {ok:false,reason:'review'};
 const cost=['seedFreight','establishment','termination','other'].reduce((sum,k)=>sum+Number(inputs[k]),0);
 return {ok:true,cost,payment:Number(inputs.payment),price:Number(inputs.price),requiredYieldChange:(cost-Number(inputs.payment))/Number(inputs.price),scope:'one rye-to-soy episode; conditional break-even threshold only'};
}
