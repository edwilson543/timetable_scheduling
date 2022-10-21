"""URLs module for view_timetables app."""

# Django imports
from django.urls import path

# Local application imports
from constants.url_names import UrlName
from . import views

urlpatterns = [
    path('selection_dash/', views.selection_dashboard, name=UrlName.VIEW_TIMETABLES_DASH.value),
    path('teachers/', views.teacher_navigator, name=UrlName.TEACHERS_NAVIGATOR.value),
    path('teachers/<int:id>', views.teacher_timetable_view, name=UrlName.TEACHER_TIMETABLE.value),
    path('pupils/', views.pupil_navigator, name=UrlName.PUPILS_NAVIGATOR.value),
    path('pupils/<int:id>', views.pupil_timetable_view, name=UrlName.PUPIL_TIMETABLE.value)
]
