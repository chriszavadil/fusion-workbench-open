// MIT. Necessary fixed-point current budget only; never a new plant-power prediction.
const $=id=>document.getElementById(id);let packet=null;
const f=(x,n=3)=>Number(x).toFixed(n);
function show(){if(!packet)return;const c=packet.cases.find(v=>v.case===$('gate-case').value),eff=Number($('gate-efficiency').value);if(!c||!Number.isFinite(eff)||eff<=0)return;
 const current=c.required_current_MA*1000,required=current/eff,slack=c.injected_ceiling_MW-c.retained_heat_only_allocation_MW-required;
 $('gate-current').textContent=`${f(c.required_current_MA)} MA externally driven current`;
 $('gate-threshold').textContent=`At least ${f(c.minimum_efficiency_at_retained_reserve_kA_per_MW)} kA/MW with ${f(c.retained_heat_only_allocation_MW,0)} MW retained heating-only.`;
 $('gate-budget').textContent=`At the selected ${f(eff,1)} kA/MW, the frozen current requirement takes ${f(required,2)} MW of drive power. After retaining the stated heating-only allocation, ${slack>=0?f(slack,2)+' MW remains':f(-slack,2)+' MW is missing'} under the 200 MW injected ceiling.`;
 $('gate-verdict').textContent=slack>=-1e-8?'Necessary total-current budget fits. Heating, deposition, current profile and control are still unvalidated.':'This efficiency cannot sustain the exact frozen current allocation within the stated power budget. This does not rule out another reoptimized reactor.';
 $('gate-conventions').textContent=`This PROCESS point records normalized gamma=${c.model_normalized_gamma} and dimensionless efficiency=${f(c.model_dimensionless_efficiency,6)}. They are different conventions; a paper using dimensionless zeta=0.3 does not validate this model input gamma=0.3.`;
}
$('gate-case').addEventListener('change',show);$('gate-efficiency').addEventListener('change',show);
fetch('actuator.json').then(r=>{if(!r.ok)throw Error();return r.json();}).then(d=>{if(d.schema!=='fusion.actuator-requirement-gate.v1'||d.physical_validation!==false||d.new_solver_runs!==0)throw Error();packet=d;
 for(const c of d.cases){const o=document.createElement('option');o.value=c.case;o.textContent=`${c.retained_heat_only_allocation_MW} MW heating-only / ${f(c.required_current_MA)} MA target`;$('gate-case').append(o);}
 show();}).catch(()=>{$('gate-verdict').textContent='Requirement data unavailable. No substitute actuator or power prediction is shown.';});
