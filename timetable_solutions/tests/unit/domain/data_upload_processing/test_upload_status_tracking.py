"""
Unit test for the upload status tracking mechanism in the domain layer
"""

# Django imports
from django import test

# Local application imports
from data import models
from domain.data_upload_processing.upload_status_tracking import UploadStatusTracker, UploadStatus


class TestUploadStatusTracker:
    """
    Unit test for instantiating the UploadStatusTracker dataclass in different ways.
    """

    def test_instantiation_with_all_uploads_as_true_all_converted_to_complete(self):
        """
        Unit test that instantiating an UploadStatusTracker with all init parameters as True converts all upload
        statuses to 'complete'
        """
        # Execute test unit
        full_status = UploadStatusTracker(
            pupils=True, teachers=True, classrooms=True, timetable=True, unsolved_classes=True, fixed_classes=True
        )

        # Check outcome
        assert full_status.pupils == UploadStatus.COMPLETE.value
        assert full_status.teachers == UploadStatus.COMPLETE.value
        assert full_status.classrooms == UploadStatus.COMPLETE.value
        assert full_status.timetable == UploadStatus.COMPLETE.value
        assert full_status.unsolved_classes == UploadStatus.COMPLETE.value
        assert full_status.fixed_classes == UploadStatus.COMPLETE.value

    def test_instantiation_with_all_uploads_as_false_gives_incomplete_and_disallowed(self):
        pass

    def test_instantiation_with_some_uploads_as_false_gives_incomplete_and_disallowed(self):
        pass

    def test_instantiation_with_only_class_uploads_as_false_gives_complete_and_incomplete(self):
        pass
