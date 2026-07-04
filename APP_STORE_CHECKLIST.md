# PayFast Odoo 19 — App Store Publication Checklist

**Audit date:** 2026-07-04  
**Module:** `payment_payfast` v19.0.1.0.0  
**Recommendation:** **READY** (after Jacques completes pre-publish E2E sandbox test)

---

## Summary

The module follows Odoo 19 payment provider patterns (`_process`, `_extract_reference`, `_extract_amount_data`, `_apply_updates`, hooks wired). Critical security issues found during audit were fixed. Remaining items are documentation/assets and a mandatory live sandbox payment test before store submission.

---

## Pass / Fail Checklist

| Item | Status | Notes |
|------|--------|-------|
| LGPL-3 license | **PASS** | `__manifest__.py` |
| Odoo 19 version string | **PASS** | `19.0.1.0.0` |
| Depends `payment`, `account` | **PASS** | |
| `post_init_hook` / `uninstall_hook` | **PASS** | Uses `setup_provider` / `reset_payment_provider` |
| `_process` flow (not deprecated handlers) | **PASS** | Controller + transaction model |
| `_extract_reference` | **PASS** | Uses `m_payment_id` |
| `_extract_amount_data` | **PASS** | Uses `amount_gross` / `amount`; base `_validate_amount` runs |
| `_apply_updates` | **PASS** | Maps `COMPLETE` / `CANCELLED` / `FAILED` |
| Redirect form template | **PASS** | Matches Buckaroo pattern; Odoo JS auto-submits via `redirect_form_html` |
| Payment provider data XML | **PASS** | `noupdate=1`, sandbox placeholders documented |
| Account payment method XML | **PASS** | `account.payment.method` code `payfast`, inbound |
| IPN signature verification | **PASS** (fixed) | ITN-specific POST-order algorithm + `hmac.compare_digest` |
| Checkout signature generation | **PASS** (fixed) | Documented field order, skips blanks, passphrase encoded |
| Amount validation on callbacks | **PASS** | Inherited `_validate_amount` via `_process` |
| CSRF disabled on public routes | **PASS** | Appropriate for external POST callbacks |
| `save_session=False` on routes | **PASS** (fixed) | Return, cancel, IPN |
| Return/cancel without signature | **PASS** (fixed) | No longer updates tx without signature |
| No secrets in repo | **PASS** | Only public PayFast sandbox placeholders in noupdate data |
| Constant-time signature compare | **PASS** | `hmac.compare_digest` |
| Duplicate `is_published` field | **PASS** (fixed) | Removed override of base `payment.provider` field |
| Sandbox URL selection | **PASS** (fixed) | Uses provider `state == 'test'` |
| `__manifest__.py` metadata | **PASS** (fixed) | `website`, `description`, `images` |
| `static/description/icon.png` | **PASS** | Present |
| README install/config/troubleshooting | **PASS** | Screenshots note added |
| `.gitignore` | **PASS** (fixed) | pycache, IDE, OS files |
| Python syntax | **PASS** | `py_compile` on all `.py` files |
| Module install/upgrade (RPC) | **PASS** | Installed and upgraded on `freequency` @ localhost:8069 |
| Routes registered | **PASS** | `/payment/payfast/ipn` → `FAIL`/`OK`; return → 303 `/payment/status` |
| Provider record exists | **PASS** | `payment.provider` code `payfast` |
| Account payment method exists | **PASS** | `account.payment.method` code `payfast` |
| Signature unit test | **PASS** | `tests/test_signature.py` runs locally |
| App Store screenshots | **FAIL** | Only icon.png; add `main_screenshot.png` before listing |
| Live PayFast sandbox E2E | **FAIL** | Must be done by Jacques before publish |
| PayFast server-side ITN validation | **WARN** | Optional hardening (pfValidIP / validate with PayFast) not implemented |

---

## Issues Fixed in This Audit

1. **IPN signature algorithm** — Replaced checkout-style dict iteration with PayFast ITN POST-order verification (`_payfast_verify_itn_signature`).
2. **Checkout signature order** — Outbound signatures now use documented PayFast field order.
3. **Return/cancel security** — Unsigned redirect callbacks no longer update transaction state (IPN is authoritative).
4. **Removed `is_published` override** — Avoided conflicting with core `payment.provider` field and onchange logic.
5. **Removed redundant `payfast_sandbox`** — Sandbox/production URL now follows standard provider `state`.
6. **IPN route `save_session=False`** — Matches Odoo 19 Buckaroo pattern.
7. **Provider data** — Wrapped in `noupdate="1"`; default state `disabled`; public sandbox placeholder credentials.
8. **Manifest / README / `.gitignore`** — App Store metadata and publishing hygiene.

---

## Remaining (Non-Blocking)

- Add **screenshots** under `static/description/` for the Apps Store listing.
- Run a **full sandbox payment** (checkout → PayFast → return + IPN via ngrok).
- Optionally implement PayFast **ITN server confirmation** (`/eng/query/validate`) and source IP checks for defense in depth.
- Fresh installs get sandbox placeholders; existing DBs keep prior credentials due to `noupdate` (expected).

---

## Pre-Publish Steps for Jacques

1. **Configure PayFast sandbox** at [sandbox.payfast.co.za](https://sandbox.payfast.co.za) — set Salt Passphrase and note Merchant ID / Key.
2. **Odoo provider** — Accounting → Payment Providers → PayFast → Test Mode, enter sandbox credentials + passphrase, publish.
3. **Bank journal** — Add **PayFast** to Incoming Payments on your bank journal (see README).
4. **Public URL for IPN** — Set `web.base.url` to HTTPS public URL; use [ngrok](https://ngrok.com) for local dev.
5. **E2E test** — Place a test web sale or invoice payment; confirm:
   - Redirect to PayFast sandbox
   - Return to `/payment/status`
   - IPN log shows `OK` and transaction → **Paid**
   - Accounting payment created with PayFast method line
6. **Screenshots** — Capture provider config + checkout flow for App Store.
7. **Separate repo** — Push `addons/payment_payfast` to `github.com/clapman/payment_payfast` (exclude nested `.git` if submodule not desired).
8. **Production** — Switch provider State to **Enabled**, production credentials, production PayFast URL.

---

## Verification Log (2026-07-04)

```
Module: payment_payfast — installed, v19.0.1.0.0
Provider: PayFast (code=payfast) — present
Account payment method: PayFast (code=payfast, inbound) — present
POST /payment/payfast/ipn (unknown tx) → FAIL
GET  /payment/payfast/return → 303 /payment/status
tests/test_signature.py → OK
```

---

## Final Recommendation

**READY** for public App Store submission **after** Jacques completes the sandbox E2E test and adds store screenshots. No critical code blockers remain.
