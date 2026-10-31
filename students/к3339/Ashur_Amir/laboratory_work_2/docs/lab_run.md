# Запуск проекта

## 1. Зависимости

```bash
python -m venv venv
venv\Scripts\activate            # Linux/macOS: source venv/bin/activate
pip install -r requirements.txt
```

## 2. База данных PostgreSQL

Создайте базу (через pgAdmin или psql):

```sql
CREATE DATABASE homework_board;
```

Параметры подключения берутся из переменных окружения. Значения по умолчанию:
`DB_NAME=homework_board`, `DB_USER=postgres`, `DB_PASSWORD=postgres`, `DB_HOST=localhost`, `DB_PORT=5432`.

```bash
# Windows (PowerShell):  $env:DB_PASSWORD="мой_пароль"
# Linux/macOS:           export DB_PASSWORD=мой_пароль
```

## 3. Миграции, демо-данные, запуск

```bash
cd homework_board
python manage.py migrate
python manage.py seed          # группы, предметы, 12 ДЗ, 18 студентов, оценки
python manage.py runserver
```

Демо-аккаунты:

| Роль | Логин | Пароль |
|---|---|---|
| Суперпользователь | `admin` | `admin` |
| Преподаватель | `teacher` | `teacher123` |
| Студент | `ashur` | `student123` |

Чтобы добавить нового преподавателя, создайте пользователя в админке и отметьте **«Статус персонала»**
(`is_staff`). Права группы «Преподаватели» он получит автоматически.

## Автотесты

```bash
python manage.py test board
```

17 тестов проверяют:

- дедлайн и штрафы;
- регистрацию и права доступа;
- сдачу, изменение и отмену работы;
- блокировку проверенной работы;
- выставление и проверку оценки;
- защиту от редиректа на чужой сайт;
- права в админке;
- устойчивость фильтров к пустым и неверным параметрам;
- поиск, пагинацию и журнал.

## Практические работы

```bash
cd practice/django_project_ashur
python manage.py migrate
python manage.py shell < seed_practice.py
python manage.py runserver
```

Практики используют SQLite, как в методичке.

## Сборка отчёта

```bash
mkdocs serve      # http://127.0.0.1:8000
mkdocs build      # статический сайт в папке site/
```
