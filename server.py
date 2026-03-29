import socket
import ssl
import threading
from protocol import SERVER_IP, UDP_PORT, TCP_PORT, BUFFER_SIZE, OPTIONS, MSG_ACK, MSG_NAK, MSG_RESULT

votes = {"A": 0, "B": 0, "C": 0}
votes_lock = threading.Lock()
tcp_clients = []
tcp_clients_lock = threading.Lock()
client_last_seq = {}
seq_lock = threading.Lock()
total_received = 0
valid_votes = 0
stats_lock = threading.Lock()

# UDP socket for receiving votes
udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_socket.bind((SERVER_IP, UDP_PORT))
print(f"UDP server listening on {SERVER_IP}:{UDP_PORT}")

# TCP+SSL socket for broadcasting results
ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ssl_context.load_cert_chain(certfile="certs/server.crt", keyfile="certs/server.key")
tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
tcp_socket.bind((SERVER_IP, TCP_PORT))
tcp_socket.listen(100)
print(f"TCP+SSL server listening on {SERVER_IP}:{TCP_PORT}")

def broadcast_results():
    with votes_lock:
        result = f"{MSG_RESULT}|A:{votes['A']}|B:{votes['B']}|C:{votes['C']}\n"
    with tcp_clients_lock:
        targets = list(tcp_clients)
    for conn in targets:
        try:
            conn.sendall(result.encode())
        except:
            with tcp_clients_lock:
                if conn in tcp_clients:
                    tcp_clients.remove(conn)

def send_ack_nak(msg, addr):
    try:
        udp_socket.sendto(msg.encode(), addr)
    except Exception as e:
        print(f"Error sending to {addr}: {e}")

def handle_udp_votes():
    global total_received, valid_votes
    print("UDP vote receiver started")
    while True:
        try:
            data, addr = udp_socket.recvfrom(BUFFER_SIZE)
            with stats_lock:
                total_received += 1
            message = data.decode().strip()
            parts = message.split("|")
            if len(parts) != 3:
                send_ack_nak(f"{MSG_NAK}|FORMAT_ERROR", addr)
                continue
            client_id, seq_str, option = parts
            try:
                seq = int(seq_str)
            except ValueError:
                send_ack_nak(f"{MSG_NAK}|BAD_SEQ", addr)
                continue
            with seq_lock:
                last = client_last_seq.get(client_id, -1)
                if seq <= last:
                    send_ack_nak(f"{MSG_ACK}|{seq}", addr)
                    continue
                if option not in OPTIONS:
                    send_ack_nak(f"{MSG_NAK}|INVALID_OPTION", addr)
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
            send_ack_nak(f"{MSG_ACK}|{seq}", addr)
            broadcast_results()
        except Exception as e:
            print(f"UDP error: {e}")

def handle_tcp_client(conn, addr):
    print(f"TCP+SSL client connected: {addr}")
    with tcp_clients_lock:
        tcp_clients.append(conn)
    try:
        while True:
            data = conn.recv(BUFFER_SIZE)
            if not data:
                break
    except Exception as e:
        print(f"TCP client {addr} error: {e}")
    finally:
        with tcp_clients_lock:
            if conn in tcp_clients:
                tcp_clients.remove(conn)
        conn.close()
        print(f"TCP+SSL client disconnected: {addr}")

def accept_tcp_clients():
    print("TCP+SSL accept loop started")
    while True:
        try:
            raw_conn, addr = tcp_socket.accept()
            ssl_conn = ssl_context.wrap_socket(raw_conn, server_side=True)
            t = threading.Thread(target=handle_tcp_client, args=(ssl_conn, addr))
            t.daemon = True
            t.start()
        except Exception as e:
            print(f"TCP accept error: {e}")

threading.Thread(target=handle_udp_votes, daemon=True).start()
threading.Thread(target=accept_tcp_clients, daemon=True).start()

print("Server running. Press Ctrl+C to stop.")
try:
    while True:
        pass
except KeyboardInterrupt:
    print("Server shutting down.")
    udp_socket.close()
    tcp_socket.close()