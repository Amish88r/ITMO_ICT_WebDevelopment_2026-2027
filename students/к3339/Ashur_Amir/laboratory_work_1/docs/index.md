# Лабораторная работа №1. Работа с сокетами

**Дисциплина:** Веб-программирование
**Студент:** Ashur Amir, группа к3339

## Цель работы

Понять принципы межсокетного взаимодействия в вебе и научиться реализовывать базовую
клиент-серверную архитектуру с помощью библиотеки `socket` языка Python.

## Состав работы

| № | Задание | Протокол | Каталог |
|---|---------|----------|---------|
| 1 | Обмен сообщениями «Hello, server» / «Hello, client» | UDP | `task1_udp/` |
| 2 | Математические вычисления на сервере | TCP | `task2_tcp/` |
| 3 | Раздача HTML-страницы из `index.html` | TCP (HTTP) | `task3_http/` |
| 4 | Многопользовательский чат с потоками | TCP | `task4_chat/` |
| 5 | Веб-сервер с обработкой GET и POST (журнал оценок) | TCP (HTTP) | `task5_web/` |

Все программы написаны на Python 3 и используют только стандартную библиотеку
(`socket`, `threading`, `json`, `math` и др.), сторонние пакеты не нужны.

## Структура каталога

```text
laboratory_work_1/
├── task1_udp/      server.py, client.py
├── task2_tcp/      server.py, client.py
├── task3_http/     server.py, index.html
├── task4_chat/     server.py, client.py
├── task5_web/      server.py
├── docs/           отчёт (Markdown)
└── mkdocs.yml      конфигурация MkDocs
```

## Как запускать

Каждое задание запускается из корня каталога `laboratory_work_1`. Сначала стартует
сервер в одном терминале, затем клиент — в другом.

```bash
# Задание 1
python3 task1_udp/server.py
python3 task1_udp/client.py

# Задание 2
python3 task2_tcp/server.py
python3 task2_tcp/client.py

# Задание 3 (затем открыть http://127.0.0.1:8080/)
python3 task3_http/server.py

# Задание 4 (клиент можно запускать сколько угодно раз в разных терминалах)
python3 task4_chat/server.py
python3 task4_chat/client.py

# Задание 5 (затем открыть http://127.0.0.1:8000/)
python3 task5_web/server.py
```

!!! note "macOS и Linux"
    На macOS и Linux команда запуска — `python3`. На Windows используйте `python` (или `py`).
    Нужен Python 3.8 или новее (`python3 --version`).

## Сборка отчёта

```bash
python3 -m venv .venv && source .venv/bin/activate   # на Windows: .venv\Scripts\activate
pip install mkdocs mkdocs-material
mkdocs serve      # предпросмотр на http://127.0.0.1:8000/ (порт можно сменить: -a 127.0.0.1:8001)
mkdocs build      # статический сайт в каталоге site/
```
