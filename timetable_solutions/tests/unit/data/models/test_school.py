"""
Unit tests for methods on the School model
"""

# Third party imports
import pytest

# Django imports
from django import test

# Local application imports
from data import models


class TestClassroom(test.TestCase):

    fixtures = ["user_school_profile.json"]

    # MISCELLANEOUS METHODS TESTS
    def test_get_new_access_key_equals_fixture_access_key_plus_one(self):
        """
        There is one school the fixtures with access key 123456, so we expect the next available access key to be
        123457
        """
        # Execute test unit
        new_access_key = models.School.get_new_access_key()

        # Check outcome
        assert new_access_key == 123457
