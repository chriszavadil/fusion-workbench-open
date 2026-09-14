"""Typed, allowlisted projection of numerical evidence. No raw logs are public.

Copyright (c) 2026 Fusion Workbench contributors. MIT license.
"""
from __future__ import annotations
import hashlib
import json
import math
from pathlib import Path
import re
from typing import Any

PHASES = (
    ('coil_precharge', 'Coil precharge'),
    ('plasma_current_ramp_up', 'Current ramp-up'),
    ('fusion_ramp', 'Fusion ramp'),
    ('burn', 'Generating phase'),
    ('plasma_current_ramp_down', 'Ramp-down'),
    ('dwell', 'Dwell'),
)
PROFILE_KEYS = {
    'net_MW': 'p_plant_electric_net',
    'gross_MW': 'p_plant_electric_gross',
    'heating_MW': 'p_hcd_electric_total',
    'cooling_MW': 'p_coolant_pump_elec_total',
    'base_MW': 'p_plant_electric_base_total',
    'toroidal_magnets_MW': 'p_tf_electric_supplies',
    'poloidal_magnets_MW': 'p_pf_electric_supplies',
    'vacuum_MW': 'vachtmw',
    'fuel_processing_MW': 'p_tritium_plant_electric',
    'cryogenics_MW': 'p_cryo_plant_electric',
}
GEOMETRY_KEYS = {
    'major_radius_m': 'rmajor', 'minor_radius_m': 'rminor',
    'elongation': 'kappa', 'triangularity': 'triang',
    'solenoid_inner_radius_m': 'dr_bore', 'solenoid_radial_width_m': 'dr_cs',
    'solenoid_height_m': 'dz_cs_full',
    'first_wall_inboard_m': 'dr_fw_inboard', 'first_wall_outboard_m': 'dr_fw_outboard',
    'blanket_inboard_m': 'dr_blkt_inboard', 'blanket_outboard_m': 'dr_blkt_outboard',
    'blanket_upper_m': 'dz_blkt_upper',
    'plasma_gap_inboard_m': 'dr_fw_plasma_gap_inboard',
    'plasma_gap_outboard_m': 'dr_fw_plasma_gap_outboard',
    'plasma_gap_upper_m': 'dz_fw_plasma_gap',
    'shield_inboard_m': 'dr_shld_inboard', 'shield_outboard_m': 'dr_shld_outboard',
    'vessel_inboard_m': 'dr_vv_inboard', 'vessel_outboard_m': 'dr_vv_outboard',
    'toroidal_coil_count': 'n_tf_coils',
}
NUMBER = re.compile(r'\(([^()]*)\)_*\s+([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eEdD][+-]?\d+)?)(?=\s|$)')

def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read_mfile(path: Path) -> dict[str, float]:
    """Single-scan numeric fields only; strings and metadata cannot pass through."""
    values: dict[str, float] = {}
    for line in path.read_text(encoding='utf-8-sig').splitlines():
        match = NUMBER.search(line)
        if not match:
            continue
        key, raw = match.groups()
        val = float(raw.replace('D', 'e').replace('d', 'e'))
        if not math.isfinite(val):
            raise ValueError('Nonfinite source value')
        if key in values and not math.isclose(values[key], val, rel_tol=1e-11, abs_tol=1e-12):
            raise ValueError('Conflicting values: multi-scan input is not supported')
        values[key] = val
    return values

def required(values: dict, key: str) -> float:
    value = values.get(key)
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value):
        raise ValueError('Required numeric source field is missing')
    return float(value)

def integrate_profile(times: list[float], powers: list[float]) -> float:
    if len(times) != len(powers) or len(times) < 2:
        raise ValueError('Profile dimensions differ')
    if any(not math.isfinite(v) for v in times + powers):
        raise ValueError('Nonfinite profile')
    if times[0] != 0 or any(b < a for a, b in zip(times, times[1:])) or times[-1] <= 0:
        raise ValueError('Invalid pulse timeline')
    return math.fsum((b-a)*(u+v)/2 for a,b,u,v in zip(times,times[1:],powers,powers[1:])) / 3.6

def verify_configuration(config: dict[str, Any]) -> dict:
    """Verification of recorded arithmetic, never experimental validation."""
    p = config['pulse']; t = p['time_s']; series = p['series']
    measured = integrate_profile(t, series['net_MW'])
    disagreement = abs(measured - config['metrics']['pulse_energy_kWh'])
    loads = [key for key in PROFILE_KEYS if key not in ('net_MW', 'gross_MW')]
    error = max(abs(series['net_MW'][i] - series['gross_MW'][i]
                    - math.fsum(series[k][i] for k in loads)) for i in range(len(t)))
    avg = measured * 3.6/t[-1] * config['assumptions']['availability']
    assert_valid = disagreement <= 1e-5 and error <= 1e-7
    return {'passed': assert_valid, 'energy_disagreement_kWh': disagreement,
            'maximum_balance_disagreement_MW': error,
            'recomputed_pulse_energy_kWh': measured,
            'conditional_average_net_MW': avg,
            'source_artifact_sha256': config['provenance']['artifact_sha256'],
            'kind': 'recorded_output_verification', 'physical_validation': False}

