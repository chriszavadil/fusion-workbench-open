"""Execute one admitted confinement-dependency case in the existing full model.
No new transport or plant model. Run in a fresh subprocess per case.
"""
import os, sys, json, re, hashlib, time, traceback, subprocess
from pathlib import Path
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMBA_NUM_THREADS'):os.environ[k]='1'
os.environ['MPLBACKEND']='Agg'
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
sys.path.insert(0,str(ROOT))
from run_warm_fixed_process import parse, digest, KEYS
PIN='c0ae5b28649f2b20fb7efc7904628b6defe4151c'
BASE=ROOT/'runs-20260907/adaptive30y_warm_fixed'
CASES={'H1_direct':(1.,BASE/'case_MFILE.DAT'),'H11_bridge':(1.1,BASE/'case_MFILE.DAT'),'H1_continued':(1.,HERE/'H11_bridge/case_MFILE.DAT')}
def save(path,obj):path.write_text(json.dumps(obj,indent=2,sort_keys=True,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
def extract_seed(path):
    values={}
    for line in path.read_text(encoding='utf-8').splitlines():
        m=re.match(r'^(.+?)_+\s+\(itvar\d+\)_+\s+([+-]?\S+)',line)
        if m:
            name=m[1].strip();value=float(m[2])
            if not re.fullmatch(r'[a-z0-9_]+(?:\(\d+\))?',name):raise ValueError('Unexpected iteration label')
            if name in values:raise ValueError('Repeated iteration label')
            values[name]=value
    if len(values)!=20 or 'hfact' not in values:raise ValueError('Expected20 labeled iterations')
    return values
def identifiers(text,key):return [int(m[1]) for line in text.splitlines() if (m:=re.match(r'\s*'+key+r'\s*=\s*(\d+)',line))]
CASES['H103_native_validation']=(1.03,HERE/'H_min_inverse/case_MFILE.DAT')
def run(case):
    cap,seed_path=CASES[case];out=HERE/case
    if out.exists():raise RuntimeError('Refuse overwrite of completed or failed evidence')
    out.mkdir()
    admission=json.loads((HERE/'ADMISSION.json').read_text())
    src=ROOT/'PROCESS-v3.4.2'; actual=subprocess.check_output(['git','-C',str(src),'rev-parse','HEAD'],text=True).strip()
    if actual!=PIN:raise ValueError('Wrong PROCESS revision')
    if digest(BASE/'case_IN.DAT')!=admission['baseline_input_sha256']:raise ValueError('Baseline input hash')
    if digest(BASE/'case_MFILE.DAT')!=admission['baseline_MFILE_sha256']:raise ValueError('Baseline result hash')
    if parse(seed_path).get('ifail')!=1:raise ValueError('Seed must be converged')
    seed=extract_seed(seed_path);text=(BASE/'case_IN.DAT').read_text(encoding='utf-8')
    append='\n* Numerical warm start from exact labeled iteration solution *\n'+'\n'.join(f'{k} = {v:.17g}' for k,v in seed.items())
    append+=f'\n* Sole changed physical assumption: confinement multiplier cap *\nboundu(10) = {cap}\nhfact = {cap}\n'
    text_new=text+append
    assert identifiers(text_new,'icc')==identifiers(text,'icc')
    assert identifiers(text_new,'ixc')==identifiers(text,'ixc')
    inp=out/'case_IN.DAT';inp.write_text(text_new,encoding='utf-8',newline='\n')
    manifest={'case':case,'cap':cap,'seed_sha256':digest(seed_path),'input_sha256':digest(inp),'seed':seed,
        'upstream':actual,'admission_sha256':digest(HERE/'ADMISSION.json'),'driver_sha256':digest(Path(__file__)),
        'runtime_modules':{n:digest(ROOT/n) for n in ['windows_output_fix.py','adaptive_fatigue.py','mission_constraint.py']},
        'constraints':identifiers(text_new,'icc'),'iteration_variables':identifiers(text_new,'ixc'),
        'objective':'native_major_radius','validation_of':'H_min_inverse','inverse_admission_sha256':digest(HERE/'INVERSE_ADMISSION.json'),'radiation_convention_retained':1,'scaling_retained':34,'later_cooling_proposals_included':False}
    save(out/'FROZEN_INPUT.json',manifest);started=time.time();error=None
    try:
        import windows_output_fix,adaptive_fatigue,mission_constraint
        windows_output_fix.install();adaptive_fatigue.install();mission_constraint.install()
        from process.main import SingleRun
        SingleRun(inp.as_posix()).run()
    except Exception as exc:error={'type':type(exc).__name__,'message':str(exc),'traceback':traceback.format_exc()}
    mfile=out/'case_MFILE.DAT';v=parse(mfile) if mfile.exists() else {}
    selected={k:v.get(k) for k in KEYS+['hfact','t_energy_confinement','i_rad_loss','b_plasma_toroidal_on_axis','j_cs_flat_top_end','p_hcd_injected_total_mw','p_plasma_imbalance_mw','p_plant_imbalance_mw']}
    numerical=error is None and v.get('ifail')==1
    power=None
    if numerical:
        if not v['hfact']<=cap+1e-7:raise ValueError('Converged but cap violated')
        power=.8*3.6*v['e_plant_net_electric_pulse_kwh']/v['t_plant_pulse_total']
    result={'schema':'fusion.confinement-dependency-case.v1','case':case,'manifest':manifest,
        'runtime_seconds':time.time()-started,'exception':error,'numerically_converged':numerical,
        'classification':'execution_error' if error else 'numerically_converged' if numerical else 'solver_not_converged',
        'values':selected,'conditional_average_net_MW':power,
        'normalized_constraint_residuals':{k:x for k,x in v.items() if k.startswith('normres')},
        'files':{p.name:digest(p) for p in out.iterdir() if p.is_file()},'physical_plant_validated':False}
    save(out/'RESULT.json',result);print(json.dumps(result,allow_nan=False),flush=True)
    return result
if __name__=='__main__':run(sys.argv[1])
