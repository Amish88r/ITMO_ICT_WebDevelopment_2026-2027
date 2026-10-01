import socket

HOST, PORT = "127.0.0.1", 9001

with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
    sock.settimeout(5)  
    sock.sendto("Hello, server".encode("utf-8"), (HOST, PORT))

    try:
        data, _ = sock.recvfrom(1024)
        print(f"[UDP-клиент] Получено: {data.decode('utf-8')}")
    except (socket.timeout, ConnectionError):
        print("[UDP-клиент] Ответ не получен. Запущен ли server.py?")
