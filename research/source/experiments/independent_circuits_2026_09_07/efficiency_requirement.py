"""One admitted follow-on: find the efficiency required for the topology benefit.
Not a compressor map, hardware selection, or held-out confirmation.
"""
from pathlib import Path
import json, hashlib
from scipy.optimize import brentq
from compare_circuits import loop, installation, benefit, write, sha
HERE=Path(__file__).resolve().parent

def run():
    prior=json.loads((HERE/'RESULT.json').read_text()); cfg=prior['inputs']['config']
    admission={'question':'How much common efficiency degradation across independent loops erases the predicted net budget?', 'source':'ThermoPower CompressorBase includes eta as a performance input, not a guaranteed value; maps unavailable.', 'selection':'adaptive follow-on to topology comparison, not held-out validation', 'root_bracket_eta':[0.1,cfg['eta']], 'fixed':'Same branch heads, flows, external heat, drive efficiency and conversion assumption; shared topology eta stays0.9', 'stop':'One root for each of four saved cases, no sweep', 'prior_sha256':sha(HERE/'RESULT.json')}
    write('EFFICIENCY_ADMISSION.json',admission); rows=[]
    for r in prior['cases']:
        base=r['independent_regional_circuits']; common=r['shared_balanced']
        def evaluate(eta):
            c={**cfg,'eta':eta}
            candidate=installation([loop(x['flow_kg_s'],x['external_heat_MW'],x['pressure_drop_Pa'],c) for x in base['loops']],c)
            return benefit(common,candidate,cfg['heat_eff'])['fixed_conversion_net_budget_MW']
        critical=brentq(evaluate,.1,cfg['eta'],xtol=1e-11)
        rows.append({'property_choice':r['property_choice'],'external_loss_case':r['external_loss_case'],'minimum_equal_independent_eta_before_auxiliary_penalty':critical,'root_residual_MW':evaluate(critical),'pass_just_above':evaluate(critical+1e-5)>0,'fail_just_below':evaluate(critical-1e-5)<0})
    result={'schema':'fusion.independent-efficiency-budget.v1','admission':admission,'results':rows,'real_circulator_performance_validated':False};write('EFFICIENCY_RESULT.json',result);print(json.dumps(rows,indent=2))
    return result
if __name__=='__main__':run()
