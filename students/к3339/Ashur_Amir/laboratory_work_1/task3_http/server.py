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
