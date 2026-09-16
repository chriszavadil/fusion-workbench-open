# Power progress: best model output, historical corrections and physical benchmarks

## The headline and what it means
The primary Workbench metric is **conditional average net electrical output**, not the largest instantaneous fusion power or a software-test count. Among the explicitly eligible recorded systems cases, the present high-water mark is274.011272896 MW average net electricity, with501.659277405 MW during the burn in the same case. It is a **physically unqualified model result**, not generated electricity, a world record or an accepted plant.

The maintained r838 reference remains213.691318020 MW conditional average. It must not be confused with the214.683127572 MW reoptimized fixed-radius control. Only the latter is the control for the274.011272896 MW alternative; their conditional difference is59.328145324 MW, about27.635%. The paired input changes and unresolved actuator assumptions are in the existing whole-plant study. Fixed major radius is not identical complete hardware.

The physical net-electric result for this project is **not measured**, stored as null rather than0. No hardware experiment occurred here. The dashboard does not turn an absent measurement into zero, a model into a measured result, or a percentage of fusion solved.

## History and record-selection policy
Twelve records are retained in the review chronology. Dated study documents supply dates; no exact within-day execution time is invented. Early model constraints, assumptions and objectives changed. A scatter of those records is not a controlled longitudinal experiment; no connecting line implies increasing physical performance.

The preserved406.53 MW earlier cross-study screen is explicitly marked superseded and excluded. It combined proposed efficiency, dwell and pumping assumptions without the final coupled whole-plant result. Showing that number as the best test would reward a rejected claim. Original no-fatigue and20k-cycle screens remain visible with their limited requirements. The native20k result that failed an adaptive check is retained rather than silently deleted.

The two failed steady-state attempts have no scored power; their raw unconverged numerical fields are not used. The zero-heating-only-reserve case is an explicitly optimistic bound and excluded from the headline. Maintained model references and numerically converged exploratory pulsed cases under the later implemented lifetime scope can enter the **model** high-water-mark calculation. Eligibility for that comparison is not experimental validation, control qualification or plant approval.

The September16 equilibrium finding is a separate qualification event, not another power point. The constructed equilibria did not reproduce the assumed q95, so the earlier model gain remains a lead needing a consistent equilibrium/current-drive/control assessment. Matching total current and energy did not close that gate. The dashboard preserves the historical number and adds the limitation instead of claiming new output or falsely saying the original concept is impossible.

## Arithmetic and energy boundaries
Average net MW = pulse net electrical energy(kWh) ×3.6 / modeled cycle duration(s) × assumed availability. The eligible project records use80% assumed availability and their recorded pulse/dwell schedule. Additional unscheduled-outage electricity is not modeled. This is distinct from burn net power, gross generation and fusion thermal power.

Each historical row links to its exact repository source path, carries the source-file hash, and preserves the original output hash when present. Where only the published report supplied a rounded historical value, that precision is declared. Exact input/output files, all underlying recorded schedules and full physics source remain in their existing modules; this dashboard is an attributed read-only projection, not another solver or fit.

## Real-world experiments: separately sourced, not ranked against the model
The physical panel contains eleven selected milestones, verified against primary laboratory/agency pages on16September2026. It is not an exhaustive database or claim about every fusion device. Experimental authors and teams retain the credit. The rows distinguish experiment dates from announcement dates and retain year-only precision where the selected source did not identify a day.

JET's energy milestones are21.7 MJ(1997),59 MJ(2021) and69 MJ(October3,2023). A separate1997 peak-power milestone is16.1 MW. These are fusion reaction outputs, not net electricity. The1997 peak and energy achievements are not assumed to be the same shot. TFTR's November2,1994 milestone is10.7 MW fusion power, credited to PPPL.

UKAEA describes the69 MJ JET result over5seconds, while the participating Max Planck institute describes5.2seconds. Both durations and their sources are retained. Derived means are13.8 and13.269230769 MW respectively; these are source-interval conversions, not peak powers or a statistical uncertainty range. The59 MJ/5s mean is11.8 MW, derived from those reported rounded values. No separate peak value is inserted into that calculation.

