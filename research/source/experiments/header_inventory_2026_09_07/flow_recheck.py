"""Fair-baseline follow-on: solve flow, do not impose favorable branch shares."""
import json
from pathlib import Path
from scipy.optimize import brentq
from header_inventory import HeaderStudy,load,save,sha
HERE=Path(__file__).resolve().parent

def solve(study,record,extra_ob=0.):
    radii={k:v['geometry']['inner_radius_m'] for k,v in record['branches'].items()}
    choice=record['choice'];split=record['configuration']=='outboard_split';net=study.net
    def cases(mi):
        return study.evaluate('inboard',radii['inboard'],split,choice,mi),study.evaluate('outboard',radii['outboard'],split,choice,net.total-mi)
    def residual(mi):
        ib,ob=cases(mi);added=extra_ob*(ob['branch']['flow_kg_s']/net.nominal['outboard'])**2
        return ib['known_branch_pressure_Pa']-ob['known_branch_pressure_Pa']-added
    mi=brentq(residual,.45*net.nominal['inboard'],1.75*net.nominal['inboard'],xtol=1e-7)
    ib,ob=cases(mi);common=ib['known_branch_pressure_Pa']
    return {'configuration':record['configuration'],'choice':choice,'IB':ib,'OB':ob,'common_pressure_Pa':common,'remaining_common_allowance_Pa':net.allowance-common,'total_flow_kg_s':net.total,'pressure_residual_Pa':residual(mi),'added_OB_drop_at_nominal_Pa':extra_ob,'local_FW_temperature_screen_passed':min(ib['native_temperature_margin_K'],ob['native_temperature_margin_K'])>=0,'physical_manifold_validated':False}
def main():
    st=HeaderStudy(load());prior=json.loads((HERE/'RESULT.json').read_text());answers=[]
    for r in prior['results']:
        unbalanced=solve(st,r)
        difference=r['branches']['inboard']['known_branch_pressure_Pa']-r['branches']['outboard']['known_branch_pressure_Pa']
        balanced=solve(st,r,difference) if difference>=0 else None
        answers.append({'configuration':r['configuration'],'choice':r['choice'],'unbalanced':unbalanced,'restored_nominal':balanced})
    out={'schema':'fusion.header-flow-recheck.v1','admission_sha256':sha(HERE/'FOLLOWON_ADMISSION.json'),'driver_sha256':sha(Path(__file__)),'header_model_sha256':sha(HERE/'header_inventory.py'),'results':answers,'limits':['Chosen topology and equal flow between modules remain idealizations; within-header jets and take-offs are unresolved.','Fixed-property pressure, frozen heat and peaking1.0; not full CFD, structural or neutron validation.','Any renewed benefit must be compared against this unsplit redistribution baseline, not its imposed-flow failure.']}
    save(HERE/'FLOW_RECHECK_RESULT.json',out)
    print(json.dumps([{'configuration':r['configuration'],'properties':r['choice'],'common_kPa':r['unbalanced']['common_pressure_Pa']/1000,'remaining_kPa':r['unbalanced']['remaining_common_allowance_Pa']/1000,'IB_K':r['unbalanced']['IB']['branch']['peak_K'],'OB_K':r['unbalanced']['OB']['branch']['peak_K'],'thermal_pass':r['unbalanced']['local_FW_temperature_screen_passed'],'IB_flow_fraction':r['unbalanced']['IB']['branch']['flow_relative_to_nominal']} for r in answers],indent=2))
    return out
if __name__=='__main__':main()
