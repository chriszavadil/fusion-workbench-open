# Periodic fuel-operability criterion: scope and derivation

This is a mathematical criterion for the four-state, assumed-parameter ledger in this repository. It is not a proof of reactor operability, actual tritium recovery, or a new general theorem in control theory. Affine periodic maps and stable linear reservoirs are standard methods. The contribution here is a reproducible gate applied to the archived pulse schedule, including a counterexample to an average-only acceptance rule.

## 1. Model and assumptions

Let H_i be tritium held in fast recycling, slow recycling, and blanket extraction, and S be immediately available tritium. All inventories are in kg; times are seconds. With k_i = 1/tau_i + lambda,

    dH_i/dt = q_i(t) - k_i H_i
    dS/dt   = sum_i(y_i H_i/tau_i) - I(t) - lambda S.

Here lambda is strictly positive radioactive decay, tau_i > 0 are fixed residence times, and 0 < y_i <= 1 are recovered fractions. Burn is either zero or the fixed flat-top rate B. If b is effective core burn fraction and g is the ratio of tritium puffing to core tritium input, I = (1+g)B/b. Exhaust is I-B. A fixed fraction of exhaust enters fast recycling; the remainder enters slow processing. Blanket production is TBR*B. Nonzero sources are constant during a rectangular burn, zero otherwise. Processing continues throughout idle periods and declared no-burn outages.

The model excludes isotope composition, plasma response, material trapping/diffusion, maximum storage, exports, fleet growth, random failures, outages of the processing equipment, and ramp-phase consumption. A chosen reserve R is a mathematical scenario input, not a regulatory or operational recommendation.

## 2. Unique limiting periodic orbit

Write x = (H_1,H_2,H_3,S). Constant coefficients give dx/dt = Ax + u(t). For a repeated schedule of period T,

    x(T) = Phi x(0) + d,    Phi = exp(A T).

A is lower triangular, with eigenvalues -k_i and -lambda. Consequently rho(Phi) = exp(-lambda*T) < 1, and

    x_star(0) = (Identity - Phi)^(-1) d

is the unique limiting periodic initial state. Every trajectory with finite initial inventories converges to this orbit at each phase. The implementation uses stable expm1 expressions for the small-decay terms, and separately checks the matrix-exponential construction and the fixed point.

If min_t S_star(t) < R, then no finite startup stock can maintain S >= R forever under this repeated, unchanged schedule. At the offending phase every finite startup perturbation eventually decays. This is stronger than failure of a finite campaign and does not imply a different physical reactor is impossible.

If min_t S_star(t) >= R, the periodic initial state itself is admissible. Starting with EMPTY processing reservoirs can also be made admissible using a sufficient initial available stock:

    S_seed = S_star(0) + sum_i y_i H_i,star(0).

For the difference from the periodic trajectory,

    delta S(t) = exp(-lambda*t) sum_i y_i H_i,star(0) exp(-t/tau_i) >= 0.

Thus S(t) >= S_star(t) >= R for every future time. This seed is sufficient, NOT asserted to be the minimum startup stock. The result assumes no storage upper bound or export policy. It does not establish that this amount of tritium can be procured or safely handled.

Together these establish necessity and sufficiency WITHIN THE SPECIFIED LEDGER for a finite-initial-stock, no-import trajectory that respects the lower reserve indefinitely.

## 3. Complete intra-period minimum test

It is insufficient to check only one sample per pulse. On the limiting orbit, each holdup lies between zero and its continuous-on equilibrium q_i,on/k_i. During a burn each holdup increases; during idle it decreases. These bounds are checked numerically before the extremum argument is used.

Let r(t) = sum_i y_i H_i/tau_i. Inside a constant-input phase,

    d/dt [exp(lambda*t) S'(t)] = exp(lambda*t) r'(t).

The right side is nonnegative during burn and nonpositive during idle. Therefore burn phases have at most one interior minimum (a negative-to-positive derivative crossing), and idle phases have at most one interior maximum. All endpoints and all possible interior extrema are evaluated using bracketed roots. There is no unsampled oscillatory trough within these assumptions. General varying-rate or failed-processing schedules would require a different argument.

## 4. Why average balance is only necessary

Averaging over a periodic schedule gives

    average(H_i) = average(q_i)/(1/tau_i + lambda)
    lambda*average(S) = sum_i y_i*average(q_i)/(1+lambda*tau_i) - average(I).

Respecting a reserve requires average(S) >= R, but the converse fails. The saved witness passes this necessary condition (including holdup decay and reserve) while its limiting minimum is approximately 0.334474 kg rather than the declared 0.5 kg reserve.

## 5. Inverse requirements and limitations

Increasing TBR adds a nonnegative source to a stable positive system. Limiting available inventory increases, allowing a bracketed critical-TBR calculation. The inverse follow-on solves for recovery loss, gas throughput, and effective burn fraction, and verifies each computed root on BOTH sides of the boundary. This is not independent physical validation or held-out discovery: those follow-on questions were selected after the initial periodic study.

The theorem must not be generalized to actual HCPB operation until residence/release kinetics, recoveries, fuel streams, plasma coupling and failure modes have been calibrated and independently checked. Good numerical closure does not make assumed physical parameters correct.
