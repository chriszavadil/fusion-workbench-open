"""Run one admitted proxy restoration and its new current-budget diagnostic. MIT."""
import sys
from current_budget import calculate
from finish_budget import finish
allowed=['dx0.18_ff1_v6','dx0.18_ff2_v6','dx0.09_ff1_v6','dx0.09_ff2_v6']
if len(sys.argv)!=2 or sys.argv[1] not in allowed:raise ValueError('Unadmitted case')
state=calculate(sys.argv[1]);finish(state)
