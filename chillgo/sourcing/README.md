# ChillGo — Automated Product Sourcing (Section 4)

Finds and scores the hero fan against the **CJ Dropshipping Open API (API 2.0)** —
no manual browsing. The script authenticates, searches the fan keywords, merges +
dedupes, pulls warehouse stock for the top candidates, scores/ranks them, auto-
selects the winner, and writes a decision record.

## Files
| File | Purpose |
|---|---|
| `source_product.py` | Orchestrator — run this. |
| `cj_client.py` | Thin CJ API 2.0 client (auth, product list, detail, inventory). |
| `scoring.py` | The rank/filter function (Section 4.3), as real code. |
| `.env.example` | Credential template. |

## Setup
```bash
cd chillgo/sourcing
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then fill in CJ_EMAIL and CJ_API_KEY
export $(grep -v '^#' .env | xargs)   # or use direnv / your own loader
```

You need CJ **API access enabled and an API key generated** first (Section 3,
step 2) — the API/Developer section of your CJ account.

## Run
```bash
python source_product.py            # live: hits the CJ API, writes the records
python source_product.py --dry-run fixture.json   # offline: score a saved JSON list
```

## Outputs (git-ignored — regenerated each run)
- `decision_record.md` — human-readable pick, score breakdown, runners-up, rejects.
- `selected_product.json` — machine-readable spec sheet. This feeds:
  - **Section 5** (Shopify import — use the product ID),
  - **Section 9** (write copy from the real `spec_source_description`, not filler),
  - **Section 12** (order the sample unit).

## Before a production run — verify against live docs
CJ changes fields over time, so the docs at
<https://developers.cjdropshipping.com> are the source of truth, not this code.
Two things are declared as constants precisely so they are easy to correct:
- **Endpoint paths** — top of `cj_client.py` (`EP_*`). A recent CJ update added a
  `deliveryTime` field to the product list, for example.
- **Field mapping** — `normalise_product()` in `cj_client.py` maps CJ's raw keys
  onto the flat schema `scoring.py` expects. Adjust the `.get()` keys here if a
  field name has drifted; you should not need to touch `scoring.py`.

Validate the whole flow against the documented **sandbox** first
(set `CJ_API_BASE`), then switch to production.

## Scoring at a glance (Section 4.3)
Hard rejects: rating < 4.3, package weight > 300 g, supplier cost too high to
support a $24.99–$39.99 retail at healthy margin, or no battery-safety docs.
Weighted score (max ~100): **warehouse 40** (US/EU stock is the dominant lever),
rating 15, bonus features 12, USB-C + mAh 10, order volume 10 (tie-breaker),
speed settings 8, price-fit 5.
