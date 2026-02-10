# PeerShare

A peer-to-peer file sharing application with network routing optimization, built as a learning project to explore distributed systems concepts.

## 🚀 PeerShare v1.1 Update (Feb 2026)
This update focuses on swarm stability and high-speed transfers.
- **Dynamic Chunking**: Adjusts chunk size based on file size (up to 8MB) to reduce overhead.
- **High-Backlog Server**: Increased socket listen limit to 100 for simultaneous requests.
- **Network Resilience**: Implemented a 1s retry delay to prevent hanging.
- **Optimized Latency Mapping**: Faster Dijkstra route calculations in `network.py`.

## ✨ Features
- **Peer-to-Peer File Transfer**: Download files from multiple peers simultaneously.
- **Network Mesh Discovery**: Automatic connection via JSON configuration.
- **Dijkstra-Based Routing**: Selects optimal peers based on measured latency.
- **Dynamic Chunking Strategies**:
  - Small (< 100MB): 64 KB
  - Medium (100MB–1GB): 512 KB
  - Large (> 1GB): 2 MB (Up to 8MB in v1.1)
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


## 👥 Contributors
- **Mahathir Mohammad** — Primary development
- **Ahmad Ibrahim Nahian** — Logic refinement and debugging