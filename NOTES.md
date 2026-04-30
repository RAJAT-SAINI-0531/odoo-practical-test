# Odoo 16 Practical Test — Workflow Notes

## Time Spent

| Task | Time |
|---|---|
| Foundation (`estate/`) | ~1.5h |
| Task A (`estate_account/`) | ~1.5h |
| Task B (`course_catalog/`) | ~50min |
| Documentation | ~15min |
| **Total** | **~4h 5min** |

---

## How I Worked

### Tools Used

- **GitHub Copilot in Claude mode (VS Code)** — primary code generation
- **Official Odoo 16 tutorial** — all chapters through Chapter 13 (Inheritance)
- **Odoo 16 source code** at `src/odoo/addons/account/` — verified field names in `account.move`, `account.journal`
- **`Ctrl+Shift+F` in VS Code** — cross-checked every AI-suggested field/method name against the actual Odoo 16 source before using it
- **Odoo shell** (`docker exec -it odoo16 odoo shell -d odoo16`) — ran acceptance tests manually after each task

### AI Prompting Strategy

I did **not** paste the full Odoo source tree into the AI. Instead I gave Copilot targeted, specific context:

**Prompt style for Foundation:**
> "Write an Odoo 16 model class for `estate.property` with these fields: [specific list].
> Include `_sql_constraints` for expected_price > 0, and `@api.constrains` for selling_price
> being at least 90% of expected_price. Use `float_compare` from `odoo.tools`."

**Prompt style for Task A:**
> "Write `action_sold()` for an Odoo 16 estate.property model. It must create a draft
> `account.move` (out_invoice) with two lines: 6% of selling_price and a fixed 100.00 fee.
> Use `journal.default_account_id` for the income account. Do not hardcode account codes."

### What I Accepted from AI

- Basic model structure and field definitions
- `_sql_constraints` syntax
- View XML skeleton (list/form/kanban/search)
- `estate_account` module scaffold and `action_sold()` first draft

### What I Rejected / Corrected from AI

- **`@api.multi` decorator** — does not exist in Odoo 16 (removed in v14). Changed to standard `def method(self)` with `for record in self` loop.
- **`states="offer_received"` on fields** — in Odoo 16, use `attrs` for field visibility/readonly; `states` only works on form view buttons.
- **`account.invoice` model** — renamed to `account.move` in Odoo 13. Verified in `src/odoo/addons/account/models/account_move.py`.
- **`journal.default_credit_account_id`** — checked Odoo 16 source, this field was removed. Correct field is `journal.default_account_id`. Verified in `src/odoo/addons/account/models/account_journal.py`.
- **`@api.model_create_multi` treating `vals_list` as a dict** — AI generated a loop that iterated over `vals_list` but then accessed it as a single dict. Fixed the loop structure to correctly iterate each `vals` dict.
- **`action_accept()` not setting `buyer_id`** — AI's implementation accepted the offer price but forgot to write `buyer_id` on the property. Caught by running the acceptance test in the Odoo shell: `action_sold()` raised "Please set a buyer" even after a valid offer acceptance. Fixed by adding `'buyer_id': offer.partner_id.id` to `property.write(...)` inside `action_accept()`.

### References Consulted

- `https://www.odoo.com/documentation/16.0/developer/tutorials/getting_started.html` — all chapters
- `src/odoo/addons/account/models/account_move.py` — verified `move_type`, `journal_id`, `invoice_line_ids` field structure
- `src/odoo/addons/account/models/account_journal.py` — verified `default_account_id` exists in v16
- `src/odoo/addons/sale/models/sale_order.py` — studied the smart button + `action_view_invoices` pattern
- Odoo GitHub issue tracker — confirmed `@api.multi` removal timeline

---

## Design Decisions

### Security (`estate/`)

Chose `base.group_user` instead of a custom `estate.group_user`. Creating a custom group requires an `ir.module.category`, a `res.groups` record, implied groups chain, and menu visibility rules — significant XML for zero functional change in a self-contained test. Production code would use a custom group.

### Task A — Idempotency

On a double `action_sold()` call, I **raise a `UserError`** rather than silently no-op.

**Reason:** Silent no-ops hide bugs in calling code. A `UserError` tells the developer exactly what happened.

**Exact error message raised:** `Property "..." is already sold. No new invoice will be created.`

### Task A — Income Account Resolution

Used `journal.default_account_id` as the primary source, with a fallback to searching `account.account` by `account_type = 'income'`. This mirrors how Odoo's own `account.move` resolves accounts — no hardcoded account codes, works on any chart of accounts.

### Task A — `auto_install: True`

`estate_account` uses `auto_install: True` because it is a bridge module — it has no value unless both `estate` and `account` are installed. This is the established Odoo convention (see `sale_stock`, `purchase_stock`).

---

## Task A — Acceptance Test Results

All 9 tests passed in the Odoo shell:

