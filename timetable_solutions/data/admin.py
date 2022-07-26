"""The user/admin setup follows the 'extending the existing User model' section of django 4.0 docs."""

# Django imports
from django.contrib import admin
from django.contrib import auth
from django.contrib.auth.admin import UserAdmin as _UserAdmin
from django.contrib.auth.models import User
from django.utils import html

# Local application imports
from data import models


class ProfileInline(admin.StackedInline):
    """Inline admin descriptor for TimetableLeadTeacher model which acts a bit like a singleton."""
    model = models.Profile
    can_delete = False
    verbose_name_plural = 'user_profile'


# Define a new User admin
class UserAdmin(auth.admin.UserAdmin):
    inlines = (ProfileInline,)


admin.site.unregister(auth.models.User)
admin.site.register(auth.models.User, UserAdmin)

# Register all models to the admin site
# Models not customised for now
admin.site.register(models.Profile)


# Customised models
@admin.register(models.School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ["school_name", "school_access_key", "get_number_registered_users"]

    def get_number_registered_users(self, obj):
        user_count = obj.number_users
        return html.format_html(f"<b><i>{user_count}<i><b>")
    get_number_registered_users.short_description = "Registered users"


@admin.register(models.Pupil)
class PupilAdmin(admin.ModelAdmin):
    list_display = ["school", "firstname", "surname", "year_group"]
    list_filter = ["school"]


@admin.register(models.Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ["school", "firstname", "surname", "title"]
    list_filter = ["school"]


@admin.register(models.Classroom)
class ClassroomAdmin(admin.ModelAdmin):
    list_display = ["school", "building", "room_number"]
    list_filter = ["school"]


@admin.register(models.TimetableSlot)
class TimetableSlotAdmin(admin.ModelAdmin):
    list_display = ["school", "day_of_week", "period_starts_at"]
    list_filter = ["school", "day_of_week", "period_starts_at"]
    search_fields = ["school__school_access_key"]
    search_help_text = "Search by school access key"


@admin.register(models.Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ["school", "lesson_id", "teacher"]
    list_filter = ["school"]
    search_fields = ["school__school_access_key", ]
    search_help_text = "Search by school access key"
