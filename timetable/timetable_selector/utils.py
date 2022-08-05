"""Utility functions called by more than one view."""

# Standard library imports
from typing import Dict, List

# Django imports
from django.db.models import QuerySet

# Local application imports
from .models import FixedClass, TimetableSlot


def _get_timetable_slot_indexed_timetable(classes: QuerySet | List[FixedClass]) -> Dict:
    """
    Function to return a timetable data structure that can easily be iterated over in a django template.

    Parameters: classes - this is a filtered QuerySet from the FixedClass model, for exactly 1 teacher/pupil
    Returns: timetable - a nested dictionary where the outermost key is the time/period (9am/10am/...), the
    innermost key is the day of the week, and the values are the subject objects at each relevant timeslot, with the
    exception that a free period is just a string 'FREE'.
    e.g. {9AM: {MONDAY: MATHS, TUESDAY: FRENCH,...}, 10AM: {...}, ...}
    This structure is chosen such that it can be efficiently iterated over in the template to create a html table.
    """
    class_indexed_timetable = {klass: klass.time_slots.all().values() for klass in classes}
    timetable = {}
    for time in TimetableSlot.PeriodStart.values:
        time_timetable = {}  # specific times as indexes to nested dicts, indexed by days: {9AM: {Monday: [...]}...}
        for day in TimetableSlot.WeekDay.values:
            # noinspection PyUnresolvedReferences
            for klass, time_slots in class_indexed_timetable.items():
                queryset = time_slots.filter(day_of_week=day, period_start_time=time)
                if queryset.exists():
                    time_timetable[day] = klass
            if day not in time_timetable:
                time_timetable[day] = FixedClass.SubjectColour.FREE.name
        timetable[time] = time_timetable
    return timetable