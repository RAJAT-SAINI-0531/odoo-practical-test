from odoo import api, fields, models


class CourseCourse(models.Model):
    _name = 'course.course'
    _description = 'Training Course'
    _order = 'name'

    name = fields.Char(string='Course Title', required=True)
    price = fields.Float(string='Price per Enrollment', digits=(10, 2))
    enrollment_ids = fields.One2many(
        comodel_name='course.enrollment',
        inverse_name='course_id',
        string='Enrollments',
    )
    enrollment_count = fields.Integer(
        string='Enrollment Count',
        compute='_compute_enrollment_count',
    )
    total_revenue = fields.Float(
        string='Total Revenue',
        compute='_compute_total_revenue',
        store=True,
        digits=(10, 2),
    )

    # BUG B5 FIX:
    # Was: @api.depends('enrollment_ids.price')
    # WRONG because 'price' is a field on course.course (self), not on enrollment.
    # Odoo silently ignores non-existent dot-paths in depends, so the compute
    # never triggered when price changed.
    # Correct: depend on the enrollment list AND on price (both affect the result).
    @api.depends('enrollment_ids', 'price')
    def _compute_total_revenue(self):
        for course in self:
            course.total_revenue = len(course.enrollment_ids) * course.price

    @api.depends('enrollment_ids')
    def _compute_enrollment_count(self):
        for course in self:
            course.enrollment_count = len(course.enrollment_ids)