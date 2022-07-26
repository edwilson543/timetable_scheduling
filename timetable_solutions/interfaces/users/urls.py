# Django imports
from django.urls import include, re_path, path

# Local application imports
from constants.url_names import UrlName
from . import htmx_views
from . import views

urlpatterns = [
    # Views relating to authentication
    re_path(r"^accounts/login", views.CustomLogin.as_view(), name=UrlName.LOGIN.value),
    re_path(r"^accounts/logout", views.custom_logout, name=UrlName.LOGOUT.value),
    re_path(r"^accounts/", include("django.contrib.auth.urls")),
    re_path(r"^dashboard/", views.dashboard, name=UrlName.DASHBOARD.value),

    # Views at each step of registration
    path("register/", views.Register.as_view(), name=UrlName.REGISTER.value),
    path("register/pivot/", views.SchoolRegisterPivot.as_view(), name=UrlName.REGISTER_PIVOT.value),
    path("register/pivot/school_id/", views.SchoolRegistration.as_view(), name=UrlName.SCHOOL_REGISTRATION.value),
    path("register/pivot/profile/", views.ProfileRegistration.as_view(), name=UrlName.PROFILE_REGISTRATION.value),

    # HTMX views - registration
    path("register/username/", htmx_views.username_field_view, name=UrlName.USERNAME_FIELD_REGISTRATION.value)
]
