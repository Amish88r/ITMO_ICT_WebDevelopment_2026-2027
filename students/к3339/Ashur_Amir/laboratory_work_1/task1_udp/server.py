import socket

HOST, PORT = "127.0.0.1", 9001

with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
    sock.bind((HOST, PORT))
    print(f"[UDP-сервер] Слушаю {HOST}:{PORT}")

    data, addr = sock.recvfrom(1024)
    print(f"[UDP-сервер] Получено от {addr}: {data.decode('utf-8')}")

    sock.sendto("Hello, client".encode("utf-8"), addr)
