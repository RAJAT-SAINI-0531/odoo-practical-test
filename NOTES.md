# Odoo 16 Practical Test — Workflow Notes

## Time Spent
- Foundation (estate/): ~2h
- Task A (estate_account/): ~1.5h
- Task B (course_catalog/): ~45min
- Documentation: ~15min
- **Total: ~4h 30min**

---

## How I Worked

### Tools Used
- GitHub Copilot in Claude mode (VS Code) — primary code generation
- Official Odoo 16 tutorial (all chapters through ch13 Inheritance)
- Odoo 16 source code at `src/odoo/addons/account/` for account.move field names
- `Ctrl+Shift+F` in VS Code to verify field names exist in core Odoo 16 source

### AI Prompting Strategy

I did NOT paste the full Odoo source tree. Instead I gave Copilot targeted context:

**Prompt style for Foundation:**
> "Write an Odoo 16 model class for `estate.property` with these fields: [specific list]. 
> Include `_sql_constraints` for expected_price > 0, and `@api.constrains` for selling_price 
> being at least 90% of expected_price. Use `float_compare` from `odoo.tools`."

**What I accepted from AI:**
- Basic model structure, field definitions, `_sql_constraints` syntax
- View XML structure (list/form/kanban/search)

**What I rejected/corrected from AI:**
- AI initially suggested `@api.multi` decorator — does not exist in Odoo 16 (removed in v14). 
  Changed to standard `def method(self)` with `for record in self` loop.
- AI suggested `states="offer_received"` on fields for readonly — in Odoo 16, use `attrs` 
  for field visibility/readonly, `states` only works on form buttons.
- AI suggested `account.invoice` model — this was renamed to `account.move` in Odoo 13. 
  Verified in `src/odoo/addons/account/models/account_move.py`.
- AI suggested `journal.default_credit_account_id` — checked Odoo 16 source, this field 
  was removed. Correct field is `journal.default_account_id`.
- AI generated `@api.model_create_multi` with `vals_list` as a list but then treated it 
  as a dict. Fixed the loop structure.

### References Consulted
- https://www.odoo.com/documentation/16.0/developer/tutorials/getting_started.html (all chapters)
- `src/odoo/addons/account/models/account_move.py` — verified `move_type`, `journal_id`, 
  `invoice_line_ids` structure
- `src/odoo/addons/account/models/account_journal.py` — verified `default_account_id` exists in v16
- `src/odoo/addons/sale/models/sale_order.py` — studied the pattern for smart button + 
  `action_view_invoices` method
- Odoo GitHub issue tracker — confirmed `@api.multi` removal timeline

---

## Design Decisions

### Security (estate/)
Chose `base.group_user` instead of a custom `estate.group_user`. Reason: creating a custom 
group requires defining an `ir.module.category`, a `res.groups` record, implied groups chain, 
and menu visibility rules — significant XML for zero functional change in a self-contained test. 
Production code would have a custom group.

### Task A — Idempotency
On double `action_sold()` call, I **raise a UserError** rather than no-op. Reason: silent 
no-ops hide bugs in calling code. A UserError tells the developer exactly what happened. 
Documented here so the evaluator knows it's intentional.

### Task A — Income Account Resolution
Used `journal.default_account_id` as primary source, with a fallback to searching 
`account.account` by `account_type = 'income'`. This mirrors how Odoo's own `account.move` 
resolves accounts — no hardcoded account codes, works on any chart of accounts.

### Task A — `auto_install: True`
`estate_account` uses `auto_install: True` because it is a bridge module — it has no value 
unless both `estate` and `account` are installed. This is the established Odoo convention 
(see `sale_stock`, `purchase_stock`, etc.).

---

## Task B — Bugs Fixed

| # | File | Line | Bug | Fix |
|---|------|------|-----|-----|
| B1 | `models/__init__.py` | 1 | `from . import course` — file `course.py` did not exist, causing `ImportError` on module load | Changed to `from . import course_course, course_enrollment` |
| B2 | `__manifest__.py` | data list | Referenced `'security/groups.xml'` which does not exist — `FileNotFoundError` on install | Removed the entry |
| B3 | `security/ir.model.access.csv` | 2-3 | `model_course_courses` and `model_course_enrollments` (extra 's') — Odoo could not resolve model refs, `AccessError` on install | Fixed to `model_course_course` and `model_course_enrollment` |
| B4 | `views/course_views.xml` | course form | `<field name="student_name"/>` directly on course form — `student_name` is on `course.enrollment`, not `course.course`, causing `ViewError` | Removed the misplaced field |
| B5 | `models/course_course.py` | `_compute_total_revenue` | `@api.depends('enrollment_ids.price')` — `price` lives on `course.course` not on `enrollment`, so Odoo never triggered recompute when price changed | Fixed to `@api.depends('enrollment_ids', 'price')` |