# Published operating evidence: helium-circulator applicability gate

## Result
Two actual source-reported operating/test records have been obtained, replacing the prior abstract-only evidence status. They are useful context but do not meet the evidence requirements for adopting a candidate compressor efficiency or fitting a map. The rated row is not a measurement. This study does not demonstrate a compressor, a new materials result, or a fusion breakthrough.

## Primary source and reading
Ye Lin et al., Commission method of the primary helium circulator of HTGR under variable resistance condition, High Power Laser and Particle Beams36(7),076001(2024), DOI10.11884/HPLPB202436.230444. The full8-page publisher PDF includes a cover; Table3 is on PDFpage8/paper076001-7. PDFsha256:575c9cb86003105ea7337cbe73c83366bbd5171faa3b01f4d759f6a09d9bb9a1. Full-text sections and numeric Table3 were inspected, including publisher HTML; no plot coordinates were digitized. The paper is an existing industrial fission-reactor circulator study, not a fusion-equipment qualification.

| Source role | Speed rpm | Motor power kW | Pressure rise kPa | Flow kg/s | Tabulated pressure MPa | Inlet degreesC |
|---|---:|---:|---:|---:|---:|---:|
| Reported200MW operation |3600|4218|122.2|127.3|6.9|239.9|
| Reported hot-function test |4000|4648|145.2|116.0|5.31|235.9|
| Rated reference, excluded from observation calculations |3800|4500|200|96|7.0|243|

The source's hot-test narrative quotes4735.5kW at4000rpm, unlike Table3's4648kW. The table and narrative are not merged into a fabricated uncertainty interval. Table1 and Table3 also differ in rated-speed entries; both are retained as source-context differences. Figures5/6 contain factory/design efficiency contours, not measured total-to-total efficiency labels for these two records.

## Bounded calculation and definitions
The admission was saved before four diagnostic evaluations. A real-helium entropy/enthalpy calculation estimates mdot*(h_isentropic_out-h_in)/reported_motor_power. Two declared interpretations treat the tabulated pressure as absolute inlet or absolute outlet pressure. Absolute/gauge status, exact taps, total-state versus static pressure, actual outlet temperature and motor-meter boundary remain unresolved. Therefore this ratio is NOT a measured shaft isentropic, polytropic or total-to-total efficiency.

The operation row gives0.57667/0.58684, and the hot-test row gives0.72568/0.74564, under the respective pressure interpretations. These alternatives are not uncertainty bounds. They must not be compared directly with the model's assumed0.90 fluid efficiency or adopted in place of it. The separately assumed0.87 drive efficiency also must not be backed out as if measured on this device.

## Compatibility with the current candidate
This assessment uses the newer42ffb73 header-accounted independent-regional-circuit state, not the previous channel-only pressure allowance. Its known pressure ratios at8MPa discharge are1.04894IB and1.028764OB; the full550kPa allowance corresponds to1.073826. The two tabulated observations span interpreted ratios1.01771-1.02811. That is insufficient point coverage, especially forIB; it is not proof that the published machine has no unreported operating capability. Temperature, scale, geometry, flow correction and power definitions differ as well. No machine count or free similarity extrapolation is inferred.

## What is reused and what remains blocked
ThermoPower's existing compressor entropy/enthalpy equations and CoolProp are reused; no new map solver was invented. Perez-Martin et al.2022(DOI10.3390/jne3040029) documents DEMO balance-of-plant circulator design/R&D needs, not measured qualification of our machine. Earlier KAERI2021/2026 studies remain relevant leads but their numerical curves were not newly retrieved here. This gate rejects another nominal-efficiency substitution rather than claiming industrial helium equipment is absent.

Needed before calibration: pressure-tap/state definitions, motor/shaft/drive boundary, mass-flow measurement and corrected-flow convention, instrument uncertainty, speed-dependent repeat curves, geometry/similarity coverage, and an independent validation interval. No additional operating experiment or new email was initiated. The previous213.69MW conditional systems average and the later comparative31-34MW equipment budget are not updated by these records.

## Verification and reproduction
Nineteen focused tests passed, including rated-point exclusion, invalid-unit/reference rejection, entropy reconstruction, a separate ideal-gas low-density check, mass/power scaling and fail-closed metadata requirements. These are numerical/source-handling checks, not experimental validation. The source files, curated rows, frozen inputs and complete diagnostic result are preserved; third-party PDFs/HTML are excluded from the shared bundle. The original PDFs remain in the desktop research folder.

Run with the observed Python3.10 environment, CoolProp8.0.0, NumPy2.2.6, SciPy1.15.3 and pytest9.1.1:

```
python assess_observations.py
python -m pytest -q test_observations.py
```

Publisher full text: https://www.hplpb.com.cn/cn/article/doi/10.11884/HPLPB202436.230444?viewType=HTML
Publisher PDF: https://www.hplpb.com.cn/cn/article/pdf/preview/10.11884/HPLPB202436.230444.pdf
Official PROCESS conventions: https://ukaea.github.io/PROCESS/physics-models/plasma_confinement/
The separate confinement-dependency workstream proceeded when this equipment-fit branch reached a real missing-definition/coverage barrier.
