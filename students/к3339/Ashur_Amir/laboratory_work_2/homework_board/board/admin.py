from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Homework, StudyGroup, Subject, Submission, User


@admin.register(User)
class BoardUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (('Учёба', {'fields': ('patronymic', 'group')}),)
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Учёба', {'fields': ('last_name', 'first_name', 'patronymic', 'group')}),)
    list_display = ('username', 'last_name', 'first_name', 'group', 'is_staff')
    list_filter = ('is_staff', 'group')


@admin.register(StudyGroup)
class StudyGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'year')


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    search_fields = ('name',)


class SubmissionInline(admin.TabularInline):
    model = Submission
    extra = 0
    fields = ('student', 'submitted_at', 'grade', 'teacher_comment')
    readonly_fields = ('student', 'submitted_at')


@admin.register(Homework)
class HomeworkAdmin(admin.ModelAdmin):
    list_display = ('title', 'subject', 'teacher', 'issue_date', 'deadline', 'max_score')
    list_filter = ('subject', 'groups', 'teacher')
    search_fields = ('title', 'text')
    filter_horizontal = ('groups',)
    inlines = [SubmissionInline]


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    """Преподаватель выставляет оценки прямо в списке (list_editable)."""
    list_display = ('student', 'homework', 'submitted_at', 'days_late', 'suggested_grade', 'grade')
    list_editable = ('grade',)
    list_filter = ('homework__subject', 'student__group', ('grade', admin.EmptyFieldListFilter))
    search_fields = ('student__last_name', 'homework__title', 'text')
    readonly_fields = ('submitted_at', 'updated_at', 'graded_at')

    @admin.display(description='Дней просрочки')
    def days_late(self, obj):
        return obj.days_late

    @admin.display(description='Оценка с учётом штрафа')
    def suggested_grade(self, obj):
        return obj.suggested_grade
