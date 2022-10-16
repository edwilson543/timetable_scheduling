# Django imports
from django import test
from django import urls

# Local application imports
from data import models
from interfaces.create_timetables import forms


class TestCreateTimetableFormView(test.TestCase):
    """
    Class for unit tests of the view allowing users to create timetable solutions.
    """
    fixtures = ["user_school_profile.json", "classrooms.json", "pupils.json", "teachers.json", "timetable.json",
                "fixed_classes_lunch.json", "unsolved_classes.json"]

    # GET request tests
    def test_get_method_returns_empty_solution_specification_form(self):
        """
        Test that by submitting GET request to the create timetable url, the empty SolutionSpecification form is
        rendered.
        """
        # Set test parameters
        self.client.login(username="dummy_teacher", password="dt123dt123")
        url = urls.reverse("create_timetables")

        # Execute test unit
        response = self.client.get(url)

        # Check outcome
        assert response.status_code == 200
        assert isinstance(response.context["form"], forms.SolutionSpecification)

    def test_get_method_redirects_to_login_for_logged_out_user(self):
        """
        Test that submitting a GET request to the create timetable page when not logged in just redirects the user.
        """
        # Set test parameters
        url = urls.reverse("create_timetables")
        expected_redirect_url = urls.reverse("login") + "?next=/create/"

        # Execute test unit
        response = self.client.get(url)

        # Check outcome
        self.assertIn(expected_redirect_url, response.url)

    # POST request tests
    def test_post_method_runs_solver_with_solution_spec_form_using_simplest_run_options(self):
        """
        Test that by submitting a POST request to the create timetable url, with a SolutionSpecification form that uses
        simple run requirements (i.e. allows all simplifications), the solver is run successfully.
        """
        # Set test parameters
        self.client.login(username="dummy_teacher", password="dt123dt123")
        url = urls.reverse("create_timetables")
        form_data = {
            "allow_split_classes_within_each_day": True,
            "allow_triple_periods_and_above": True,
        }
        expected_url_redirect = urls.reverse("selection_dashboard")

        # Execute test unit
        response = self.client.post(url, data=form_data)

        # Check outcome
        self.assertRedirects(response=response, expected_url=expected_url_redirect)
        assert response.status_code == 302  # Redirection

        # Check that a solution has been produced
        fixed_classes = models.FixedClass.objects.get_all_instances_for_school(school_id=123456)
        assert fixed_classes.count() == 24  # 12 user defined, 12 from solver
        for fc in fixed_classes:
            if not fc.user_defined:  # i.e. this fc was produced by the solver
                assert fc.time_slots.count() == 8  # per UnsolvedClass requirements

    def test_post_method_runs_solver_with_solution_spec_using_default_options(self):
        """
        Test that by submitting a POST request to the create timetable url, with a SolutionSpecification form that
        forces all components (i.e. constraints / objective) of the solver to be uses, the solver is run successfully.
        """
        # Set test parameters
        self.client.login(username="dummy_teacher", password="dt123dt123")
        url = urls.reverse("create_timetables")
        form_data = {
            "allow_split_classes_within_each_day": False,
            "allow_triple_periods_and_above": False,
        }
        expected_url_redirect = urls.reverse("selection_dashboard")

        # Execute test unit
        response = self.client.post(url, data=form_data)

        # Check outcome
        self.assertRedirects(response=response, expected_url=expected_url_redirect)
        assert response.status_code == 302  # Redirection

        # Check that a solution has been produced
        fixed_classes = models.FixedClass.objects.get_all_instances_for_school(school_id=123456)
        assert fixed_classes.count() == 24  # 12 user defined, 12 from solver
        for fc in fixed_classes:
            if not fc.user_defined:  # i.e. this fc was produced by the solver
                assert fc.time_slots.count() == 8  # per UnsolvedClass requirements