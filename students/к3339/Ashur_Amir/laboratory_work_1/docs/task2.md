# Задание 2. Вычисления через TCP

## Постановка задачи

Клиент запрашивает выполнение математической операции, параметры которой вводятся с клавиатуры.
Сервер выполняет вычисление и возвращает результат. Используются `socket` и протокол TCP.

Вариант операции зависит от номера студента в журнале:

| Вариант | Операция |
|---------|----------|
| 1 | Теорема Пифагора |
| 2 | Решение квадратного уравнения |
| 3 | Поиск площади трапеции |
| 4 | Поиск площади параллелограмма |

!!! note "Про вариант"
    Реализованы **все четыре** варианта, поэтому программа подходит для любого номера.
    В отчёте для сдачи можно оставить только свой вариант либо показать все.

## Описание решения

* **Сервер** (`SOCK_STREAM`): `bind` → `listen` → `accept`. После подключения читает запросы
  построчно и на каждый отвечает одной строкой. Клиентов обслуживает по очереди; после отключения
  клиента снова ждёт новое подключение.
* **Клиент**: `connect`, затем текстовое меню. Пользователь выбирает операцию и вводит параметры,
  клиент отправляет запрос и печатает ответ.
* **Протокол прикладного уровня.** TCP — потоковый протокол и не сохраняет границы сообщений,
  поэтому запросы и ответы оформлены как JSON-строки, заканчивающиеся символом `\n`:

```text
запрос:  {"op": "trapezoid", "args": [4.0, 6.0, 8.0]}
ответ:   {"ok": true, "result": "Площадь трапеции S = 40.0000"}
```

Сервер проверяет входные данные: неизвестная операция, неверное число параметров, деление на ноль
(`a = 0` в квадратном уравнении), отрицательные стороны, гипотенуза, не превосходящая катет, —
всё это возвращается клиенту как `{"ok": false, ...}`, а не роняет сервер.

### Используемые формулы

| Операция | Формула |
|----------|---------|
| Гипотенуза | c = √(a² + b²) |
| Катет | b = √(c² − a²) |
| Квадратное уравнение | D = b² − 4ac;  x₁,₂ = (−b ± √D) / 2a |
| Площадь трапеции | S = (a + b) / 2 · h |
| Площадь параллелограмма | S = a · h  или  S = a · b · sin α |

## Код сервера (`task2_tcp/server.py`)

```python
"""TCP-сервер: выполняет математические операции (все 4 варианта задания).

Протокол: клиент шлёт одну строку JSON {"op": "...", "args": [...]},
сервер отвечает одной строкой JSON {"ok": true/false, "result": "..."}.
"""
import json
import math
import socket

HOST, PORT = "127.0.0.1", 9002


def pythagoras_hyp(a, b):
    """Вариант 1: гипотенуза по двум катетам."""
    return f"Гипотенуза c = {math.hypot(a, b):.4f}"


def pythagoras_leg(c, a):
    """Вариант 1: катет по гипотенузе и другому катету."""
    if c <= a:
        raise ValueError("Гипотенуза должна быть больше катета")
    return f"Катет b = {math.sqrt(c * c - a * a):.4f}"


def quadratic(a, b, c):
    """Вариант 2: решение ax^2 + bx + c = 0."""
    if a == 0:
        raise ValueError("Коэффициент a не должен быть равен 0")
    d = b * b - 4 * a * c
    if d > 0:
        x1 = (-b + math.sqrt(d)) / (2 * a)
        x2 = (-b - math.sqrt(d)) / (2 * a)
        return f"D = {d:.4f}; два корня: x1 = {x1:.4f}, x2 = {x2:.4f}"
    if d == 0:
        return f"D = 0; один корень: x = {-b / (2 * a):.4f}"
    return f"D = {d:.4f} < 0; действительных корней нет"


def trapezoid(a, b, h):
    """Вариант 3: площадь трапеции по основаниям и высоте."""
    if min(a, b, h) <= 0:
        raise ValueError("Все величины должны быть положительными")
    return f"Площадь трапеции S = {(a + b) / 2 * h:.4f}"


def parallelogram_h(a, h):
    """Вариант 4: площадь параллелограмма по основанию и высоте."""
    if min(a, h) <= 0:
        raise ValueError("Все величины должны быть положительными")
    return f"Площадь параллелограмма S = {a * h:.4f}"


def parallelogram_angle(a, b, angle):
    """Вариант 4: площадь параллелограмма по двум сторонам и углу (в градусах)."""
    if min(a, b) <= 0 or not 0 < angle < 180:
        raise ValueError("Стороны > 0, угол в диапазоне (0; 180)")
    return f"Площадь параллелограмма S = {a * b * math.sin(math.radians(angle)):.4f}"


OPERATIONS = {
    "pythagoras_hyp": (pythagoras_hyp, 2),
    "pythagoras_leg": (pythagoras_leg, 2),
    "quadratic": (quadratic, 3),
    "trapezoid": (trapezoid, 3),
    "parallelogram_h": (parallelogram_h, 2),
    "parallelogram_angle": (parallelogram_angle, 3),
}


def process(request_line):
    try:
        req = json.loads(request_line)
        func, n_args = OPERATIONS[req["op"]]
        args = [float(x) for x in req["args"]]
        if len(args) != n_args:
            raise ValueError(f"Ожидается параметров: {n_args}")
        return {"ok": True, "result": func(*args)}
    except KeyError:
        return {"ok": False, "result": "Неизвестная операция"}
    except json.JSONDecodeError:
        return {"ok": False, "result": "Ошибка: некорректный формат запроса"}
    except (ValueError, TypeError) as e:
        return {"ok": False, "result": f"Ошибка: {e}"}


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((HOST, PORT))
        server.listen(1)
        print(f"[TCP-сервер] Слушаю {HOST}:{PORT}")

        while True:
            conn, addr = server.accept()
            print(f"[TCP-сервер] Подключился {addr}")
            try:
                with conn, conn.makefile("rw", encoding="utf-8", newline="\n") as f:
                    for line in f:
                        print(f"[TCP-сервер] Запрос: {line.strip()}")
                        f.write(json.dumps(process(line), ensure_ascii=False) + "\n")
                        f.flush()
            except OSError as e:  # клиент оборвал соединение - сервер продолжает работу
                print(f"[TCP-сервер] Соединение с {addr} разорвано: {e}")
            print(f"[TCP-сервер] {addr} отключился")


if __name__ == "__main__":
    main()
```

