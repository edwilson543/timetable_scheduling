# Django imports
from django.http import HttpResponse
from django.template import loader

# Local application imports
from .models import Pupil, TimetableSlot


def selection_navigator(request):
    """View to bring up the main navigation screen for guiding the user towards individual timetables."""
    template = loader.get_template("selection_navigator.html")
    return HttpResponse(template.render({}, request))


def teacher_navigator(request):
    """View to bring up a list of teachers which can be linked out to each of their timetables."""
    pass


def pupil_navigator(request):
    """
    View to provide a dictionary of pupils which can be linked out to each of their timetables.
    This is pre-processed to be indexed by year group for display in the template.
    """
    # noinspection PyUnresolvedReferences
    year_indexed_pupils = {year: Pupil.objects.filter(year_group=year).order_by("surname").values() for
                           year in Pupil.YearGroup.values}
    year_indexed_pupils = {key: value for key, value in year_indexed_pupils.items() if len(value) > 0}
    template = loader.get_template("pupils_navigator.html")
    context = {
        "all_pupils": year_indexed_pupils
    }
    return HttpResponse(template.render(context, request))


def pupil_timetable_view(request, pk: int):
    # noinspection PyUnresolvedReferences
    pupil = Pupil.objects.get(id=pk)
    timetable = {(day, time): pupil.classes.filter(
        time_slots=TimetableSlot(day_of_week=day, period_start_time=time))
        for day in TimetableSlot.WeekDay.values for time in TimetableSlot.PeriodStart.value}
    template = loader.get_template("timetable.html")
    context = {
        "timetable": timetable,
        "name": pupil.firstname,
    }
    return HttpResponse(template.render(context, request))

