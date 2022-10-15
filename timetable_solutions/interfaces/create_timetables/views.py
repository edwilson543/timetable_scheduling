
# Standard library imports
from typing import List

# Django imports
from django.views.generic.edit import FormView
from django import urls

# Local application imports
from domain import solver
from interfaces.create_timetables import forms


class CreateTimetable(FormView):
    """
    View relating to the 'dashboard' / homepage of the 'create' component on the wider application, which allows
    users to initiate the creation of timetable solutions.

    We use a FormView since this is simply an exercise in taking the user's form data and using it to initiate some
    processing.
    """
    form_class = forms.SolutionSpecification
    template_name = "create_timetables.html"
    # Note we use reverse_lazy since a URL reversal is needed BEFORE the URLConf is loaded, to avoid circular imports
    success_url = urls.reverse_lazy("selection_dashboard")

    def form_valid(self, form):
        """
        Method
        """
        # error_messages = self._run_solver_from_view(form=form)
        error_messages = ["vdwfvwvqfv"]
        if len(error_messages) == 0:
            return super().form_valid(form)  # Method inherited from ModelFormMixin
        else:
            context_data = super().get_context_data()  # Method inherited from views.generic.edit.FormMixin
            context_data["error_messages"] = error_messages
            return super().render_to_response(context=context_data)  # from views.generic.base.TemplateResponseMixin

    def _run_solver_from_view(self, form) -> List[str]:
        """
        Method to run the solver at the point when the user submits their form.
        :return - error_messages - the list of error messages encountered by the solver (hopefully will have length 0).
        """
        school_access_key = self.request.user.profile.school.school_access_key
        solution_spec = solver.SolutionSpecification(**form.cleaned_data)
        error_messages = solver.produce_timetable_solutions(
            school_access_key=school_access_key, solution_specification=solution_spec)
        return error_messages
