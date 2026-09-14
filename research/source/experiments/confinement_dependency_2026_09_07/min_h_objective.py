"""Runtime-only scalar objective adapter; same native models and constraints.
Native slot1 banner refers to radius; this experiment instead minimizes hfact.
"""
import math
from process.core import caller
from process.core.solver import objectives
ORIGINAL=objectives.objective_function
def minimum_hfact(slot,data):
    if slot!=1:raise ValueError('Adapter only admits positive objective slot1')
    h=float(data.physics.hfact)
    if not math.isfinite(h) or h<=0:raise ValueError('Invalid H multiplier')
    return h
def install():
    if caller.objective_function is not ORIGINAL:raise RuntimeError('Unexpected existing objective patch')
    caller.objective_function=minimum_hfact
    objectives.objective_function=minimum_hfact
