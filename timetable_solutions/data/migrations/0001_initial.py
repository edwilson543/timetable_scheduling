# Generated by Django 4.0.6 on 2022-09-21 06:28

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Classroom',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('classroom_id', models.IntegerField()),
                ('building', models.CharField(max_length=20)),
                ('room_number', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Pupil',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pupil_id', models.IntegerField()),
                ('firstname', models.CharField(max_length=20)),
                ('surname', models.CharField(max_length=20)),
                ('year_group', models.IntegerField(choices=[(1, '#b3f2b3'), (2, '#ffbfd6'), (3, '#c8d4e3'), (4, '#fcc4a2'), (5, '#babac2')])),
            ],
        ),
        migrations.CreateModel(
            name='School',
            fields=[
                ('school_access_key', models.SmallIntegerField(primary_key=True, serialize=False)),
                ('school_name', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='Teacher',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('teacher_id', models.IntegerField()),
                ('firstname', models.CharField(max_length=20)),
                ('surname', models.CharField(max_length=20)),
                ('title', models.CharField(max_length=10)),
                ('school', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='data.school')),
            ],
        ),
        migrations.CreateModel(
            name='UnsolvedClass',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('class_id', models.CharField(max_length=20)),
                ('subject_name', models.CharField(choices=[('MATHS', '#b3f2b3'), ('ENGLISH', '#ffbfd6'), ('FRENCH', '#c8d4e3'), ('LUNCH', '#b3b3b3'), ('FREE', '#feffba')], max_length=20)),
                ('total_slots', models.PositiveSmallIntegerField()),
                ('min_distinct_slots', models.PositiveSmallIntegerField()),
                ('classroom', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='unsolved_classes', to='data.classroom')),
                ('pupils', models.ManyToManyField(related_name='unsolved_classes', to='data.pupil')),
                ('school', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='data.school')),
                ('teacher', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='unsolved_classes', to='data.teacher')),
            ],
        ),
        migrations.CreateModel(
            name='TimetableSlot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('slot_id', models.IntegerField()),
                ('day_of_week', models.CharField(choices=[('MONDAY', 'Monday'), ('TUESDAY', 'Tuesday'), ('WEDNESDAY', 'Wednesday'), ('THURSDAY', 'Thursday'), ('FRIDAY', 'Friday')], max_length=9)),
                ('period_starts_at', models.TimeField()),
                ('period_duration', models.DurationField(default=datetime.timedelta(seconds=3600))),
                ('school', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='data.school')),
            ],
        ),
        migrations.AddField(
            model_name='pupil',
            name='school',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='data.school'),
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('school', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='data.school')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='FixedClass',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('class_id', models.CharField(max_length=20)),
                ('subject_name', models.CharField(choices=[('MATHS', '#b3f2b3'), ('ENGLISH', '#ffbfd6'), ('FRENCH', '#c8d4e3'), ('LUNCH', '#b3b3b3'), ('FREE', '#feffba')], max_length=20)),
                ('user_defined', models.BooleanField()),
                ('classroom', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='classes', to='data.classroom')),
                ('pupils', models.ManyToManyField(related_name='classes', to='data.pupil')),
                ('school', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='data.school')),
                ('teacher', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='classes', to='data.teacher')),
                ('time_slots', models.ManyToManyField(related_name='classes', to='data.timetableslot')),
            ],
        ),
        migrations.AddField(
            model_name='classroom',
            name='school',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='data.school'),
        ),
    ]
