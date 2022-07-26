"""
Base classes relevant to the custom admin site.
"""

# Django imports
from django import http
from django.contrib import admin
from django.db.models import QuerySet
from django.utils import html

# Local application imports
from data import models
from data import utils


class CustomModelAdminBase(admin.ModelAdmin):
    """
    Base class which the ModelAdmin for each model inherits from.
    This class provides all major functionality for the custom admin site:
        - Permissions
        - Queryset filtering
    """

    class Meta:
        """
        Allow the option to customise the grouping of models on the django-admin sidebar.
        """
        custom_app_label: str = None

    exclude = ("school",)  # Since we only want users to be able to add / change data to their own school...

    # Methods relating to list display - note these only get used where relevant for subclasses
    def get_lessons_per_week(self, obj: utils.ModelSubclass) -> int:
        """
        Method to display the lessons per week of Pupil, Teacher and Classroom models.
        """
        lessons_per_week = obj.get_lessons_per_week()
        return html.format_html(f"<b><i>{lessons_per_week}</i></b>")
    get_lessons_per_week.short_description = "Lessons / week"

    def get_occupied_percentage(self, obj: utils.ModelSubclass) -> str:
        """
        Method to display the lessons per week of Pupil, Teacher and Classroom models.
        """
        percentage = round(obj.get_occupied_percentage(), 1) * 100
        return html.format_html(f"<b><i>{percentage} %</i></b>")
    get_occupied_percentage.short_description = "% time busy"

    # Method ensuring users can only interact with their own school's data
    def save_model(self, request, obj, form, change):
        """
        When saving all model instances, we add the user's school to it
        """
        school = request.user.profile.school
        obj.school = school
        obj.save()

    def get_queryset(self, request: http.HttpRequest) -> QuerySet:
        """
        Queryset filtering is customised, to only show the user their school's data.
        """
        school_access_key = request.user.profile.school.school_access_key
        queryset = super().get_queryset(request=request)
        filtered_qs = queryset.filter(school_id=school_access_key)
        return filtered_qs

    # PROPERTIES
    @property
    def meta(self):
        return self.Meta

    # PERMISSIONS METHODS
    # ALL permissions require SCHOOL_ADMIN status, and so we just use the has_module_permission method above
    def has_module_permission(self, request: http.HttpRequest) -> bool:
        """
        Users with the role SCHOOL_ADMIN have module permissions
        """
        if hasattr(request.user, "profile"):
            return request.user.is_active and (request.user.profile.role == models.UserRole.SCHOOL_ADMIN.value)
        else:
            return False

    def has_add_permission(self, request: http.HttpRequest) -> bool:
        return self.has_module_permission(request=request)

    def has_view_permission(self, request: http.HttpRequest, obj=None) -> bool:
        return self.has_module_permission(request=request)

    def has_change_permission(self, request: http.HttpRequest, obj=None) -> bool:
        return self.has_module_permission(request=request)

    def has_delete_permission(self, request: http.HttpRequest, obj=None) -> bool:
        return self.has_module_permission(request=request)
