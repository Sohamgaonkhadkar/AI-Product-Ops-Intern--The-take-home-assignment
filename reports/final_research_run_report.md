# Full-population native capture reconciliation

- **Status:** 100/100 manifest IDs have a research record; 76 new LIVE_AGENT native-web captures replace the previous NOT_RUN placeholders, while 24 historical rows remain PRIOR_CAPTURE. This is not an all-live provider run.
- **Run ID:** `native-capture-reconciliation-20260925`
- **Started/completed (UTC):** 2026-09-25T06:56:09Z / 2026-09-25T06:56:09Z
- **Canonical manifest:** `apps/apps.json`
- **Initial raw dataset:** preserved byte-for-byte in `data/archive/pre_native_capture_reconciliation_2026-09-25/`; the original values remain auditable.
- **Reconciled first-pass raw dataset:** `data/raw/final_full_research.json` and `.csv` (still separate from `data/verified/final_dataset.json`).
- **Attempt log:** `data/raw/final_full_attempts.json`; **quality audit:** `data/raw/final_full_quality_report.json`.
- **Source modes:** {'LIVE_AGENT': 76, 'PRIOR_CAPTURE': 24}
- **Research status:** {'COMPLETE': 97, 'PARTIAL': 3}
- **Record/trace coverage:** 100/100 records and 100/100 traces, exact ID match.
- **Queries / source packets:** 236 / 468
- **Logged LIVE_AGENT attempts:** 641; historical PRIOR_CAPTURE per-call attempt counts were not preserved and were not reconstructed.
- **Claim-linked evidence rows:** 759
- **Unknown critical-field slots:** 31 (UNKNOWN remains distinct from NO).
- **Manifest-wide quality:** WARN — {'PASS': 72, 'WARN': 28, 'FAIL': 0}; blocking errors: 0; warnings: 29.
- **Verification sample:** not selected by this reconciliation step; it must be selected only after this full-population gate passes.
- **Human checks / authenticated access:** not performed or claimed.

## Capture batches

| Capture | Run ID | Apps | IDs | SHA-256 |
|---|---|---:|---|---|
| `data/evidence/native_web_capture_batch01_2026-09-24.json` | `arena-native-web-batch01-20260924` | 10 | 21, 23, 24, 25, 26, 27, 28, 29, 30, 31 | `62e0344623d8185b1571a85246bca933eacd62fc03960caa8cbd3b9c3573a5f0` |
| `data/evidence/native_web_capture_batch02_2026-09-24.json` | `arena-native-web-batch02-20260924` | 10 | 32, 33, 34, 35, 36, 37, 38, 39, 40, 41 | `8904ddf041b15c81172083940d847a71a9449c2d6ec0cc9ae0fb655b7c58db08` |
| `data/evidence/native_web_capture_batch03_2026-09-24.json` | `arena-native-web-batch03-20260924` | 9 | 42, 43, 44, 45, 46, 47, 48, 50, 51 | `f94f70811743ac2ac852bc90c84b5e1d46650f463d3f1e02e3261f76778374d1` |
| `data/evidence/native_web_capture_batch04_2026-09-24.json` | `arena-native-web-batch04-20260924` | 9 | 52, 53, 54, 55, 56, 57, 58, 59, 60 | `702d17fd5d7ef8e3f6cbd7fdb5e2aa678e59fefe6a865dae616017c72639cf62` |
| `data/evidence/native_web_capture_batch05_2026-09-24.json` | `arena-native-web-batch05-20260924` | 9 | 62, 63, 64, 65, 66, 67, 68, 69, 70 | `5080f42c87f906eabf271631744b33cfa5138e0f33a8cf9382abd22a5a6db2d9` |
| `data/evidence/native_web_capture_batch06_2026-09-24.json` | `arena-native-web-batch06-20260924` | 9 | 71, 72, 73, 74, 75, 76, 77, 78, 79 | `3d99fed4f304d52d7c83a6563fc6545f56ddca0373850e1aed71ffb40c80f895` |
| `data/evidence/native_web_capture_batch07_2026-09-25.json` | `arena-native-web-batch07-20260925` | 20 | 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 93, 94, 95, 96, 97, 98, 99, 100 | `86acef52676f13c8d580dc5b3de800f759a9fa6b35a21b0ea52599ae43e3b468` |

## Quality warnings

