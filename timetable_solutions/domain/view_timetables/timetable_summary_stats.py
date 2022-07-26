"""
Module providing summary stats for the view timetable app's dashboard
"""

# Standard library imports
from typing import Dict

# Local application imports
from data import models
from domain.view_timetables.timetable_colours import TimetableColourAssigner


def get_summary_stats_for_dashboard(school_access_key: int) -> Dict:
    """
    Function to extract some summary statistics on the timetable solutions that have been found, to be displayed on
    the selection_dashboard.
    :return - stats - a dictionary that gets added to the HTTP response context for the view_timetables' dashboard
    """
    # Call data layer to get required query sets
    all_lessons = models.Lesson.objects.get_all_instances_for_school(school_id=school_access_key)
    all_slots = models.TimetableSlot.objects.get_all_instances_for_school(school_id=school_access_key)
    all_pupils = models.Pupil.objects.get_all_instances_for_school(school_id=school_access_key)
    all_teachers = models.Teacher.objects.get_all_instances_for_school(school_id=school_access_key)

    # High-level dict / stats used to calculate all other stats
    all_slot_lessons = {slot: slot.solver_lessons for slot in all_slots}
    slot_lesson_count = {
        slot: len([lesson for lesson in lessons.all() if  # Abuse of colour matcher, to avoid counting e.g. lunch
                   TimetableColourAssigner.check_lesson_for_colour_in_regex(lesson_name=lesson.subject_name) is None])
        for slot, lessons in all_slot_lessons.items()}

    distinct_lessons = len(all_lessons)
    total_lessons_taught = sum(slot_lesson_count.values())

    # Check whether there are in fact any summary stats to calculate
    if total_lessons_taught == 0:
        stats = {
            "has_solutions": False
        }
        return stats

    # Stats relating to days of the week
    day_of_week_counts = {day.label: sum(total_lessons for slot, total_lessons in slot_lesson_count.items() if
                                         slot.day_of_week == day.value) for day in models.WeekDay}
    busiest_day = max(day_of_week_counts, key=day_of_week_counts.get)
    busiest_day_pct = round(day_of_week_counts.get(busiest_day) / total_lessons_taught, 2) * 100
    quietest_day = min(day_of_week_counts, key=day_of_week_counts.get)
    quietest_day_pct = round(day_of_week_counts.get(quietest_day) / total_lessons_taught, 2) * 100

    # Stats relating to times of day
    distinct_times = {slot.period_starts_at for slot in slot_lesson_count}
    time_of_day_counts = {time_of_day.strftime("%H:%M"):
                          sum(total_lessons for slot, total_lessons in slot_lesson_count.items() if
                          slot.period_starts_at == time_of_day) for time_of_day in distinct_times}
    busiest_time = max(time_of_day_counts, key=time_of_day_counts.get)
    busiest_time_pct = round(time_of_day_counts.get(busiest_time) / total_lessons_taught, 2) * 100

    # Summary dict
    stats = {
        "has_solutions": True,  # We only reach this line if there are solutions

        "total_classes": distinct_lessons,
        "total_lessons": total_lessons_taught,
        "total_pupils": len(all_pupils),
        "total_teachers": len(all_teachers),

        "busiest_day": busiest_day,
        "busiest_day_pct": busiest_day_pct,
        "quietest_day": quietest_day,
        "quietest_day_pct": quietest_day_pct,

        "busiest_time": busiest_time,
        "busiest_time_pct": busiest_time_pct,
    }
    return stats
