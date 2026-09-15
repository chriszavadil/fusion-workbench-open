# Breeding benchmark selection: reuse existing validation, not its numerical answer

## Decision
A directly relevant OpenMC validation study already exists. Felipe S. Novais and Ethan E. Peterson published *FNG HCPB Tritium Breeder Module Mock-Up Benchmarking of OpenMC and Uncertainty Quantification* online in October 2025 (Fusion Science and Technology 82(4), 844-852, 2026). We checked its publisher and American Nuclear Society abstracts and bibliographic metadata. We have not retrieved its complete model, per-detector results or uncertainty files, or reproduced its experiment in this project.

The abstract reports comparisons with MCNP-4C and SINBAD measurements of tritium production in lithium-carbonate pellets in a beryllium mock-up. It also describes SANDY-based sampling of nuclear data and an average tritium-production underprediction of about 9%. This is prior work by those authors, not a result of Fusion Workbench and not a substitute for a benchmark run on our installed stack. [1,2]

Our existing LiF leakage reproduction is useful for transport and data-interface checks but does not qualify Li4SiO4/TiBe12 blanket tritium production. The next justified step is to obtain and reproduce the existing HCPB package with its exact source, material specifications, pellet normalization and uncertainties, rather than build another generic benchmark framework or repeat the same LiF run.

## Do not turn another experiment's result into a correction factor
The roughly 9% number must not be added to, subtracted from or used to rescale our candidate's breeding result. It concerns a different assembly and response. It also does not establish the uncertainty of our roughly 2.71% front-versus-rear header comparison.

For a layout difference D = Y_front - Y_rear, the variance depends on both layouts and their covariance:

    Var(D) = Var(Y_front) + Var(Y_rear) - 2 Cov(Y_front, Y_rear)

A shared nuclear-data effect may partially cancel in a layout comparison or may affect the layouts differently. Its magnitude cannot be inferred from one average absolute discrepancy in a separate experiment. A justified uncertainty study would use the same physically supported nuclear-data realizations for both layouts, retain their correlation, and estimate transport sampling error separately. This is an uncertainty requirement, not a new sampled result or an invitation to invent arbitrary error bars.

## The original experiment and access scope
The NEA SINBAD record NEA-1553/71 credits the ENEA experiment and analysis, including P. Batistoni, M. Angelone, M. Pillon and L. Petrizzi, with compilation by I. Kodeli and review by S. Villari. It identifies the 2005 mock-up and lists measurements and input files. Its source description explicitly distinguishes older and revised D-T source routines. That matters: a source routine cannot silently be interchanged while calling a comparison source matched. We read the public summary and file inventory; the complete experimental package was not obtained. [3]

The summary's legacy availability label does not establish that every linked file has been downloaded or that a modern redistribution license covers an entire package. The NEA's 2025 announcement describes request routes for SINBAD version 2. No access fee, agreement, restricted data download or redistribution was authorized or undertaken here. [4]

## Completion and reopening conditions
This selection review is complete. Its sources and exact reading scope are entered in the searchable prior-work register. Reopen the HCPB task when the full geometry/source specification, pellet responses, source normalization, experimental-error definitions, exact code/data versions and applicable reuse terms are available. A current repository listing or an article abstract is not that complete package.

This review did not run another neutron calculation or alter accepted reactor dimensions, power, fuel recovery or experimental-validation status. It prevents two wasteful steps: recreating an existing validation method as a claimed discovery, and applying its unrelated numerical bias to our design. The recovered LiF calculation is reported separately, with every bin and attribution retained.

## Primary sources and reading scope
[1] Felipe S. Novais and Ethan E. Peterson, *FNG HCPB Tritium Breeder Module Mock-Up Benchmarking of OpenMC and Uncertainty Quantification*, DOI: https://doi.org/10.1080/15361055.2025.2567167 . Publisher abstract and metadata read; no full-text reproduction claimed.

[2] American Nuclear Society abstract of the same paper: https://www.ans.org/pubs/journals/fst/article-60202/ . This is another publisher record of the same study, not an independent experiment.

[3] NEA SINBAD NEA-1553/71, *FNG HCPB Tritium Breeder Module Mock-up*: https://www.oecd-nea.org/science/wprs/shielding/sinbad/fng_hcpb/fnghcpb-a.htm . Public summary and file inventory read, not the complete original benchmark package.

[4] OECD Nuclear Energy Agency, *New version released: The NEA Shielding Integral Benchmark Archive and Database (SINBAD)*, 2 July 2025: https://www.oecd-nea.org/jcms/pl_107605/new-version-released-the-nea-shielding-integral-benchmark-archive-and-database-sinbad . Distribution-process announcement, not a grant of data reuse rights.

No endorsement by the named authors or organizations is implied. No third-party article or restricted input package is bundled with this review.
