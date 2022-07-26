"""
Module defining the data upload page, its context, and required ancillaries.
"""

# Standard library imports
from dataclasses import dataclass
from typing import Dict

# Django imports
from django import urls, forms, http
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import TemplateView

# Local application imports
from constants.url_names import UrlName
from domain import data_upload_processing
from interfaces.data_upload import forms


@dataclass(frozen=True)
class RequiredUpload:
    """
    Dataclass to store information relating to an individual required upload (form).
    This is used to control how the corresponding row of the table containing file uploads is rendered - e.g. whether
    to mark a form as complete and offer a reset button, or as incomplete and to offer an upload button.
    It also stores the urls related to different actions.
    """
    form_name: str  # Name of the form that will be shown to the user
    upload_status: data_upload_processing.UploadStatus  # User interpretable status string
    empty_form: forms.Form
    upload_url_name: UrlName
    reset_url_name:  UrlName
    example_download_url_name: UrlName


class UploadPage(LoginRequiredMixin, TemplateView):
    """
    Template view with the following main purposes:
        - Handling HTTP to the base data upload page (whose url this class is attached to)
        - Defining the logic for gathering all the required upload forms into one set of context data
        - Being subclassed, to provide its rendering of the data upload page (with the full context) to other views.
    """

    login_url = urls.reverse_lazy("login")
    template_name = "file_upload.html"

    def get_context_data(self, *args, **kwargs) -> Dict[str, Dict[str, RequiredUpload]]:
        """
        Method to get a dictionary of 'RequiredUpload' instances which are used to then control the rendering of either
        an empty form, or a completion message.

        Note the context also provides several url names for reversing in the template tags.
        """
        school = self.request.user.profile.school
        upload_status = data_upload_processing.UploadStatusTracker.get_upload_status(school=school)

        if upload_status.all_uploads_complete:
            message = "You have uploaded all the required files, and can now start generating timetable solutions!\n" \
                      f"Navigate over to the " \
                      f"<a href='{urls.reverse(UrlName.CREATE_TIMETABLES.value)}'>create</a> page to get started."
            messages.add_message(request=self.request, level=messages.INFO, message=message, extra_tags="safe")

        context = {
            "required_forms": {
                    "pupils": RequiredUpload(form_name="Pupils", upload_status=upload_status.pupils,
                                             empty_form=forms.PupilListUpload(),
                                             upload_url_name=UrlName.PUPIL_LIST_UPLOAD.value,
                                             reset_url_name=UrlName.PUPIL_LIST_RESET.value,
                                             example_download_url_name=UrlName.PUPIL_DOWNLOAD.value),
                    "teachers": RequiredUpload(form_name="Teachers", upload_status=upload_status.teachers,
                                               empty_form=forms.TeacherListUpload(),
                                               upload_url_name=UrlName.TEACHER_LIST_UPLOAD.value,
                                               reset_url_name=UrlName.TEACHER_LIST_RESET.value,
                                               example_download_url_name=UrlName.TEACHER_DOWNLOAD.value),
                    "classrooms": RequiredUpload(form_name="Classrooms", upload_status=upload_status.classrooms,
                                                 empty_form=forms.ClassroomListUpload(),
                                                 upload_url_name=UrlName.CLASSROOM_LIST_UPLOAD.value,
                                                 reset_url_name=UrlName.CLASSROOM_LIST_RESET.value,
                                                 example_download_url_name=UrlName.CLASSROOM_DOWNLOAD.value),
                    "timetable": RequiredUpload(form_name="Timetable structure", upload_status=upload_status.timetable,
                                                empty_form=forms.TimetableStructureUpload(),
                                                upload_url_name=UrlName.TIMETABLE_STRUCTURE_UPLOAD.value,
                                                reset_url_name=UrlName.TIMETABLE_STRUCTURE_RESET.value,
                                                example_download_url_name=UrlName.TIMETABLE_DOWNLOAD.value),
                    "lessons": RequiredUpload(form_name="Lessons", upload_status=upload_status.lessons,
                                              empty_form=forms.LessonUpload(),
                                              upload_url_name=UrlName.LESSONS_UPLOAD.value,
                                              reset_url_name=UrlName.LESSONS_RESET.value,
                                              example_download_url_name=UrlName.LESSONS_DOWNLOAD.value)
                    }
            }
        return context

    def post(self, request: http.HttpRequest, *args, **kwargs) -> http.HttpResponse:
        """
        POST requests to the data upload page's base URL should just be handled the same as GET requests.
        """
        return self.get(request=request, *args, **kwargs)
