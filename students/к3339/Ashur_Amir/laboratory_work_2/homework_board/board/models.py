from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone


class StudyGroup(models.Model):
    """Учебная группа (класс)."""
    name = models.CharField('Название', max_length=20, unique=True)
    year = models.PositiveSmallIntegerField('Курс', default=1)

    class Meta:
        verbose_name = 'Группа'
        verbose_name_plural = 'Группы'
        ordering = ['name']

    def __str__(self):
        return self.name


class User(AbstractUser):
    """Пользователь: студент (обычный) или преподаватель (is_staff)."""
    patronymic = models.CharField('Отчество', max_length=50, blank=True)
    group = models.ForeignKey(StudyGroup, on_delete=models.SET_NULL, null=True, blank=True,
                              related_name='students', verbose_name='Группа')

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['last_name', 'first_name']

    @property
    def is_teacher(self):
        return self.is_staff

    @property
    def full_name(self):
        return ' '.join(p for p in (self.last_name, self.first_name, self.patronymic) if p) or self.username

    @property
    def short_name(self):
        if not self.last_name:
            return self.username
        initials = ''.join(f'{p[0]}.' for p in (self.first_name, self.patronymic) if p)
        return f'{self.last_name} {initials}'.strip()

    def __str__(self):
        return self.full_name


class Subject(models.Model):
    name = models.CharField('Название', max_length=100, unique=True)
    description = models.TextField('Описание', blank=True)

    class Meta:
        verbose_name = 'Предмет'
        verbose_name_plural = 'Предметы'
        ordering = ['name']

    def __str__(self):
        return self.name


class Homework(models.Model):
    """Домашнее задание: предмет, преподаватель, дата выдачи, период выполнения, текст, штрафы."""
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='homeworks',
                                verbose_name='Предмет')
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
                                related_name='issued_homeworks', verbose_name='Преподаватель',
                                limit_choices_to={'is_staff': True})
    groups = models.ManyToManyField(StudyGroup, related_name='homeworks', verbose_name='Группы')
    title = models.CharField('Тема', max_length=200)
    text = models.TextField('Текст задания')
    issue_date = models.DateField('Дата выдачи', default=timezone.localdate)
    period_days = models.PositiveSmallIntegerField('Период выполнения (дней)', default=7,
                                                   validators=[MinValueValidator(1)])
    max_score = models.PositiveSmallIntegerField('Максимальный балл', default=10,
                                                 validators=[MinValueValidator(1), MaxValueValidator(100)])
    penalty_info = models.TextField('Информация о штрафах', blank=True,
                                    help_text='Например: −1 балл за каждый день просрочки')
    penalty_per_day = models.PositiveSmallIntegerField('Штраф за день просрочки (баллы)', default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Домашнее задание'
        verbose_name_plural = 'Домашние задания'
        ordering = ['-issue_date', 'subject__name']

    def __str__(self):
        return f'{self.subject}: {self.title}'

    def get_absolute_url(self):
        return reverse('homework_detail', args=[self.pk])

    @property
    def deadline(self):
        return self.issue_date + timedelta(days=self.period_days)

    @property
    def is_overdue(self):
        return timezone.localdate() > self.deadline

    @property
    def days_left(self):
        return (self.deadline - timezone.localdate()).days


class Submission(models.Model):
    """Сдача домашнего задания студентом в текстовом виде + оценка преподавателя."""
    homework = models.ForeignKey(Homework, on_delete=models.CASCADE, related_name='submissions',
                                 verbose_name='Задание')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                related_name='submissions', verbose_name='Студент')
    text = models.TextField('Ответ')
    submitted_at = models.DateTimeField('Сдано', auto_now_add=True)
    updated_at = models.DateTimeField('Изменено', auto_now=True)
    grade = models.PositiveSmallIntegerField('Оценка', null=True, blank=True)
    teacher_comment = models.TextField('Комментарий преподавателя', blank=True)
    graded_at = models.DateTimeField('Дата проверки', null=True, blank=True)

    class Meta:
        verbose_name = 'Сданное задание'
        verbose_name_plural = 'Сданные задания'
        ordering = ['-submitted_at']
        constraints = [models.UniqueConstraint(fields=['homework', 'student'], name='one_submission_per_student')]

    def __str__(self):
        return f'{self.student.short_name} — {self.homework}'

    @property
    def is_graded(self):
        return self.grade is not None

    @property
    def days_late(self):
        return max(0, (timezone.localdate(self.submitted_at) - self.homework.deadline).days)

    @property
    def suggested_grade(self):
        """Рекомендуемая оценка с учётом штрафа (максимум минус штраф за просрочку)."""
        return max(0, self.homework.max_score - self.days_late * self.homework.penalty_per_day)

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.grade is not None and self.homework_id and self.grade > self.homework.max_score:
            raise ValidationError({'grade': f'Оценка не может быть больше {self.homework.max_score}'})

    def save(self, *args, **kwargs):
        if self.grade is not None and self.graded_at is None:
            self.graded_at = timezone.now()
        if self.grade is None:
            self.graded_at = None
        super().save(*args, **kwargs)
