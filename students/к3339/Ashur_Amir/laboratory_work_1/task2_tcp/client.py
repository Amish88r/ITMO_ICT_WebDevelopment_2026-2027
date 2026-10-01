import json
import socket

HOST, PORT = "127.0.0.1", 9002

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
