<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>UDP Voting System</title>
<style>
  body { font-family: Arial, sans-serif; max-width: 860px; margin: 40px auto; padding: 0 20px; color: #222; }
  h1 { border-bottom: 2px solid #333; padding-bottom: 8px; }
  h2 { margin-top: 36px; border-left: 4px solid #0077cc; padding-left: 10px; }
  code { background: #f4f4f4; padding: 2px 6px; border-radius: 4px; font-size: 0.9em; }
  pre { background: #f4f4f4; padding: 14px; border-radius: 6px; overflow-x: auto; }
  table { border-collapse: collapse; width: 100%; margin-top: 10px; }
  th { background: #0077cc; color: white; padding: 8px 12px; text-align: left; }
  td { padding: 8px 12px; border-bottom: 1px solid #ddd; }
  tr:hover { background: #f9f9f9; }
  .badge { display: inline-block; background: #0077cc; color: white; padding: 3px 10px; border-radius: 12px; font-size: 0.8em; margin-right: 6px; }
  .warn { background: #fff3cd; border-left: 4px solid #ffc107; padding: 10px 14px; border-radius: 4px; }
</style>
</head>
<body>

<h1>UDP Voting System with SSL/TLS</h1>
<span class="badge">Python</span>
<span class="badge">TCP + SSL</span>
<span class="badge">Multi-Client</span>
<span class="badge">Real-Time</span>

<p>A secure, multi-client real-time voting system built using TCP sockets with SSL/TLS encryption. Supports concurrent voters, duplicate detection, live result broadcasting, and performance benchmarking.</p>

<h2>Architecture</h2>
<pre>
  Client 1 ──┐
  Client 2 ──┼──[ SSL/TLS ]──► Server ──► Tally Votes
  Client N ──┘                    │
                                  └──► Broadcast Results to All Clients
</pre>

<table>
  <tr><th>Component</th><th>Role</th></tr>
  <tr><td><code>server.py</code></td><td>Accepts clients, validates votes, broadcasts results</td></tr>
  <tr><td><code>client.py</code></td><td>Sends votes, receives live results</td></tr>
  <tr><td><code>bench.py</code></td><td>Simulates N clients, measures performance</td></tr>
  <tr><td><code>protocol.py</code></td><td>Shared constants and message types</td></tr>
  <tr><td><code>certs/</code></td><td>SSL certificate and private key</td></tr>
</table>

<h2>Protocol Design</h2>
<table>
  <tr><th>Message</th><th>Format</th><th>Direction</th><th>Description</th></tr>
  <tr><td>Vote</td><td><code>client_id|seq|option</code></td><td>Client → Server</td><td>Cast a vote for A, B, or C</td></tr>
  <tr><td>ACK</td><td><code>ACK|seq</code></td><td>Server → Client</td><td>Vote accepted</td></tr>
  <tr><td>NAK</td><td><code>NAK|reason</code></td><td>Server → Client</td><td>Vote rejected with reason</td></tr>
  <tr><td>Result</td><td><code>RESULT|A:n|B:n|C:n</code></td><td>Server → All</td><td>Live tally broadcast</td></tr>
</table>

<h2>Security</h2>
<ul>
  <li>All communication encrypted with <strong>SSL/TLS</strong> using a self-signed certificate</li>
  <li>Duplicate votes detected via per-client sequence numbers</li>
  <li>Invalid options and malformed packets rejected with NAK</li>
  <li>All shared state protected with <strong>threading locks</strong></li>
</ul>

<h2>Setup</h2>

<h3>1. Install Dependencies</h3>
<pre>pip install matplotlib</pre>

<h3>2. Generate SSL Certificate</h3>
<pre>openssl req -x509 -newkey rsa:2048 -keyout certs\server.key -out certs\server.crt -days 365 -nodes -subj "/CN=localhost"</pre>

<h3>3. Run the Server</h3>
<pre>python server.py</pre>

<h3>4. Run a Client (in a new terminal)</h3>
<pre>python client.py</pre>

<h3>5. Run Performance Benchmark (server must be running)</h3>
<pre>python bench.py</pre>

<h2>Voting Options</h2>
<table>
  <tr><th>Key</th><th>Action</th></tr>
  <tr><td><code>A</code></td><td>Vote for option A</td></tr>
  <tr><td><code>B</code></td><td>Vote for option B</td></tr>
  <tr><td><code>C</code></td><td>Vote for option C</td></tr>
  <tr><td><code>Q</code></td><td>Quit the client</td></tr>
</table>

<h2>Performance Evaluation</h2>
<p>Run <code>bench.py</code> with the server active. It tests with 1, 5, 10, 20, and 50 concurrent clients and outputs:</p>
<ul>
  <li><code>results.csv</code> — raw metrics per client count</li>
  <li><code>perf_graphs.png</code> — throughput, latency, and packet loss graphs</li>
</ul>

<h2>File Structure</h2>
<pre>
udp-voting-system/
├── server.py
├── client.py
├── bench.py
├── protocol.py
├── README.md
├── .gitignore
└── certs/
    ├── server.crt
    └── server.key
</pre>

<div class="warn">
  <strong>Note:</strong> <code>certs/server.key</code> is excluded from version control via <code>.gitignore</code> for security.
</div>

</body>
</html>