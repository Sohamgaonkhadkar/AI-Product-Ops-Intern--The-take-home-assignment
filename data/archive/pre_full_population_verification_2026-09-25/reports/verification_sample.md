# Verification sample selection

**Status: INCOMPLETE — candidate sample only; not representative of the 100-app manifest.**

- **Selection file:** `data/evidence/verification_sample_selection.json`
- **Manifest size:** 100 apps
- **Eligible records:** 24 (only COMPLETE/PARTIAL; excludes NOT_RUN/FAILED placeholders)
- **Target / selected:** 20 / 20
- **Deterministic seed:** `20260924`
- **Selected IDs:** 22, 49, 92, 4, 13, 61, 15, 14, 1, 9, 3, 5, 16, 6, 12, 8, 11, 2, 10, 19

## Selection rule

The selector greedily maximizes newly covered strata using the fixed weights below. If candidate scores tie, the lower SHA-256 digest of `seed:app_id` is selected first. Sampling is without replacement and is reproducible from `data/raw/final_full_research.json`.

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
| 49 | Amazon Selling Partner | Ecommerce | PRIOR_CAPTURE | PARTIAL |
| 92 | Otter AI | AI, Research and Media-native | PRIOR_CAPTURE | COMPLETE |
| 4 | Attio | CRM and Sales | PRIOR_CAPTURE | COMPLETE |
| 13 | Freshdesk | Support and Helpdesk | PRIOR_CAPTURE | COMPLETE |
| 61 | GitHub | Developer, Infra and Data platforms | PRIOR_CAPTURE | COMPLETE |
| 15 | Pylon | Support and Helpdesk | PRIOR_CAPTURE | COMPLETE |
| 14 | Front | Support and Helpdesk | PRIOR_CAPTURE | COMPLETE |
| 1 | Salesforce | CRM and Sales | PRIOR_CAPTURE | COMPLETE |
| 9 | Copper | CRM and Sales | PRIOR_CAPTURE | COMPLETE |
| 3 | Pipedrive | CRM and Sales | PRIOR_CAPTURE | COMPLETE |
| 5 | Twenty | CRM and Sales | PRIOR_CAPTURE | COMPLETE |
| 16 | LiveAgent | Support and Helpdesk | PRIOR_CAPTURE | COMPLETE |
| 6 | Podio | CRM and Sales | PRIOR_CAPTURE | COMPLETE |
| 12 | Intercom | Support and Helpdesk | PRIOR_CAPTURE | COMPLETE |
| 8 | Close | CRM and Sales | PRIOR_CAPTURE | COMPLETE |
| 11 | Zendesk | Support and Helpdesk | PRIOR_CAPTURE | COMPLETE |
| 2 | HubSpot | CRM and Sales | PRIOR_CAPTURE | COMPLETE |
| 10 | DealCloud | CRM and Sales | PRIOR_CAPTURE | COMPLETE |
| 19 | Gorgias | Support and Helpdesk | PRIOR_CAPTURE | COMPLETE |

## Strata coverage

- **Categories covered:** 6/10 manifest categories.
- **Categories not represented among eligible source records:** Data, SEO and Scraping, Finance and Fintech, Marketing, Ads, Email and Social, Productivity and Project Management.
- **Observed strata covered by the candidate sample:** 34/34.
- **Observed strata omitted by this sample:** none.

## Limits and next step

This candidate uses only the 24 existing `PRIOR_CAPTURE` records (23 complete, one partial); the other 76 manifest rows are explicit `NOT_RUN` placeholders because provider credentials were absent. Thus it is a transparent audit of available baseline records, not a probability sample or a representative 15–20-app sample of the researched 100-app population. Categories with no eligible records, `mcp.status=NOT_FOUND`, and buildability labels not observed in the baseline cannot be covered. After a genuine manifest-wide research run, rerun this deterministic selector and replace this candidate report with the actual representative-sample report.

Human account checks remain pending in `reports/human_qa.md`; selecting this sample does not imply a person reviewed it.
