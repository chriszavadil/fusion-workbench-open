"""Read-only independent arithmetic checks of the completed inverse budget. MIT."""
from pathlib import Path
import hashlib,json
import numpy as np
from scipy.integrate import simpson
ROOT=Path(__file__).resolve().parent
checks=[]
for folder in sorted((ROOT/'runs').iterdir()):
 r=json.loads((folder/'RESULT.json').read_text());d=r['result']
 with np.load(folder/'CURRENT_FIELDS.npz') as z:a={k:z[k] for k in z.files}
 assert hashlib.sha256((folder/'CURRENT_FIELDS.npz').read_bytes()).hexdigest()==r['fields_sha256']
 assert all(np.isfinite(x).all() for x in a.values());assert len(a['psi_norm'])==401
 for field,key in [('total_A_per_normalized_flux','total_current_in_tested_shell_A'),('bootstrap_A_per_normalized_flux','bootstrap_current_in_tested_shell_A'),('residual_A_per_normalized_flux','remaining_current_in_tested_shell_A')]:
  assert abs(simpson(a[field],x=a['psi_norm'])-d[key])<1e-6
 assert np.array_equal(a['total_A_per_normalized_flux']-a['bootstrap_A_per_normalized_flux'],a['residual_A_per_normalized_flux'])
 assert np.all(a['trapped_fraction']>=0) and np.all(a['trapped_fraction']<=1)
 assert np.all(a['nu_e_star']>=0) and np.all(a['nu_i_star']>=0)
 # A sign-convention conversion must reverse every pre-conversion value, not discard negatives.
 assert np.allclose(a['jB_Redl'],-a['jB_raw_unconverted_sign_diagnostic'],rtol=1e-12,atol=1e-7)
 assert r['passed_numerical_checks'] and r['restoration']['q_relative_error']<2e-4
 checks.append({'case':r['id'],'all401points_checked':True,'interior_bootstrap_A':d['bootstrap_current_in_tested_shell_A'],'bootstrap_minus_original_total_A':d['bootstrap_current_in_tested_shell_A']-d['original_bootstrap_total_A'],'positive_residual_min_A_m2':float(np.min(a['residual_A_per_normalized_flux']/a['area_per_normalized_flux_m2'])),'projection_difference_fraction':d['native_approximate_projection_integral_A']/d['bootstrap_current_in_tested_shell_A']-1,'passed':True})
assert len(checks)==4
for exponent in [1,2]:
 coarse=next(c for c in checks if c['case']==f'dx0.18_ff{exponent}_v6');fine=next(c for c in checks if c['case']==f'dx0.09_ff{exponent}_v6');fine['bootstrap_relative_mesh_change']=fine['interior_bootstrap_A']/coarse['interior_bootstrap_A']-1;assert abs(fine['bootstrap_relative_mesh_change'])<.01
result={'passed':True,'checks':checks,'new_solver_runs':0,'physical_validation':False};(ROOT/'INDEPENDENT_CHECKS.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
