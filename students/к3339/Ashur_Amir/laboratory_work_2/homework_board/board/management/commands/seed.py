"""Наполнение БД демо-данными: python manage.py seed"""
import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from board.models import Homework, StudyGroup, Subject, Submission, User

STUDENTS = [('Аксёнова', 'Алина', 'Рустамовна'), ('Ашур', 'Амир', 'Куссаевич'), ('Барецкий', 'Максим', 'Степанович'),
            ('Блинова', 'Полина', 'Вячеславовна'), ('Воронцов', 'Максим', 'Михайлович'), ('Востров', 'Илья', 'Анатольевич'),
            ('Глухов', 'Влад', 'Вячеславович'), ('Голинский', 'Данила', 'Владимирович'), ('Григорьев', 'Максим', 'Юрьевич'),
            ('Грицкевич', 'Константин', 'Олегович'), ('Данилова', 'Айаана', 'Васильевна'), ('Дидык', 'Глеб', 'Олегович'),
            ('Иванова', 'Аайа', 'Гаврильевна'), ('Ипатова', 'Ульяна', 'Юрьевна'), ('Каприн', 'Семён', 'Евгеньевич'),
            ('Колпаков', 'Артём', 'Сергеевич'), ('Конанчук', 'Иван', 'Алексеевич'), ('Котков', 'Дмитрий', 'Александрович')]
SUBJECTS = {
    'Web-программирование': ['Сокеты на Python', 'Простой сайт на Django', 'Django REST Framework', 'Vue.js: SPA'],
    'Базы данных': ['ER-диаграмма предметной области', 'Нормализация до 3НФ', 'Запросы SQL с JOIN'],
    'Математический анализ': ['Пределы последовательностей', 'Производные и дифференциалы', 'Интегралы'],
    'Английский язык': ['Essay: My future profession', 'Present Perfect vs Past Simple'],
}
ANSWERS = ['Решение приложено ниже. Использовал подход из лекции, все тесты проходят.',
           'Выполнил все пункты задания, в конце — выводы и ссылки на источники.',
           'Код в репозитории, кратко: реализованы модели, представления и шаблоны.',
           'Сделал основную часть, дополнительное задание — частично.']


class Command(BaseCommand):
    help = 'Создаёт демо-данные (группы, преподавателей, студентов, ДЗ и оценки)'

    def handle(self, *args, **kw):
        random.seed(42)
        Submission.objects.all().delete(); Homework.objects.all().delete()
        g1, _ = StudyGroup.objects.get_or_create(name='K3340', defaults={'year': 3})
        g2, _ = StudyGroup.objects.get_or_create(name='K3341', defaults={'year': 3})

        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@example.com', 'admin',
                                          last_name='Говоров', first_name='Антон', patronymic='Игоревич')
        teachers = []
        for u, l, f, p in [('teacher', 'Петров', 'Сергей', 'Николаевич'), ('teacher2', 'Смирнова', 'Ольга', 'Павловна')]:
            t, _ = User.objects.get_or_create(username=u, defaults=dict(last_name=l, first_name=f, patronymic=p, is_staff=True))
            t.set_password('teacher123'); t.save(); teachers.append(t)

        students = []
        for i, (l, f, p) in enumerate(STUDENTS):
            uname = 'ashur' if l == 'Ашур' else f'student{i + 1}'
            s, _ = User.objects.get_or_create(username=uname, defaults=dict(last_name=l, first_name=f, patronymic=p))
            s.group = g1 if i < 12 else g2
            s.set_password('student123'); s.save(); students.append(s)

        today = timezone.localdate()
        hws = []
        for si, (subj_name, topics) in enumerate(SUBJECTS.items()):
            subj, _ = Subject.objects.get_or_create(name=subj_name)
            for ti, topic in enumerate(topics):
                hw = Homework.objects.create(
                    subject=subj, teacher=teachers[si % 2], title=topic,
                    text=f'Тема: «{topic}».\n1. Изучите материалы лекции.\n2. Выполните практическую часть.\n3. Оформите ответ и отправьте его через форму.',
                    issue_date=today - timedelta(days=30 - ti * 9 - si * 2), period_days=random.choice([7, 10, 14]),
                    max_score=random.choice([5, 10, 15, 20]), penalty_per_day=1,
                    penalty_info='После 3 дней просрочки работа принимается максимум на 50%.')
                hw.groups.set([g1, g2] if ti % 2 == 0 else [g1])
                hws.append(hw)

        for hw in hws:
            for st in students:
                if not hw.groups.filter(pk=st.group_id).exists() or random.random() < 0.25:
                    continue
                if hw.issue_date > today - timedelta(days=1):
                    continue
                late = random.random() < 0.15
                when = timezone.now() - timedelta(days=max(0, (today - hw.deadline).days - (2 if late else -1)) if hw.is_overdue else random.randint(0, 2))
                sub = Submission.objects.create(homework=hw, student=st, text=random.choice(ANSWERS))
                Submission.objects.filter(pk=sub.pk).update(submitted_at=when)
                if hw.is_overdue or random.random() < 0.5:
                    sub.refresh_from_db()
                    sub.grade = max(0, min(hw.max_score, round(hw.max_score * random.uniform(.45, 1)) - sub.days_late))
                    sub.teacher_comment = random.choice(['Отлично!', 'Хорошо, но есть недочёты', 'Нужно доработать оформление', ''])
                    sub.save()
        self.stdout.write(self.style.SUCCESS(
            f'Готово: {len(students)} студентов, {len(hws)} заданий, {Submission.objects.count()} сдач. '
            'Логины: admin/admin, teacher/teacher123, ashur/student123'))
