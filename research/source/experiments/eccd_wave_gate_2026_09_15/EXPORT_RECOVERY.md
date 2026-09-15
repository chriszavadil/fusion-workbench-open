# Provisional equilibrium output recovery

The corrected profile exporter completed. It reproduced the archived higher-output net power to relative difference2.55e-14 and exported all201 density/temperature points plus numeric physics quantities. Artifact10423567981/run35037058554 preserves the profiles and all attempt logs.

Both provisional Grad-Shafranov solves converged (13 and12 iterations for0.15m and0.075m meshes), but gEQDSK export failed while tracing psi=0.999. Therefore the workflow's top-level success did not establish a wave-ready equilibrium; each child status correctly records failure. No wave calculation has used those unavailable outputs.

The exporter is corrected to write the equilibrium field/profile/statistics before attempting gEQDSK export. Admit one bounded replay of each same equilibrium using the already exported profile artifact; no PROCESS optimization is repeated. Use TokaMaker's documented default `lcfs_pad=0.01` instead of the over-tight0.001. Keep `truncate_eq=False`, and record the edge pad explicitly. This changes an output/tracing convention, not the force-balance equations or candidate physics. Preserve all earlier failures. If export or mesh-consistency checks still fail, no candidate wave result is claimed.

Exact recovered profile SHA-256:598f2a42100123962b5fb3d6612813dd1ed2bd2f206bd53aeff30cfc37db9a42. Runtime remains one thread,120seconds per equilibrium, maximum100 nonlinear iterations. A current-profile or field mismatch remains visible regardless of numerical convergence.
