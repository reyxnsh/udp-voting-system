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
send_lock = threading.Lock()

raw_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
conn = context.wrap_socket(raw_socket, server_hostname=SERVER_IP)
conn.connect((SERVER_IP, SERVER_PORT))
print(f"Connected to server at {SERVER_IP}:{SERVER_PORT} over SSL")

buffer = ""
buffer_lock = threading.Lock()
response_event = threading.Event()
last_response = [""]

def receive_loop():
    global buffer
    while True:
        try:
            data = conn.recv(BUFFER_SIZE)
            if not data:
                break
            with buffer_lock:
                buffer += data.decode()
            while True:
                with buffer_lock:
                    if "\n" not in buffer:
                        break
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
                elif line.startswith(MSG_ACK) or line.startswith(MSG_NAK):
                    last_response[0] = line
                    response_event.set()
        except Exception as e:
            print(f"Receive error: {e}")
            break

def send_vote(vote):
    global seq
    with seq_lock:
        current_seq = seq
    packet = f"{client_id}|{current_seq}|{vote}\n"
    retries = 0
    while retries < MAX_RETRIES:
        try:
            response_event.clear()
            with send_lock:
                conn.sendall(packet.encode())
            print(f"Sending vote (seq {current_seq})...")
            got = response_event.wait(timeout=3)
            if not got:
                print(f"Timeout! Retry {retries+1}/{MAX_RETRIES}...")
                retries += 1
                continue
            response = last_response[0]
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
            print(f"Error: {e}")
        retries += 1
    print("Max retries reached. Vote not sent.")

def vote_loop():
    while True:
        vote = input("Enter vote (A/B/C) or Q to quit: ").strip().upper()
        if vote == "Q":
            conn.close()
            break
        if vote not in ["A", "B", "C"]:
            print("Invalid option.")
            continue
        send_vote(vote)

threading.Thread(target=receive_loop, daemon=True).start()
vote_loop()