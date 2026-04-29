# BUG B1 FIX: was `from . import course` — no file named course.py existed.
# Correct imports match the actual filenames.
from . import course_course
from . import course_enrollment