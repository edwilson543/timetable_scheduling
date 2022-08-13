"""Module containing utility class used to do the processing of the uploaded csv files into the database."""

# Standard library imports
import ast
from io import StringIO
from math import isnan
from typing import List, Type, TypeVar

# Third party imports
import pandas as pd
from pandas import read_csv

# Django imports
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from django.db.models import Model

# Local application imports
from .constants.csv_headers import Header

ModelInstance = TypeVar("ModelInstance", bound=Model)  # Typehint when referring to specific django Model subclasses


class FileUploadProcessor:
    """
    Class for the processing unit which, following a POST request from the user involving a file upload, will take that
    file, check it fits the requirements, and then upload to the database or not as appropriate.
    """
    __nan_handler = "###ignorenan"

    def __init__(self,
                 csv_file: UploadedFile,
                 csv_headers: List[str],
                 id_column_name: str | None,
                 model: Type[ModelInstance],
                 is_unsolved_class_upload: bool = False,
                 is_fixed_class_upload: bool = False):
        """
        :param csv_file: the file as received from the user upload
        :param csv_headers: the column headers from the csv file, which will correspond to the model fields
        :param id_column_name: string depending on whether the input file contains an id column
        :param model: the model that the file is used to create instances of

        :param is_unsolved_class_upload/is_fixed_class_upload - these represent special cases of the file upload
        process since the models the data are being uploaded to contain many-to-many relationships, and thus require
        their own methods (see _create_model_instance_from_row variations below)
        """
        self._csv_headers = csv_headers
        self._id_column_name = id_column_name
        self._model = model
        self._is_unsolved_class_upload = is_unsolved_class_upload
        self._is_fixed_class_upload = is_fixed_class_upload

        # Try uploading the file to the database
        self.upload_successful = False  # This only gets switched to True if a successful upload is made.
        self.upload_error_message = ""  # Provides details on why the upload has failed
        self._upload_file_content(file=csv_file)

    def _upload_file_content(self, file: UploadedFile) -> None:
        """Method to attempt to save the file to the database. If successful, upload status will become True."""
        file_bytes = file.read().decode("utf-8")
        file_stream = StringIO(file_bytes)
        # noinspection PyTypeChecker
        upload_df = read_csv(file_stream, sep=",")
        upload_df.fillna(value=self.__nan_handler, inplace=True)

        if not self._check_headers_valid_and_ids_unique(upload_df=upload_df):
            return

        valid_model_instances = self._get_valid_model_instances(upload_df=upload_df)

        if valid_model_instances is None:
            return
        for model in valid_model_instances:
            model.save()
        self.upload_successful = True

    def _check_headers_valid_and_ids_unique(self, upload_df: pd.DataFrame) -> bool:
        headers_valid = all(upload_df.columns == self._csv_headers)
        if not headers_valid:
            self.upload_error_message = "Input file headers did not match required format."
            return False
        if self._id_column_name is not None:
            # This needs to be done upfront, as .validate_unique() called by .full_clean() is redundant below
            ids_unique = upload_df[self._id_column_name].is_unique
            if not ids_unique:
                self.upload_error_message = f"Input file contained repeated ids (id column is {self._id_column_name})"
                return False
        return True

    def _get_valid_model_instances(self, upload_df: pd.DataFrame) -> List | None:
        valid_model_instances = []
        for _, data_ser in upload_df.iterrows():

            if self._is_unsolved_class_upload:
                model_instance = self._create_unsolved_class_instance_from_row(row=data_ser)
                if model_instance is None:
                    return None
                valid_model_instances.append(model_instance)  # Cant yet upload to database, if later row invalid

            elif self._is_fixed_class_upload:
                model_instance = self._create_fixed_class_instance_from_row(row=data_ser)
                if model_instance is None:
                    return None
                valid_model_instances.append(model_instance)

            else:
                model_instance = self._create_model_instance_from_row(row=data_ser)
                if model_instance is None:
                    return None
                valid_model_instances.append(model_instance)

        return valid_model_instances

    def _create_model_instance_from_row(self, row: pd.Series) -> Type[ModelInstance] | None:
        """
        Method to take an individual row from the csv file, validate that it corresponds to a valid model instance,
        and then create that model instance.
        """
        model_dict = row.to_dict()
        try:
            model_instance = self._model(**model_dict)
            model_instance.full_clean()
            return model_instance
        except ValidationError:
            self.upload_error_message = f"Could not create valid {self._model.__name__} instance from " \
                                        f"row: {row.to_dict()}"
            return None

    def _create_unsolved_class_instance_from_row(self, row: pd.Series) -> Type[ModelInstance] | None:
        """
        Method to process each row of the unsolved class csv file upload and try to return a UnsolvedClass
        instance
        """
        model_dict = {  # Note we don't include the pupil_ids here
            Header.CLASS_ID: row[Header.CLASS_ID], Header.SUBJECT_NAME: row[Header.SUBJECT_NAME],
            Header.TEACHER_ID: row[Header.TEACHER_ID], Header.CLASSROOM_ID: row[Header.CLASSROOM_ID],
            Header.TOTAL_SLOTS: row[Header.TOTAL_SLOTS], Header.MIN_SLOTS: row[Header.MIN_SLOTS]}
        try:
            model_instance = self._model(**model_dict)
            pups = ast.literal_eval(row[Header.PUPIL_IDS])
            pups = {int(val) for val in pups}
            model_instance.pupils.add(*pups)
            model_instance.full_clean()
            return model_instance
        except ValidationError:
            self.upload_error_message = f"Could not create valid UnsolvedClass instance from row: {row.to_dict()}"
            return None

    def _create_fixed_class_instance_from_row(self, row: pd.Series) -> Type[ModelInstance] | None:
        """Method to process each row of the fixed class csv file upload and try to return a FixedClass instance"""
        model_dict = {  # Note we don't include the pupil_ids or slot_ids here
            Header.CLASS_ID: row[Header.CLASS_ID], Header.SUBJECT_NAME: row[Header.SUBJECT_NAME],
            Header.TEACHER_ID: row[Header.TEACHER_ID], Header.CLASSROOM_ID: row[Header.CLASSROOM_ID]}
        model_dict = {key: value for key, value in model_dict.items() if value != self.__nan_handler}
        try:
            model_instance = self._model(**model_dict)

            pups = ast.literal_eval(row[Header.PUPIL_IDS])
            pups = {int(val) for val in pups}
            model_instance.pupils.add(*pups)

            slots = ast.literal_eval(row[Header.SLOT_IDS])
            slots = {int(val) for val in slots}
            model_instance.time_slots.add(*slots)

            model_instance.full_clean()
            return model_instance
        except ValidationError:
            self.upload_error_message = f"Could not create valid FixedClass instance from row: {row.to_dict()}"
            return None