def project_configuration(path: Path, ident: str, title: str) -> dict:
    values = read_mfile(path)
    if required(values, 'ifail') != 1:
        raise ValueError('An unconverged case cannot supply accepted output')
    geometry = {out: required(values, key) for out, key in GEOMETRY_KEYS.items()}
    if geometry['major_radius_m'] <= geometry['minor_radius_m'] or geometry['minor_radius_m'] <= 0:
        raise ValueError('Invalid geometric envelope')
    if not 0 <= geometry['triangularity'] < 1:
        raise ValueError('Unsupported triangularity')
    time_s = [0.0]
    phase_names = []
    for key, label in PHASES:
        duration = required(values, 't_plant_pulse_' + key)
        if duration < 0:
            raise ValueError('Negative phase duration')
        time_s.append(time_s[-1] + duration); phase_names.append(label)
    series = {out: [required(values, f'{key}_profile_mw{i}') for i in range(7)]
              for out, key in PROFILE_KEYS.items()}
    available = required(values, 'f_t_plant_available')
    if not 0 < available <= 1:
        raise ValueError('Invalid assumed availability')
    result = {
        'id': ident, 'title': title,
        'status': 'numerically_converged_concept',
        'geometry': geometry,
        'metrics': {
            'flat_top_net_MW': required(values, 'p_plant_electric_net_mw'),
            'fusion_MW': required(values, 'p_fusion_total_mw'),
            'gross_MW': required(values, 'p_plant_electric_gross_mw'),
            'pulse_energy_kWh': required(values, 'e_plant_net_electric_pulse_kwh'),
            'cycle_s': required(values, 't_plant_pulse_total'),
            'fatigue_cycles': required(values, 'n_cycle'),
            'required_fatigue_cycles': required(values, 'n_cycle_min'),
            'solenoid_hoop_MPa': required(values, 'stress_hoop_cs_inner')/1e6,
            'solenoid_current_MA_m2': required(values, 'j_cs_flat_top_end')/1e6,
            'internal_confinement_multiplier': required(values, 'hfact'),
            'plant_accounting_residual_MW': required(values, 'p_plant_imbalance_mw'),
        },
        'assumptions': {'availability': available, 'EC_wall_plug_efficiency': 0.5,
                        'thermal_conversion_efficiency': required(values, 'eta_turbine'),
                        'additional_outage_electricity_modelled': False},
        'pulse': {'time_s': time_s, 'phase_names': phase_names, 'series': series,
                  'interpolation': 'piecewise_linear_recorded_profiles',
                  'spatial_field': False, 'mode': 'recorded_simulation_not_live_plasma'},
        'provenance': {'artifact_sha256': sha256(path), 'solver': 'UKAEA PROCESS',
                       'version': '3.4.2',
                       'public_upstream': 'https://github.com/ukaea/PROCESS/tree/c0ae5b28649f2b20fb7efc7904628b6defe4151c'},
        'scope': [
            'A conceptual systems-model result, not produced electricity or an operating reactor.',
            'Geometry is a display envelope derived from model dimensions, not manufactured CAD or an equilibrium reconstruction.',
            'The fatigue constraint has no newly validated material uncertainty margin.',
            'No matched neutron heating or tritium breeding tally is available for this geometry.',
            'Internal confinement multiplier is not automatically an experimental global H98 value.',
            'Do not combine other configurations\' cooling, fuel or equipment gains with these outputs.'
        ],
        'components': [
            {'id':'plasma','title':'Plasma envelope','evidence':'analytic_display_only',
             'detail':'Shape illustrates native major/minor radius, elongation and triangularity. No plasma simulation is implied by the glow.'},
            {'id':'solenoid','title':'Central solenoid','evidence':'dimensional_envelope',
             'detail':'Native bore radius, radial width and total height. Winding detail and qualified material life are not supplied.'},
            {'id':'first_wall','title':'First-wall envelope','evidence':'conceptual_shell',
             'detail':'Native side thicknesses and gaps; interpolated surface is not a resolved heat map or certified geometry.'},
            {'id':'blanket','title':'Breeding blanket envelope','evidence':'conceptual_shell',
             'detail':'Native inboard/outboard thicknesses. Internal channels, isotope geometry and measured breeding remain unresolved.'},
            {'id':'shield','title':'Shield envelope','evidence':'conceptual_shell',
             'detail':'Approximate visualization of native radial build. Top/bottom closure is illustrative.'},
            {'id':'vessel','title':'Vacuum-vessel envelope','evidence':'conceptual_shell',
             'detail':'Simplified boundary shell, not pressure-vessel design or structural qualification.'},
            {'id':'coils','title':'Toroidal-field coils','evidence':'schematic_only',
             'detail':'Native coil count; each surrounding coil shape is deliberately schematic, not an imported winding/structure solution.'},
        ],
    }
    check = verify_configuration(result)
    if not check['passed'] or abs(result['metrics']['cycle_s'] - time_s[-1]) > 1e-5:
        raise ValueError('Independent recorded-output verification rejected the source')
    result['metrics']['conditional_average_net_MW'] = check['conditional_average_net_MW']
    result['verification'] = check
    return result

def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False)+'\n', encoding='utf-8')
