# PeerShare

A peer-to-peer file sharing application with network routing optimization, built as a learning project to explore distributed systems concepts.

## 🚀 PeerShare v1.1 — The "Dynamic Swarm" Update (11 Feb, 2026)

This major update transforms **PeerShare** from a static client-server model into a fully decentralized, availability-aware swarm network. Peers now dynamically trade file chunks in real-time, significantly increasing transfer efficiency across the LAN.

### 🛠 Swarm Intelligence & Efficiency
* **HAVE Protocol (Bitfield Tracking):** Implemented real-time availability maps where peers broadcast a `HAVE` message as soon as they finish a chunk, allowing others to download from them immediately.
* **Hybrid Peer Roles:** The system now identifies **Seeders** and **Leechers** during the initial handshake, allowing leechers to act as data sources the moment they acquire a piece.
* **Intelligent Worker Threads:** Workers perform an **Availability Check** before requesting data, preventing "Empty Peer Deadlocks" by skipping peers that do not yet possess the required chunk.
* **Dynamic Chunking:** Automatically adjusts chunk sizes—512KB for small files, 2MB for medium, and 8MB for large files—to minimize connection overhead.

### ⚡ Performance & Resilience
* **High-Backlog Server:** Increased the socket listen limit to 100, allowing peers to handle rapid, simultaneous chunk requests without dropping connections.
* **Latency-Optimized Routing:** Streamlined `network.py` to provide faster shortest-path calculations using Dijkstra's algorithm based on real-time LAN latency.
* **Network Resilience:** Added a 1s retry delay and CPU backoff logic to prevent worker threads from hanging or spiking CPU during high-traffic transfers.
* **Auto-Sync GUI:** The interface now re-loads the network configuration on every download start, ensuring newly joined peers are instantly integrated into the swarm.

## ✨ Features
- **Peer-to-Peer File Transfer**: Download files from multiple peers simultaneously.
- **Network Mesh Discovery**: Automatic connection via JSON configuration.
- **Dijkstra-Based Routing**: Selects optimal peers based on measured latency.
- **Dynamic Chunking Strategies**:
  - Small (< 100MB): 512 KB
  - Medium (100MB–1GB): 2 MB
  - Large (> 1GB): 8 MB
- **GUI & Monitoring**: Tkinter-based manager with live console logs.

## 🛠️ Built With
* **Python 3**
* **Tkinter** (GUI framework)
* **Socket Programming** (Network communication)
* **Threading** (Concurrent chunk downloads)
* **JSON** (Network configuration)

## 🚀 How to Run
1. **Launch the manager**: `python main.py`
2. **Configure**: Set the number of peers and select a file.
3. **Seed**: Choose which peers start with the file.
4. **Deploy**: Click "Launch Network Environment."
5. **Download**: Use the peer GUIs to start the swarm.

## 📁 Project Structure
```text
├── main.py          # Network launcher GUI
├── gui.py           # Individual peer interface
├── peer.py          # Core P2P logic and swarm download
├── network.py       # Network graph and latency measurement
├── dijkstra.py      # Shortest path algorithm
└── network_config.json  # Auto-generated peer mesh config
```

## 🔧 Beginner-Friendly Update Checklist :
- Replace silent `except: pass` blocks with clear error messages.
- Move hardcoded values (ports, delays, chunk sizes) into one config section.
- Add a clean stop/shutdown flow so sockets and threads close properly.
- Split long methods (like `swarm_download`) into smaller helper functions.
- Add basic input checks in GUI fields (file name, peer list, IP, port).
- Use simple logging levels (`INFO`, `WARNING`, `ERROR`) instead of only `print`.
- Keep README values synced with real code behavior when logic changes.
- Add a few starter tests (e.g., Dijkstra path and chunk size selection).

## 👥 Contributors
- **Mahathir Mohammad** — Primary development
- **Ahmad Ibrahim Nahian** — Logic refinement and debugging

## 📋 Prerequisites
- Python 3.8+
- `tkinter` (usually comes with Python, but may need `sudo apt-get install python3-tk` on Linux)
