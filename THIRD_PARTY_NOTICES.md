# Third-party notices

Original Fusion Workbench application code, research contributions and generated display meshes use the MIT license, except where a file retains a different upstream notice. This does not relicense dependency software, publications, external datasets or Unreal Engine.

Three.js 0.180.0 is MIT-licensed. Its complete notice is in `app/web/vendor/LICENSE-three.txt`; source and checksums are in `app/web/vendor/manifest.json`. The browser rendering library is not reattributed to this project.

UKAEA PROCESS provides the conceptual systems model. Approved inputs pin version 3.4.2 and upstream commit c0ae5b28649f2b20fb7efc7904628b6defe4151c. The optional setup retrieves the upstream source separately. Required UKAEA MIT notices are retained in `research/runtime/UPSTREAM_LICENSE.txt` and the archival source subtree where applicable.

The native Windows release contains Unreal Engine runtime object code as an inseparable part of the application, governed by Epic's terms; it is not wholly MIT software. Engine source, editor tools, compiler installations, debugging symbols and private logs are not part of the public source snapshot. See `ENGINE_RUNTIME_NOTICE.md`. Applicable engine third-party notices accompany the Windows distribution in `ThirdPartyLicenses/`.

Blender is a separate, independently licensed tool used to generate the visualization meshes; it is not bundled. Scientific publications and external experimental data retain their source-specific rights. A citation is not permission to redistribute a full paper or restricted dataset. Research correspondence and private evidence archives are withheld.


## OKTAVIAN LiF benchmark and measurement data (2026-09-14 update)

The original measurements are credited to Chihiro Ichihara, Shu A. Hayashi, Katsuhei Kobayashi, Itsuro Kimura, Junji Yamamoto, Mikio Izumi and Akito Takahashi (1988 proceedings). Selected IAEA-NDS/open-benchmarks data and inputs retain CC BY4.0; OpenMC Fusion Benchmarks code/reference material retains the MIT PSFC MIT notice. See `research/source/experiments/oktavian_lif_2026_09_14/ATTRIBUTION.md`, unchanged licenses and exact per-file source hashes. Our transformations, comparison uncertainty limits and reading scope are disclosed. No affiliation or endorsement is implied. These data are not relabeled solely under the workbench MIT license.
