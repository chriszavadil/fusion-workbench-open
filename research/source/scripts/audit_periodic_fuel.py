#!/usr/bin/env python3
"""Periodic-operability test for the inherited, assumed-parameter fuel ledger.

No new transport, reactor optimization, safety or experimental claim. The binary
pulse model has three residence-time reservoirs and one available store. Decay
makes the repeated affine map stable. We test the entire limiting periodic orbit,
not just mean breeding surplus or survival over a finite startup-funded campaign.

Copyright: project-original extension; imports the prior audit without modifying it.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, replace
import hashlib
import json
import math
from pathlib import Path
import time

import numpy as np
import scipy
from scipy.constants import electron_volt, physical_constants
from scipy.linalg import expm
from scipy.optimize import brentq

from audit_fuel_campaign import FuelConfig, analytic_step, matrix_generator, rates
from audit_coupled_candidate import load_baseline, YEAR_S, ARCHIVE_SHA


@dataclass(frozen=True)
class Schedule:
    """Identical rectangular pulses, plus an optional tail outage, repeated forever.

    Transfer/processing remains ON during idle/outage. Outages of processing itself
    need a different transition matrix and are outside this model.
    """
    before_s: float
    burn_s: float
    after_s: float
    repeats: int = 1
    tail_outage_s: float = 0.0

    def validate(self) -> None:
        for key in ('before_s', 'burn_s', 'after_s', 'tail_outage_s'):
            v = getattr(self, key)
            if not math.isfinite(v) or v < 0:
                raise ValueError(f'Invalid {key}')
        if self.burn_s <= 0:
            raise ValueError('A strictly positive burn phase is required')
        if isinstance(self.repeats, bool) or not isinstance(self.repeats, int) or not 1 <= self.repeats <= 100_000:
            raise ValueError('repeats must be an integer in [1,100000]')

    @property
    def pulse_s(self) -> float:
        return self.before_s + self.burn_s + self.after_s

    @property
    def period_s(self) -> float:
        return self.repeats * self.pulse_s + self.tail_outage_s

    def phases(self):
        for n in range(self.repeats):
            for dt, on, label in ((self.before_s, False, 'before'), (self.burn_s, True, 'burn'), (self.after_s, False, 'after')):
                if dt:
                    yield dt, on, n, label
        if self.tail_outage_s:
            yield self.tail_outage_s, False, self.repeats, 'tail_outage'


def validate(c: FuelConfig, s: Schedule, burn: float, reserve: float = 0.0) -> None:
    c.validate(); s.validate()
    # The inherited validation is reinforced here, including the routing fraction.
    for k, v in asdict(c).items():
        if not math.isfinite(v):
            raise ValueError(f'Nonfinite fuel parameter {k}')
    if not math.isfinite(burn) or burn <= 0:
        raise ValueError('burn must be finite and positive')
    if not math.isfinite(reserve) or reserve < 0:
        raise ValueError('reserve must be finite and nonnegative')


def linear_transition(c: FuelConfig, dt: float) -> np.ndarray:
    """Closed-form exp(A dt) of the triangular 4-state reservoir/store system."""
    lam = c.decay
    F = np.zeros((4, 4))
    F[np.arange(3), np.arange(3)] = np.exp(-(1 / c.tau + lam) * dt)
    F[3, 3] = math.exp(-lam * dt)
    F[3, :3] = math.exp(-lam * dt) * c.yields * (-np.expm1(-dt / c.tau))
    return F


def phase_map(c: FuelConfig, burn: float, dt: float) -> np.ndarray:
    """Affine map as a 5x5 homogeneous matrix; no inverse of A is used."""
    F = np.eye(5)
    F[:4, :4] = linear_transition(c, dt)
    F[:4, 4] = analytic_step(c, np.zeros(4), burn, dt)
    return F


def period_map(c: FuelConfig, s: Schedule, burn: float, *, matrix_method=False) -> np.ndarray:
    def step(b, dt):
        if matrix_method:
            ind = [0, 1, 2, 3, 8]
            return expm(matrix_generator(c, b)[np.ix_(ind, ind)] * dt)
        return phase_map(c, b, dt)
    pulse = step(0.0, s.after_s) @ step(burn, s.burn_s) @ step(0.0, s.before_s)
    return step(0.0, s.tail_outage_s) @ np.linalg.matrix_power(pulse, s.repeats)


def periodic_initial(c: FuelConfig, s: Schedule, burn: float, *, matrix_method=False) -> tuple[np.ndarray, dict]:
    """Solve the unique affine-map fixed point with stable small-decay arithmetic."""
    validate(c, s, burn)
    M = period_map(c, s, burn, matrix_method=matrix_method)
    T = s.period_s
    # F is source-independent and exactly known even after many matrix products.
    if matrix_method:
        x = np.linalg.solve(np.eye(4) - M[:4, :4], M[:4, 4])
    else:
        x = np.zeros(4)
        x[:3] = M[:3, 4] / (-np.expm1(-(1 / c.tau + c.decay) * T))
        numerator = M[3, 4] + math.exp(-c.decay * T) * np.dot(c.yields * (-np.expm1(-T / c.tau)), x[:3])
        x[3] = numerator / (-math.expm1(-c.decay * T))
    if not np.all(np.isfinite(x)) or np.any(x[:3] < -1e-9):
        raise ValueError('Invalid limiting reservoir state')
    err = float(np.max(abs(M[:4, :4] @ x + M[:4, 4] - x)))
    return x, {'period_map_residual_kg': err, 'spectral_radius': math.exp(-c.decay * T)}


def stored_derivative(c: FuelConfig, x: np.ndarray, burn: float) -> float:
    _, inj = rates(c, burn)
    return float(np.dot(c.yields / c.tau, x[:3]) - inj - c.decay * x[3])


def orbit_extrema(c: FuelConfig, s: Schedule, burn: float, x0: np.ndarray) -> dict:
    """All phase endpoints and all possible interior minima are evaluated.

    In ON phases every holdup increases toward its ON equilibrium; in OFF phases
    every holdup decreases. Thus d/dt[exp(lambda*t)*S'] has a fixed sign per phase.
    Each ON phase has at most one interior minimum. Each OFF phase has at most one
    interior maximum; its minimum is at an endpoint. These properties are verified.
    """
    x = np.array(x0, dtype=float, copy=True)
    q_on, _ = rates(c, burn)
    upper_h = q_on / (1 / c.tau + c.decay)
    minimum = (float(x[3]), 0.0, -1, 'start', 0.0)
    max_store = float(x[3]); t = 0.0; roots = 0
    for dt, on, pulse, label in s.phases():
        if np.any(x[:3] < -1e-8) or np.any(x[:3] - upper_h > 1e-8):
            raise ValueError('Monotone-phase extremum proof does not apply')
        b = burn if on else 0.0
        start = x.copy(); end = analytic_step(c, start, b, dt)
        candidates = [(0.0, start), (dt, end)]
        d0 = stored_derivative(c, start, b); d1 = stored_derivative(c, end, b)
        if (on and d0 < 0 < d1) or (not on and d0 > 0 > d1):
            root = brentq(lambda z: stored_derivative(c, analytic_step(c, start, b, z), b), 0., dt, xtol=1e-7)
            candidates.append((root, analytic_step(c, start, b, root)))
            roots += 1
        for local_t, candidate in candidates:
            if candidate[3] < minimum[0]:
                minimum = (float(candidate[3]), t + local_t, pulse, label, local_t)
            max_store = max(max_store, float(candidate[3]))
        x = end; t += dt
    return {'min_available_kg': minimum[0], 'min_time_s': minimum[1], 'min_pulse_index': minimum[2],
            'min_phase': minimum[3], 'min_local_time_s': minimum[4], 'max_available_kg': max_store,
            'end_state_kg': x.tolist(), 'interior_extrema_count': roots,
            'direct_period_closure_error_kg': float(np.max(abs(x-x0)))}


def periodic_assessment(c: FuelConfig, s: Schedule, burn: float, reserve: float = 0.5) -> dict:
    validate(c, s, burn, reserve)
    x, check = periodic_initial(c, s, burn)
    extreme = orbit_extrema(c, s, burn, x)
    margin = extreme['min_available_kg'] - reserve
    tolerance = 1e-7  # numerical classification tolerance, not physical uncertainty
    disposition = 'periodic_reserve_pass' if margin > tolerance else 'periodic_reserve_fail' if margin < -tolerance else 'numerical_boundary'
    return {'config': asdict(c), 'schedule': asdict(s), 'reserve_floor_kg_assumed': reserve,
            'periodic_initial_state_kg': x.tolist(), **check, **extreme,
            'reserve_margin_kg': margin, 'classification': disposition,
            'unexported_surplus_can_cause_large_storage': True,
            'physical_plant_self_sufficiency_validated': False}


def threshold(c: FuelConfig, s: Schedule, burn: float, reserve: float = 0.5) -> dict:
    """Minimum TBR in this ledger: limiting orbit stays >= reserve at every time.

    Increasing TBR adds only a nonnegative breeding source in a positive stable
    linear system, so limiting available inventory is strictly increasing.
    """
    validate(c, s, burn, reserve)
    cache = {}
    def objective(tbr):
        if tbr not in cache:
            cache[tbr] = periodic_assessment(replace(c, TBR=tbr), s, burn, reserve)
        return cache[tbr]['reserve_margin_kg']
    lo = 0.0; hi = max(2.0, c.TBR)
    while objective(hi) < 0 and hi < 32:
        hi *= 2
    if objective(hi) < 0:
        return {'status': 'no_bracket_below_TBR32', 'physical_claim': False}
    root = brentq(objective, lo, hi, xtol=1e-13, rtol=1e-14)
    certified = periodic_assessment(replace(c, TBR=root), s, burn, reserve)
    physical_initial = np.array(certified['periodic_initial_state_kg'])
    # With empty processing reservoirs, this finite sufficient initial store
    # dominates the limiting available trajectory at every future time.
    # delta S(t)=exp(-lambda*t) sum_i y_i*h_i(0)*exp(-t/tau_i) >=0.
    sufficient_seed = physical_initial[3] + float(np.dot(c.yields, physical_initial[:3]))
    return {'status': 'threshold_computed', 'critical_TBR': root, 'assessment_at_threshold': certified,
            'sufficient_empty_reservoir_initial_store_kg': sufficient_seed,
            'seed_is_sufficient_not_minimum': True, 'threshold_function_evaluations': len(cache)}


def mean_balance_lower_bound(c: FuelConfig, s: Schedule, burn: float, reserve: float) -> float:
    """Necessary cycle-average condition, including reservoir decay and reserve.

    It is NOT sufficient: a nonnegative average can coexist with a negative trough.
    """
    q, inj = rates(replace(c, TBR=1.0), burn)
    duty = s.repeats * s.burn_s / s.period_s
    delivered = c.yields / (1 + c.decay * c.tau)
    return (inj - np.dot(delivered[:2], q[:2]) + c.decay * reserve / duty) / (delivered[2] * burn)


def inherited_schedule(v: dict) -> Schedule:
    return Schedule(v['t_plant_pulse_coil_precharge'] + v['t_plant_pulse_plasma_current_ramp_up'] + v['t_plant_pulse_fusion_ramp'],
                    v['t_plant_pulse_burn'], v['t_plant_pulse_plasma_current_ramp_down'] + 600.)


def write_json(path: Path, obj) -> str:
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, allow_nan=False) + '\n')
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(archive: Path, output: Path) -> dict:
    start = time.perf_counter(); v, mhash = load_baseline(archive)
    burn = v['p_plasma_dt_mw'] * 1e6 / (17.6e6*electron_volt) * physical_constants['triton mass'][0]
    base = inherited_schedule(v)
    # These are schedule sensitivities, not statements about achievable reliability.
    n = math.floor(.8*YEAR_S/base.pulse_s)
    macro = replace(base, repeats=n, tail_outage_s=YEAR_S-n*base.pulse_s)
    distributed = replace(base, after_s=base.after_s+(YEAR_S-n*base.pulse_s)/n)
    cases = [FuelConfig(puff_tritium_core_ratio=g, direct_recycling_fraction=d, recycle_yield=1-loss)
             for g in (0., 1., 10.) for d in (0., .8) for loss in (.0001, .0005)]
    output.mkdir(parents=True, exist_ok=True)
    frozen = {'schema': 'fusion-solution-set.periodic-fuel-input.v1', 'prior_commit': '18c2d9f4daf9753d14739e5ca02cd14d51e648dd',
              'power_archive_sha256': ARCHIVE_SHA, 'baseline_mfile_sha256': mhash, 'burn_rate_kg_s': burn,
              'periodic_cases': [asdict(c) for c in cases], 'reserve_floors_kg': [0.0, 0.5, 2.0],
              'schedules': {'pulse_no_extra_outage': asdict(base), 'clustered_annual_outage': asdict(macro),
                            'distributed_same_annual_burn': asdict(distributed)},
              'outage_comparison_configs': [asdict(FuelConfig(puff_tritium_core_ratio=g, recycle_yield=1-loss))
                                            for g, loss in ((0.,.0005),(10.,.0001),(10.,.0005))],
              'boundary_witness_fraction': .5,
              'scope': ['All recoveries, residence times, TBR, and reserves are assumed; physical calibration remains outstanding.',
                        'Fuel burn is rectangular; ramp consumption and deuterium/core feedback are not represented.',
                        'All fuel processing continues during no-burn outages; processing failures are not included.',
                        'No maximum storage capacity, exports, fleet growth, or actual machine safety certification.',
                        'A limiting periodic-orbit test within a reduced ledger is NOT an experimental or whole-plant result.']}
    input_sha = write_json(output/'PERIODIC_FUEL_FROZEN_INPUT_2026-09-07.json', frozen)
    rows = []
    for c in cases:
        for reserve in frozen['reserve_floors_kg']:
            th = threshold(c, base, burn, reserve)
            lb = mean_balance_lower_bound(c, base, burn, reserve)
            th.update({'input_config':asdict(c), 'reserve_floor_kg_assumed':reserve,
                       'necessary_mean_balance_TBR':lb,
                       'nominal_TBR_1_15_passes_periodic_reserve':1.15 >= th['critical_TBR']})
            rows.append(th)
    outage = []
    for d in frozen['outage_comparison_configs']:
        c = FuelConfig(**d)
        for name, s in [('clustered_annual_outage', macro), ('distributed_same_annual_burn', distributed)]:
            th = threshold(c, s, burn, .5)
            th.update({'schedule_label':name, 'input_config':asdict(c),
                       'annual_burn_kg':burn*n*base.burn_s,
                       'necessary_mean_balance_TBR':mean_balance_lower_bound(c,s,burn,.5)})
            outage.append(th)
    # Deliberately adversarial point between mean sufficiency and true trough test.
    witness_base = FuelConfig(puff_tritium_core_ratio=10., recycle_yield=.9999)
    th = threshold(witness_base, base, burn, .5)
    lower = mean_balance_lower_bound(witness_base, base, burn, .5)
    witness_c = replace(witness_base, TBR=(lower+th['critical_TBR'])/2)
    witness = periodic_assessment(witness_c,base,burn,.5)
    # Independent matrix-exponential fixed point vs closed-form transitions.
    verification = []
    for c in [FuelConfig(), witness_c, replace(witness_base,TBR=th['critical_TBR'])]:
        direct, chk = periodic_initial(c, base, burn)
        independent, _ = periodic_initial(c, base, burn, matrix_method=True)
        verification.append({'TBR':c.TBR,'puff_ratio':c.puff_tritium_core_ratio,
                             'maximum_initial_state_difference_kg':float(np.max(abs(direct-independent))),
                             **chk})
    result = {'schema':'fusion-solution-set.periodic-fuel-result.v1','frozen_input_sha256':input_sha,
              'input':frozen,'periodic_thresholds':rows,'equal_burn_outage_comparisons':outage,
              'mean_pass_periodic_fail_witness':{'mean_threshold':lower,'true_periodic_threshold':th['critical_TBR'],
                                               'test_TBR':witness_c.TBR,'assessment':witness},
              'independent_numerical_checks':verification,
              'runtime_seconds':time.perf_counter()-start,'environment':{'numpy':np.__version__,'scipy':scipy.__version__},
              'claim_boundary':frozen['scope']}
    write_json(output/'PERIODIC_FUEL_RESULT_2026-09-07.json',result)
    return result


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--archive',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=run(a.archive,a.output)
    print(json.dumps({'cases':len(r['periodic_thresholds']),'outage_cases':len(r['equal_burn_outage_comparisons']),
                      'runtime_seconds':r['runtime_seconds'],'result':str(a.output/'PERIODIC_FUEL_RESULT_2026-09-07.json')}))