The NIF series includes3.15 MJ(December2022),3.88 MJ(July2023),5.2 MJ(February2024),5.0 MJ(February2025),8.6 MJ(April2025) and7.9 MJ(June2026). The latter follow-up is kept even though it is not the largest. LLNL reports measurement uncertainty of±0.45 MJ for the8.6 MJ result and±0.4 MJ for7.9 MJ; no confidence level is invented. Missing reported uncertainty is null, not zero.

The8.6 MJ shot used2.08 MJ laser energy at the target, with reported target gain4.13. The page keeps reported gain separate from ratios derived from rounded numbers. Target gain does not include the facility's other energy inputs and is not net-electric gain. No assumed NIF burn duration, laser peak power or repetition rate is used to create a misleading comparable MW value. No common plot or leaderboard mixes NIF shot energy, tokamak peak power and our modeled electrical output.

## App, verification and update policy
The live homepage receives the primary model score, maintained reference and physical-result status. The detailed Power progress page includes metric switching, historical point inspection, the excluded-record toggle, all twelve records including failures, the two qualification events, three distinct physical-measurement series, source links, all eleven experimental rows, JSON and CSV exports, and a metric glossary.

`tools/build_power_progress.py` rebuilds the packet from the catalog, recorded plant study, existing reports and `research/power_progress/WORLD_MILESTONES.json`. `tools/build_pages.py` invokes it. Future contributors must register a new record's scope/eligibility and provenance rather than assuming that the newest or largest number is an improvement. New measurements need primary-source checking and a new verification date; this is not unattended monitoring. Superseded, failed and unfavorable results remain visible.

The software checks independently validate average-power arithmetic, exact source hashes, exclusion of the retired406.53 MW claim, failed/no-score handling, selection of the best eligible result, the distinction between maintained reference and paired control, source-specific units, the retained JET duration discrepancy, and separation of latest from highest NIF yield. A local pure-Node DOM test is used for selector/point/data contracts without browser navigation. It is not a real-browser rendering test; the prior administrator navigation restriction is not bypassed.

No new scientific simulation or physical experiment is performed for this presentation update. The accepted reactor, existing power studies, canonical neutron/equilibrium arrays and downloadable Unreal executable are unchanged. Original Workbench integration is MIT; source publications are linked and numeric facts summarized, not copied as full papers or relicensed.

## Primary sources and credit
- UKAEA, JET historical milestones: https://www.gov.uk/government/news/jet-set-for-its-40th-birthday .
- UKAEA/UK government,59 MJ result and energy-versus-power explanation,9February2022: https://www.gov.uk/government/news/fusion-energy-record-demonstrates-powerplant-future .
- UKAEA,69 MJ announcement,8February2024: https://www.gov.uk/government/news/jets-final-tritium-experiments-yield-new-fusion-energy-record .
- Max Planck Institute for Plasma Physics, pulse104522/date and5.2-second description: https://www.ipp.mpg.de/5405892/jet_rekord_2024 .
- Princeton Plasma Physics Laboratory,1994 site report abstract, V.Finley and M.Wieczorek: https://bp-pub.pppl.gov/pub_report/1996/PPPL-3159-abs.html .
- LLNL/NIF, dated ignition/yield history, including June2026: https://lasers.llnl.gov/science/achieving-fusion-ignition .
- LLNL fiscal2025 annual report,8.6 MJ and target gain: https://annual.llnl.gov/fy-2025/national-ignition-facility-2025 .

Full original Workbench model provenance is in the existing `FULL_PROCESS_LIFECYCLE`, `PLANT_CURRENT_DRIVE_DECISION` and `EC_EQUILIBRIUM_INTERFACE` reports. The systems solver is UKAEA PROCESS; the inherited generic tokamak input credits James Morris. Experimental measurements belong to PPPL, UKAEA/EUROfusion, LLNL and their collaborators, not Workbench. A primary-source press/summary statement is not a raw experimental dataset or an independent reproduction of its measurement.
