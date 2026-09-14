#!/usr/bin/env python3
"""Read-only, hash-pinned audit of PR42 outputs; not a new reactor simulation.

Requires Python>=3.10 and scipy. Run with the three original GitHub artifact
ZIPs in --archive-dir. Outputs preserve model/counterfactual/statistical scope.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import re
import sys
import zipfile
from scipy.stats import t as student_t

SOURCES = {
    'power': ('process-power-cycle-33906304781.zip', '5aae03f0d4dc4e7eff11b46488f6c3bddc290d29a759cd38712ea79a0b9b627b', 33906304781, 9949782922),
    'neutronics': ('openmc-pb17li-33906304435.zip', '3476dd8251dfd96ade76b457cb95d46b69afc026596836d0cdb6f4f3a6a965db', 33906304435, 9949937103),
    'reactor': ('process-reactor-feasibility-33906304626.zip', '8fcefa7510ab2abe8b82c9b89f0e164ac78f6e3f89216ce333db727a3c00abab', 33906304626, 9949678670),
}
NUMBER = re.compile(r'\(([^()]*)\)_*\s+([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eEdD][+-]?\d+)?)(?=\s|$)')
DURATIONS = ['coil_precharge', 'plasma_current_ramp_up', 'fusion_ramp', 'burn', 'plasma_current_ramp_down', 'dwell']
LOADS = ['p_plant_electric_base_total', 'p_hcd_electric_total', 'p_coolant_pump_elec_total', 'p_tf_electric_supplies', 'p_pf_electric_supplies', 'vachtmw', 'p_tritium_plant_electric', 'p_cryo_plant_electric']


def parse_mfile(text: str) -> dict[str, float]:
    """Single-scan numeric subset. Never substitute zero for a missing key."""
    values: dict[str, float] = {}
    for line in text.splitlines():
        match = NUMBER.search(line)
        if not match:
            continue
        key, raw = match.groups()
        value = float(raw.replace('D', 'e').replace('d', 'e'))
        if not math.isfinite(value):
            raise ValueError(f'Nonfinite value for {key}')
        if key in values and not math.isclose(values[key], value, rel_tol=1e-12, abs_tol=1e-12):
            raise ValueError(f'Conflicting values / multiple scans for {key}')
        values[key] = value
    return values


def required(values: dict[str, float], key: str) -> float:
    if key not in values or not math.isfinite(values[key]):
        raise ValueError(f'Missing finite field: {key}')
    return values[key]


def integrate(values: list[float], durations: list[float]) -> float:
    """Independent piecewise-linear integral in MW*s (MJ)."""
    if len(values) != len(durations) + 1 or not durations:
        raise ValueError('Profile/time dimensions do not match')
    if any(not math.isfinite(x) for x in values + durations) or any(x < 0 for x in durations):
        raise ValueError('Invalid profile or durations')
    if sum(durations) <= 0:
        raise ValueError('Empty cycle')
    return math.fsum(0.5 * (a+b) * dt for a, b, dt in zip(values, values[1:], durations))


def profile(values: dict[str, float], key: str) -> list[float]:
    return [required(values, f'{key}_profile_mw{i}') for i in range(7)]


def classify(values: dict[str, float], exception: dict | None) -> str:
    if exception:
        if 'Constraint 52 is only supported when running the IFE model' in exception.get('message', ''):
            return 'unsupported_configuration'
        return 'execution_error'
    flag = values.get('ifail')
    if flag is None:
        return 'missing_solver_status'
    # Optimizer failure is not a proof that the feasible physical set is empty.
    return 'numerically_feasible_under_enabled_constraints' if flag == 1 else 'solver_not_converged'


def verify_archive(path: Path, expected: str) -> zipfile.ZipFile:
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        raise ValueError(f'Archive hash mismatch: {path.name}')
    z = zipfile.ZipFile(path)
    if len(z.namelist()) != len(set(z.namelist())):
        z.close()
        raise ValueError('Duplicate ZIP entries')
    # Original manifests use paths relative to the CI workspace; archives are flat.
    for line in z.read('evidence-sha256.txt').decode().splitlines():
        digest, name = line.split(maxsplit=1)
        relative = '/'.join(name.split('/')[2:])
        if hashlib.sha256(z.read(relative)).hexdigest() != digest:
            z.close()
            raise ValueError(f'Manifest mismatch: {relative}')
    return z


def fixed_design(values: dict[str, float], eta: float, dwell: float, availability: float) -> dict:
    """Electrical accounting only; all delivered plasma heating stays unchanged."""
    if not 0 < eta <= 1 or dwell < 0 or not 0 < availability <= 1:
        raise ValueError('Unphysical accounting parameter')
    inj = required(values, 'p_hcd_ecrh_injected_total_mw')
    total_inj = required(values, 'p_hcd_injected_total_mw')
    electric = required(values, 'p_hcd_electric_total_mw')
    if not math.isclose(inj, total_inj, rel_tol=1e-10) or electric <= 0:
        raise ValueError('This counterfactual requires exclusively ECRH heating')
    eta0 = inj / electric
    ds = [required(values, 't_plant_pulse_'+k) for k in DURATIONS]
    ds[-1] = dwell
    net0 = profile(values, 'p_plant_electric_net')
    hcd = profile(values, 'p_hcd_electric_total')
    if any(x > 0 for x in hcd):
        raise ValueError('HCD profile must use negative load sign')
    net = [n + h * (eta0/eta-1) for n, h in zip(net0, hcd)]
    mj = integrate(net, ds)
    return {'eta_wallplug': eta, 'dwell_s': dwell, 'availability_assumed': availability,
            'flat_top_net_mw': net[3], 'cycle_average_net_mw': mj/sum(ds),
            'availability_adjusted_net_mw': availability*mj/sum(ds),
            'pulse_energy_kwh': mj/3.6, 'cycle_s': sum(ds)}


def conditional_lower(mean: float, se: float, batches: int, family_size: int, alpha: float=.05) -> tuple[float, float]:
    if not math.isfinite(mean) or not math.isfinite(se) or se < 0 or batches < 2 or family_size < 1 or not 0 < alpha < 1:
        raise ValueError('Invalid statistical input')
    q = float(student_t.ppf(1-alpha/family_size, batches-1))
    return mean-q*se, q


def matched_blanket_gate(power: dict, neutronics: dict) -> dict:
    required_fields = ['material_system', 'geometry_sha256', 'material_inventory_sha256', 'neutron_source_sha256', 'nuclear_heating_feedback_sha256']
    missing = [f'{side}.{key}' for side, obj in [('power',power),('neutronics',neutronics)] for key in required_fields if not obj.get(key)]
    mismatches = [key for key in required_fields if power.get(key) and neutronics.get(key) and power[key] != neutronics[key]]
    return {'coupling_identity_gate_passed': not missing and not mismatches,
            'missing': missing, 'mismatches': mismatches,
            'meaning': 'Identity/provenance check only; even a pass is not physical or fuel-cycle validation.'}


def audit(archive_dir: Path) -> dict:
    archives = {}
    try:
        for key, (filename, digest, _, _) in SOURCES.items():
            archives[key] = verify_archive(archive_dir/filename, digest)
        pz, rz, nz = (archives[k] for k in ['power','reactor','neutronics'])
        prior_power = json.loads(pz.read('PROCESS_POWER_CYCLE_SENSITIVITY.json'))
        prior_reactor = json.loads(rz.read('PROCESS_REACTOR_FEASIBILITY_RESULT.json'))
        neutron = json.loads(nz.read('OPENMC_PB17LI_TBR_SCREEN.json'))
        power_rows, reactor_rows = [], []
        models = {}
        for row in prior_power['results']:
            ident = row['case']['id']
            raw = pz.read(f'cases/{ident}/{ident}_MFILE.DAT').decode()
            values = parse_mfile(raw); models[ident] = values
            if classify(values,row['exception']) != 'numerically_feasible_under_enabled_constraints':
                raise ValueError(f'Power case not converged: {ident}')
            ds = [required(values, 't_plant_pulse_'+k) for k in DURATIONS]
            net = profile(values, 'p_plant_electric_net'); gross = profile(values, 'p_plant_electric_gross')
            load_profiles = [profile(values,k) for k in LOADS]
            balance_error = max(abs(n-g-math.fsum(load[i] for load in load_profiles)) for i,(n,g) in enumerate(zip(net,gross)))
            energy = integrate(net, ds)/3.6
            energy_error = abs(energy-required(values, 'e_plant_net_electric_pulse_kwh'))
            time_error = abs(sum(ds)-required(values,'t_plant_pulse_total'))
            if balance_error > 1e-8 or energy_error > 1e-6 or time_error > 1e-7:
                raise ValueError(f'Independent power accounting failed: {ident}')
            avg = energy*3.6/sum(ds)
            power_rows.append({'case':ident, 'ifail':values['ifail'], 'flat_top_net_mw': values['p_plant_electric_net_mw'],
                'fusion_mw':values['p_fusion_total_mw'], 'gross_mw':values['p_plant_electric_gross_mw'],
                'hcd_electric_mw':values['p_hcd_electric_total_mw'], 'pump_mw':values['p_coolant_pump_elec_total_mw'],
                'cycle_average_net_mw':avg,'availability_adjusted_net_mw':avg*row['case']['availability'],
                'profile_balance_error_mw':balance_error,'energy_error_kwh':energy_error,'time_error_s':time_error})
        for row in prior_reactor['cases']:
            ident = row['case']['id']
            name = f'cases/{ident}/{ident}_MFILE.DAT'
            values = parse_mfile(rz.read(name).decode()) if name in rz.namelist() else {}
            reactor_rows.append({'case':ident,'classification':classify(values,row['run_exception']),
                'raw_ifail':values.get('ifail'),'raw_tbr_present':'tbr' in values,
                'tbr_value':values.get('tbr') if row['run_exception'] is None else None,
                'old_scientific_feasible':row['scientific_feasible'], 'exception':row['run_exception']})
        baseline = models['baseline']
        counterfactuals = [fixed_design(baseline,e,d,a) for e in [.5,.6,.7] for d in [1800.,900.,300.,0.] for a in [.8,.9]]
        requirements = []
        for e in [.5,.6,.7,1.]:
            for a in [.8,.9]:
                zero = fixed_design(baseline,e,0,a)
                power_dwell = profile(baseline,'p_plant_electric_net')[-1]
                for target in [300.,400.]:
                    # A(E0+P_dwell*D)/(T0+D)>=target. D is nonnegative.
                    max_dwell = (a*zero['pulse_energy_kwh']*3.6-target*zero['cycle_s'])/(target-a*power_dwell)
                    requirements.append({'target_average_mw':target,'eta':e,'availability':a,
                        'zero_dwell_average_mw':zero['availability_adjusted_net_mw'],
                        'nonnegative_dwell_solution':max_dwell>=0,'maximum_dwell_s':max_dwell if max_dwell>=0 else None})
        rows = neutron['results']; n = len(rows)
        if n != 42 or len({r['case_id'] for r in rows}) != 42:
            raise ValueError('Expected the complete 42-point neutronics grid')
        neutron_rows = []
        for row in rows:
            lower,q = conditional_lower(row['tbr_mean'],row['tbr_std_dev'],row['batches'],n)
            neutron_rows.append({**row,'conditional_grid_lower_tbr':lower,'t_multiplier':q,
                'maximum_fractional_reduction_for_target_1_15':(1-1.15/lower) if lower>0 else None})
        stress_frontiers = []
        for loss in [0.,.1,.15,.2]:
            for enrich in sorted({r['li6_enrichment_pct'] for r in rows}):
                eligible = [r for r in neutron_rows if r['li6_enrichment_pct']==enrich and r['conditional_grid_lower_tbr']*(1-loss)>=1.15]
                if eligible:
                    row = min(eligible,key=lambda r:r['blanket_thickness_cm'])
                    stress_frontiers.append({'fractional_reduction_assumed':loss,'enrichment_pct':enrich,
                        'min_tested_thickness_cm':row['blanket_thickness_cm'],'case_id':row['case_id']})
        material_match = 'CCFE HCPB model' in pz.read('cases/baseline/baseline_MFILE.DAT').decode()
        if not material_match:
            raise ValueError('Expected explicit baseline HCPB identifier')
        contract = {'source_process_commit':pz.read('environment/process_commit.txt').decode().strip(),
            'material_system':'HCPB_helium_ceramic_TiBe12',
            'geometry_native':{k:required(baseline,k) for k in ['rmajor','rminor','kappa','triang','dr_blkt_inboard','dr_blkt_outboard','dz_blkt_upper','dr_fw_inboard','dr_fw_outboard','dr_fw_plasma_gap_inboard','dr_fw_plasma_gap_outboard','dz_fw_plasma_gap']},
            'native_material_fields':{k:required(baseline,k) for k in ['f_vol_blkt_tibe12','f_vol_blkt_li4sio4','f_vol_blkt_steel','vfcblkt']},
            'warning':'Native fractions are not a complete spatial material inventory; do not renormalize or silently assign missing volume. Li-6 enrichment not present in this MFILE.'}
        coupling = matched_blanket_gate(contract, {'material_system':'Pb17Li_liquid'})
        return {'schema':'fusion-solution-set.plant-closure-audit.v1','date':'2026-09-06',
            'source_repo_commit':'40cdde9f77c67e6e16fdac221fd1462a7ea3cb1f',
            'provenance':{k:{'archive':v[0],'sha256':v[1],'run_id':v[2],'artifact_id':v[3]} for k,v in SOURCES.items()},
            'all_archive_and_manifest_hashes_verified':True,
            'reactor_classification_counts':dict(Counter(r['classification'] for r in reactor_rows)),
            'reactor_case_audit':reactor_rows,'independent_power_replay':power_rows,
            'fixed_design_counterfactuals':counterfactuals,'fixed_design_dwell_requirements':requirements,
            'neutronics_conditional_diagnostic':neutron_rows,'neutronics_stress_frontiers':stress_frontiers,
            'matched_plant_contract_seed':contract,'coupling_gate':coupling,
            'scope':['New work: independent accounting, fixed-design electrical counterfactual, conditional statistical/derating audit, coupling rejection.',
                'No new PROCESS optimization, OpenMC transport, fuel inventory simulation, or experimental validation ran in this audit.',
                'Fixed-design changes assume unchanged delivered plasma heating, gross electricity, pumping, cooling, magnets, pulse shape and maintenance.',
                'Availability is assumed outside the pulse/dwell cycle, not achieved or a separately modelled reliability result.',
                'Student-t/Bonferroni limits assume independent approximately normal batch means; original batch histories/statepoints were not retained, so this remains conditional.',
                'TBR derating is a sensitivity parameter, not a prediction of port loss or plant self-sufficiency. Spherical coverage is not a proved global upper bound.',
                'The HCPB power baseline cannot be coupled to Pb17Li neutron outputs; no integrated plant feasibility or sustainable-fusion claim follows.']}
    finally:
        for z in archives.values():
            z.close()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--archive-dir',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args()
    try:
        result=audit(args.archive_dir)
        args.output.mkdir(parents=True,exist_ok=True)
        dest=args.output/'PLANT_CLOSURE_AUDIT_2026-09-06.json'
        dest.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n')
        print(json.dumps({'result':str(dest),'audit_completed':True,'counts':result['reactor_classification_counts'],
            'power_replays':len(result['independent_power_replay']),'coupling_gate_passed':result['coupling_gate']['coupling_identity_gate_passed']}))
        return 0
    except (OSError,ValueError,KeyError,zipfile.BadZipFile) as exc:
        print(f'Audit rejected: {exc}',file=sys.stderr)
        return 2

if __name__=='__main__':
    raise SystemExit(main())
