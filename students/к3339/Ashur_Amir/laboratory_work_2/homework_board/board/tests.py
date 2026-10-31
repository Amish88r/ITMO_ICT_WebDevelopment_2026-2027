from datetime import timedelta

from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Homework, StudyGroup, Subject, Submission, User


class BoardTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.g1 = StudyGroup.objects.create(name='K3340')
        cls.g2 = StudyGroup.objects.create(name='K3341')
        cls.subject = Subject.objects.create(name='Web')
        cls.teacher = User.objects.create_user('teacher', password='pass', is_staff=True, last_name='Петров')
        cls.student = User.objects.create_user('st', password='pass', group=cls.g1, last_name='Ашур')
        cls.other = User.objects.create_user('st2', password='pass', group=cls.g2, last_name='Другой')
        today = timezone.localdate()
        cls.hw = Homework.objects.create(subject=cls.subject, teacher=cls.teacher, title='Django',
                                         text='Сделать сайт', issue_date=today, period_days=7, max_score=10)
        cls.hw.groups.set([cls.g1])
        cls.old = Homework.objects.create(subject=cls.subject, teacher=cls.teacher, title='Сокеты', text='...',
                                          issue_date=today - timedelta(days=20), period_days=7,
                                          max_score=10, penalty_per_day=1)
        cls.old.groups.set([cls.g1, cls.g2])

    def login(self, user):
        self.client.force_login(user)

    # --- модели
    def test_deadline_and_overdue(self):
        self.assertEqual(self.hw.deadline, self.hw.issue_date + timedelta(days=7))
        self.assertFalse(self.hw.is_overdue)
        self.assertTrue(self.old.is_overdue)

    def test_late_penalty(self):
        sub = Submission.objects.create(homework=self.old, student=self.student, text='ответ')
        self.assertEqual(sub.days_late, 13)
        self.assertEqual(sub.suggested_grade, 0)

    # --- регистрация и доступ
    def test_signup_creates_student(self):
        r = self.client.post(reverse('signup'), {
            'username': 'new', 'last_name': 'Новый', 'first_name': 'Студент', 'patronymic': '',
            'email': '', 'group': self.g1.pk, 'password1': 'Sl0zhnyi-parol', 'password2': 'Sl0zhnyi-parol'})
        self.assertRedirects(r, reverse('homework_list'))
        self.assertFalse(User.objects.get(username='new').is_staff)

    def test_anonymous_redirected_to_login(self):
        self.assertEqual(self.client.get(reverse('homework_list')).status_code, 302)

    def test_student_cannot_open_teacher_pages(self):
        self.login(self.student)
        self.assertEqual(self.client.get(reverse('homework_create')).status_code, 403)
        self.assertEqual(self.client.get(reverse('review')).status_code, 302)
        sub = Submission.objects.create(homework=self.hw, student=self.student, text='x')
        self.client.post(reverse('grade_submission', args=[sub.pk]), {f's{sub.pk}-grade': 10})
        sub.refresh_from_db()
        self.assertIsNone(sub.grade)

    def test_student_sees_only_own_group(self):
        self.login(self.other)
        r = self.client.get(reverse('homework_list'))
        self.assertNotContains(r, 'Django')
        self.assertContains(r, 'Сокеты')
        self.assertRedirects(self.client.get(reverse('homework_detail', args=[self.hw.pk])), reverse('homework_list'))

    def test_student_cannot_change_group_in_profile(self):
        self.login(self.student)
        self.client.post(reverse('profile'), {'last_name': 'Ашур', 'first_name': 'А', 'group': self.g2.pk})
        self.student.refresh_from_db()
        self.assertEqual(self.student.group, self.g1)

    # --- сдача работы
    def test_submit_edit_cancel(self):
        self.login(self.student)
        url = reverse('homework_detail', args=[self.hw.pk])
        self.client.post(url, {'text': 'первый'})
        sub = Submission.objects.get(homework=self.hw, student=self.student)
        self.client.post(url, {'text': 'второй'})
        sub.refresh_from_db()
        self.assertEqual(sub.text, 'второй')
        self.assertEqual(Submission.objects.count(), 1)
        self.client.post(reverse('submission_delete', args=[sub.pk]))
        self.assertFalse(Submission.objects.exists())

    def test_graded_submission_is_locked(self):
        sub = Submission.objects.create(homework=self.hw, student=self.student, text='ответ', grade=8)
        self.login(self.student)
        self.client.post(reverse('homework_detail', args=[self.hw.pk]), {'text': 'новый'})
        self.client.post(reverse('submission_delete', args=[sub.pk]))
        sub.refresh_from_db()
        self.assertEqual(sub.text, 'ответ')

    def test_cannot_delete_foreign_submission(self):
        sub = Submission.objects.create(homework=self.old, student=self.other, text='чужое')
        self.login(self.student)
        self.assertEqual(self.client.post(reverse('submission_delete', args=[sub.pk])).status_code, 404)

    # --- преподаватель
    def test_teacher_grades_with_validation(self):
        sub = Submission.objects.create(homework=self.hw, student=self.student, text='ответ')
        self.login(self.teacher)
        url = reverse('grade_submission', args=[sub.pk])
        self.client.post(url, {f's{sub.pk}-grade': 99})
        sub.refresh_from_db()
        self.assertIsNone(sub.grade)
        r = self.client.post(url, {f's{sub.pk}-grade': 9, f's{sub.pk}-teacher_comment': 'ок',
                                   'next': 'https://evil.example.com/'})
        self.assertRedirects(r, reverse('review'), fetch_redirect_response=False)
        sub.refresh_from_db()
        self.assertEqual(sub.grade, 9)
        self.assertIsNotNone(sub.graded_at)

    def test_teacher_creates_homework(self):
        self.login(self.teacher)
        r = self.client.post(reverse('homework_create'), {
            'subject': self.subject.pk, 'groups': [self.g1.pk, self.g2.pk], 'title': 'Новое', 'text': 'т',
            'issue_date': timezone.localdate().isoformat(), 'period_days': 5, 'max_score': 10,
            'penalty_per_day': 1, 'penalty_info': ''})
        hw = Homework.objects.get(title='Новое')
        self.assertRedirects(r, hw.get_absolute_url())
        self.assertEqual(hw.teacher, self.teacher)
        self.assertEqual(hw.groups.count(), 2)

    def test_teacher_has_admin_permissions(self):
        self.assertTrue(self.teacher.groups.filter(name='Преподаватели').exists())
        self.assertTrue(self.teacher.has_perm('board.change_submission'))
        self.assertFalse(self.student.groups.exists())
        self.login(self.teacher)
        self.assertEqual(self.client.get(reverse('admin:board_submission_changelist')).status_code, 200)

    # --- фильтры, пагинация, журнал
    def test_filters_tolerate_bad_params(self):
        self.login(self.teacher)
        for url in ['/?subject=&status=&group=&teacher=', '/?subject=abc', '/review/?group=x&subject=',
                    '/grades/?group=&subject=&q=', '/grades/?group=zzz']:
            self.assertEqual(self.client.get(url).status_code, 200, url)
        self.login(self.student)
        self.assertEqual(self.client.get('/submissions/?subject=&graded=').status_code, 200)

    def test_search_and_status_filter(self):
        self.login(self.teacher)
        r = self.client.get('/?q=Сокет')
        self.assertContains(r, 'Сокеты')
        self.assertNotContains(r, 'Сделать сайт')
        r = self.client.get('/?status=overdue')
        self.assertEqual([h.pk for h in r.context['homeworks']], [self.old.pk])

    def test_pagination(self):
        for i in range(10):
            h = Homework.objects.create(subject=self.subject, teacher=self.teacher, title=f'Тема {i}', text='t')
            h.groups.set([self.g1])
        self.login(self.student)
        r = self.client.get('/?page=2')
        self.assertEqual(r.context['page_obj'].number, 2)
        self.assertEqual(r.context['paginator'].num_pages, 2)

    def test_grades_table(self):
        Submission.objects.create(homework=self.old, student=self.student, text='x', grade=7)
        self.login(self.student)
        r = self.client.get(reverse('grades_table'))
        row = next(x for x in r.context['page_obj'] if x['student'] == self.student)
        self.assertEqual(row['total'], 7)
        self.assertEqual(r.context['group'], self.g1)
