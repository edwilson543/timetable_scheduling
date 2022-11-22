"""
Views relating to user authentication and registration.

User registration has the following steps:
Step 1 - provide basic details (name, email address, password etc.)
Step 2 - a pivot - either the user belongs to a school that is already registered at TTS (c) or must the must also
register their school
Step 3a - the user must also register themselves with the school
Step 3b - the user must provide a school access key to associate themselves with a school that is already registered.
"""

# Standard library imports
from typing import Dict

# Django imports
from django.contrib.auth import login, logout
from django import http
from django.shortcuts import render, redirect
from django.views import View
from django.urls import reverse

# Local application imports
from constants.url_names import UrlName
from data import models
from . import forms


# Create your views here.
class Register(View):
    """View for step 1 of registering - entering basic details."""
    @staticmethod
    def get(request: http.HttpRequest, context: Dict | None = None) -> http.HttpResponse:
        if context is None:
            context = {"form": forms.CustomUserCreation}
        if request.user.is_authenticated:
            logout(request)
        return render(request, "users/register.html", context)

    def post(self, request: http.HttpRequest) -> http.HttpResponse:
        form = forms.CustomUserCreation(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect(reverse(UrlName.REGISTER_PIVOT.value))
        else:
            context = {
                "error_messages": form.error_messages,
                "form": forms.CustomUserCreation
            }
            return self.get(request, context=context)


class SchoolRegisterPivot(View):
    """View for step 2 of registering - whether the user's school also needs registering"""

    @staticmethod
    def get(request: http.HttpRequest) -> http.HttpResponse:
        context = {"form": forms.SchoolRegistrationPivot}
        return render(request, "users/register_school_pivot.html", context)

    @staticmethod
    def post(request: http.HttpRequest) -> http.HttpResponse:
        form = forms.SchoolRegistrationPivot(request.POST)
        if form.is_valid():
            if form.cleaned_data.get("existing_school") == "EXISTING":
                return redirect(reverse(UrlName.PROFILE_REGISTRATION.value))
            else:
                return redirect(reverse(UrlName.SCHOOL_REGISTRATION.value))
        else:
            return redirect(reverse(UrlName.REGISTER.value))


class SchoolRegistration(View):
    """
    View for step 3a of registering - when the school is not registered.
    In this case, the user receives the role "SCHOOL_ADMIN", giving them ownership of their school's data, and since
    they are a school admin, they are approved by the school admin...
    """

    @staticmethod
    def get(request: http.HttpRequest) -> http.HttpResponse:
        context = {"form": forms.SchoolRegistration}
        return render(request, "users/register_school.html", context)

    @staticmethod
    def post(request: http.HttpRequest) -> http.HttpResponse:
        """
        A School instance is created, allowing a Profile instance (for the user) to be created.
        """
        form = forms.SchoolRegistration(request.POST)
        if form.is_valid():
            school_name = form.cleaned_data.get("school_name")
            new_school = models.School.create_new(school_name=school_name)

            models.Profile.create_and_save_new(user=request.user, school_id=new_school.school_access_key,
                                               role=models.UserRole.SCHOOL_ADMIN.value, approved_by_school_admin=True)
            return redirect(reverse(UrlName.DASHBOARD.value))
        else:
            context = {
                "form": forms.SchoolRegistration,
                "errors": form.errors
            }
            return render(request, "users/register_school.html", context)


class ProfileRegistration(View):
    """
    View for step 3b of registering - when the school is already registered, just need the access key.
    In this case, the user receives the role "TEACHER", which can only be upgraded by the "SCHOOL_ADMIN", and they
    are initially set to not be approved by the school admin.
    """

    @staticmethod
    def get(request, context: Dict | None = None):
        if context is None:
            context = {"form": forms.ProfileRegistration}
        return render(request, "users/register_profile_existing_school.html", context)

    def post(self, request):
        form = forms.ProfileRegistration(request.POST)
        if form.is_valid():
            access_key = form.cleaned_data.get("school_access_key")
            models.Profile.create_and_save_new(user=request.user, school_id=access_key,
                                               role=models.UserRole.TEACHER.value, approved_by_school_admin=False)
            return redirect(reverse(UrlName.DASHBOARD.value))
        else:
            context = {
                "form": forms.ProfileRegistration,
                "error_message": form.error_message,
            }
            return self.get(request, context=context)


def custom_logout(request):
    """
    View redirecting users to the login page when they logout rather than the dashboard, since there is no
    application unless the user is logged in.
    """
    logout(request)
    return redirect(reverse(UrlName.LOGIN.value))


def dashboard(request):
    """
    Method to add some context to the dashboard view, for rendering in the template.
    This is to restrict the list of options available to users.
    """
    if not request.user.is_authenticated:
        return redirect(reverse(UrlName.LOGIN.value))

    return render(request, "users/dashboard.html")
