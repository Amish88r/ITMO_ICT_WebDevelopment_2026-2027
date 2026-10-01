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
            except OSError as e: 
                print(f"[TCP-сервер] Соединение с {addr} разорвано: {e}")
            print(f"[TCP-сервер] {addr} отключился")


if __name__ == "__main__":
    main()
