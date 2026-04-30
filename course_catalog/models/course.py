from odoo import api, fields, models


class Course(models.Model):
    _name = "course.catalog"
    _description = "Course"
    _order = "name"

    name = fields.Char(required=True)
    code = fields.Char(required=True)

    # BUG 1 FIX (models/course.py line 11):
    # Was: fields.Many2one("res.user", ...)
    # "res.user" does not exist in Odoo 16. The correct model name is "res.users" (plural).
    # This caused a ValueError / KeyError in the ORM registry at MODULE LOAD time,
    # preventing the module from loading at all.
    instructor_id = fields.Many2one("res.users", string="Instructor")

    description = fields.Text()
    price = fields.Monetary(currency_field="currency_id")
    currency_id = fields.Many2one(
        "res.currency",
        default=lambda self: self.env.company.currency_id,
        required=True,
    )

    enrollment_ids = fields.One2many(
        "course.enrollment",
        "course_id",
        string="Enrollments",
    )
    enrollment_count = fields.Integer(
        compute="_compute_enrollment_count",
        store=True,
    )
    total_revenue = fields.Monetary(
        compute="_compute_total_revenue",
        store=True,
        currency_field="currency_id",
    )

    # @api.depends("enrollment_ids") is CORRECT here: enrollment_count only
    # needs to change when records are added to or removed from the One2many.
    # The count does not depend on the content of individual enrollment fields.
    @api.depends("enrollment_ids")
    def _compute_enrollment_count(self):
        for course in self:
            course.enrollment_count = len(course.enrollment_ids)

    # BUG 4 FIX (models/course.py line 39):
    # Was: @api.depends("enrollment_ids")
    # Plain "enrollment_ids" only triggers a recompute when enrollment records
    # are ADDED or REMOVED from the One2many. It does NOT trigger when the
    # "amount" field on an EXISTING enrollment is changed.
    # Fix: use the dot-notation path "enrollment_ids.amount" so the ORM also
    # recomputes total_revenue whenever any enrollment's amount changes.
    # Stage: RUNTIME — total_revenue would stay stale after editing an amount.
    @api.depends("enrollment_ids.amount")
    def _compute_total_revenue(self):
        for course in self:
            course.total_revenue = sum(course.enrollment_ids.mapped("amount"))