import socket
import ssl
import threading
from protocol import SERVER_IP, SERVER_PORT, BUFFER_SIZE, OPTIONS, MSG_ACK, MSG_NAK, MSG_RESULT

votes = {"A": 0, "B": 0, "C": 0}
votes_lock = threading.Lock()
clients = []
clients_lock = threading.Lock()
client_last_seq = {}
seq_lock = threading.Lock()
total_received = 0
valid_votes = 0
stats_lock = threading.Lock()

context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain(certfile="certs/server.crt", keyfile="certs/server.key")

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((SERVER_IP, SERVER_PORT))
server_socket.listen(100)
print(f"Server started on {SERVER_IP}:{SERVER_PORT} with SSL")

def broadcast_results():
    with votes_lock:
        result = f"{MSG_RESULT}|A:{votes['A']}|B:{votes['B']}|C:{votes['C']}\n"
    with clients_lock:
        targets = list(clients)
    for conn in targets:
        try:
            conn.sendall(result.encode())
        except:
            pass

def handle_client(conn, addr):
    global total_received, valid_votes
    print(f"Client connected: {addr}")
    with clients_lock:
        clients.append(conn)
    buffer = ""
    try:
        while True:
            data = conn.recv(BUFFER_SIZE)
            if not data:
                break
            buffer += data.decode()
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()
                if not line:
                    continue
                with stats_lock:
                    total_received += 1
                parts = line.split("|")
                if len(parts) != 3:
                    conn.sendall(f"{MSG_NAK}|FORMAT_ERROR\n".encode())
                    continue
                client_id, seq_str, option = parts
                try:
                    seq = int(seq_str)
                except ValueError:
                    conn.sendall(f"{MSG_NAK}|BAD_SEQ\n".encode())
                    continue
                with seq_lock:
                    last = client_last_seq.get(client_id, -1)
                    if seq <= last:
                        conn.sendall(f"{MSG_ACK}|{seq}\n".encode())
                        continue
                    if option not in OPTIONS:
                        conn.sendall(f"{MSG_NAK}|INVALID_OPTION\n".encode())
                        continue
                    with votes_lock:
                        votes[option] += 1
                    client_last_seq[client_id] = seq
                with stats_lock:
                    valid_votes += 1
                    t = total_received
                    v = valid_votes
                loss = ((t - v) / t) * 100
                print(f"Vote from {client_id}: {option} | Total: {t} Valid: {v} Loss: {loss:.2f}%")
                conn.sendall(f"{MSG_ACK}|{seq}\n".encode())
                broadcast_results()
    except Exception as e:
        print(f"Client {addr} error: {e}")
    finally:
        with clients_lock:
            if conn in clients:
                clients.remove(conn)
        conn.close()
        print(f"Client disconnected: {addr}")

while True:
    try:
        raw_conn, addr = server_socket.accept()
        ssl_conn = context.wrap_socket(raw_conn, server_side=True)
        t = threading.Thread(target=handle_client, args=(ssl_conn, addr))
        t.daemon = True
        t.start()
    except Exception as e:
        print(f"Accept error: {e}")