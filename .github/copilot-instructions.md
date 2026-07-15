# Copilot Instructions

## No Magic Numbers
- Do not use unexplained numeric literals in production code.
- Replace numeric literals with named constants that describe intent.
- Prefer constants with units or domain meaning, for example `MAX_RETRY_COUNT`, `REQUEST_TIMEOUT_MS`, or `DEFAULT_PAGE_SIZE`.
- Keep constants close to where they are used unless they are shared broadly.

## Allowed Exceptions
- Simple sentinel values used idiomatically are allowed when clear in context: `0`, `1`, and `-1`.
- Numeric literals in tests are allowed when they are part of the test scenario and improve readability.
