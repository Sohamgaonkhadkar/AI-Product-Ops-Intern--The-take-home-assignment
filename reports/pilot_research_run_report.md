# Research run report

- **Mode:** Capture replay (tool-assisted source captures)
- **Captured at:** 2026-09-24T15:34:58Z
- **Apps in this run:** 5
- **Complete records:** 4
- **Partial records:** 1
- **Failed records:** 0
- **Unknown critical field slots:** 1 (not counted as failures; see per-record limitations)
- **Claim-linked evidence items:** 39
- **Retrieved source packets logged:** 19
- **Retries/errors:** Capture/replay stores per-app query/source traces in `data/raw/pilot_attempts.json` but has no per-call retry/error events; no retry count is claimed.
- **Manifest reconciliation:** passed for selected IDs 1, 22, 49, 61, 92

## Method and limitations

This report describes the actual run mode. Capture replay validates and writes source-captured research; it does not claim to have called a search provider. Live mode performs targeted web search and structured extraction, but still requires independent verification. Unknown is not silently converted to a negative.
