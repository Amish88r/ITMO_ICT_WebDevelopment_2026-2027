# Задание 3. Раздача HTML-страницы по HTTP

## Постановка задачи

Клиент подключается к серверу и в ответ получает HTTP-сообщение, содержащее HTML-страницу,
которую сервер загружает из файла `index.html`. Используется библиотека `socket`.

## Описание решения

HTTP-ответ — это обычный текст строгого формата:

```text
HTTP/1.1 200 OK                          <- строка статуса
Content-Type: text/html; charset=utf-8   <- заголовки
Content-Length: 563
Connection: close
                                         <- пустая строка (\r\n\r\n)
<!DOCTYPE html>...                       <- тело
```

Сервер принимает подключение, читает запрос, считывает `index.html` **в байтах** (чтобы
`Content-Length` был длиной именно в байтах, а не в символах — важно для кириллицы в UTF-8),
формирует заголовки и отправляет заголовки и тело одним `sendall()`.

Так как это обычный HTTP, страницу можно открыть и браузером: `http://127.0.0.1:8080/`.

## Код сервера (`task3_http/server.py`)

```python
import socket
from pathlib import Path

HOST, PORT = "127.0.0.1", 8080
INDEX = Path(__file__).with_name("index.html")


def build_response():
    body = INDEX.read_bytes()
    headers = (
        "HTTP/1.1 200 OK\r\n"
        "Content-Type: text/html; charset=utf-8\r\n"
        f"Content-Length: {len(body)}\r\n"
        "Connection: close\r\n"
        "\r\n"
    )
    return headers.encode("utf-8") + body


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((HOST, PORT))
        server.listen(5)
        print(f"[HTTP-сервер] Открой в браузере http://{HOST}:{PORT}/")

        while True:
            conn, addr = server.accept()
            with conn:
                request = conn.recv(4096).decode("utf-8", errors="replace")
                print(f"[HTTP-сервер] {addr}: {request.splitlines()[0] if request else '(пусто)'}")
                conn.sendall(build_response())


if __name__ == "__main__":
    main()
```

## Файл `task3_http/index.html`

```html
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="utf-8">
    <title>Сервер на сокетах</title>
    <style>
        body { font-family: sans-serif; max-width: 640px; margin: 60px auto; }
        h1 { color: #3949ab; }
    </style>
</head>
<body>
    <h1>Привет из сокетного сервера!</h1>
    <p>Эта страница прочитана из файла <code>index.html</code> и отправлена клиенту
       в виде HTTP-ответа через обычный TCP-сокет.</p>
</body>
</html>
```

## Результат работы

Ответ сервера на `GET / HTTP/1.1`:

```text
HTTP/1.1 200 OK
Content-Type: text/html; charset=utf-8
Content-Length: 563
Connection: close
```

Длина тела совпала с `Content-Length` (563 байта), тег `<h1>` присутствует в теле.
В браузере открывается страница «Привет из сокетного сервера!».
