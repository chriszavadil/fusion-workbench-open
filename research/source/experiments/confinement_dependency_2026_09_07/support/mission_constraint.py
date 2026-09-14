"""30-year no-replacement CS duty requirement, coupled to actual pulse timing.
Assumed 80% availability; no maintenance reliability or physical life validation.
"""
from process.core.solver.constraints import ConstraintManager, geq
YEAR_SECONDS=8766.*3600.

def install():
    registration=ConstraintManager.get_constraint(90)
    def mission_equation(reg,data):
        duration=float(data.times.t_plant_pulse_total)
        if duration<=0:raise ValueError('Invalid full-cycle duration')
        required=float(data.costs.life_plant)*float(data.costs.f_t_plant_available)*YEAR_SECONDS/duration
        data.cs_fatigue.n_cycle_min=required
        return geq(data.cs_fatigue.n_cycle,required,reg)
    registration.constraint_equation=mission_equation
