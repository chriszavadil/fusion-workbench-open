"""Portable, bounded replay of the cooling screen using an exact input subset.
Requires the pinned official PROCESS checkout and its Python environment.
"""
from pathlib import Path
import argparse,contextlib,hashlib,inspect,json,math,subprocess,sys
PIN='c0ae5b28649f2b20fb7efc7904628b6defe4151c'
DATA_HASH='e4b60da381973ff3950e90a7edec234b26f0959925aa88e58da8f6768249f619'
def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--input',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
    data=json.loads(args.input.read_text(encoding='utf-8'))
    if hashlib.sha256(canonical(data)).hexdigest()!=DATA_HASH:raise ValueError('Input subset does not match the verified candidate')
    from process.models.fw import FirstWall
    source=Path(inspect.getfile(FirstWall)).resolve().parents[2]
    if subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip()!=PIN:raise ValueError('Wrong PROCESS revision')
    if subprocess.check_output(['git','-C',str(source),'status','--porcelain'],text=True).strip():raise ValueError('Unrecorded changes in upstream source')
    args.output.mkdir(parents=True,exist_ok=False)
    # Legacy evaluators read this filename; here it deliberately contains ONLY
    # the verified fields they consume, not the entire original simulation state.
    (args.output/'SOLVED_STATE.json').write_text(json.dumps(data,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    provenance={'source_commit':PIN,'canonical_input_sha256':DATA_HASH,'full_original_state_sha256':'cedcfa6d695fd45d4be17ea1ee77ae40d821064ea15eb1244822804f3001f9ea','replay_state_is_subset':True,'full_reactor_optimization':False,'new_physical_validation':False}
    (args.output/'REPLAY_PROVENANCE.json').write_text(json.dumps(provenance,indent=2)+'\n',encoding='utf-8')
    import evaluate_frozen_fw_final as fw, coolant_volume_gate as volume, split_fw_intervention as split
    with (args.output/'replay.log').open('w',encoding='utf-8') as log,contextlib.redirect_stdout(log):
        for module in (fw,volume,split):module.OUT=args.output;module.main()
    thermal=json.loads((args.output/'FW_MAPPING_FINAL_RESULT.json').read_text());hyd=json.loads((args.output/'COOLANT_VOLUME_RESULT.json').read_text());s=json.loads((args.output/'SPLIT_FW_RESULT.json').read_text())
    expected=[949.327117548056,958.0680792461076,798.2410597947791,779.2009876960561]
    for row,value in zip(thermal['rows'],expected):
        if not math.isclose(row['peak_K'],value,abs_tol=1e-6,rel_tol=0):raise ValueError('Thermal replay changed')
    ob=next(r for r in hyd['rows'] if r['side']=='outboard' and r['mapping']=='inventory_matched_diagnostic')
    if not math.isclose(ob['estimates']['outlet_properties']['combined_FW_BZ_dp_Pa'],574781.0139177173,abs_tol=.01,rel_tol=0):raise ValueError('Hydraulic replay changed')
    proposed=next(r for r in s['rows'] if r['side']=='outboard')
    if not math.isclose(proposed['split_FW']['peak_K'],793.4053516046565,abs_tol=1e-6,rel_tol=0):raise ValueError('Intervention thermal replay changed')
    if not math.isclose(proposed['estimates']['outlet_properties']['combined_channel_dp_Pa'],141211.79316928383,abs_tol=.01,rel_tol=0):raise ValueError('Intervention hydraulic replay changed')
    result={'replay_verified':True,'output':str(args.output),'temperature_tolerance_K':1e-6,'pressure_tolerance_Pa':.01,'new_physical_result':False}
    (args.output/'REPLAY_VERIFIED.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))
if __name__=='__main__':main()
