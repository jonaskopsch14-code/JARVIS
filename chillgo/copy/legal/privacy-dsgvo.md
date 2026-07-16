# Privacy Policy (DSGVO / GDPR)

_Draft template — fill placeholders, then review. Not legal advice._
_Start from Shopify's generated privacy policy and merge these DSGVO specifics._

## 1. Controller
The controller responsible for data processing on {{store_url}} is:
**{{legal_name}}**, {{c_o_address}}, {{contact_email}}.

## 2. What we process and why
| Data | Purpose | Legal basis (Art. 6 DSGVO) |
|---|---|---|
| Order & contact details (name, address, email) | Fulfil your order, ship it, support | Art. 6(1)(b) — contract |
| Payment data (via PayPal / Shopify Payments / Stripe) | Process payment | Art. 6(1)(b) — contract |
| Cookies & pixel data (Meta, TikTok) — **only after consent** | Marketing / retargeting | Art. 6(1)(a) — consent |
| Server logs | Security, operation | Art. 6(1)(f) — legitimate interest |

## 3. Cookies & tracking pixels
We use a **cookie-consent banner**. Marketing/analytics cookies and the Meta and
TikTok pixels load **only if you accept** them — you can decline or withdraw
consent at any time via the banner settings. Declining does not affect your
ability to shop or check out.

## 4. Order fulfilment via CJ Dropshipping
To ship your order, the necessary delivery details are shared with our
fulfilment partner **CJ Dropshipping** and the carrier. This is required to
perform the purchase contract (Art. 6(1)(b) DSGVO). Where processing involves a
transfer outside the EU/EEA, appropriate safeguards (e.g. EU Standard
Contractual Clauses) apply.

## 5. Payment processors
Payments are handled by PayPal, Shopify Payments, and/or Stripe. These providers
process your payment data as independent controllers under their own privacy
policies.

## 6. Your rights (Art. 15–21 DSGVO)
You have the right to access, rectification, erasure, restriction, data
portability, and objection, and the right to withdraw consent at any time. To
exercise any right, email {{contact_email}}. You may also lodge a complaint with
a supervisory authority.

## 7. Retention
We keep order data as long as required by tax and commercial law
(typically up to 10 years in Germany), then delete it.

---
**Operator notes**
- The consent banner is **mandatory** before any pixel fires (Section 8) — this
  is the natural future ConsentFlow use case noted in the masterprompt.
- Name the actual payment providers you enable; remove the ones you don't use.
- Fill the Shopify sub-processor list from Shopify's own DPA.
