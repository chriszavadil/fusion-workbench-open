"""Existing LiF benchmark: exact normalization audit, not a new physical result. MIT."""
from pathlib import Path
import csv,hashlib,json,math
import numpy as np
HERE=Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def compare():
 r=json.loads((HERE/'RESULT.json').read_text());a=json.loads((HERE/'ARCHIVE_PROJECTION.json').read_text())
 if not r['completed']:raise ValueError('Unfinished transport must not be compared')
 area=4*math.pi*19.95**2;rows={};summary={}
 for name in ['nspectrum','gspectrum']:
  s=r['spectra'][name];low=np.array(s['energy_low_eV']);high=np.array(s['energy_high_eV']);m=np.array(s['current_per_source']);se=np.array(s['statistical_standard_error']);ref=a['computed_reference']['spectra'][name]
  assert np.array_equal(low,ref['energy low [eV]']) and np.array_equal(high,ref['energy high [eV]'])
  assert np.isfinite(m).all() and (m>=0).all() and np.isfinite(se).all() and (se>=0).all() and (high>low).all() and (low>0).all()
  archived=np.array(ref['mean'])*area;ase=np.array(ref['std. dev.'])*area;width=np.log(high/low);sigma=np.hypot(se,ase)
  # A no-score bin has no estimated variance, not proven zero physical uncertainty.
  usable=(m>0)&(se>0)&(archived>0)&(ase>0);z=[float((m[i]-archived[i])/sigma[i]) if usable[i] else None for i in range(len(m))]
  flags=['scored' if ok else 'no_score_or_zero_variance: Gaussian residual not evaluated' for ok in usable]
  rows[name]={'energy_low_eV':low.tolist(),'energy_high_eV':high.tolist(),'current_per_source':m.tolist(),'current_standard_error':se.tolist(),'lethargy_width':width.tolist(),'current_per_source_lethargy':(m/width).tolist(),'current_standard_error_per_lethargy':(se/width).tolist(),'archived_current_recovered':archived.tolist(),'archived_current_standard_error':ase.tolist(),'archive_difference_combined_z':z,'bin_status':flags}
  zz=np.array([v for v in z if v is not None]);ratio=float(m.sum()/archived.sum())
  summary[name]={'bins':len(m),'integrated_current_per_source':float(m.sum()),'archived_integrated_current_per_source':float(archived.sum()),'ratio_to_archived_calculation':ratio,'relative_integral_difference_percent_vs_archive':100*(ratio-1),'gaussian_diagnostic_bins':int(usable.sum()),'zero_or_unresolved_variance_bins':np.where(~usable)[0].tolist(),'fraction_eligible_bins_within_three_combined_MC_se':float(np.mean(abs(zz)<=3)),'largest_eligible_combined_MC_z':float(abs(zz).max()),'diagnostic_only_no_joint_acceptance_test':True,'integral_uncertainty_not_computed_without_covariance':True}
 p=HERE/'upstream/IAEA_Oktavian_LiF Neutron flux.csv'
 with p.open(newline='',encoding='utf-8') as f:raw=list(csv.DictReader(f))
 energy=np.array([float(x['Energy']) for x in raw]);y=np.array([float(x['Value']) for x in raw]);e=np.array([float(x['Error']) for x in raw]);n=rows['nspectrum'];w=np.array(n['lethargy_width'])
 assert np.allclose(energy*1e6,n['energy_high_eV'],rtol=1e-12,atol=1e-8)
 assert len(y)==len(w) and np.isfinite(y).all() and (y>0).all() and (e>=0).all()
 calc=np.array(n['current_per_source_lethargy']);old=np.array(a['experiment']['spectra']['nspectrum']['mean']);norm=old*area/(y*w)
 n.update(experiment_energy_MeV=energy.tolist(),experiment_value=y.tolist(),experiment_reported_error=e.tolist(),calculation_to_experiment=(calc/y).tolist(),legacy_experiment_to_primary_ratio=norm.tolist(),legacy_experiment_per_source_lethargy=(old*area/w).tolist(),experimental_error_covariance_available=False,experimental_error_confidence_not_reestablished=True,source_of_experiment='IAEA-NDS/open-benchmarks, CC-BY-4.0; original OKTAVIAN experiment credited in ATTRIBUTION.md',comparison_units='surface-integrated current per source per unit natural-log lethargy; energy entries matched as listed to tally upper bounds',comparison_scope='Conditional published-data convention audit, not a re-evaluation of detector response or physical uncertainty.')
 measured_integral=float(np.sum(y*w));ratio=float(np.sum(n['current_per_source'])/measured_integral)
 summary['nspectrum'].update(primary_table_integral_under_stated_bin_convention=measured_integral,ratio_to_primary_experiment_integral=ratio,relative_integral_difference_percent=100*(ratio-1),legacy_first_bin_conversion_factor=float(norm[0]),legacy_other_bin_conversion_factor_range=[float(norm[1:].min()),float(norm[1:].max())],first_bin_retained=True,source_experiment_agreement_certified=False)
 with (HERE/'upstream/IAEA_Oktavian_LiF Gamma flux.csv').open(encoding='utf-8') as f:gamma=list(csv.DictReader(f))
 rows['gspectrum']['experimental_csv_uninterpreted']=[{k:float(v) for k,v in x.items()} for x in gamma]
 rows['gspectrum']['experiment_comparison_status']='Withheld: CSV coordinates and differential convention are not reconciled. Do not apply the neutron conversion blindly.'
 out={'schema':'fusion.lif-benchmark-comparison.v2','date':'2026-09-14','classification':'Attributable reproduction of an existing benchmark; not new reactor physics','histories':r['histories'],'elapsed_seconds':r['elapsed_seconds'],'result_sha256':sha(HERE/'RESULT.json'),'admission_sha256':sha(HERE/'ADMISSION.json'),'archive_projection_sha256':sha(HERE/'ARCHIVE_PROJECTION.json'),'primary_neutron_csv_sha256':sha(p),'model_outer_radius_cm':30.5,'archive_helper_radius_cm':19.95,'sphere_area_ratio':(30.5/19.95)**2,'spectra':rows,'summary':summary,'physical_reactor_validation':False,'global_TBR_computed':False,'new_reactor_performance':False,
 'decision':'Keep reactor physical validation open: computational integrals agree closely, but the primary neutron table differs and legacy first-bin normalization is inconsistent. Preserve all bins. Do not tune or apply a blanket correction factor.',
 'limitations':['LiF leakage is not Li4SiO4/TiBe12 tritium breeding or usable-fuel validation.','No fitted rescaling or repeat transport run was used to improve agreement.','Actual data hashes are captured; equal library labels do not prove identical old processing files.','Primary experimental Error values and all points are retained; full covariance, detector response and systematic uncertainties are not reconstructed.','The final neutron bin has zero score and zero reported sampling error; no Gaussian significance or physical zero is inferred.','Photon experiment comparison remains unqualified.'],
 'analysis_review':['Corrected the provisional all-bin Gaussian diagnostic: no-score bin133 is now marked unevaluable, not a21-sigma physical discrepancy. Raw zero and archived tiny nonzero score remain visible.','The radius19.95cm is used only to undo the documented archive normalization, not substituted into the actual30.5cm transport geometry.']}
 (HERE/'KEY_RESULTS.json').write_text(json.dumps(out,indent=2,sort_keys=True,allow_nan=False)+'\n',encoding='utf-8');return out
if __name__=='__main__':print(json.dumps(compare()['summary'],indent=2))
