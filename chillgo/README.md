# ChillGo — Single-Product Shopify Store Build

Everything code- and copy-shaped from the ChillGo masterprompt, built and staged
for review. A single-product "hero store" for a rechargeable handheld turbo fan,
fulfilled via CJ Dropshipping, sold globally in English, marketed organically on
TikTok/Reels.

Nothing here spends money, deploys live, or touches customer data — those steps
are gated behind operator approval (see `OPERATOR-CHECKLIST.md`).

## What's in here
```
chillgo/
├── README.md                  ← you are here
├── OPERATOR-CHECKLIST.md      ← the short, phone-friendly manual steps
├── sourcing/                  ← Section 4: automated CJ product sourcing
│   ├── source_product.py        run this — auth, search, score, pick, report
│   ├── cj_client.py             CJ API 2.0 client (endpoints easy to update)
│   ├── scoring.py               the rank/filter function (Section 4.3)
│   ├── requirements.txt / .env.example / README.md
├── theme/                     ← Section 5: Dawn single-product sections
│   ├── sections/*.liquid        hero, problem, benefits, comparison, social,
│   │                            bundle, faq, sticky-add-to-cart
│   ├── snippets/*.liquid         product JSON-LD, pixels (consent-gated)
│   ├── assets/                   chillgo.css, sticky-atc.js
│   └── README.md                 install + wiring instructions
├── copy/                      ← Section 9: product page + FAQ
│   ├── product-page.md
│   ├── faq.md
│   └── legal/                    Impressum, DSGVO privacy, terms, shipping,
│                                 refund/Widerruf (drafts w/ placeholders)
└── marketing/                 ← Section 10 & 11
    ├── tiktok-scripts.md         5 hooks × 3 variations, no-face/no-voice
    └── week1-calendar.md         daily plan + metrics + success bar
```

## The flow (Section 13 execution sequence)
1. **Operator** completes Section A of `OPERATOR-CHECKLIST.md` (accounts + CJ API key).
2. **`sourcing/source_product.py`** finds and auto-selects the hero product,
   writing `decision_record.md` + `selected_product.json`.
3. That spec feeds the **theme** import, the **copy** (real specs, not filler),
   and the sample-unit order.
4. Assemble the theme sections on an **unpublished** Shopify theme; preview.
5. Fill placeholders in `copy/` (especially legal + real shipping window).
6. Shoot B-roll from the sample; post per the week-1 calendar.
7. **Go-live gates** (publish, order sample, spend money) → operator approves first.

## Design rules honored throughout
- **Autonomous build**, but hard stop before money / live deploy / customer comms.
- **No fake urgency or fabricated scarcity**, no unverified performance claims —
  real UWG/DSGVO risk, not just best practice (Sections 5.5 / 8).
- **US/EU warehouse** is the dominant scoring lever — fastest path to good
  reviews and conversion (Section 4.3).
- **Async, phone-only** operator: every manual step is a short numbered checklist.

## Note on placement
This lives in the JARVIS workspace repo as a self-contained `chillgo/` project;
it doesn't touch any existing JARVIS code. If you'd rather it be its own repo,
the folder lifts out cleanly.
