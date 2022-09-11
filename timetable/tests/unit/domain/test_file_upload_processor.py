"""Module containing unit tests for the FileUploadProcessor"""

# Django imports
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

# Local application imports
from base_files.settings import BASE_DIR
from data import models
from domain import data_upload_processing


class TestFileUploadProcessor(TestCase):

    fixtures = ["user_school_profile.json"]
    test_data_folder = BASE_DIR / "tests" / "test_data"

    def test_upload_teachers_to_database_valid_upload(self):
        """Unit test that the FileUploadProcessor is able to take a csv file and save it to the database."""
        with open(self.test_data_folder / "teachers.csv", "rb") as csv_file:
            upload_file = SimpleUploadedFile(csv_file.name, csv_file.read())
            upload_processor = data_upload_processing.FileUploadProcessor(
                csv_file=upload_file, csv_headers=data_upload_processing.UploadFileStructure.TEACHERS.headers,
                id_column_name=data_upload_processing.UploadFileStructure.TEACHERS.id_column,
                model=models.Teacher, school_access_key=123456)

        # Test that attribute 'upload_successful' has been set to True, indicating that everything has worked
        self.assertTrue(upload_processor.upload_successful)

        # Test that the database is as expected
        all_teachers = models.Teacher.objects.get_all_school_teachers(school_id=123456)
        self.assertEqual(len(all_teachers), 11)
        greg = models.Teacher.objects.get_individual_teacher(school_id=123456, teacher_id=6)
        self.assertIsInstance(greg, models.Teacher)
        self.assertEqual(greg.firstname, "Greg")
        self.assertEqual(greg.surname, "Thebaker")