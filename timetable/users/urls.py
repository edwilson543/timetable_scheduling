from django.urls import include, re_path, path
from django.views.generic import TemplateView
from .views import Register

urlpatterns = [
    re_path(r"^accounts/", include("django.contrib.auth.urls")),
    re_path(r"^dashboard/", TemplateView.as_view(template_name="users/dashboard.html"), name="dashboard"),
    re_path(r"^register/", Register.as_view(), name="register")
]