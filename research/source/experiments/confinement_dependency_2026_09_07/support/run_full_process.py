#!/usr/bin/env python3
"""Bounded, full-framework PROCESS comparison; not whole-plant validation."""
import os, sys, json, hashlib, time, re, subprocess, traceback, platform
from pathlib import Path
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMBA_NUM_THREADS'):
    os.environ[key]='1'
os.environ['MPLBACKEND']='Agg'
ROOT=Path(__file__).resolve().parent
SOURCE=ROOT/'PROCESS-v3.4.2'
PIN='c0ae5b28649f2b20fb7efc7904628b6defe4151c'
CASES={'baseline':{'fatigue':False,'adaptive':False},'native20k':{'fatigue':True,'adaptive':False},'adaptive20k':{'fatigue':True,'adaptive':True}}
KEYS='ifail rmajor dr_cs dr_bore f_a_cs_turn_steel stress_hoop_cs_inner n_cycle n_cycle_min p_fusion_total_mw p_plant_electric_gross_mw p_plant_electric_net_mw p_coolant_pump_elec_total_mw p_fw_blkt_coolant_pump_mw p_fw_blkt_coolant_pump_elec_mw p_plant_primary_heat_mw eta_turbine p_hcd_electric_total_mw e_plant_net_electric_pulse_kwh t_plant_pulse_total t_plant_pulse_burn t_plant_pulse_dwell dz_cs_turn_conduit dr_cs_turn_conduit life_plant fjohc fjohc0'.split()
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def parse(path):
    values={}
    for line in path.read_text(encoding='utf-8').splitlines():
        m=re.search(r'\(([^()]*)\)_*\s+([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eEdD][+-]?\d+)?)(?=\s|$)',line)
        if m:values[m[1]]=float(m[2].replace('D','e').replace('d','e'))
    return values
CASES['baseline_iofix']={'fatigue':False,'adaptive':False}
def run(case):
    cfg=CASES[case]; out=ROOT/'runs-20260907'/case
    if out.exists():raise RuntimeError('Refuse to overwrite an existing case')
    out.mkdir(parents=True)
    actual=subprocess.check_output(['git','-C',str(SOURCE),'rev-parse','HEAD'],text=True).strip()
    if actual!=PIN:raise RuntimeError('Wrong upstream revision')
    text=(SOURCE/'examples/data/large_tokamak_IN.DAT').read_text(encoding='utf-8')
    text=text.rstrip()+'\n\n* Fusion Solution Set pulse-power sensitivity overrides *\np_plant_electric_net_required_mw = 400.0\nt_plant_pulse_dwell = 1800.0\neta_ecrh_injector_wall_plug = 0.5\nf_t_plant_available = 0.8\n'
    if cfg['fatigue']:text+='\n* Only added engineering requirement: CS fatigue *\nicc = 90\nn_cycle_min = 20000.0\nbkt_life_csf = 0\n'
    inp=out/'case_IN.DAT'; inp.write_text(text,encoding='utf-8',newline='\n')
    if not cfg['fatigue'] and digest(inp)!='5a816f638a48fd0263aed36fda58187bff46e23b5e2f787383bef8905d891e94':raise RuntimeError('Baseline input differs from authenticated archive')
    manifest={'schema':'fusion.full-framework-input.v1','case':case,'config':cfg,'upstream':actual,'input_sha256':digest(inp),'platform':platform.platform(),'python':sys.version,'scope':'Integration/constraint test, not discovery or physical validation','prior_art':'PROCESS documented constraint 90; project prior-art audit applies','stop_rule':'One baseline and native/adaptive 20k comparison; no arbitrary performance sweeps','changed_assumptions':'No improved pump, efficiency, availability or dwell assumptions'}
    (out/'FROZEN_INPUT.json').write_text(json.dumps(manifest,indent=2)+'\n')
    subprocess.run([sys.executable,'-m','pip','freeze'],stdout=(out/'pip-freeze.txt').open('w'),check=True)
    manifest['runtime_shims']=['windows_output_fix'] if case!='baseline' else []
    manifest['driver_sha256']=digest(Path(__file__))
    manifest['shim_sha256']=digest(ROOT/'windows_output_fix.py')
    manifest['adaptive_sha256']=digest(ROOT/'adaptive_fatigue.py')
    (out/'FROZEN_INPUT.json').write_text(json.dumps(manifest,indent=2)+'\n')
    started=time.time(); exc=None
    try:
        if case!='baseline':
            import windows_output_fix; windows_output_fix.install()
        if cfg['adaptive']:
            from adaptive_fatigue import install
            install()
        from process.main import SingleRun
        simulation=SingleRun(inp.as_posix()); simulation.run()
    except Exception as error:
        exc={'type':type(error).__name__,'message':str(error),'traceback':traceback.format_exc()}
    raw=list(out.glob('*MFILE.DAT')); values=parse(raw[0]) if raw else {}
    selected={k:values.get(k) for k in KEYS}
    numerical=exc is None and selected.get('ifail')==1
    average=None
    if selected.get('e_plant_net_electric_pulse_kwh') is not None and (selected.get('t_plant_pulse_total') or 0)>0:
        average=.8*3.6*selected['e_plant_net_electric_pulse_kwh']/selected['t_plant_pulse_total']
    result={'schema':'fusion.full-framework-result.v1','case':case,'manifest':manifest,'runtime_seconds':time.time()-started,'exception':exc,'numerically_converged':numerical,'values':selected,'availability_adjusted_cycle_average_mw':average,'physical_plant_validated':False,'files':{p.name:digest(p) for p in out.iterdir() if p.is_file()}}
    (out/'RESULT.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');print(json.dumps(result,allow_nan=False),flush=True)
    if exc:raise RuntimeError(exc['message'])
if __name__=='__main__':run(sys.argv[1])