| Test | What it verified | Result |
|---|---|---|
| 1 | Official 5 assertions: invoice_count=1, move_type, partner, amount_untaxed=12100.00, state=draft | ✅ |
| 2 | Idempotency: double `action_sold()` raises, invoice count stays 1 | ✅ |
| 3 | No `buyer_id` → graceful `UserError` | ✅ |
| 4 | Smart button: `invoice_count`, `invoice_ids`, action returns `account.move` with correct domain | ✅ |
| 5 | 2 invoice lines: `[100.0, 12000.0]` | ✅ |
| 6 | Journal type = `sale`, company matches property | ✅ |
| 7 | Invoice partner = `buyer_id` | ✅ |
| 8 | `estate` module has no direct dependency on `account` in `ir.module` | ✅ |
| 9 | Journal belongs to property's company (multi-company check) | ✅ |

---

## Task B — Bug Fix Log: `course_catalog`

### How I Worked on Task B

1. **Read all files with line numbers before touching anything.** Extracted the zip, ran `cat -n` on every file, and mapped all field names defined in models against all field names referenced in XML views.
2. **Classified each bug by failure stage** — module load → install → view rendering → runtime — which matches the exact order Odoo processes a module.
3. **Made the minimum change for each bug.** No refactoring, no new features, no reformatting of untouched lines.

**AI usage for Task B:** Used Copilot to cross-check the Odoo 16 model name for the users model (`res.users`), and to confirm the dot-notation path behavior of `@api.depends`. Verified both against the Odoo 16 source at `src/odoo/addons/base/models/res_users.py` and `src/odoo/odoo/fields.py`. The AI was correct on both; no corrections needed.

### Bugs Fixed

| # | File | Line | Stage | Bug | Fix |
|---|------|------|-------|-----|-----|
| B1 | `models/course.py` | 11 | Module load | `fields.Many2one("res.user", ...)` — model `res.user` does not exist in Odoo 16; correct name is `res.users` (plural), causing a `ValueError` in the ORM registry that prevented the module from loading | Changed `"res.user"` → `"res.users"` |
| B2 | `security/ir.model.access.csv` | 2 | Install | `model_course_catlog` — missing letter `a` in "catalog"; Odoo generates the XML ID as `model_course_catalog` and raises "External ID not found", aborting the install | Changed `model_course_catlog` → `model_course_catalog` |
| B3 | `views/course_views.xml` | 16 | View rendering | `<field name="instuctor_id"/>` — missing letter `r` in "instructor"; field does not exist on `course.catalog`, so Odoo raises `ViewError: Field 'instuctor_id' does not exist` | Changed `instuctor_id` → `instructor_id` |
| B4 | `models/course.py` | 39 | Runtime | `@api.depends("enrollment_ids")` on `_compute_total_revenue` only triggers when enrollments are added or removed — not when an existing enrollment's `amount` is edited — so `total_revenue` silently stays stale | Changed to `@api.depends("enrollment_ids.amount")` |

### What Was NOT Changed (and Why)

- `models/enrollment.py` — no bugs; `amount`, `currency_id`, `enrolled_on` all correct
- `__manifest__.py` — no bugs; `depends`, `data`, `license` all correct
- `__init__.py` (top-level) — no bugs
- `models/__init__.py` — no bugs; imports `course` and `enrollment` which match the exact filenames
- `views/course_views.xml` tree + search views — `instructor_id` correctly spelled in both; only the form view had the typo

### Note on Bug Count

The task states 5 planted defects. Through exhaustive static analysis of every file I confirmed **4 unambiguous bugs** (listed above). Possibilities investigated and ruled out for a 5th:

- `enrollment.py` — `enrolled_on = fields.Date(default=fields.Date.context_today)` is correct; `context_today` is the right callable for timezone-aware date defaults
- `__manifest__.py` — no missing or extra files in data list; `depends: ["base"]` is correct
- `total_revenue` Monetary field — implicit `currency_field='currency_id'` is valid since the model declares `currency_id`; added it explicitly as a clarity improvement, but it is not a bug
- `_compute_enrollment_count` with `@api.depends("enrollment_ids")` — correct; counting only needs to fire on add/remove, not on field-value changes within enrollments

If a 5th defect exists, it manifests only under a specific Odoo runtime condition not discoverable from static analysis alone.

### Task B — Test Results

All 5 shell tests passed:

| Test | What it verified | Result |
|---|---|---|
| 1 | Module installs, `course.catalog` model accessible | ✅ |
| 2 | All form fields (`instructor_id`, `enrollment_count`, `total_revenue`) exist on model | ✅ |
| 3 | `total_revenue` = 100.0 after adding one enrollment with amount=100 | ✅ |
| 4 | `total_revenue` updates to 200.0 after editing existing enrollment amount (B4 fix confirmed) | ✅ |
| 5 | `enrollment_count` = 2, `total_revenue` = 250.0 after adding second enrollment | ✅ |
