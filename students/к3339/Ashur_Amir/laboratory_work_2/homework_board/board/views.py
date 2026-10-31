from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator
from django.db.models import Avg, Count, Exists, OuterRef, Q, Subquery
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from .forms import GradeForm, HomeworkForm, ProfileForm, SignUpForm, SubmissionForm
from .models import Homework, StudyGroup, Subject, Submission, User


def int_param(request, name):
    """Безопасно читает числовой GET-параметр: пустое или нечисловое значение -> None."""
    value = request.GET.get(name, '')
    return int(value) if value.isdigit() else None


def safe_next(request, default):
    """Защита от открытого редиректа через параметр next."""
    nxt = request.POST.get('next', '')
    if nxt and url_has_allowed_host_and_scheme(nxt, allowed_hosts={request.get_host()},
                                               require_https=request.is_secure()):
        return nxt
    return default


def staff_required(view):
    return login_required(user_passes_test(lambda u: u.is_staff)(view))


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff


# ---------------------------------------------------------------- auth
def signup(request):
    if request.user.is_authenticated:
        return redirect('homework_list')
    form = SignUpForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, 'Регистрация прошла успешно. Добро пожаловать!')
        return redirect('homework_list')
    return render(request, 'registration/signup.html', {'form': form})


@login_required
def profile(request):
    form = ProfileForm(request.POST or None, instance=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Профиль обновлён')
        return redirect('profile')
    stats = request.user.submissions.aggregate(total=Count('id'), graded=Count('grade'), avg=Avg('grade'))
    return render(request, 'board/profile.html', {'form': form, 'stats': stats})


# ---------------------------------------------------------------- homeworks
class HomeworkListView(LoginRequiredMixin, ListView):
    """Все ДЗ с поиском, фильтрами и пагинацией."""
    template_name = 'board/homework_list.html'
    context_object_name = 'homeworks'
    paginate_by = 6

    def get_queryset(self):
        user, p = self.request.user, self.request.GET
        qs = Homework.objects.select_related('subject', 'teacher').prefetch_related('groups')
        if user.is_staff:
            qs = qs.annotate(sub_count=Count('submissions', distinct=True),
                             ungraded=Count('submissions', filter=Q(submissions__grade__isnull=True), distinct=True))
            if int_param(self.request, 'group'):
                qs = qs.filter(groups__id=int_param(self.request, 'group'))
            if p.get('teacher') == 'me':
                qs = qs.filter(teacher=user)
        else:
            qs = qs.filter(groups=user.group) if user.group else qs.none()
            mine = Submission.objects.filter(homework=OuterRef('pk'), student=user)
            qs = qs.annotate(submitted=Exists(mine), my_grade=Subquery(mine.values('grade')[:1]))
            state = p.get('state')
            if state == 'todo':
                qs = qs.filter(submitted=False)
            elif state == 'submitted':
                qs = qs.filter(submitted=True, my_grade__isnull=True)
            elif state == 'graded':
                qs = qs.filter(my_grade__isnull=False)

        if p.get('q'):
            qs = qs.filter(Q(title__icontains=p['q']) | Q(text__icontains=p['q']))
        if int_param(self.request, 'subject'):
            qs = qs.filter(subject_id=int_param(self.request, 'subject'))
        # дедлайн считается в Python, поэтому фильтруем по нему через список id
        status = p.get('status')
        if status in ('active', 'overdue'):
            ids = [h.pk for h in qs if h.is_overdue == (status == 'overdue')]
            qs = qs.filter(pk__in=ids)
        # явная сортировка: при annotate(Count) Django не применяет Meta.ordering
        return qs.distinct().order_by('-issue_date', 'subject__name', 'pk')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(subjects=Subject.objects.all(), groups=StudyGroup.objects.all())
        return ctx


@login_required
def homework_detail(request, pk):
    hw = get_object_or_404(Homework.objects.select_related('subject', 'teacher'), pk=pk)
    user = request.user
    if not user.is_staff and not hw.groups.filter(pk=getattr(user.group, 'pk', None)).exists():
        messages.error(request, 'Это задание не для вашей группы')
        return redirect('homework_list')

    ctx = {'hw': hw}
    if user.is_staff:
        subs = hw.submissions.select_related('student', 'student__group').order_by('student__last_name')
        ctx['submissions'] = [(s, GradeForm(instance=s, prefix=f's{s.pk}')) for s in subs]
        students = User.objects.filter(group__in=hw.groups.all(), is_staff=False)
        ctx['not_submitted'] = students.exclude(submissions__homework=hw)
    else:
        submission = hw.submissions.filter(student=user).first()
        can_edit = submission is None or not submission.is_graded
        form = SubmissionForm(request.POST or None, instance=submission)
        if request.method == 'POST':
            if not can_edit:
                messages.error(request, 'Работа уже проверена — изменить её нельзя')
            elif form.is_valid():
                obj = form.save(commit=False)
                obj.homework, obj.student = hw, user
                obj.save()
                messages.success(request, 'Ответ сохранён' if submission else 'Задание сдано!')
                return redirect('homework_detail', pk=pk)
        ctx.update(submission=submission, form=form, can_edit=can_edit)
    return render(request, 'board/homework_detail.html', ctx)


class HomeworkCreateView(StaffRequiredMixin, CreateView):
    model = Homework
    form_class = HomeworkForm
    template_name = 'board/homework_form.html'

    def form_valid(self, form):
        form.instance.teacher = self.request.user
        messages.success(self.request, 'Задание опубликовано')
        return super().form_valid(form)


class HomeworkUpdateView(StaffRequiredMixin, UpdateView):
    model = Homework
    form_class = HomeworkForm
    template_name = 'board/homework_form.html'

    def form_valid(self, form):
        messages.success(self.request, 'Задание обновлено')
        return super().form_valid(form)


class HomeworkDeleteView(StaffRequiredMixin, DeleteView):
    model = Homework
    template_name = 'board/confirm_delete.html'
    success_url = reverse_lazy('homework_list')


# ---------------------------------------------------------------- submissions
@login_required
def my_submissions(request):
    qs = request.user.submissions.select_related('homework', 'homework__subject').order_by('-submitted_at', '-pk')
    if int_param(request, 'subject'):
        qs = qs.filter(homework__subject_id=int_param(request, 'subject'))
    if request.GET.get('graded') == '1':
        qs = qs.filter(grade__isnull=False)
    elif request.GET.get('graded') == '0':
        qs = qs.filter(grade__isnull=True)
    page = Paginator(qs, 8).get_page(request.GET.get('page'))
    return render(request, 'board/my_submissions.html',
                  {'page_obj': page, 'subjects': Subject.objects.all()})


@login_required
def submission_delete(request, pk):
    sub = get_object_or_404(Submission, pk=pk, student=request.user)
    if sub.is_graded:
        messages.error(request, 'Проверенную работу отменить нельзя')
        return redirect('homework_detail', pk=sub.homework_id)
    if request.method == 'POST':
        hw_pk = sub.homework_id
        sub.delete()
        messages.info(request, 'Сдача отменена')
        return redirect('homework_detail', pk=hw_pk)
    return render(request, 'board/confirm_delete.html', {'object': sub})


@staff_required
def review(request):
    """Очередь проверки для преподавателя."""
    p = request.GET
    qs = (Submission.objects.select_related('student', 'student__group', 'homework', 'homework__subject')
          .order_by('-submitted_at', '-pk'))
    if p.get('state', 'ungraded') == 'ungraded':
        qs = qs.filter(grade__isnull=True)
    elif p.get('state') == 'graded':
        qs = qs.filter(grade__isnull=False)
    if int_param(request, 'group'):
        qs = qs.filter(student__group_id=int_param(request, 'group'))
    if int_param(request, 'subject'):
        qs = qs.filter(homework__subject_id=int_param(request, 'subject'))
    if p.get('q'):
        qs = qs.filter(Q(student__last_name__icontains=p['q']) | Q(homework__title__icontains=p['q']))
    page = Paginator(qs, 10).get_page(p.get('page'))
    rows = [(s, GradeForm(instance=s, prefix=f's{s.pk}')) for s in page]
    return render(request, 'board/review.html', {
        'page_obj': page, 'rows': rows, 'state': p.get('state', 'ungraded'),
        'groups': StudyGroup.objects.all(), 'subjects': Subject.objects.all()})


@staff_required
@require_POST
def grade_submission(request, pk):
    sub = get_object_or_404(Submission, pk=pk)
    form = GradeForm(request.POST, instance=sub, prefix=f's{sub.pk}')
    if form.is_valid():
        form.save()
        messages.success(request, f'Оценка для {sub.student.short_name} сохранена')
    else:
        messages.error(request, '; '.join(e for errs in form.errors.values() for e in errs))
    return redirect(safe_next(request, reverse('review')))


# ---------------------------------------------------------------- grades table
@login_required
def grades_table(request):
    """Таблица оценок всех студентов группы (журнал)."""
    user = request.user
    groups = StudyGroup.objects.all()
    if user.is_staff:
        group = groups.filter(pk=int_param(request, 'group')).first() or groups.first()
    else:
        group = user.group
    subjects = Subject.objects.filter(homeworks__groups=group).distinct() if group else Subject.objects.none()
    subject = subjects.filter(pk=int_param(request, 'subject')).first()

    homeworks = Homework.objects.filter(groups=group).select_related('subject').order_by('subject__name', 'issue_date')
    if subject:
        homeworks = homeworks.filter(subject=subject)
    students = User.objects.filter(group=group, is_staff=False) if group else User.objects.none()
    if request.GET.get('q'):
        students = students.filter(last_name__icontains=request.GET['q'])

    subs = Submission.objects.filter(homework__in=homeworks, student__in=students)
    cell = {(s.student_id, s.homework_id): s for s in subs}
    rows = []
    for st in students:
        cells = [cell.get((st.pk, hw.pk)) for hw in homeworks]
        grades = [c.grade for c in cells if c and c.grade is not None]
        total = sum(grades)
        max_total = sum(hw.max_score for hw in homeworks)
        rows.append({'student': st, 'cells': cells, 'total': total,
                     'percent': round(100 * total / max_total) if max_total else 0,
                     'is_me': st.pk == user.pk})
    page = Paginator(rows, 15).get_page(request.GET.get('page'))
    return render(request, 'board/grades_table.html', {
        'group': group, 'groups': groups, 'subjects': subjects, 'subject': subject,
        'homeworks': homeworks, 'page_obj': page, 'today': timezone.localdate()})
