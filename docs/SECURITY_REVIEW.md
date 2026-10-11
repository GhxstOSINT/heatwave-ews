# Security review — OWASP Top 10:2025

Reviewed 11 October 2026 against the OWASP Top 10:2025. This is a source-code and dependency review of this repository, not a penetration test, compliance certification, or confirmation of the live Render configuration.

## Fixes in this review

- Added a request-body cap (1 MiB by default; 15 MB for forecast bundles and 16 MB for the explicitly bounded health-data import).
- Added per-process sliding-window limits for password login (10 per 15 minutes per client), account registration (4 per hour), and OAuth initiation (20 per 15 minutes), with `429` and `Retry-After` responses. Render's proxy client-IP header is trusted only when the blueprint explicitly enables that setting.
- Added CSP, HSTS for strict HTTPS deployments, frame denial, MIME sniffing protection, referrer and permissions policies; authentication responses are `no-store`.
- Made API documentation endpoints subject to strict-mode authentication and allowed the public HeatSafe mark to load before login.
- Removed JavaScript-readable bearer-session storage and bearer authentication from the browser flow. The browser now uses the existing HttpOnly, SameSite=Lax session cookie; legacy sessionStorage tokens are cleared.
- Replaced MapLibre popup HTML-string insertion with DOM text nodes so district/ward labels are not interpreted as HTML.
- Stopped returning raw filesystem/network exception text from replay failures and added safe password-authentication event logs.
- Fixed the high-severity `source-map-js` advisory by overriding affected dependency resolutions to `^1.2.2`; `npm audit --audit-level=high` now reports zero findings.
- Updated pinned `requests` to 2.33.0 and `urllib3` to 2.8.0 after `pip-audit` found advisories in the previous pins; the pinned Python dependency audit now reports no known vulnerabilities.
- Added npm and Python advisory checks to CI and weekly Dependabot updates for npm, pip and GitHub Actions.

## Top 10 coverage

| OWASP category | Source review status | Notes |
|---|---|---|
| A01 Broken Access Control | Reviewed; protections present | Strict-mode route gate plus role dependencies; database-backed role recheck. Runtime Render mode still needs confirmation. |
| A02 Security Misconfiguration | Hardened in code | Security headers added; strict-mode API docs now require a session. CSP retains `unsafe-inline` because the existing landing page uses inline scripts/styles. |
| A03 Software Supply Chain Failures | Improved; follow-up required | Frontend advisory fixed; npm/Python checks and Dependabot added. GitHub Actions currently use version tags rather than immutable commit SHAs. |
| A04 Cryptographic Failures | Reviewed | Session HMAC and salted scrypt remain; strict mode requires an environment-backed session secret. Entropy, rotation, database encryption and Render secrets are outside this source-only review. |
| A05 Injection | Hardened in reviewed sinks | SQL uses bound parameters; map popups now use text nodes. No direct SQL injection or unsafe HTML sink was confirmed in inspected paths. |
| A06 Insecure Design | Partially hardened | Request size and abuse controls added. Process-local limits reset on restart and do not coordinate multiple replicas; use an edge/WAF/shared store before production. |
| A07 Authentication Failures | Improved; residual gaps | HttpOnly cookie-only browser sessions and attempt limits; OAuth state/PKCE already present. No MFA, verified-email flow, password recovery, or server-side session revocation. |
| A08 Software or Data Integrity Failures | Improved; follow-up required | Dependency lock is checked and audited in CI; forecast uploads already check size, path set, hashes, timestamps and provenance. Action refs are not commit-pinned. |
| A09 Security Logging & Alerting Failures | Partially improved | Password and OAuth failures log safe metadata; there is no configured alerting/retention review in this repo. |
| A10 Mishandling of Exceptional Conditions | Hardened in reviewed path | Replay I/O errors now return a generic message and safe log metadata; request limits reject oversized bodies. Other integrations still need runtime failure-injection tests. |

## Verification and remaining limits

- `npm audit --audit-level=high`: passed, zero findings after the `source-map-js` override.
- `pip-audit --no-deps --disable-pip -r requirements.lock`: passed, no known vulnerabilities after updating `requests` and `urllib3`.
- Frontend production build: passed.
- Added backend regression tests for body limits, login throttling, response headers and strict-mode docs access. They require the project Python dependencies; the current workstation Python lacks FastAPI, so they could not be executed locally in this session.
- The Render service, hosted headers, actual environment variables/secrets, database permissions, provider allow-lists, and deployed image were not inspected or changed. Deploy this branch and verify the live service separately.
- The process-local throttle is a useful single-instance guard, not a distributed brute-force defense. Set an edge-level rate limit before public operation.
- This review does not establish that the service is safe for life-critical warnings or an official IMD deployment.
