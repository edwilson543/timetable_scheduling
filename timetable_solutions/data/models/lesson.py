"""
Module defining the model for a SchoolClass, and its manager.
"""

# Standard library imports
from typing import Self, Tuple

# Django imports
from django.core.exceptions import ValidationError
from django.db import models

# Local application imports (other models)
from data.models.classroom import Classroom
from data.models.pupil import Pupil, PupilQuerySet
from data.models.school import School
from data.models.teacher import Teacher
from data.models.timetable_slot import TimetableSlot, TimetableSlotQuerySet, WeekDay


class LessonQuerySet(models.QuerySet):
    """
    Custom queryset manager for the Lesson model
    """
    def get_all_instances_for_school(self, school_id: int) -> Self:
        """Method to return the full queryset of lessons for a given school"""
        return self.filter(school_id=school_id)

    def get_individual_lesson(self, school_id: int, lesson_id: int) -> Self:
        """Method to return an individual Lesson instance"""
        return self.get(models.Q(school_id=school_id) & models.Q(lesson_id=lesson_id))


class Lesson(models.Model):
    """
    Model representing a school lesson occurring at multiple timeslots every week
    """

    # MODEL FIELDS
    # Basic fixed value fields
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    lesson_id = models.CharField(max_length=20)
    subject_name = models.CharField(max_length=20)
    teacher = models.ForeignKey(Teacher, on_delete=models.PROTECT,
                                related_name="lessons", blank=True, null=True)  # Null for e.g. lunch
    pupils = models.ManyToManyField(Pupil, related_name="lessons")
    classroom = models.ForeignKey(Classroom, on_delete=models.PROTECT,
                                  related_name="lessons", blank=True, null=True)  # Null for e.g. sport

    # Fulfillment fields
    user_defined_time_slots = models.ManyToManyField(TimetableSlot, related_name="user_lessons")
    solver_defined_time_slots = models.ManyToManyField(TimetableSlot, related_name="solver_lessons")

    # Fulfillment requirement fields - note that both counts include any user defined instances
    total_required_slots = models.PositiveSmallIntegerField()
    total_required_double_periods = models.PositiveSmallIntegerField()

    # Introduce a custom manager
    objects = LessonQuerySet.as_manager()

    class Meta:
        """
        Django Meta class for the Lesson model
        """
        unique_together = [["school", "lesson_id"]]

    class Constant:
        """
        Additional constants to store about the Lesson model (that aren't an option in Meta)
        """
        human_string_singular = "lesson"
        human_string_plural = "lessons"

        # Field names
        pupils = "pupils"
        user_defined_time_slots = "user_defined_time_slots"
        solver_defined_time_slots = "solver_defined_time_slots"

    def __str__(self) -> str:
        """String representation of the model for the django admin site"""
        return f"{self.lesson_id}".title().replace("_", " ")

    def __repr__(self):
        """String representation of the model for debugging"""
        return f"{self.school}: {self.lesson_id}"

    # FACTORIES
    @classmethod
    def create_new(cls,
                   school_id: int, lesson_id: str, subject_name: str,
                   total_required_slots: int, total_required_double_periods: int,
                   teacher_id: int | None = None, classroom_id: int | None = None,  # IDs since it's a foreign key
                   pupils: PupilQuerySet | None = None,
                   user_defined_time_slots: TimetableSlotQuerySet | None = None,
                   solver_defined_time_slots: TimetableSlotQuerySet | None = None,
                   ) -> Self:
        """
        Method to create a new Lesson instance.
        Note that pupils and timetable slots get added separately, since they have a many-to-many relationship to the
        model, so the lesson instance must be saved first.
        """
        if teacher_id is not None:
            teacher = Teacher.objects.get_individual_teacher(school_id=school_id, teacher_id=teacher_id)
        else:
            teacher = None

        if classroom_id is not None:
            classroom = Classroom.objects.get_individual_classroom(school_id=school_id, classroom_id=classroom_id)
        else:
            classroom = None

        subject_name = subject_name.upper()

        lesson = cls.objects.create(
            school_id=school_id, lesson_id=lesson_id, subject_name=subject_name,
            total_required_slots=total_required_slots,
            total_required_double_periods=total_required_double_periods,
            teacher=teacher, classroom=classroom)
        lesson.full_clean()
        lesson.save()

        if (pupils is not None) and (pupils.count() > 0):
            lesson.add_pupils(pupils=pupils)
        if (user_defined_time_slots is not None) and (user_defined_time_slots.count()) > 0:
            lesson.add_user_defined_time_slots(time_slots=user_defined_time_slots)
        if (solver_defined_time_slots is not None) and (solver_defined_time_slots.count()) > 0:
            lesson.add_solver_defined_time_slots(time_slots=solver_defined_time_slots)

        return lesson

    @classmethod
    def delete_all_lessons_for_school(cls, school_id: int) -> Tuple:
        """Method deleting all entries for a school in the Lesson table"""
        lessons = cls.objects.get_all_instances_for_school(school_id=school_id)
        outcome = lessons.delete()
        return outcome

    @classmethod
    def delete_solver_solution_for_school(cls, school_id: int) -> None:
        """Method deleting all associations in the solver_defined_time_slots field, of a school's Lessons"""
        lessons = cls.objects.get_all_instances_for_school(school_id=school_id)
        for lesson in lessons:
            lesson.solver_defined_time_slots.clear()

    # MUTATORS
    def add_pupils(self, pupils: PupilQuerySet | Pupil) -> None:
        """Method adding a queryset of pupils to the Lesson instance's many-to-many pupils field"""
        if isinstance(pupils, PupilQuerySet):
            self.pupils.add(*pupils)
        elif isinstance(pupils, Pupil):
            self.pupils.add(pupils)

    def add_user_defined_time_slots(self, time_slots: TimetableSlotQuerySet | TimetableSlot) -> None:
        """Method adding a queryset of time slots to the Lesson's many-to-many user_defined_time_slot field"""
        if isinstance(time_slots, TimetableSlotQuerySet):
            self.user_defined_time_slots.add(*time_slots)
        elif isinstance(time_slots, TimetableSlot):
            self.user_defined_time_slots.add(time_slots)

    def add_solver_defined_time_slots(self, time_slots: TimetableSlotQuerySet) -> None:
        """Method adding a queryset of time slots to the Lesson's many-to-many solver_defined_time_slot field"""
        if isinstance(time_slots, TimetableSlotQuerySet):
            self.solver_defined_time_slots.add(*time_slots)
        elif isinstance(time_slots, TimetableSlot):
            self.solver_defined_time_slots.add(time_slots)

    # QUERIES
    @classmethod
    def get_lessons_requiring_solving(cls, school_id: int) -> LessonQuerySet:
        """
        Method to retrieve the lessons where the total required slots is greater than the user defined slots count.
        """
        all_lessons = cls.objects.get_all_instances_for_school(school_id=school_id)
        filtered_lesson_pks = [lesson.pk for lesson in all_lessons if lesson.requires_solving()]
        lessons = cls.objects.filter(pk__in=filtered_lesson_pks)
        return lessons

    def get_all_time_slots(self) -> TimetableSlotQuerySet:
        """
        Method to provide ALL time slots when a particular lesson is known to take place.
        The .distinct() prevents duplicates, but there should be none anyway - for some reason, there seems to be a bug
        where duplicates are created within one of the individual query sets, at the point of combining.
        """
        return (self.user_defined_time_slots.all() | self.solver_defined_time_slots.all()).distinct()

    def get_n_solver_slots_required(self) -> int:
        """
        Method to calculate the total additional number of slots that the solver must produce.
        """
        return self.total_required_slots - self.user_defined_time_slots.all().count()

    def get_n_solver_double_periods_required(self) -> int:
        """
        Method to calculate the total additional number of double periods that the solver must produce.
        """
        total_user_defined = sum(self.get_user_defined_double_period_count_on_day(day_of_week=day) for
                                 day in WeekDay.values)
        return self.total_required_double_periods - total_user_defined

    def requires_solving(self) -> bool:
        """
        Method to check whether a lesson requires solving, or if it is solved by the user.
        To require solving, the user must have specified more total slots than they have themselves specified
        """
        return self.get_n_solver_slots_required() > 0

    def get_user_defined_double_period_count_on_day(self, day_of_week: WeekDay) -> int:
        """
        Method to count the number of user-defined double periods on the given day
        To achieve this, we iterate through the full set of ordered TimeTable Slot
        :return - an integer specifying how many double periods the Lesson instance has on the given day
        """

        # Note that slots will be ordered in time, using the TimetableSlot Meta class
        user_slots_on_day = self.user_defined_time_slots.all().get_timeslots_on_given_day(
            school_id=self.school.school_access_key, day_of_week=day_of_week)

        # Set initial parameters affected by the for loop
        double_period_count = 0
        previous_slot = None

        for slot in user_slots_on_day:
            if (previous_slot is not None) and slot.check_if_slots_are_consecutive(other_slot=previous_slot):
                double_period_count += 1
            previous_slot = slot

        return double_period_count

    # MISCELLANEOUS METHODS
    def clean(self) -> None:
        """
        Additional validation on Lesson instances. Note that we cannot imply a number of double periods that
        would exceed the total number of slots.
        """
        if not hasattr(self, "school"):
            # When a Lesson instance is created from the django-admin, the full_clean method is called before saving
            # the instance. Since the additional cleaning performed by the clean method includes checks on the m2m
            # fields, an error is thrown, because the m2m fields require the instance to be saved before they can be
            # used. This if condition therefore bypasses the custom cleaning when calling full_clean from a ModelForm
            return

        if self.user_defined_time_slots.all().count() > self.total_required_slots:
            raise ValidationError(f"User has defined more slots for {self.__repr__()} than the total requirement")

        for slot in self.solver_defined_time_slots.all():
            if slot in self.user_defined_time_slots.all():
                raise ValidationError(f"{slot} appears in both user and solver slots for {self.__repr__}")
