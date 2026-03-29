# UDP Voting System with SSL/TLS

![Python](https://img.shields.io/badge/Python-3.x-blue) ![SSL](https://img.shields.io/badge/Security-SSL%2FTLS-green) ![TCP](https://img.shields.io/badge/Protocol-TCP-orange) ![Multi-Client](https://img.shields.io/badge/Multi--Client-Supported-brightgreen)

A secure, multi-client real-time voting system built using TCP sockets with SSL/TLS encryption. Supports concurrent voters, duplicate detection, live result broadcasting, and performance benchmarking.

---

## Architecture
```
Client 1 ──┐
Client 2 ──┼──[ SSL/TLS ]──► Server ──► Tally Votes
Client N ──┘                    │
                                └──► Broadcast Results to All Clients
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
| Vote | `client_id\|seq\|option` | Client → Server | Cast a vote for A, B, or C |
| ACK | `ACK\|seq` | Server → Client | Vote accepted |
| NAK | `NAK\|reason` | Server → Client | Vote rejected with reason |
| Result | `RESULT\|A:n\|B:n\|C:n` | Server → All | Live tally broadcast |

---

## Security

- All communication encrypted with **SSL/TLS** using a self-signed certificate
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

---

> **Note:** `certs/server.key` is excluded from version control via `.gitignore` for security.