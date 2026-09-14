# Native Windows research preview v0.2.0

The native C++/Slate Unreal 5.7 application is built and packaged. The packaged executable was run, rather than only tested in Unreal Editor. Both configurations passed native geometry, layer and recorded electrical-balance checks. It also completed an actual full PROCESS reproduction through the optional local worker; the fresh conditional average was 213.69131801996207 MW, not generated electricity. See `NATIVE_SOLVER_VALIDATION.json`.

The successful native solver smoke test used the same 600-second worker limit as ordinary runs; its test-only waiting limit is 630 seconds. An earlier 180-second smoke timeout cancelled a run before completion. A setup-test isolation bug was also fixed: tests now resolve their root within the temporary test directory rather than overwriting the local execution adapter. Those failures were retained privately, not recast as successful checks.

The two configuration geometries remain separate. The eight-area dashboard describes evidence and missing validation, not a percentage of fusion solved. Seven-point electrical playback is recorded output interpolation, not live plasma, temperature, stress or neutron-field simulation. Display meshes are dimension-linked envelopes, not engineering CAD.

Current research source is projected from revision `2adb4b5c925dfe7c5fc7c0ab887def3c92deb601`. Original audit modules and the current experiment folders are included with publication manifests. Private path strings and correspondence are removed; numerical constants and arithmetic ASTs in the added Python experiment projection were checked for preservation. Archival raw-input hashes refer to their original files, not transformed public text. Historical scripts may need additional source data and local path configuration; only the two approved solver reproductions have a supported public setup path.

The Windows app works offline for viewing and recorded-output checks. Fresh full-system solves require the separately installed local worker. It never accepts arbitrary client code or automatically promotes a returned result to an accepted reactor design. The public repository supports reviewed model/data proposals; central public live-compute hosting and complete historical visualization integration remain future work.

Original code and generated display assets are MIT-licensed; dependency and engine rights remain separate. This is an unsigned research preview, not a physically validated reactor, a safety tool, a qualified digital twin or a fusion breakthrough. No X post is sent automatically.
