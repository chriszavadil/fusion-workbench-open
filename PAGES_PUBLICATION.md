# Public website and release maintenance

This is the clean public Fusion Workbench repository: https://github.com/chriszavadil/fusion-workbench-open . The browser site is https://chriszavadil.github.io/fusion-workbench-open/ . It serves reviewed static files from `main:/docs`; it does not need the research workstation running.

## Rebuild a reviewed update
1. Review new reports and numerical packets for scientific scope, data rights, private details and executable content. Preserve failed and superseded findings and configuration boundaries.
2. Add cleared research records and metadata; run `python tools/build_research_library.py` when changing the library. Confirm browser/native reader packets match. The historical runtime build must not be silently relabeled as a newer binary.
3. Update `project-status.json` with the actual completed milestone, then run `python tools/build_pages.py` and `python -m pytest -q tests`.
4. Review the resulting data hashes, relative URLs, content security policy and privacy checks. Commit the generated `docs/` files along with the reviewed sources. GitHub Pages publishes committed files; new evidence does not appear until its update is reviewed and pushed.
5. Verify the public page and key assets anonymously, then record its checked revision. The Atom feed is `feed.xml`; the dashboard checks a same-origin release-status file every five minutes while open and reports when a reload is needed.

## What the site does not do
It does not execute Unreal, PROCESS or OpenMC on GitHub, accept arbitrary code execution, contact the research computer, stream a desktop, or claim that a solver is running. Data visualizations replay recorded results. Actual compute requires the reviewed local-worker setup or a separately designed and authorized compute service.

The public repository accepts issues and pull requests. The proposal form downloads a brief for the contributor to review and submit; it does not transmit private content automatically. Keep untrusted submissions out of persistent development-machine execution.

## Publication scope
This repository is initialized from a reviewed clean snapshot, without private Git history, correspondence or raw execution logs. Original research-record hashes remain intact. User-identifying machine paths, credentials and engine debugging artifacts are excluded; mandatory third-party attribution remains.

Version `v0.5.1-public` publishes the static app and source. Its Windows asset is the unchanged, reviewed `0.5.0-preview` build. Release checksums and metadata distinguish these versions. Public source and issue access do not establish scientific validity: complete reactor breeding, fuel closure, robust thermal/structural performance and experimental fusion-power validation remain unresolved.

The historical research documents intentionally retain their dated publication-status notes. This file and the current repository README describe current hosting; `public-deployment.json`, once present, records completed external checks rather than a promise.

Primary documentation: https://docs.github.com/en/rest/pages/pages and https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site .
