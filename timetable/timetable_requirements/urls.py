"""Urls module for the timetable_requirements app"""

# Django imports
from django.urls import path

# Local application imports
from . import views

urlpatterns = [
    path('file_upload/', views.upload_page_view, name='file_upload_page'),
    path('file_upload/teacher_list', views.TeacherListUploadView.as_view(), name='teacher_list')
]
