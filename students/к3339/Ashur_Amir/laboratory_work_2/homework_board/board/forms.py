from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import Homework, StudyGroup, Submission, User


class BootstrapMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            w = field.widget
            if isinstance(w, (forms.CheckboxInput, forms.CheckboxSelectMultiple)):
                w.attrs.setdefault('class', 'form-check-input')
            elif isinstance(w, forms.Select):
                w.attrs.setdefault('class', 'form-select')
            else:
                w.attrs.setdefault('class', 'form-control')


class SignUpForm(BootstrapMixin, UserCreationForm):
    first_name = forms.CharField(label='Имя', max_length=150)
    last_name = forms.CharField(label='Фамилия', max_length=150)
    group = forms.ModelChoiceField(label='Группа', queryset=StudyGroup.objects.all())

    class Meta:
        model = User
        fields = ('username', 'last_name', 'first_name', 'patronymic', 'email', 'group')


class ProfileForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ('last_name', 'first_name', 'patronymic', 'email', 'group')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # группу выбирают при регистрации; потом менять её может только администратор,
        # иначе студент мог бы смотреть журнал чужой группы
        if self.instance.is_staff:
            del self.fields['group']
        elif self.instance.group_id:
            self.fields['group'].disabled = True
            self.fields['group'].help_text = 'Сменить группу может только администратор'


class SubmissionForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Submission
        fields = ('text',)
        widgets = {'text': forms.Textarea(attrs={'rows': 8, 'placeholder': 'Ваш ответ…'})}


class GradeForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Submission
        fields = ('grade', 'teacher_comment')
        widgets = {'teacher_comment': forms.Textarea(attrs={'rows': 2})}

    def clean_grade(self):
        grade = self.cleaned_data.get('grade')
        if grade is not None and grade > self.instance.homework.max_score:
            raise forms.ValidationError(f'Максимум {self.instance.homework.max_score}')
        return grade


class HomeworkForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Homework
        fields = ('subject', 'groups', 'title', 'text', 'issue_date', 'period_days',
                  'max_score', 'penalty_per_day', 'penalty_info')
        widgets = {
            'issue_date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'groups': forms.CheckboxSelectMultiple,
            'text': forms.Textarea(attrs={'rows': 6}),
            'penalty_info': forms.Textarea(attrs={'rows': 2}),
        }
