# Real-data acceptance contract

A source is accepted as experimental replay data only when all of the following are present before scoring:

1. Numeric shot timeseries, not only metadata, schemas, loader code, screenshots, or undocumented object keys.
2. Shot identifiers and monotonic timebases.
3. Explicit units and sign/coordinate conventions.
4. Plasma current, magnetic-axis R/Z or documented equivalents, and at least one active PF-current channel.
5. Source/version provenance, processing level, quality flags, and redistribution/publication terms.
6. A deterministic shot-level train/calibration/holdout split frozen before holdout outcomes are inspected.
7. No signal mapping inferred from ambiguous abbreviations when multiple interpretations remain possible.

Failure of this contract is an access/schema result, not a scientific result. Synthetic coverage remains synthetic until this contract passes.
