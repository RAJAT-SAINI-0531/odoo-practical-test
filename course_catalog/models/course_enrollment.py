from odoo import fields, models


class CourseEnrollment(models.Model):
    _name = 'course.enrollment'
    _description = 'Course Enrollment'
    _order = 'date_enrolled desc'

    course_id = fields.Many2one(
        comodel_name='course.course',
        string='Course',
        required=True,
        ondelete='cascade',
    )
    student_name = fields.Char(string='Student Name', required=True)
    date_enrolled = fields.Date(
        string='Enrollment Date',
        default=fields.Date.today,
    )