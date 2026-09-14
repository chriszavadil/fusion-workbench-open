# Common-action protection lower bound

Let two state hypotheses be indistinguishable to the controller at the decision time and produce terminal vertical outputs `z1` and `z2` under the same future disturbance convention. Any common control waveform contributes the same additive terminal response `b` to both hypotheses in a linear plant. Therefore

```text
min_b max(|z1 + b|, |z2 + b|) = |z1 - z2| / 2.
```

Proof: write `a = (z1-z2)/2` and absorb `(z1+z2)/2+b` into `c`. The triangle inequality gives

```text
2|a| = |(a+c)-(-a+c)| <= |a+c|+|-a+c| <= 2 max(|a+c|,|-a+c|).
```

Equality is reached by shifting the midpoint to zero when the necessary common shift is attainable. With constrained actuation the optimum can only be worse. Over a trajectory, the worst-case peak is bounded below by half of the maximum time-indexed output diameter.

Engineering consequence: a protection layer must refuse a pre-identification recovery certificate whenever half of the certified future-output diameter exceeds the declared vertical budget after latency and model-discrepancy factors, unless additional information arrives before the action must be chosen.

This is a general convex-geometry/control fact, not a novelty claim. The research contribution under test is its prospective machine-derived calibration and engineering use under tokamak-specific profile, passive-current, latency, voltage, slew, and shared-authority constraints.
