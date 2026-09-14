# Security and privacy boundary

The bundled Python server is for one local user. It binds only to loopback, validates Host and Origin, requires an application request header for writes, rejects arbitrary paths/commands/configuration IDs and permits one active experiment. Do not port-forward it or deploy it publicly.

Raw solver logs and local adapter settings stay under `.local/`, which is neither served nor included in release bundles. Only schema-selected numeric data and reviewed static text are public. Error messages returned by the worker do not include private tracebacks. Application-generated Unreal/Blender files remain local until binary metadata and dependencies have been separately reviewed.

Approved solver code is trusted, not sandboxed hostile code. Public contributions need review and an isolated worker before execution. The present prototype has no public user authentication, untrusted-code sandbox, Internet-facing queue, signed-release service or continuous research automation.

Do not change the private research repository's visibility. Publishing a URL under a personal account can disclose the owner even when the UI is anonymous. Neutral branding therefore applies to publishing accounts, commit authorship, URLs, logs, package metadata and analytics as well as the interface.

The automated release scanner complements allowlisting and human review; it cannot prove that all possible secrets or identifiers are absent. No secrets were intentionally loaded or copied to build this preview.
