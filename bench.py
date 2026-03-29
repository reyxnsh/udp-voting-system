import socket
import ssl
import threading
import time
import csv
import matplotlib.pyplot as plt
from protocol import SERVER_IP, UDP_PORT, TCP_PORT, BUFFER_SIZE, MAX_RETRIES, MSG_ACK, MSG_NAK, MSG_RESULT

results = []
results_lock = threading.Lock()

ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
ssl_context.load_verify_locations("certs/server.crt")
ssl_context.check_hostname = False

def simulate_client(client_id, num_votes):
    latencies = []
    success = 0
    failed = 0

    # UDP socket for votes
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.settimeout(3)

    # TCP+SSL socket for results
    try:
        raw_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_conn = ssl_context.wrap_socket(raw_tcp, server_hostname=SERVER_IP)
        tcp_conn.connect((SERVER_IP, TCP_PORT))
        tcp_conn.settimeout(3)
    except Exception as e:
        print(f"Client {client_id} TCP connect failed: {e}")
        with results_lock:
            results.append({"client_id": client_id, "success": 0, "failed": num_votes,
                            "avg_latency_ms": 0, "min_latency_ms": 0, "max_latency_ms": 0})
        return

    # drain results in background
    def drain_tcp():
        try:
            while True:
                data = tcp_conn.recv(BUFFER_SIZE)
                if not data:
                    break
        except:
            pass
    threading.Thread(target=drain_tcp, daemon=True).start()

    seq = 1
    options = ["A", "B", "C"]
    for i in range(num_votes):
        vote = options[i % 3]
        packet = f"{client_id}|{seq}|{vote}"
        sent = False
        for retry in range(MAX_RETRIES):
            try:
                start = time.time()
                udp_sock.sendto(packet.encode(), (SERVER_IP, UDP_PORT))
                data, _ = udp_sock.recvfrom(BUFFER_SIZE)
                end = time.time()
                response = data.decode().strip()
                if response.startswith(MSG_ACK):
                    latencies.append((end - start) * 1000)
                    success += 1
                    seq += 1
                    sent = True
                    break
                elif response.startswith(MSG_NAK):
                    failed += 1
                    sent = True
                    break
            except socket.timeout:
                continue
            except Exception as e:
                break
        if not sent:
            failed += 1

    try:
        tcp_conn.close()
    except:
        pass
    udp_sock.close()

    with results_lock:
        results.append({
            "client_id": client_id,
            "success": success,
            "failed": failed,
            "avg_latency_ms": round(sum(latencies) / len(latencies), 2) if latencies else 0,
            "min_latency_ms": round(min(latencies), 2) if latencies else 0,
            "max_latency_ms": round(max(latencies), 2) if latencies else 0,
        })

def run_benchmark(num_clients, num_votes=10):
    global results
    results = []
    threads = []
    print(f"Running benchmark: {num_clients} clients x {num_votes} votes each")
    start = time.time()
    for i in range(num_clients):
        t = threading.Thread(target=simulate_client, args=(f"bench_{num_clients}_{i}", num_votes))
        threads.append(t)
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    end = time.time()
    total_time = end - start
    total_success = sum(r["success"] for r in results)
    total_failed = sum(r["failed"] for r in results)
    total_votes = total_success + total_failed
    throughput = total_success / total_time if total_time > 0 else 0
    avg_lat = sum(r["avg_latency_ms"] for r in results) / len(results) if results else 0
    loss = (total_failed / total_votes * 100) if total_votes > 0 else 0
    print(f"  Done | Throughput: {throughput:.2f} votes/sec | Avg latency: {avg_lat:.2f}ms | Loss: {loss:.2f}%")
    return {
        "num_clients": num_clients,
        "throughput": round(throughput, 2),
        "avg_latency_ms": round(avg_lat, 2),
        "packet_loss_pct": round(loss, 2),
        "total_time": round(total_time, 2)
    }

def save_csv(data, filename="results.csv"):
    with open(filename, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    print(f"Results saved to {filename}")

def plot_graphs(data):
    clients = [d["num_clients"] for d in data]
    throughput = [d["throughput"] for d in data]
    latency = [d["avg_latency_ms"] for d in data]
    loss = [d["packet_loss_pct"] for d in data]
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    fig.suptitle("Voting System - Performance Evaluation", fontsize=14)
    axes[0].plot(clients, throughput, marker="o", color="green")
    axes[0].set_title("Throughput vs Clients")
    axes[0].set_xlabel("Number of Clients")
    axes[0].set_ylabel("Votes/sec")
    axes[0].grid(True)
    axes[1].plot(clients, latency, marker="o", color="blue")
    axes[1].set_title("Avg Latency vs Clients")
    axes[1].set_xlabel("Number of Clients")
    axes[1].set_ylabel("Latency (ms)")
    axes[1].grid(True)
    axes[2].plot(clients, loss, marker="o", color="red")
    axes[2].set_title("Packet Loss vs Clients")
    axes[2].set_xlabel("Number of Clients")
    axes[2].set_ylabel("Loss (%)")
    axes[2].grid(True)
    plt.tight_layout()
    plt.savefig("perf_graphs.png")
    print("Graphs saved to perf_graphs.png")
    plt.show()

if __name__ == "__main__":
    client_counts = [1, 5, 10, 20, 50]
    benchmark_data = []
    for n in client_counts:
        row = run_benchmark(num_clients=n, num_votes=10)
        benchmark_data.append(row)
        time.sleep(2)
    save_csv(benchmark_data)
    plot_graphs(benchmark_data)