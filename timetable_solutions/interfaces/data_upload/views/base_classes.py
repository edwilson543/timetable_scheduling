"""
A separate view is used for each file that gets uploaded, since they are uploaded separately.
These views are virtually identical, and thus can just be instances of some generic view class.
This module defines that generic view class, and its ancillaries.
"""

# Standard library imports
from dataclasses import dataclass
from typing import Dict, Type

# Django imports
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django import http
from django import forms
from django.views.generic import TemplateView, View
from django import urls

# Local application imports
from constants.url_names import UrlName
from data.utils import ModelSubclass
from domain import data_upload_processing
from interfaces.data_upload import forms


@dataclass(frozen=True)
class RequiredUpload:
    """
    Dataclass to store information relating to an individual required upload (form).
    This is used to control how the corresponding row of the table containing file uploads is rendered - e.g. whether
    to mark a form as complete and offer a reset button, or as incomplete and to offer an upload button.
    """
    form_name: str  # Name of the form that will be shown to the user
    upload_status: data_upload_processing.UploadStatus  # User interpretable status string
    empty_form: forms.Form
    upload_url_name: UrlName
    reset_url_name:  UrlName


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
        We retrieve the upload status of each of the necessary datasets for the given school
        """
        school = self.request.user.profile.school
        upload_status = data_upload_processing.UploadStatusTracker.get_upload_status(school=school)

        context = {
            "required_forms": {
                    "pupils": RequiredUpload(form_name="Pupils", upload_status=upload_status.pupils,
                                             empty_form=forms.PupilListUpload(),
                                             upload_url_name=UrlName.PUPIL_LIST_UPLOAD.value,
                                             reset_url_name=UrlName.PUPIL_LIST_RESET.value),
                    "teachers": RequiredUpload(form_name="Teachers", upload_status=upload_status.teachers,
                                               empty_form=forms.TeacherListUpload(),
                                               upload_url_name=UrlName.TEACHER_LIST_UPLOAD.value,
                                               reset_url_name=UrlName.TEACHER_LIST_RESET.value),
                    "classrooms": RequiredUpload(form_name="Classrooms", upload_status=upload_status.classrooms,
                                                 empty_form=forms.ClassroomListUpload(),
                                                 upload_url_name=UrlName.CLASSROOM_LIST_UPLOAD.value,
                                                 reset_url_name=UrlName.CLASSROOM_LIST_RESET.value),
                    "timetable": RequiredUpload(form_name="Timetable structure", upload_status=upload_status.timetable,
                                                empty_form=forms.TimetableStructureUpload(),
                                                upload_url_name=UrlName.TIMETABLE_STRUCTURE_UPLOAD.value,
                                                reset_url_name=UrlName.TIMETABLE_STRUCTURE_RESET.value),
                    "unsolved_classes": RequiredUpload(
                        form_name="Class requirements", upload_status=upload_status.unsolved_classes,
                        empty_form=forms.UnsolvedClassUpload(),
                        upload_url_name=UrlName.UNSOLVED_CLASSES_UPLOAD.value,
                        reset_url_name=UrlName.UNSOLVED_CLASSES_RESET.value),
                    "fixed_classes": RequiredUpload(
                        form_name="Fixed classes", upload_status=upload_status.fixed_classes,
                        empty_form=forms.FixedClassUpload(),
                        upload_url_name=UrlName.FIXED_CLASSES_UPLOAD.value,
                        reset_url_name=UrlName.FIXED_CLASSES_RESET.value)
                    }
            }
        return context

    def post(self, request: http.HttpRequest, *args, **kwargs) -> http.HttpResponse:
        """
        POST requests to the data upload page's base URL should just be handled the same as GET requests.
        """
        return self.get(request=request, *args, **kwargs)


class DataUploadBase(LoginRequiredMixin, View):
    """
    Base view class for views handling the upload of a single file type to the database (via the post method).
    One subclass is declared per file type that the user needs to upload.
    Note - subclasses are used, rather than creating instances, since View.as_view(), used in the url
    dispatcher, is only available on classes and not on instances. (and from upload_views.py its clear that each subclass
    requires virtually no code anyway).
    This class itself subclasses UploadPage, for the get method and login authorisation.

    :param file_structure - the column headers and id column of the uploaded file
    :param model - the model the uploaded file is seeking to create instances of
    :param form - the form that the view receives input from
    :param is_unsolved_class_upload_view & is_fixed_class_upload_view - boolean values handling special cases
    requiring different processing of the user uploaded file
    """

    file_structure: data_upload_processing.FileStructure
    model: Type[ModelSubclass]
    form: Type[forms.FormSubclass]
    is_fixed_class_upload_view: bool = False
    is_unsolved_class_upload_view: bool = False

    @staticmethod
    def get() -> http.HttpResponseRedirect:
        """
        Method to redirect users accessing the endpoints directly to data upload page.
        """
        return http.HttpResponseRedirect(urls.reverse(UrlName.FILE_UPLOAD_PAGE.value))

    def post(self, request: http.HttpRequest) -> http.HttpResponseRedirect:
        """
        All subclasses of this View upload a single file, which this post method handles.
        If the upload is successful, the remaining empty forms are displayed, otherwise the error messages are shown.
        """
        form = self.form(request.POST, request.FILES)
        school_access_key = request.user.profile.school.school_access_key
        if form.is_valid():
            file = request.FILES[self.form.Meta.file_field_name]
            upload_processor = data_upload_processing.FileUploadProcessor(
                csv_file=file, csv_headers=self.file_structure.headers, id_column_name=self.file_structure.id_column,
                model=self.model, school_access_key=school_access_key,
                is_fixed_class_upload=self.is_fixed_class_upload_view,
                is_unsolved_class_upload=self.is_unsolved_class_upload_view
            )

            # Create a flash message
            if upload_processor.upload_error_message is not None:
                messages.add_message(request, level=messages.ERROR, message=upload_processor.upload_error_message)
            elif upload_processor.upload_successful:
                message = f"Successfully saved your data for {upload_processor.n_model_instances_created} " \
                          f"{self.model.Constant.human_string_plural}!"
                messages.add_message(request, level=messages.SUCCESS, message=message)
            else:
                # Added insurance, in case the file upload processor hasn't uploaded, or made an error message
                message = "Could not read data from file. Please check it matches the example file and try again."
                messages.add_message(request, level=messages.ERROR, message=message)

        return http.HttpResponseRedirect(urls.reverse(UrlName.FILE_UPLOAD_PAGE.value))


class DataResetBase(LoginRequiredMixin, View):
    """
    View for handling the reset data buttons provided on the data reset page.
    """
    # Tables which can be reset by this view - each subclass sets these as appropraite (typically just one to True)
    pupils: bool = False
    teachers: bool = False
    classrooms: bool = False
    timetable: bool = False
    unsolved_classes: bool = False
    fixed_classes: bool = False

    @staticmethod
    def get() -> http.HttpResponseRedirect:
        """
        Method to redirect users accessing the endpoints directly to data upload page.
        """
        return http.HttpResponseRedirect(urls.reverse(UrlName.FILE_UPLOAD_PAGE.value))

    def post(self, request: http.HttpRequest) -> http.HttpResponseRedirect:
        """
        Post method to carry out the resetting of the user's data.
        We use the ResetUploads class to allow extendability of the reset logic without ending up with an enormous
        view, and to keep the HTTP handling / domain-focused logic distinct
        """
        school_access_key = request.user.profile.school.school_access_key

        data_upload_processing.ResetUploads(
            school_access_key=school_access_key,
            pupils=self.pupils, teachers=self.teachers, classrooms=self.classrooms, timetable=self.timetable,
            unsolved_classes=self.unsolved_classes, fixed_classes=self.fixed_classes
        )

        return http.HttpResponseRedirect(urls.reverse(UrlName.FILE_UPLOAD_PAGE.value))