"""Unit tests for views of the data_upload app"""

# Standard library imports
from datetime import time, timedelta

# Django imports
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpResponse
from django.test import TestCase
from django.urls import reverse

# Local application imports
from constants.url_names import UrlName
from data import models
from interfaces.data_upload import forms
from tests.input_settings import TEST_DATA_DIR


class TestCaseWithUpload(TestCase):
    """Subclass of the TestCase class, capable of uploading test csv files (subclasses twice below)."""
    fixtures = ["user_school_profile.json"]

    def upload_test_file(self, filename: str, url_name: UrlName, file_field_name: str) -> HttpResponse:
        """
        :param filename: the name of the csv file we are simulating the upload of
        :param url_name: the url extension for the given test file upload (also dict key in the data post request)
        :param file_field_name: name of the field in the form used to hold the uploaded file
        """
        self.client.login(username="dummy_teacher", password="dt123dt123")
        with open((TEST_DATA_DIR / "valid_uploads" / filename), "rb") as csv_file:
            upload_file = SimpleUploadedFile(csv_file.name, csv_file.read())
        url = reverse(url_name)
        response = self.client.post(url, data={file_field_name: upload_file})
        return response


class TestIndependentFileUploadViews(TestCaseWithUpload):
    """
    Unit tests for the views controlling the upload of files which do not depend on the prior success of earlier
    uploads
    """

    def test_teacher_list_upload_view_file_uploads_successfully(self):
        """
        Unit test for the TeacherListUpload View, that simulating a csv file upload of teachers successfully populates
        the database.
        """
        # Execute test unit
        self.upload_test_file(filename="teachers.csv", url_name=UrlName.TEACHER_LIST_UPLOAD.value,
                              file_field_name=forms.TeacherListUpload.Meta.file_field_name)

        # Test that the database is as expected
        all_teachers = models.Teacher.objects.get_all_instances_for_school(school_id=123456)
        self.assertEqual(all_teachers.count(), 11)
        greg = models.Teacher.objects.get_individual_teacher(school_id=123456, teacher_id=6)
        self.assertEqual(greg.firstname, "Greg")
        self.assertEqual(greg.surname, "Thebaker")

    def test_teacher_list_upload_view_file_unsuccessful_with_invalid_file(self):
        """
        Unit test for the TeacherListUpload View. We try uploading the demo pupils file, to check that this does not
        work, and also that the database is unaffected.
        """
        # Try uploading the wrong file (pupils.csv)
        response = self.upload_test_file(
            filename="lessons.csv", url_name=UrlName.TEACHER_LIST_UPLOAD.value,
            file_field_name=forms.TeacherListUpload.Meta.file_field_name)

        # Check outcome
        self.assertEqual(models.Lesson.objects.get_all_instances_for_school(school_id=123456).count(), 0)
        assert isinstance(response.cookies["messages"].value, str)

    def test_pupil_list_upload_view_file_uploads_successfully(self):
        """
        Unit test for PupilListUpload View, that simulating a csv file upload of pupils successfully populates the
        database.
        """
        # Execute test unit
        self.upload_test_file(filename="pupils.csv", url_name=UrlName.PUPIL_LIST_UPLOAD.value,
                              file_field_name=forms.PupilListUpload.Meta.file_field_name)

        # Test that the database is as expected
        all_pupils = models.Pupil.objects.get_all_instances_for_school(school_id=123456)
        self.assertEqual(all_pupils.count(), 6)
        teemu = models.Pupil.objects.get_individual_pupil(school_id=123456, pupil_id=5)
        self.assertEqual(teemu.firstname, "Teemu")
        self.assertEqual(teemu.surname, "Pukki")

    def test_pupil_list_upload_view_file_unsuccessful_with_invalid_file(self):
        """
        Unit test for PupilListUpload. We try uploading the demo teachers file, to check that this does not work,
        and also that the database is unaffected.
        """
        # Try uploading the wrong file (teachers.csv)
        response = self.upload_test_file(filename="teachers.csv", url_name=UrlName.PUPIL_LIST_UPLOAD.value,
                                         file_field_name=forms.PupilListUpload.Meta.file_field_name)

        # Assert that nothing has happened
        self.assertEqual(models.Pupil.objects.get_all_instances_for_school(school_id=123456).count(), 0)
        assert isinstance(response.cookies["messages"].value, str)

    def test_classroom_list_upload_view_file_uploads_successfully(self):
        """
        Unit test for the ClassrromListView, that simulating a csv file upload of classrooms successfully populates the
        database.
        """
        self.upload_test_file(filename="classrooms.csv", url_name=UrlName.CLASSROOM_LIST_UPLOAD.value,
                              file_field_name=forms.ClassroomListUpload.Meta.file_field_name)

        # Test that the database is as expected
        all_classrooms = models.Classroom.objects.get_all_instances_for_school(school_id=123456)
        self.assertEqual(all_classrooms.count(), 12)
        room = models.Classroom.objects.get_individual_classroom(school_id=123456, classroom_id=11)
        self.assertEqual(room.room_number, 40)

    def test_timetable_structure_list_upload_view_file_uploads_successfully(self):
        """
        Unit test for the TimetableStructureUpload view, that simulating a csv file upload of tt slots successfully
        populates the database.
        """
        self.upload_test_file(filename="timetable.csv", url_name=UrlName.TIMETABLE_STRUCTURE_UPLOAD.value,
                              file_field_name=forms.TimetableStructureUpload.Meta.file_field_name)

        # Test that the database is as expected
        all_slots = models.TimetableSlot.objects.get_all_instances_for_school(school_id=123456)
        self.assertEqual(all_slots.count(), 35)
        slot = models.TimetableSlot.objects.get_individual_timeslot(school_id=123456, slot_id=1)
        self.assertEqual(slot.day_of_week, 1)
        self.assertEqual(slot.period_starts_at, time(hour=9))
        self.assertEqual(slot.period_duration, timedelta(hours=1))

    def test_file_upload_page_redirects_logged_out_users_who_submit_get_requests(self):
        """
        Unit test that an anonymous user will be redirected to login, when submitting a GET request to the data
        upload page
        """
        # Set test parameters
        url = reverse(UrlName.FILE_UPLOAD_PAGE.value)

        # Execute test unit - note no login
        response = self.client.get(url)

        # Check outcome
        self.assertIn("users/accounts/login", response.url)


class TestLessonFileUpload(TestCaseWithUpload):
    """
    Unit tests for the view controlling the upload of the lesson file,
    which depends on the prior completiong of all other files.
    """

    fixtures = ["user_school_profile.json", "classrooms.json", "pupils.json", "teachers.json", "timetable.json"]

    def test_lesson_upload_view_file_uploads_successfully(self):
        """
        Unit test for the Lesson View, that simulating a csv file upload of lessons successfully populates the database.
        """
        self.upload_test_file(filename="lessons.csv", url_name=UrlName.LESSONS_UPLOAD.value,
                              file_field_name=forms.LessonUpload.Meta.file_field_name)

        # Test the database is as expected
        all_lessons = models.Lesson.objects.get_all_instances_for_school(school_id=123456)
        assert all_lessons.count() == 24

        # Check a random specific class
        lesson = models.Lesson.objects.get_individual_lesson(school_id=123456, lesson_id="YEAR_ONE_MATHS_A")
        self.assertQuerysetEqual(lesson.pupils.all(), models.Pupil.objects.filter(pupil_id__in={1, 2}), ordered=False)
        self.assertEqual(lesson.teacher, models.Teacher.objects.get_individual_teacher(school_id=123456, teacher_id=1))
