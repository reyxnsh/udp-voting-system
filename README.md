# UDP Voting System with SSL/TLS

![Python](https://img.shields.io/badge/Python-3.x-blue) ![SSL](https://img.shields.io/badge/Security-SSL%2FTLS-green) ![UDP](https://img.shields.io/badge/Protocol-UDP-orange) ![Multi-Client](https://img.shields.io/badge/Multi--Client-Supported-brightgreen)

A secure, multi-client real-time voting system using UDP for vote transmission and TCP+SSL for encrypted result broadcasting. Supports concurrent voters, duplicate detection, live result broadcasting, and performance benchmarking.

---

## Architecture
```
Client 1 ──┐                          ┌──► Tally Votes
Client 2 ──┼──[ UDP port 5000 ]──────► Server
Client N ──┘                          └──► Broadcast Results
                                               │
Client 1 ◄─┐                                  │
Client 2 ◄─┼──[ TCP+SSL port 5001 ]───────────┘
Client N ◄─┘
```

---

## File Structure
```
udp-voting-system/
├── server.py       # Accepts clients, validates votes, broadcasts results
├── client.py       # Sends votes, receives live results
├── bench.py        # Simulates N clients, measures performance
├── protocol.py     # Shared constants and message types
├── README.md
├── .gitignore
└── certs/
    └── server.crt  # SSL certificate (key is gitignored)
```

---

## Protocol Design

| Message | Format | Direction | Description |
|---|---|---|---|
| Vote | `client_id\|seq\|option` | Client → Server | Cast a vote for A, B, or C (UDP) |
| ACK | `ACK\|seq` | Server → Client | Vote accepted (UDP) |
| NAK | `NAK\|reason` | Server → Client | Vote rejected with reason (UDP) |
| Result | `RESULT\|A:n\|B:n\|C:n` | Server → All | Live tally broadcast (TCP+SSL) |

> Votes and ACK/NAK travel over UDP (port 5000). Results are broadcast over TCP+SSL (port 5001).

---

## Security

- Vote results broadcast encrypted with **SSL/TLS** over TCP using a self-signed certificate
- Votes transmitted over **UDP** for speed and simplicity
- Duplicate votes detected via per-client sequence numbers
- Invalid options and malformed packets rejected with NAK
- All shared state protected with **threading locks**

---

## Setup

### 1. Install Dependencies
```bash
pip install matplotlib
```

### 2. Generate SSL Certificate
```bash
openssl req -x509 -newkey rsa:2048 -keyout certs/server.key -out certs/server.crt -days 365 -nodes -subj "/CN=localhost"
```

### 3. Run the Server
```bash
python server.py
```

### 4. Run a Client (new terminal)
```bash
python client.py
```

### 5. Run Performance Benchmark (server must be running)
```bash
python bench.py
```

---

## Voting Options

| Key | Action |
|---|---|
| `A` | Vote for option A |
| `B` | Vote for option B |
| `C` | Vote for option C |
| `Q` | Quit the client |

---

## Performance Evaluation

`bench.py` tests with 1, 5, 10, 20, and 50 concurrent clients and outputs:

- `results.csv` — raw metrics per client count
- `perf_graphs.png` — throughput, latency, and packet loss graphs

## Performance Observations

| Clients | Throughput | Avg Latency | Loss |
|---|---|---|---|
| 1 | 15.78 votes/sec | 57.87ms | 0% |
| 5 | 8.90 votes/sec | 482.40ms | 0% |
| 10 | 5.76 votes/sec | 1526.44ms | 0% |
| 20 | 4.80 votes/sec | 1169.52ms | 0% |
| 50 | 4.23 votes/sec | 1531.39ms | 33% |

Throughput decreases as concurrent clients increase, demonstrating UDP's connectionless nature — packets from multiple clients contend for the same server socket. Latency rises significantly under load due to UDP having no flow control or congestion management. Packet loss appears at 50 concurrent clients (33%), which is expected UDP behavior under high contention on a single machine. In a production environment this would be mitigated with load balancing and receive buffer tuning.

---

> **Note:** `certs/server.key` is excluded from version control via `.gitignore` for security.