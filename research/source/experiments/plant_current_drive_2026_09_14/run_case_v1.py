"""Bounded candidate-specific PROCESS architecture test. No model refit. MIT."""
from pathlib import Path
import os,sys,json,hashlib,time,traceback,subprocess,re
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMBA_NUM_THREADS'):os.environ[key]='1'
os.environ['MPLBACKEND']='Agg'
ROOT=Path(__file__).resolve().parent
UP=ROOT.parent/'PROCESS-v3.4.2'
PIN='c0ae5b28649f2b20fb7efc7904628b6defe4151c'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def parse(p):
 out={}
 for line in p.read_text(encoding='utf-8').splitlines():
  m=re.search(r'\(([^()]*)\)_*\s+([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eEdD][+-]?\d+)?)(?=\s|$)',line)
  if m:out[m[1]]=float(m[2].replace('D','e').replace('d','e'))
 return out

def run(case):
 target=ROOT/case;inp=target/'case_IN.DAT';manifest=json.loads((target/'FROZEN_INPUT.json').read_text(encoding='utf-8'))
 if (target/'STARTED.json').exists():raise RuntimeError('Run already started; preserve its outcome')
 assert sha(inp)==manifest['input_sha256']
 git=Path('C:/Program Files/Git/mingw64/bin/git.exe')
 pin=subprocess.check_output([str(git),'-C',str(UP),'rev-parse','HEAD'],text=True,timeout=15).strip();assert pin==PIN
 (target/'STARTED.json').write_text(json.dumps({'input_sha256':sha(inp),'driver_sha256':sha(Path(__file__)),'upstream':PIN,'adaptive_sha256':sha(ROOT/'adaptive_fatigue.py'),'windows_shim_sha256':sha(ROOT/'windows_output_fix.py'),'steady_state_mission_patch_installed':False},indent=2)+'\n',encoding='utf-8')
 import windows_output_fix,adaptive_fatigue
 windows_output_fix.install();adaptive_fatigue.install()
 import process.core.init as init
 init.get_git_summary=lambda:('pinned-official-source',PIN[:12])
 from process.main import SingleRun
 started=time.monotonic();error=None
 try:SingleRun(inp.as_posix()).run()
 except Exception:error=traceback.format_exc();print(error,flush=True)
 mfile=target/'case_MFILE.DAT';values=parse(mfile) if mfile.exists() else {}
 keys='ifail convergence_parameter rmajor rminor dr_cs dr_bore b_plasma_toroidal_on_axis hfact plasma_current p_fusion_total_mw p_hcd_injected_total_mw p_hcd_primary_injected_mw p_hcd_primary_extra_heat_mw p_hcd_electric_total_mw p_plant_electric_gross_mw p_plant_electric_net_mw p_plant_electric_recirc_mw p_coolant_pump_elec_total_mw p_plant_core_systems_elec_mw f_c_plasma_bootstrap f_c_plasma_auxiliary f_c_plasma_inductive f_c_plasma_non_inductive n_cycle n_cycle_min t_plant_pulse_burn t_plant_pulse_total p_plasma_separatrix_mw p_l_h_threshold_mw p_plant_imbalance_mw p_electric_imbalance p_plant_primary_heat_mw eta_turbine eta_cd_hcd_primary eta_cd_norm_ecrh eta_hcd_primary_injector_wall_plug p_hcd_injected_max i_pulsed_plant'.split()
 feasible=not error and values.get('ifail')==1
 result={'case':case,'numerically_converged':feasible,'physical_plant_validated':False,'runtime_s':time.monotonic()-started,'error':error,'metrics':{k:values.get(k) for k in keys},'input_sha256':sha(inp),'mfile_sha256':sha(mfile) if mfile.exists() else None,'admission_sha256':sha(ROOT/'ADMISSION.json'),'screening_availability_adjusted_net_MW':.8*values['p_plant_electric_net_mw'] if feasible else None,'scope':'Continuous-operation electrical screening only; no startup/outage energy, current-profile stability, experimental confinement, maintenance or fuel closure validated.'}
 (target/'RESULT.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf-8');print(json.dumps(result),flush=True)
 return 0 if error is None else 2
if __name__=='__main__':raise SystemExit(run(sys.argv[1]))
