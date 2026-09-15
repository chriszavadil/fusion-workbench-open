"""Rebuild the exact controlled-pair inputs from the approved r838 input. MIT.
No network calls or solver execution. Does not modify the accepted reference.
Original generic tokamak input: James Morris / UKAEA; upstream license retained.
"""
from pathlib import Path
import argparse,hashlib,re
BASE_SHA='2bc99ba58a1a9305a8e395a21d9ab9a2bba64fb31c06486d05617d89d3ecb9b4'
EXPECTED={75:'0fa5c072789a60f79d75be047f74333893aac884a8450f8b265dbee621086433',30:'6335932f13fe7962a3e81829a6da4ff9055909e8257c275df0a742b723a46f2a'}
WARM={
'b_plasma_toroidal_on_axis':5.0071864336153595,'rmajor':8.379532870755202,
 'temp_plasma_electron_vol_avg_kev':16.839192238847357,'beta_total_vol_avg':0.04659869567962229,
 'nd_plasma_electrons_vol_avg':7.595295450960187e19,'hfact':1.1999999999864892,
 'dr_cs':0.8545609414076564,'q95':3.0000000000885643,'dr_bore':2.057422935161185,
 't_tf_superconductor_quench':16.546772457344904,'dr_tf_nose_case':0.225757555162991,
 'dx_tf_turn_steel':0.008000000005889681,'f_a_tf_turn_cable_copper':0.8909112509886631,
 'c_tf_turn':89999.9999373309,'f_nd_alpha_thermal_electron':0.06939586150848474,
 'f_a_cs_turn_steel':0.8975341269141387,'dr_tf_wp_with_insulation':0.5155787324218746,
 'j_cs_flat_top_end':10185602.925584838}
def make_input(base:bytes,reserve:int)->bytes:
 if hashlib.sha256(base).hexdigest()!=BASE_SHA:raise ValueError('Approved base input changed')
 if reserve not in EXPECTED:raise ValueError('Only the two admitted controlled cases are supported')
 text=base.decode('utf-8').replace('\r\n','\n')
 text+='\n* Exact converged r838 warm start *\n'+''.join(f'{n} = {v:.17g}\n' for n,v in WARM.items())
 text+='\nf_nd_impurity_electrons(13) = 1.28850278937939666e-03\nf_c_plasma_non_inductive = 0.6749892825312551\n\n* Optimistic all-current-driving HCD allocation; not validated control reserve *\np_hcd_primary_extra_heat_mw = 0.0\n'
 text=re.sub(r'(?m)^\s*ixc\s*=\s*3(?:\s.*)?$','* Major radius fixed for fair footprint comparison',text)
 text+='\n* Native electrical-output objective, fixed original radius *\ni_figure_merit = -17\nrmajor = 8.379532870755202\n'
 text+=f'\np_hcd_primary_extra_heat_mw = {reserve}\n'
 raw=text.encode('utf-8')
 if hashlib.sha256(raw).hexdigest()!=EXPECTED[reserve]:raise ValueError('Reconstructed input does not match the executed input hash')
 return raw
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 if a.output.exists():raise FileExistsError('Use a new output directory; no previous cases are overwritten')
 base=a.base.read_bytes();generated={n:make_input(base,n) for n in EXPECTED};a.output.mkdir(parents=True)
 for n,b in generated.items():(a.output/f'pulsedFixedR{n}.IN.DAT').write_bytes(b)
 print('Two exact executed inputs reconstructed; no solver was run.')
