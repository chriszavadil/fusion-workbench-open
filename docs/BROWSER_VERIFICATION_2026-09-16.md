# Browser verification repaired and executed

## What actually blocked the earlier test
The preserved September15 `OFFLINE_VIEW_TEST.json` describes `ERR_BLOCKED_BY_ADMINISTRATOR` on the first offline-file navigation **inside the ChatGPT container**. It explicitly says no live-site or workstation navigation was attempted. That establishes an environment-specific denial, not a diagnosis that the research computer or public website was inaccessible. That sandbox restriction was not changed or retried.

For this repair, the user authorized resolving the remaining verification problem. The research computer was online, its existing Playwright installation and stable Edge were present, and read-only machine/user browser-policy-name checks showed no configured Chrome/Edge policy keys in those locations. That registry inventory alone is not proof that every possible management layer is absent. No plugin permission mode, browser policy, proxy, certificate setting or firewall rule was changed.

A normal installed-Edge test of the public HTTPS app then loaded successfully. The homepage, power history, experimental-series controls, CSV export and narrow-screen power layout passed. An animation test used Playwright's dynamic predicate evaluator, which the application's strict Content Security Policy rejected. This was a **test-adapter error**, not a need to add `unsafe-eval` to the site. The check was replaced with a retrying locator-value assertion. Site CSP, TLS validation and the browser sandbox remain enabled.

## Completed real-browser checks
The corrected run passed on installed Edge153.0.4234.32 in an isolated unsigned-in context. It inspected actual rendered pages and controls, not a simulated DOM. The public snapshot tested is recorded by repository commit in `validation/browser-20260916/RESULT.json`.

- Homepage:274.0 MW best conditional model and213.7 MW reference labels.
- Power progress:12 history rows,11 physical milestones, retained excluded screen, average/burn selection, all three experimental series, both JET duration calculations, CSV download, and390×844 layout without page-level horizontal overflow.
- EC-wave view:all four equilibrium selections, analytical filters, complete343-point reference-ray access and actual animated traversal.
- Plant decision:case selector, displayed power ledger and end-of-cycle power inspection.

No page script errors or same-site HTTP errors were recorded. Screenshots and CSV hashes are preserved with the result. A visual review also found misdecoded punctuation in the homepage template; the middle dot and arrow were repaired in the source template without changing numeric or scientific records.

These checks do not certify all browsers, physical devices, accessibility conformance, the full3D application or the native Unreal binary. Mobile coverage here is a narrow Edge viewport, not a physical iPhone test. No new scientific experiment, simulation or measured power is implied.

## Repeatable release verification
`tools/verify_live_browser.py` uses the existing installed Edge channel; it does not install a browser or modify policy. Run it explicitly in an environment authorized to test this public app, with Playwright available:

```sh
python tools/verify_live_browser.py --expected-revision REVISION_FROM_docs/release-status.json --output NEW_EMPTY_RESULT_DIRECTORY
```

The expected value is the `revision_id` string, not the Git commit. The runner checks deployed publication metadata before certifying pages, creates a fresh test context without user login data, requires HTTPS validation and browser sandboxing, refuses an existing result directory, and performs no scientific job submissions. The parent execution should be bounded to240seconds. An access/administrator denial must stop the run; do not switch browser channels, disable security, or change proxies to evade it. On application/test failures, preserve the error and correct the responsible code before a separately recorded verification.

The asserted values and record counts correspond to the dated current dataset. When a new reviewed scientific record changes them, update the assertions alongside that record; never change science or delete failed records merely to make UI tests pass. Screenshots and raw failure reports remain local until reviewed for privacy. Successful public-page screenshots can be attached to a reviewed result.

Official Playwright browser documentation explains installed Chrome/Edge channels and policy limitations: https://playwright.dev/python/docs/browsers . The code now uses locator assertions rather than evaluating a string predicate in the application context. Historical reports saying rendering had not yet been verified remain accurate for their original checkpoints; this dated record closes the current workstation/public-page verification gap.
