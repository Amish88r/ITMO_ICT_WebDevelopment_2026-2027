# Задание 1. Обмен сообщениями по UDP

## Постановка задачи

Клиент отправляет серверу сообщение «Hello, server», оно выводится на стороне сервера.
В ответ сервер отправляет «Hello, client», которое выводится у клиента.
Необходимо использовать библиотеку `socket` и протокол UDP.

## Описание решения

UDP — протокол без установления соединения, поэтому нет ни `listen()`/`accept()`, ни `connect()`.

* **Сервер** создаёт сокет типа `SOCK_DGRAM`, привязывает его к адресу (`bind`) и ждёт датаграмму
  через `recvfrom()`. Этот вызов возвращает и данные, и адрес отправителя — он же используется
  для ответа через `sendto()`.
* **Клиент** создаёт такой же сокет, отправляет датаграмму `sendto()` на адрес сервера и
  ожидает ответ через `recvfrom()`.

Порядок запуска важен: сервер должен быть запущен первым, иначе датаграмма клиента будет потеряна
(UDP не гарантирует доставку).

## Код сервера (`task1_udp/server.py`)

```python
import socket

HOST, PORT = "127.0.0.1", 9001

with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
    sock.bind((HOST, PORT))
    print(f"[UDP-сервер] Слушаю {HOST}:{PORT}")

    data, addr = sock.recvfrom(1024)
    print(f"[UDP-сервер] Получено от {addr}: {data.decode('utf-8')}")

    sock.sendto("Hello, client".encode("utf-8"), addr)
```

## Код клиента (`task1_udp/client.py`)

```python
import socket

HOST, PORT = "127.0.0.1", 9001

with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
    sock.settimeout(5)  # UDP не гарантирует доставку: не ждём ответ бесконечно
    sock.sendto("Hello, server".encode("utf-8"), (HOST, PORT))

    try:
        data, _ = sock.recvfrom(1024)
        print(f"[UDP-клиент] Получено: {data.decode('utf-8')}")
    except (socket.timeout, ConnectionError):
        print("[UDP-клиент] Ответ не получен. Запущен ли server.py?")
```

## Результат работы

Сервер:

```text
[UDP-сервер] Слушаю 127.0.0.1:9001
[UDP-сервер] Получено от ('127.0.0.1', 53741): Hello, server
```

Клиент:

```text
[UDP-клиент] Получено: Hello, client
```
