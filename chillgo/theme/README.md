# ChillGo — Shopify Theme Sections (Section 5)

Drop-in sections + snippets for a **single-product landing page** built on
Dawn (Shopify's free OS 2.0 theme). These do **not** replace Dawn — they add
ChillGo-specific sections you assemble on the product template in the theme
editor, keeping the buy logic on Dawn's proven `buy-buttons` / `product-form`.

## What's here
| File | Section 5.2 role |
|---|---|
| `sections/chillgo-hero.liquid` | #1 Hero — headline, video/GIF, price, CTA |
| `sections/chillgo-problem.liquid` | #2 Problem/agitate + #3 solution intro |
| `sections/chillgo-benefits.liquid` | #4 Feature-benefit bullets |
| `sections/chillgo-comparison.liquid` | #5 Basic fan vs ChillGo table |
| `sections/chillgo-social-proof.liquid` | #6 Reviews (hosts your reviews-app block) |
| `sections/chillgo-bundle.liquid` | #7 Buy-2-save bundle offer |
| `sections/chillgo-faq.liquid` | #8 FAQ accordion (+ FAQ JSON-LD) |
| `sections/sticky-add-to-cart.liquid` | #9 Sticky mobile add-to-cart |
| `snippets/chillgo-product-jsonld.liquid` | 5.4 Product structured data |
| `snippets/chillgo-pixels.liquid` | 5.4 Meta + TikTok pixel (fallback) |
| `assets/chillgo.css` | Shared styles (scoped, uses Dawn variables) |
| `assets/sticky-atc.js` | IntersectionObserver for the sticky bar |

## Install
Two ways, pick one:

**A. Shopify CLI (recommended, keeps a local copy in git)**
```bash
shopify theme dev              # or pull your live theme into a folder first
# copy chillgo/theme/sections/*   -> <theme>/sections/
# copy chillgo/theme/snippets/*   -> <theme>/snippets/
# copy chillgo/theme/assets/*     -> <theme>/assets/
shopify theme push --unpublished   # push as a NEW unpublished theme, never live
```

**B. Admin > Online Store > Themes > Edit code** — create each file by name and
paste the contents. Slower, but no CLI needed.

> Push to an **unpublished** theme copy and preview it. Do **not** publish over
> the live theme until the operator approves (Section 13, step 8).

## Wire it up (in the theme editor, on the product template)
1. Add the sections in this order: **ChillGo hero → problem/solution → benefits
   → comparison → social proof → bundle → FAQ**. Remove Dawn's default
   `main-product` section, or hide its duplicated blocks so you don't show the
   buy box twice.
2. Add **Sticky add to cart** once, anywhere on the template.
3. In `layout/theme.liquid`, inside `<head>`, add:
   ```liquid
   {% render 'chillgo-product-jsonld', product: product %}
   {% render 'chillgo-pixels' %}
   ```
4. Load the sticky-bar script. Either add to `theme.liquid` before `</body>`:
   ```liquid
   <script src="{{ 'sticky-atc.js' | asset_url }}" defer></script>
   ```
   or reference it from the sticky section.

## Pixels & structured data
- **Pixels:** prefer Shopify's native **Customer events** for Meta and the
  TikTok app for TikTok — they respect cookie consent (DSGVO). The
  `chillgo-pixels` snippet is a consent-gated fallback only; it stays dormant
  unless you set `pixels_via_snippet` + the two IDs in theme settings.
- **JSON-LD:** `chillgo-product-jsonld` emits only real values from the product
  object (no invented review counts — Section 8: no unverified claims).

## Guardrails baked in (Sections 5.5 / 8)
- **No fake countdown timers or fabricated scarcity** anywhere — legal risk
  under German UWG. Use Shopify's real inventory display if you want scarcity.
- Shipping copy in the FAQ says "the window shown at checkout for your country"
  rather than a hardcoded "2–5 days" — set the real figure to match the
  warehouse the sourcing script picked (Section 4).
- The bundle discount must be a **real** Shopify automatic discount; the section
  only pitches it and pre-fills a 2-pack.
