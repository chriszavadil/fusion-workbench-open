# Sources, attribution and original September 15 reading scope

This file accompanies the restored analytic study. The original computation ran while workstation access was paused. The September 16 continuation is a separate study and records its new raw-profile check, equilibrium calculations and software setup separately. Historical access limitations below describe the original computation, not the restored connection.

## Reused physics—not a new method

1. N. A. Lopez, A. Alieva, S. A. M. McNamara and X. Zhang, **Fast physics-based launcher optimization for electron cyclotron current drive**, Plasma Physics and Controlled Fusion 67, 055012 (2025), DOI 10.1088/1361-6587/adcae7. The January 15, 2026 arXiv v2 was read as full HTML: https://arxiv.org/html/2501.04619v2 . Equations 4–10 provide the local HARE seed prescription; Equation 13na defines the local dimensionless current-drive normalization. Their demonstrated workflow includes GENRAY reverse/forward rays and current-drive calculations. Those calculations were **not** performed by the September 15 screen.

2. E. Poli, M. Müller, H. Zohm and M. Kovari, **Fast evaluation of the current driven by electron cyclotron waves for reactor studies**, Physics of Plasmas 25, 122501 (2018), DOI 10.1063/1.5050345. Original HARE credit, as cited by [1]. This screen implements equations explicitly restated in [1]; it does not claim to reproduce the full original HARE efficiency implementation. https://doi.org/10.1063/1.5050345

3. Richard Fitzpatrick, **Cold-Plasma Dielectric Permittivity** and **Cold-Plasma Dispersion Relation**, University of Texas at Austin lecture notes (2016): https://farside.ph.utexas.edu/teaching/plasma/Plasma/node64.html and https://farside.ph.utexas.edu/teaching/plasma/Plasma/node65.html . The Stix dielectric matrix and Maxwell determinant were read. The screen uses their electron-only high-frequency limit, with an independently derived quadratic in perpendicular index squared. It is not a hot-dielectric or absorption model.

## Candidate and profile provenance

4. Fusion Workbench public commit `f297593e9d4f30b647fe4042c9f364b0bcec437f`: https://github.com/chriszavadil/fusion-workbench-open/tree/f297593e9d4f30b647fe4042c9f364b0bcec437f . Input field projections and Git blob identifiers are recorded in INPUTS.json. The existing candidate study—not this analytic screen—supplies the scalar operating points. Original MFILE SHA-256 references are retained; those private raw files were not reacquired or modified in the September 15 computation.

5. UKAEA PROCESS commit `c0ae5b28649f2b20fb7efc7904628b6defe4151c`:
   - `process/models/physics/profiles.py`, Git blob `2a655789b2cbf6eb59235858041683fa4488a82b`.
   - `process/data_structure/physics_variables.py`, Git blob `910ce574c185c9ea3e342c669431006cd9a700ed`.
   - `documentation/source/physics-models/profiles/plasma_density_profile.md`, Git blob `97a118b04d813207e8d0683d8b02255099fdb5b3`.
   Source: https://github.com/ukaea/PROCESS/tree/c0ae5b28649f2b20fb7efc7904628b6defe4151c . Relevant equations, profile endpoints and default density settings were read. The profile convention cites HELIOS / J. Jean (2011), DOI 10.13182/FST11-A11650. This is an independent equation implementation using the published scalar state, not an execution of PROCESS.

## Scope and reuse

No article full text, restricted benchmark package, GENRAY source distribution, credentials, personal correspondence, engine source, or private execution history is bundled in this analytic module. Existing methods and their developers receive the credit above. All values produced here are labeled analytic/reconstructed rather than measured or full ray/current-drive output. No endorsement is implied.

Original analysis, tests and interface code are MIT licensed. Named third-party methods and publications retain their own rights; citation is not a transfer of rights or physical validation. Constants come from the installed SciPy constants module. Runtime versions are recorded in RESULTS.json, so a restored run may have different runtime metadata without becoming a new physics result.
