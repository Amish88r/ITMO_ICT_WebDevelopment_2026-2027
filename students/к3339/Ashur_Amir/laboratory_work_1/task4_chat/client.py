import argparse
import os
import socket
import threading


def receive_loop(f): 
    try:
        for line in f:
            print(line.rstrip("\n"))
    except (ConnectionError, OSError, ValueError):
        pass
    print("Соединение с сервером закрыто.")
    os._exit(0)


def main():
    parser = argparse.ArgumentParser(description="Клиент чата")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9004)
    parser.add_argument("--name", help="имя пользователя (иначе спросим при запуске)")
    args = parser.parse_args()

    name = args.name or input("Введите ваше имя: ").strip()
    if not name:
        print("Имя не может быть пустым.")
        return

    sock = socket.create_connection((args.host, args.port))
    f = sock.makefile("rw", encoding="utf-8", newline="\n")
    f.write(name + "\n")
    f.flush()

    threading.Thread(target=receive_loop, args=(f,), daemon=True).start()

    try:
        while True:
            text = input()
            f.write(text + "\n")
            f.flush()
            if text.strip() == "/quit":
                break
    except (EOFError, KeyboardInterrupt):
        try:
            f.write("/quit\n")
            f.flush()
        except OSError:
            pass
    finally:
        sock.close()


if __name__ == "__main__":
    main()
