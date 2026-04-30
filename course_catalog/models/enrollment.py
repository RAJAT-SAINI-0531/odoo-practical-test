from odoo import fields, models


class Enrollment(models.Model):
    _name = "course.enrollment"
    _description = "Course Enrollment"

    course_id = fields.Many2one(
        "course.catalog",
        required=True,
        ondelete="cascade",
    )
    student_id = fields.Many2one(
        "res.partner",
        required=True,
        string="Student",
    )
    # BUG 5 FIX (models/enrollment.py line 18):
    # Was: fields.Monetary(currency_field="currency_id")
    # Missing required=True allowed enrollments to be created with amount=NULL,
    # causing a NotNullViolation at the database level and silently corrupting
    # total_revenue calculations on the course.
    # Stage: RUNTIME — silent data integrity failure.
    amount = fields.Monetary(currency_field="currency_id", required=True)
    currency_id = fields.Many2one(
        "res.currency",
        related="course_id.currency_id",
        store=True,
        readonly=True,
    )
    enrolled_on = fields.Date(default=fields.Date.context_today)