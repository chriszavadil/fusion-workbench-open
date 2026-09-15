"""Independent checks of reference data, units, attribution and no-score handling."""
from pathlib import Path
import csv,hashlib,importlib.util,json,math
import numpy as np
import pytest
ROOT=Path(__file__).resolve().parents[1];E=ROOT/'research/source/experiments/oktavian_lif_2026_09_14'
K=json.loads((E/'KEY_RESULTS.json').read_text(encoding='utf-8'));R=json.loads((E/'RESULT.json').read_text(encoding='utf-8'));A=json.loads((E/'ARCHIVE_PROJECTION.json').read_text(encoding='utf-8'))
@pytest.mark.parametrize('name,count',[('nspectrum',134),('gspectrum',49)])
def test_all_bins_retained_exact_normalization(name,count):
 s=K['spectra'][name];raw=R['spectra'][name];lo=np.asarray(s['energy_low_eV']);hi=np.asarray(s['energy_high_eV']);w=np.log(hi/lo)
 assert len(lo)==len(hi)==len(s['current_per_source'])==count
 assert s['current_per_source']==raw['current_per_source']
 assert np.array_equal(lo,raw['energy_low_eV']) and np.array_equal(hi,raw['energy_high_eV'])
 # libm/SIMD logarithms can differ by a few ULP across operating systems; raw data remains exact.
 np.testing.assert_array_max_ulp(w,np.asarray(s['lethargy_width']),maxulp=8)
 np.testing.assert_array_max_ulp(np.asarray(raw['current_per_source'])/w,np.asarray(s['current_per_source_lethargy']),maxulp=8)
 assert w.sum()==pytest.approx(math.log(hi[-1]/lo[0]),rel=1e-12)
 archived=np.array(A['computed_reference']['spectra'][name]['mean'])*4*math.pi*19.95**2
 assert np.allclose(archived,s['archived_current_recovered'],rtol=1e-14)

def test_no_score_is_not_zero_physical_uncertainty():
 s=K['spectra']['nspectrum'];assert s['current_per_source'][-1]==s['current_standard_error'][-1]==0
 assert s['archived_current_recovered'][-1]>0
 assert s['archive_difference_combined_z'][-1] is None
 assert 'no_score' in s['bin_status'][-1]
 assert K['summary']['nspectrum']['gaussian_diagnostic_bins']==133

def test_primary_values_preserved_and_no_fit():
 with (E/'upstream/IAEA_Oktavian_LiF Neutron flux.csv').open(encoding='utf-8') as f:rows=list(csv.DictReader(f))
 s=K['spectra']['nspectrum'];assert s['experiment_value']==[float(r['Value']) for r in rows]
 assert s['experiment_reported_error']==[float(r['Error']) for r in rows]
 total=sum(y*w for y,w in zip(s['experiment_value'],s['lethargy_width']))
 assert sum(s['current_per_source'])/total==pytest.approx(K['summary']['nspectrum']['ratio_to_primary_experiment_integral'],rel=1e-13)

def test_first_bin_disagreement_not_hidden():
 s=K['summary']['nspectrum'];assert s['legacy_first_bin_conversion_factor']>500
 assert s['legacy_other_bin_conversion_factor_range'][0]>.99 and s['legacy_other_bin_conversion_factor_range'][1]<1.01
 assert s['first_bin_retained'] and not s['source_experiment_agreement_certified']
def test_benchmark_not_labeled_reactor_validation():
 assert not K['physical_reactor_validation'] and not K['global_TBR_computed'] and not K['new_reactor_performance']
 assert 'Withheld' in K['spectra']['gspectrum']['experiment_comparison_status']
 assert K['summary']['nspectrum']['integral_uncertainty_not_computed_without_covariance']

def test_upstream_files_unchanged_and_licenses_present():
 for item in json.loads((E/'UPSTREAM_MANIFEST.json').read_text()):assert hashlib.sha256((E/'upstream'/item['local_name']).read_bytes()).hexdigest()==item['sha256']
 assert 'Copyright (c) 2025 MIT PSFC' in (E/'upstream/OFB_LICENSE').read_text()
 assert 'Attribution 4.0 International' in (E/'upstream/IAEA_LICENSE').read_text(encoding='utf-8')
 assert 'Ichihara' in (E/'ATTRIBUTION.md').read_text(encoding='utf-8')
def test_reference_and_registry_are_same_in_native_source_and_browser():
 for name in ['lif_benchmark.json','prior_work.json']:
  assert (ROOT/'app/data'/name).read_bytes()==(ROOT/'native/Content/WorkbenchData'/name).read_bytes()==(ROOT/'docs/data'/name).read_bytes()
 packet=json.loads((ROOT/'app/data/lif_benchmark.json').read_text(encoding='utf-8'));assert packet['result']==K
 assert packet['original_csvs']['IAEA_Oktavian_LiF Neutron flux.csv']==(E/'upstream/IAEA_Oktavian_LiF Neutron flux.csv').read_text(encoding='utf-8')
 assert not packet['native_executable_updated']
def test_prior_work_gate_fields_and_unique_ids():
 d=json.loads((ROOT/'research/prior_work_register.json').read_text(encoding='utf-8'));assert len(d['entries'])==len({e['id'] for e in d['entries']})>=5
 for e in d['entries']:
  assert all(e.get(k) for k in ['attribution','classification','our_use','do_not_repeat','reopen_when','sources','license_scope','reading_scope'])
 assert any('not yet reproduced' in e['classification'] for e in d['entries'])
def test_hosted_reference_has_no_worker_or_html_evaluation():
 js=(ROOT/'docs/benchmarks.js').read_text(encoding='utf-8');assert 'innerHTML' not in js and 'eval(' not in js and 'method:' not in js
 assert "fetch('./data/lif_benchmark.json')" in js and "fetch('/" not in js

def test_independent_first_bin_integral_review():
 d=json.loads((E/'INDEPENDENT_NORMALIZATION_REVIEW.json').read_text(encoding='utf-8'))
 assert d['new_transport_runs']==0 and not d['experimental_validation']
 assert abs(d['remaining_bins_net_integral_difference'])<1e-5
 assert d['simple_missing_log_width_explanation_rejected']
 assert d['unqualified_ratio_using_legacy_table']<.57
 assert d['conditional_ratio_using_primary_table']>.93
