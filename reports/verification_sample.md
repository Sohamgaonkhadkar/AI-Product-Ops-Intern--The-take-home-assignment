# Verification sample selection

**Status: FULL-POPULATION RESEARCH GATE PASSED — reproducible coverage-oriented audit sample selected.**

- **Selection file:** `data/evidence/verification_sample_selection.json`
- **Research dataset:** `data/raw/final_full_research.json`
- **Manifest / researched records / eligible:** 100 / 100 / 100
- **Source modes:** {'LIVE_AGENT': 76, 'PRIOR_CAPTURE': 24}
- **Research statuses:** {'COMPLETE': 97, 'PARTIAL': 3}
- **Target / selected:** 20 / 20
- **Deterministic seed:** `20260924`
- **Selected IDs (selection order):** 22, 84, 49, 98, 4, 13, 31, 78, 67, 52, 27, 91, 45, 88, 65, 1, 23, 100, 62, 9

## Selection rule

The selector greedily maximizes newly covered, research-observed strata using the fixed weights below. If candidates tie, the lower SHA-256 digest of `seed:app_id` wins. Sampling is without replacement and is reproducible from the specified first-pass dataset. This is a purposive coverage sample, not a probability sample; its accuracy will not be generalized statistically to the 100-app population.

| Stratum | Weight |
|---|---:|
| `category` | 20 |
| `auth_status` | 3 |
| `auth_method` | 3 |
| `self_serve_status` | 8 |
| `credential_status` | 7 |
| `api_available` | 6 |
| `api_type` | 5 |
| `api_breadth` | 3 |
| `mcp_status` | 8 |
| `buildability` | 8 |
| `low_confidence` | 1 |
| `partial_record` | 2 |
| `source_conflict` | 2 |

## Selected apps

| ID | App | Category | Provenance | Research status |
|---:|---|---|---|---|
| 22 | Twilio | Communications and Messaging | PRIOR_CAPTURE | COMPLETE |
| 84 | Paygent Connect | Finance and Fintech | LIVE_AGENT | COMPLETE |
| 49 | Amazon Selling Partner | Ecommerce | PRIOR_CAPTURE | PARTIAL |
| 98 | Mermaid CLI | AI, Research and Media-native | LIVE_AGENT | COMPLETE |
| 4 | Attio | CRM and Sales | PRIOR_CAPTURE | COMPLETE |
| 13 | Freshdesk | Support and Helpdesk | PRIOR_CAPTURE | COMPLETE |
| 31 | Google Ads | Marketing, Ads, Email and Social | LIVE_AGENT | COMPLETE |
| 78 | Coda | Productivity and Project Management | LIVE_AGENT | COMPLETE |
| 67 | Snowflake | Developer, Infra and Data platforms | LIVE_AGENT | COMPLETE |
| 52 | SE Ranking | Data, SEO and Scraping | LIVE_AGENT | COMPLETE |
| 27 | Telegram | Communications and Messaging | LIVE_AGENT | PARTIAL |
| 91 | NotebookLM | AI, Research and Media-native | LIVE_AGENT | COMPLETE |
| 45 | Magento (Adobe Commerce) | Ecommerce | LIVE_AGENT | COMPLETE |
| 88 | Brex | Finance and Fintech | LIVE_AGENT | COMPLETE |
| 65 | Supabase | Developer, Infra and Data platforms | LIVE_AGENT | COMPLETE |
| 1 | Salesforce | CRM and Sales | PRIOR_CAPTURE | COMPLETE |
| 23 | Zoho Cliq | Communications and Messaging | LIVE_AGENT | COMPLETE |
| 100 | Grain | AI, Research and Media-native | LIVE_AGENT | COMPLETE |
| 62 | Vercel | Developer, Infra and Data platforms | LIVE_AGENT | COMPLETE |
| 9 | Copper | CRM and Sales | PRIOR_CAPTURE | COMPLETE |

## Strata coverage

- **Categories covered:** 10/10 manifest categories.
- **Categories not represented in the selected sample (but observed in research):** none.
- **Observed strata covered:** 54/54.
- **Observed strata omitted:** none.
- **Critical MCP/buildability strata not observed anywhere in the researched population:** buildability:BUILDABLE_NOW, buildability:NOT_REALISTIC_TODAY.

## Next steps and limits

Independently re-open fresh official sources for each selected app and adjudicate all six critical groups: authentication, self-serve/plan gating, credential access, API, MCP, and buildability. Keep each first-pass value unchanged in the raw dataset; record corrections separately with source evidence and an audit reason. Human account/tenant checks remain pending until an authorized person performs them.

The full researched population contains both `LIVE_AGENT` native-web captures and `PRIOR_CAPTURE` records. `PRIOR_CAPTURE` is not relabeled as live, and sample selection is not evidence of authenticated vendor access, human review, or public-source re-verification.

