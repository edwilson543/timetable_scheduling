"""Module defining the model for a teacher and any ancillary objects."""

# Django imports
from django.db import models

# Local application imports (other models)
from data.models import School


class Teacher(models.Model):
    """
    Model for storing a unique list of teachers.
    Note that the teacher_id is NOT set as a manual primary key since users will need to use this when uploading
    their own data, and certain primary keys may already be taken in the database by other schools.
    """
    teacher_id = models.IntegerField()
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    firstname = models.CharField(max_length=20)
    surname = models.CharField(max_length=20)
    title = models.CharField(max_length=10)

    def __str__(self):
        """String representation of the model for the django admin site"""
        return f"{self.school}: {self.title} {self.surname}, {self.firstname}"
