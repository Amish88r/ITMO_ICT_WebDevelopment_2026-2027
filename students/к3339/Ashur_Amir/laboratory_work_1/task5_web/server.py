"""Веб-сервер на чистых сокетах: журнал оценок (GET - страница, POST - добавление)."""
import json
import socket
from html import escape
from urllib.parse import parse_qs

HOST, PORT = "127.0.0.1", 8000

# Журнал, сгруппированный по дисциплинам: {"Математика": [5, 4], "Физика": [3]}
grades = {}


def recv_request(conn):
    """Читает запрос целиком: заголовки до \\r\\n\\r\\n и тело по Content-Length."""
    data = b""
    while b"\r\n\r\n" not in data:
        chunk = conn.recv(4096)
        if not chunk:
            return None
        data += chunk
    head, _, body = data.partition(b"\r\n\r\n")

    lines = head.decode("utf-8", errors="replace").split("\r\n")
    method, path, _version = lines[0].split(" ", 2)
    headers = {}
    for line in lines[1:]:
        key, _, value = line.partition(":")
        headers[key.strip().lower()] = value.strip()

    length = int(headers.get("content-length", 0))
    while len(body) < length:
        chunk = conn.recv(4096)
        if not chunk:
            break
        body += chunk
    return method, path, headers, body[:length].decode("utf-8", errors="replace")


def make_response(status, body="", content_type="text/html; charset=utf-8", extra_headers=None):
    body_bytes = body.encode("utf-8")
    lines = [
        f"HTTP/1.1 {status}",
        f"Content-Type: {content_type}",
        f"Content-Length: {len(body_bytes)}",
        "Connection: close",
    ]
    for k, v in (extra_headers or {}).items():
        lines.append(f"{k}: {v}")
    return ("\r\n".join(lines) + "\r\n\r\n").encode("utf-8") + body_bytes


def render_page(message=""):
    if grades:
        rows = "".join(
            f"<tr><td>{escape(subject)}</td>"
            f"<td>{', '.join(map(str, marks))}</td>"
            f"<td>{sum(marks) / len(marks):.2f}</td></tr>"
            for subject, marks in grades.items()
        )
        table = (
            "<table><tr><th>Дисциплина</th><th>Оценки</th><th>Среднее</th></tr>"
            f"{rows}</table>"
        )
    else:
        table = "<p>Оценок пока нет.</p>"

    return f"""<!DOCTYPE html>
<html lang="ru"><head><meta charset="utf-8"><title>Журнал оценок</title>
<style>
 body {{ font-family: sans-serif; max-width: 640px; margin: 40px auto; }}
 table {{ border-collapse: collapse; width: 100%; margin-bottom: 24px; }}
 th, td {{ border: 1px solid #999; padding: 6px 10px; text-align: left; }}
 th {{ background: #e8eaf6; }}
 .error {{ color: #c62828; }}
</style></head><body>
<h1>Журнал оценок</h1>
{f'<p class="error">{escape(message)}</p>' if message else ''}
{table}
<h2>Добавить оценку</h2>
<form method="POST" action="/">
  <input name="subject" placeholder="Дисциплина" required>
  <input name="grade" type="number" min="1" max="5" placeholder="Оценка" required>
  <button type="submit">Сохранить</button>
</form>
</body></html>"""


def add_grade(subject, grade_raw):
    """Добавляет оценку в журнал; возвращает текст ошибки или None."""
    subject = (subject or "").strip()
    if not subject:
        return "Не указана дисциплина"
    try:
        grade = int(grade_raw)
    except (TypeError, ValueError):
        return "Оценка должна быть целым числом"
    if not 1 <= grade <= 5:
        return "Оценка должна быть от 1 до 5"
    grades.setdefault(subject, []).append(grade)
    return None


def handle(method, path, headers, body):
    if path.split("?")[0] != "/":
        return make_response("404 Not Found", "<h1>404 Not Found</h1>")

    if method == "GET":
        return make_response("200 OK", render_page())

    if method == "POST":
        if "application/json" in headers.get("content-type", ""):
            try:
                data = json.loads(body)
                error = add_grade(data.get("subject"), data.get("grade"))
            except (json.JSONDecodeError, AttributeError):
                error = "Некорректный JSON"
            if error:
                return make_response("400 Bad Request", json.dumps({"error": error}, ensure_ascii=False),
                                     "application/json; charset=utf-8")
            return make_response("201 Created", json.dumps(grades, ensure_ascii=False),
                                 "application/json; charset=utf-8")

        form = parse_qs(body)
        error = add_grade(form.get("subject", [""])[0], form.get("grade", [""])[0])
        if error:
            return make_response("400 Bad Request", render_page(error))
        # Post/Redirect/Get: после успешного POST возвращаем пользователя на страницу
        return make_response("303 See Other", "", extra_headers={"Location": "/"})

    return make_response("405 Method Not Allowed", "<h1>405 Method Not Allowed</h1>",
                         extra_headers={"Allow": "GET, POST"})


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((HOST, PORT))
        server.listen(5)
        print(f"[Веб-сервер] Открой в браузере http://{HOST}:{PORT}/")

        while True:
            conn, addr = server.accept()
            with conn:
                try:
                    request = recv_request(conn)
                    if request is None:
                        continue
                    method, path, headers, body = request
                    print(f"[Веб-сервер] {addr} {method} {path}")
                    conn.sendall(handle(method, path, headers, body))
                except Exception as e:  # плохой запрос не должен ронять сервер
                    print(f"[Веб-сервер] Ошибка: {e!r}")
                    conn.sendall(make_response("400 Bad Request", "<h1>400 Bad Request</h1>"))


if __name__ == "__main__":
    main()
