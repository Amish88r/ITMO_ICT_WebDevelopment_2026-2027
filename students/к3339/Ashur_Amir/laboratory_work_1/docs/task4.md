# Задание 4. Чат на сокетах

## Постановка задачи

Реализовать многопользовательский чат. Требования: библиотека `socket`, для многопользовательского
режима — `threading`; пользователей можно идентифицировать; пользователь может выйти из чата.
Выбран протокол **TCP** (100 % баллов за это задание).

## Описание решения

### Сервер

* Главный поток в цикле вызывает `accept()`. Для каждого подключения запускается отдельный
  поток `handle_client` — так один клиент не блокирует остальных.
* Активные пользователи хранятся в словаре `clients: имя → файловый объект сокета`.
  Доступ к словарю защищён `threading.Lock`, потому что его одновременно изменяют разные потоки.
* **Идентификация.** Первая строка, присланная клиентом, — его имя. Если имя уже занято, сервер
  сообщает об этом и закрывает соединение.
* **Рассылка.** Функция `broadcast` отправляет сообщение всем пользователям, кроме отправителя.
  О входе и выходе пользователей все остальные получают служебные сообщения.
* **Выход.** Команда `/quit` (а также обрыв соединения) приводит к удалению пользователя из словаря
  и закрытию сокета.

### Клиент

Клиент — **один** скрипт. Имя задаётся при запуске (вводом или параметром `--name`), поэтому
несколько пользователей запускают один и тот же файл в разных терминалах. Приём и отправка
идут параллельно: приём сообщений от сервера работает в отдельном потоке, отправка — в основном.

## Код сервера (`task4_chat/server.py`)

```python
"""Многопользовательский чат на TCP + threading.

Протокол (текстовые строки, разделитель \n):
  клиент -> сервер: первая строка - имя пользователя, далее - сообщения;
                    "/quit" - выход из чата;
  сервер -> клиент: готовые к выводу строки.
"""
import socket
import threading

HOST, PORT = "127.0.0.1", 9004

clients = {}  # имя -> файловый объект сокета
clients_lock = threading.Lock()


def broadcast(text, exclude=None):
    """Разослать сообщение всем, кроме пользователя exclude."""
    with clients_lock:
        for name, f in list(clients.items()):
            if name == exclude:
                continue
            try:
                f.write(text + "\n")
                f.flush()
            except OSError:
                pass  # клиент отвалился - его обработчик сам всё уберёт


def handle_client(conn, addr):
    name = None
    f = conn.makefile("rw", encoding="utf-8", newline="\n")
    try:
        name = f.readline().strip()
        if not name:
            return
        with clients_lock:
            if name in clients:
                f.write("Имя уже занято, подключитесь с другим именем.\n")
                f.flush()
                name = None
                return
            clients[name] = f
            # приветствие пишем под блокировкой, чтобы не перемешаться с чужой рассылкой
            f.write(f"Добро пожаловать в чат, {name}! Для выхода введите /quit\n")
            f.flush()
        print(f"[Чат] {name} подключился с {addr}")
        broadcast(f"*** {name} присоединился к чату ***", exclude=name)

        for line in f:
            text = line.strip()
            if text == "/quit":
                break
            if text:
                print(f"[Чат] {name}: {text}")
                broadcast(f"{name}: {text}", exclude=name)
    except (ConnectionError, OSError):
        pass
    finally:
        if name:
            with clients_lock:
                clients.pop(name, None)
            broadcast(f"*** {name} покинул чат ***")
            print(f"[Чат] {name} отключился")
        try:
            f.close()
        except OSError:
            pass
        conn.close()


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((HOST, PORT))
        server.listen()
        print(f"[Чат] Сервер запущен на {HOST}:{PORT}")
        while True:
            conn, addr = server.accept()
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()


if __name__ == "__main__":
    main()
```

## Код клиента (`task4_chat/client.py`)

```python
"""Единый клиент чата: запускается в нескольких терминалах, имя вводится при старте."""
import argparse
import os
import socket
import threading


def receive_loop(f):
    """Принимает сообщения от сервера и печатает их (работает в отдельном потоке)."""
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
```

## Результат работы

Три клиента (Alice, Bob, Carol) обмениваются сообщениями, четвёртый пытается войти под занятым именем.

Экран Alice:

```text
Добро пожаловать в чат, Alice! Для выхода введите /quit
*** Bob присоединился к чату ***
*** Carol присоединился к чату ***
Bob: Привет, Alice!
Carol: Я тоже тут
*** Bob покинул чат ***
*** Carol покинул чат ***
```

Экран Bob (вышел по `/quit`, поэтому не видит последних сообщений):

```text
Добро пожаловать в чат, Bob! Для выхода введите /quit
*** Carol присоединился к чату ***
Alice: Всем привет!
Carol: Я тоже тут
```

Повторное подключение под именем `Alice`:

```text
Имя уже занято, подключитесь с другим именем.
Соединение с сервером закрыто.
```

Журнал сервера:

```text
[Чат] Сервер запущен на 127.0.0.1:9004
[Чат] Alice подключился с ('127.0.0.1', 59758)
[Чат] Bob подключился с ('127.0.0.1', 59772)
[Чат] Carol подключился с ('127.0.0.1', 59782)
[Чат] Alice: Всем привет!
[Чат] Bob: Привет, Alice!
[Чат] Carol: Я тоже тут
[Чат] Bob отключился
[Чат] Alice: Bob ушёл?
[Чат] Carol отключился
[Чат] Alice отключился
```
