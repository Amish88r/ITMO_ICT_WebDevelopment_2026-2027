import socket
import threading

HOST, PORT = "127.0.0.1", 9004

clients = {}  # имя -> файловый объект сокета
clients_lock = threading.Lock()


def broadcast(text, exclude=None):
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
