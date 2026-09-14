# Contributing

We welcome physicists, engineers, research-software developers, experimentalists and careful reviewers. The project belongs to its contributors, not a personal brand.

## Before changing a model
Describe the closest published solution and what is still unresolved. Identify the exact configuration, source artifact, assumptions, units and evidence. State the decision your proposal could change and a finite falsification criterion. Do not repeat a known result unless reproduction is required to validate an implementation or compare a change.

Use a model proposal, dataset proposal or software bug issue. Reports must distinguish measured values, fitted parameters, design ratings, assumptions and illustrative geometry. Never transpose cooling or breeding results between the two reactor configurations without rematching their geometry and sources.

## Code and data
Original contributions should be supplied under the repository's MIT terms unless separately agreed and clearly labeled. Include provenance and a source-specific data license; third-party publications and restricted experimental datasets cannot be relicensed by this project. Do not submit credentials, account identifiers, private correspondence, absolute user-directory paths or personal machine metadata. Attribution can use a neutral contributor handle, but retain required upstream copyright notices.

## Reproducibility
The local worker checks pinned source, input and adapter hashes. Changes need a new reviewed manifest; do not weaken hash checks to make an altered input pass. Keep failed runs and deviations in a private evidence ledger and publish reviewed, non-identifying numerical summaries. State which tests ran and which did not.

Run `python -m pytest -q tests` for the browser/worker numerical and security checks. The native Windows preview has `-WorkbenchSelfTest -WorkbenchScreenshot` startup options that test configuration isolation, dimensional consistency, electrical replay and layer state, then exit. These are software checks, not physical validation.

## Review and execution
Maintainers review proposed changes before running them. Public issues and pull requests must never execute automatically on a personal workstation. Use isolated, resource-limited workers for untrusted code. There is no public code-upload or shell-execution endpoint in this preview.

A successful solver exit does not mean physical success. Compare numerical constraint residuals, uncertainty, operational feasibility and all relevant penalties. An accepted contribution needs an explicit conclusion and evidence; it does not silently replace the accepted reference.

## First useful contributions
Review the confinement/radiation convention; obtain compatible circulator definitions and measurements; specify a geometry-matched neutron/material model; connect existing compatible historical datasets; test the native application on another Windows machine. Check existing issues and cite prior work before starting.
