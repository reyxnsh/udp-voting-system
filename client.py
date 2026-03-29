import socket
import ssl
import threading
from protocol import SERVER_IP, SERVER_PORT, BUFFER_SIZE, MAX_RETRIES, MSG_ACK, MSG_NAK, MSG_RESULT

context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
context.load_verify_locations("certs/server.crt")
context.check_hostname = False

client_id = input("Enter client ID: ")
seq = 1
seq_lock = threading.Lock()

raw_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
conn = context.wrap_socket(raw_socket, server_hostname=SERVER_IP)
conn.connect((SERVER_IP, SERVER_PORT))
print(f"Connected to server at {SERVER_IP}:{SERVER_PORT} over SSL")

def receive_results():
    while True:
        try:
            data = conn.recv(BUFFER_SIZE)
            if not data:
                break
            message = data.decode().strip()
            if message.startswith(MSG_RESULT):
                parts = message.split("|")
                print("\n--- LIVE RESULTS ---")
                for p in parts[1:]:
                    print(p)
                print("--------------------")
                print("Enter vote (A/B/C) or Q to quit: ", end="", flush=True)
        except Exception as e:
            print(f"Receive error: {e}")
            break

def send_vote(vote):
    global seq
    with seq_lock:
        current_seq = seq
    packet = f"{client_id}|{current_seq}|{vote}"
    retries = 0
    while retries < MAX_RETRIES:
        try:
            print(f"Sending vote (seq {current_seq})...")
            conn.sendall(packet.encode())
            data = conn.recv(BUFFER_SIZE)
            if not data:
                print("Server closed connection.")
                return
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
        except Exception as e:
            print(f"Error sending vote: {e}")
        retries += 1
        print(f"Retry {retries}/{MAX_RETRIES}...")
    print("Max retries reached. Vote not sent.")

def vote_loop():
    while True:
        vote = input("Enter vote (A/B/C) or Q to quit: ").strip().upper()
        if vote == "Q":
            print("Exiting.")
            conn.close()
            break
        if vote not in ["A", "B", "C"]:
            print("Invalid option. Choose A, B or C.")
            continue
        send_vote(vote)

threading.Thread(target=receive_results, daemon=True).start()
vote_loop()