## Код клиента (`task2_tcp/client.py`)

```python
import json
import socket

HOST, PORT = "127.0.0.1", 9002

# (ключ операции, название, подписи параметров)
MENU = {
    "1": ("pythagoras_hyp", "Теорема Пифагора: гипотенуза по катетам", ["катет a", "катет b"]),
    "2": ("pythagoras_leg", "Теорема Пифагора: катет по гипотенузе и катету", ["гипотенуза c", "катет a"]),
    "3": ("quadratic", "Квадратное уравнение ax^2 + bx + c = 0", ["a", "b", "c"]),
    "4": ("trapezoid", "Площадь трапеции", ["основание a", "основание b", "высота h"]),
    "5": ("parallelogram_h", "Площадь параллелограмма (основание и высота)", ["основание a", "высота h"]),
    "6": ("parallelogram_angle", "Площадь параллелограмма (стороны и угол)", ["сторона a", "сторона b", "угол, градусы"]),
}


def ask_number(prompt):
    while True:
        try:
            return float(input(f"  Введите {prompt}: ").replace(",", "."))
        except ValueError:
            print("  Нужно число, попробуйте ещё раз.")


def main():
    try:
        sock = socket.create_connection((HOST, PORT))
    except OSError:
        print(f"Не удалось подключиться к серверу {HOST}:{PORT}. Запущен ли server.py?")
        return

    with sock, sock.makefile("rw", encoding="utf-8", newline="\n") as f:
        while True:
            print("\nВыберите операцию:")
            for key, (_, title, _) in MENU.items():
                print(f"  {key} - {title}")
            print("  0 - выход")
            choice = input("Ваш выбор: ").strip()
            if choice == "0":
                break
            if choice not in MENU:
                print("Нет такого пункта меню.")
                continue

            op, _, labels = MENU[choice]
            args = [ask_number(label) for label in labels]

            f.write(json.dumps({"op": op, "args": args}) + "\n")
            f.flush()

            line = f.readline()
            if not line:
                print("Сервер закрыл соединение.")
                break
            reply = json.loads(line)
            print(("Результат: " if reply["ok"] else "") + reply["result"])


if __name__ == "__main__":
    try:
        main()
    except (EOFError, KeyboardInterrupt):
        print("\nВыход.")
    except (ConnectionError, BrokenPipeError):
        print("\nСоединение с сервером потеряно.")
```

## Результат работы

Клиент (ввод пользователя сокращён до результатов; для каждого пункта меню вводились параметры):

```text
Гипотенуза c = 5.0000                          (катеты 3 и 4)
Катет b = 4.0000                               (гипотенуза 5, катет 3)
D = 1.0000; два корня: x1 = 2.0000, x2 = 1.0000   (x² − 3x + 2 = 0)
D = 0; один корень: x = -1.0000                   (x² + 2x + 1 = 0)
D = -4.0000 < 0; действительных корней нет        (x² + 1 = 0)
Площадь трапеции S = 40.0000                   (основания 4 и 6, высота 8)
Площадь параллелограмма S = 21.0000            (основание 7, высота 3)
Площадь параллелограмма S = 10.0000            (стороны 5 и 4, угол 30°)
Ошибка: Все величины должны быть положительными   (основание 0, высота 5)
```

Журнал сервера:

```text
[TCP-сервер] Слушаю 127.0.0.1:9002
[TCP-сервер] Подключился ('127.0.0.1', 35588)
[TCP-сервер] Запрос: {"op": "pythagoras_hyp", "args": [3.0, 4.0]}
[TCP-сервер] Запрос: {"op": "pythagoras_leg", "args": [5.0, 3.0]}
[TCP-сервер] Запрос: {"op": "quadratic", "args": [1.0, -3.0, 2.0]}
[TCP-сервер] Запрос: {"op": "quadratic", "args": [1.0, 2.0, 1.0]}
[TCP-сервер] Запрос: {"op": "quadratic", "args": [1.0, 0.0, 1.0]}
[TCP-сервер] Запрос: {"op": "trapezoid", "args": [4.0, 6.0, 8.0]}
```