- app_id=3 quality warning: claim evidence URL is absent from the recorded source trace: https://developers.pipedrive.com/docs/api/v1/Oauth
- app_id=4 quality warning: claim evidence URL is absent from the recorded source trace: https://docs.attio.com/rest-api/overview
- app_id=5 quality warning: evidence URL reused 4 times; review for over-broad source reuse: https://twenty.com/pricing
- app_id=6 quality warning: claim evidence URL is absent from the recorded source trace: https://developers.podio.com/
- app_id=9 quality warning: generic homepage is the only supporting source for specific api claim
- app_id=15 quality warning: claim evidence URL is absent from the recorded source trace: https://www.usepylon.com/schedule-demo
- app_id=16 quality warning: evidence URL reused 4 times; review for over-broad source reuse: https://support.liveagent.com/647358-mcp-integration-for-agents
- app_id=20 quality warning: evidence URL reused 4 times; review for over-broad source reuse: https://help.gladly.com/developer-tutorials/docs/setup-and-testing
- app_id=22 quality warning: claim evidence URL is absent from the recorded source trace: https://www.twilio.com/en-us
- app_id=61 quality warning: claim evidence URL is absent from the recorded source trace: https://github.com/about
- app_id=80 quality warning: evidence URL reused 5 times; review for over-broad source reuse: https://support.getharvest.com/hc/en-us/articles/46293697226381-harvest-mcp
- app_id=81 quality warning: evidence URL reused 6 times; review for over-broad source reuse: https://docs.stripe.com/mcp
- app_id=82 quality warning: evidence URL reused 6 times; review for over-broad source reuse: https://plaid.com/docs/resources/mcp
- app_id=83 quality warning: evidence URL reused 6 times; review for over-broad source reuse: https://developers.binance.com/en/docs/agent-native/mcp-server/agentic
- app_id=84 quality warning: COMPLETE record has LOW confidence; review completion classification
- app_id=85 quality warning: evidence URL reused 5 times; review for over-broad source reuse: https://www.ipayx.ai/developers
- app_id=86 quality warning: evidence URL reused 6 times; review for over-broad source reuse: https://github.com/intuit/quickbooks-online-mcp-server/blob/main/readme.md
- app_id=87 quality warning: evidence URL reused 5 times; review for over-broad source reuse: https://github.com/xeroapi/xero-mcp-server/blob/main/readme.md
- app_id=88 quality warning: evidence URL reused 6 times; review for over-broad source reuse: https://developer.brex.com/docs/mcp
- app_id=89 quality warning: evidence URL reused 6 times; review for over-broad source reuse: https://docs.ramp.com/developer-api/v1/ramp-mcp
- app_id=90 quality warning: evidence URL reused 4 times; review for over-broad source reuse: https://pitchbook.com/help/pitchbook-api
- app_id=91 quality warning: evidence URL reused 4 times; review for over-broad source reuse: https://docs.cloud.google.com/gemini/enterprise/notebooklm-enterprise/docs/set-up-notebooklm
- app_id=92 quality warning: evidence URL reused 4 times; review for over-broad source reuse: https://help.otter.ai/hc/en-us/articles/36130822688279-otter-ai-public-api
- app_id=94 quality warning: evidence URL reused 4 times; review for over-broad source reuse: https://docs.consensus.app/api-plans-and-access
- app_id=95 quality warning: evidence URL reused 5 times; review for over-broad source reuse: https://docs.reducto.ai/mcp-server
- app_id=98 quality warning: evidence URL reused 7 times; review for over-broad source reuse: https://github.com/mermaid-js/mermaid-cli
- app_id=99 quality warning: generic homepage is the only supporting source for specific self_serve claim
- app_id=99 quality warning: evidence URL reused 5 times; review for over-broad source reuse: https://transcriptapi.com/docs/mcp
- app_id=100 quality warning: evidence URL reused 5 times; review for over-broad source reuse: https://support.grain.com/en/articles/15507288-grain-api

## Provenance and unresolved findings

- `LIVE_AGENT` means native web search and direct page inspection only. It is never used for the historical 24 `PRIOR_CAPTURE` rows.
- ID84 Paygent Connect remains unresolved by explicit instruction; product-specific API/auth/MCP fields remain UNKNOWN.
- ID100 Grain retains the first-party API-version conflict and unverified MCP authentication/tool entitlements.
- ID99 TranscriptAPI preserves conflicting official rate-limit statements across REST, MCP, and pricing tiers.
- No sample correction, human account check, deployment, or repository publication occurred in this stage.
