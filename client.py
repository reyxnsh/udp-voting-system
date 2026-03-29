import socket
import ssl
import threading
from protocol import SERVER_IP, UDP_PORT, TCP_PORT, BUFFER_SIZE, MAX_RETRIES, MSG_ACK, MSG_NAK, MSG_RESULT

# UDP socket for sending votes
udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_socket.settimeout(2)

# TCP+SSL socket for receiving results
ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
ssl_context.load_verify_locations("certs/server.crt")
ssl_context.check_hostname = False
raw_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcp_conn = ssl_context.wrap_socket(raw_tcp, server_hostname=SERVER_IP)
tcp_conn.connect((SERVER_IP, TCP_PORT))
print(f"Connected to server at {SERVER_IP} over SSL (TCP:{TCP_PORT} UDP:{UDP_PORT})")

client_id = input("Enter client ID: ")
seq = 1
seq_lock = threading.Lock()

def receive_results():
    buffer = ""
    while True:
        try:
            data = tcp_conn.recv(BUFFER_SIZE)
            if not data:
                break
            buffer += data.decode()
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()
                if not line:
                    continue
                if line.startswith(MSG_RESULT):
                    parts = line.split("|")
                    print("\n--- LIVE RESULTS ---")
                    for p in parts[1:]:
                        print(p)
                    print("--------------------")
                    print("Enter vote (A/B/C) or Q to quit: ", end="", flush=True)
        except Exception as e:
            print(f"Result receive error: {e}")
            break

def send_vote(vote):
    global seq
    with seq_lock:
        current_seq = seq
    packet = f"{client_id}|{current_seq}|{vote}"
    for retry in range(MAX_RETRIES):
        try:
            print(f"Sending vote over UDP (seq {current_seq})...")
            udp_socket.sendto(packet.encode(), (SERVER_IP, UDP_PORT))
            data, _ = udp_socket.recvfrom(BUFFER_SIZE)
            response = data.decode().strip()
            if response.startswith(MSG_ACK):
                ack_seq = int(response.split("|")[1])
                if ack_seq == current_seq:
                    print("Vote acknowledged.")
                    with seq_lock:
                        seq += 1
                    return
            elif response.startswith(MSG_NAK):
                reason = response.split("|")[1] if "|" in response else "unknown"
                print(f"Vote rejected: {reason}")
                return
        except socket.timeout:
            print(f"Timeout! Retry {retry+1}/{MAX_RETRIES}...")
        except Exception as e:
            print(f"Error: {e}")
    print("Max retries reached. Vote not sent.")

def vote_loop():
    while True:
        vote = input("Enter vote (A/B/C) or Q to quit: ").strip().upper()
        if vote == "Q":
            tcp_conn.close()
            udp_socket.close()
            break
        if vote not in ["A", "B", "C"]:
            print("Invalid option.")
            continue
        send_vote(vote)

threading.Thread(target=receive_results, daemon=True).start()
vote_loop()