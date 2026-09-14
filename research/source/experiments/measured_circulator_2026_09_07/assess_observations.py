"""Limited source-observation assessment; no compressor-map fit or scale-up.
The computed ratio uses tabulated pressure rise as an assumed isentropic pressure
increment and reported motor power as electrical input. It is NOT a measured
shaft, polytropic, or total-to-total efficiency. Boundary ambiguity is retained.
"""
from __future__ import annotations
import hashlib, json, math, sys
from pathlib import Path
from typing import Any
from importlib.metadata import version
from CoolProp.CoolProp import PropsSI
ROOT = Path(__file__).resolve().parent
OBSERVED = {'reported_operation', 'reported_test'}
DEFINITIONS = ('pressure_taps_and_absolute_reference', 'static_to_total_state_definition',
               'power_meter_boundary_and_heat_loss', 'massflow_measurement_and_uncertainty',
               'speed_dependent_curve_with_repeats', 'candidate_similarity_or_same_machine',
               'independent_validation_interval')
def sha(p: Path) -> str: return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p: Path, obj: Any) -> None:
    p.write_text(json.dumps(obj,indent=2,sort_keys=True,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
def positive(name: str, x: float) -> None:
    if not math.isfinite(x) or x <= 0: raise ValueError(f'{name} must be finite and positive')
def eligible(row: dict) -> bool:
    return row.get('classification') in OBSERVED
def pressure_pair(pressure_Pa: float, rise_Pa: float, interpretation: str) -> tuple[float,float]:
    positive('pressure',pressure_Pa); positive('rise',rise_Pa)
    if interpretation=='absolute_inlet': return pressure_Pa,pressure_Pa+rise_Pa
    if interpretation=='absolute_outlet' and pressure_Pa>rise_Pa: return pressure_Pa-rise_Pa,pressure_Pa
    raise ValueError('Unknown pressure interpretation or nonpositive suction pressure')
def pressure_work_proxy(row: dict, interpretation: str) -> dict:
    if not eligible(row): raise ValueError('Rated/design points cannot be evaluated as observations')
    T=float(row['inlet_C'])+273.15; m=float(row['massflow_kg_s']); power=1000*float(row['power_kW'])
    for name,x in [('temperature_K',T),('massflow',m),('power',power)]: positive(name,x)
    p1,p2=pressure_pair(1e6*float(row['pressure_MPa']),1000*float(row['pressure_rise_kPa']),interpretation)
    h1=PropsSI('Hmass','T',T,'P',p1,'Helium'); s1=PropsSI('Smass','T',T,'P',p1,'Helium')
    h2s=PropsSI('Hmass','P',p2,'Smass',s1,'Helium'); T2s=PropsSI('T','P',p2,'Smass',s1,'Helium')
    rho=PropsSI('Dmass','T',T,'P',p1,'Helium'); ratio=m*(h2s-h1)/power
    R=PropsSI('gas_constant','Helium')/PropsSI('molar_mass','Helium'); gamma=5/3
    ideal=(gamma/(gamma-1))*R*T*((p2/p1)**((gamma-1)/gamma)-1)
    entropy_error=PropsSI('Smass','T',T2s,'P',p2,'Helium')-s1
    return {'source_row':row['id'],'pressure_interpretation':interpretation,'p1_assumed_Pa':p1,
        'p2_assumed_Pa':p2,'inlet_K':T,'pressure_ratio_assumed':p2/p1,'inlet_density_kg_m3':rho,
        'inlet_volume_flow_m3_s':m/rho,'isentropic_pressure_work_MW':m*(h2s-h1)/1e6,
        'reported_motor_power_MW':power/1e6,'conditional_pressure_work_electrical_ratio':ratio,
        'ideal_gas_pressure_work_J_kg':ideal,'real_He_pressure_work_J_kg':h2s-h1,
        'incompressible_pressure_work_ratio':m*(p2-p1)/(rho*power),
        'reconstructed_entropy_error_J_kgK':entropy_error,
        'is_reported_efficiency':False,'usable_as_candidate_efficiency':False}
def assess_gate(definitions: dict) -> dict:
    missing=[key for key in DEFINITIONS if definitions.get(key) is not True]
    return {'missing_evidence':missing,'complete_interface_evidence':not missing,
            'candidate_efficiency_update_authorized':False,
            'reason':'Even complete metadata requires physical validation; this script never updates a reactor.'}
def header_envelope(candidate: dict, evaluated: list[dict]) -> dict:
    observed_pr=[x['pressure_ratio_assumed'] for x in evaluated]; p=candidate['p_discharge_Pa']
    targets={side:p/(p-dp) for side,dp in candidate['known_model_dp_Pa'].items()}
    return {'observed_interpretation_pressure_ratios':observed_pr,'known_candidate_ratios':targets,
        'full_budget_pressure_ratio':p/(p-candidate['total_dp_budget_Pa']),
        'candidate_known_ratios_above_observed_points':{s:q>max(observed_pr) for s,q in targets.items()},
        'meaning':'Point-coverage check only; no interpolation/map or proof that an untested machine setting is impossible.'}
def run(folder: Path=ROOT) -> dict:
    source=json.loads((folder/'SOURCE_ROWS.json').read_text(encoding='utf-8'))
    candidate=json.loads((folder/'CANDIDATE_INTERFACE.json').read_text(encoding='utf-8'))
    admission=json.loads((folder/'ADMISSION.json').read_text(encoding='utf-8'))
    if len(source['rows'])!=3 or len({r['id'] for r in source['rows']})!=3: raise ValueError('Unexpected source table')
    frozen={'source_rows_sha256':sha(folder/'SOURCE_ROWS.json'),'candidate_sha256':sha(folder/'CANDIDATE_INTERFACE.json'),
        'admission_sha256':sha(folder/'ADMISSION.json'),'code_sha256':sha(Path(__file__)),
        'pressure_interpretations':['absolute_inlet','absolute_outlet'],'definition_gate_inputs':{},
        'not_an_uncertainty_interval':True,'no_regression':True}
    save(folder/'FROZEN_INPUT.json',frozen)
    included=[r for r in source['rows'] if eligible(r)]
    out=[pressure_work_proxy(r,mode) for r in included for mode in frozen['pressure_interpretations']]
    result={'schema':'fusion.measured-circulator-assessment.v1','frozen_input_sha256':sha(folder/'FROZEN_INPUT.json'),
        'source_doi':source['doi'],'source_reported_rows':included,'diagnostics':out,
        'excluded_rows':[{'id':r['id'],'reason':r['classification']} for r in source['rows'] if not eligible(r)],
        'source_internal_discrepancies':source['not_to_merge'],'definition_gate':assess_gate({}),
        'current_header_envelope':header_envelope(candidate,out),
        'candidate_assumed_product_not_directly_comparable':candidate['eta_fluid_assumed']*candidate['eta_drive_assumed'],
        'model_versions':{k:version(k) for k in ['CoolProp','numpy','scipy']},
        'new_empirical_information':'Two public source-reported high-flow operating/test rows now preserved with units and exclusions; not a new measurement.',
        'decision':'Retain as empirical context; do not use it as a qualified fluid efficiency, similarity map, or a plant-output update.',
        'scope':admission['boundaries']+['Source pressure reference and instrumentation uncertainties remain unresolved.',
            'Different pressure-work ratios at different operating conditions are not a measurement of our candidate efficiency.',
            'Figure design contours and rated rows have not become fitted observations.','No source PDF is required for numerical replay; its hash and locator are preserved.']}
    save(folder/'RESULT.json',result)
    print(json.dumps({'rows':len(included),'diagnostics':out,'coverage':result['current_header_envelope']},indent=2),flush=True)
    return result
if __name__=='__main__': run()
