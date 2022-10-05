"""Integration test for the entry-point method on the TimetableSolverConstraints class"""

# Django imports
from django import test

# Third party imports
import pulp as lp

# Local application imports
from domain import solver as slvr


class TestSolverConstraints(test.TestCase):

    fixtures = ["user_school_profile.json", "classrooms.json", "pupils.json", "teachers.json", "timetable.json",
                "fixed_classes_lunch.json", "unsolved_classes.json"]

    def test_add_all_constraints_to_problem(self):
        """
        Test that the full set of constraints necessary to specify the timetabling problem is added to the problem
        """
        # Set test parameters
        school_access_key = 123456
        data = slvr.TimetableSolverInputs(school_id=school_access_key)
        variables = slvr.TimetableSolverVariables(inputs=data).get_variables()
        constraint_maker = slvr.TimetableSolverConstraints(inputs=data, variables=variables)

        dummy_problem = lp.LpProblem()  # In real life, will be the defined LpProblem subclass

        # Execute test unit
        constraint_maker.add_constraints_to_problem(problem=dummy_problem)

        # Check outcome - note the dummy_problem is modified in-place
        constraints = dummy_problem.constraints
        assert len(constraints) == 12 + (6 * 35) + (11 * 35) + (12 * 35)   # fulfillment + pupil + teacher + classroom