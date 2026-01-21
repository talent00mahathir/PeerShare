# PeerShare


# PeerShare
===

# A peer-to-peer file sharing application with network routing optimization, built as a learning project to explore distributed systems concepts.

# 

# \## 📋 Overview

# PeerShare is a Python-based P2P file transfer system that allows multiple peers to collaboratively share files across a local network. The system uses Dijkstra's algorithm for peer selection and implements dynamic chunking strategies based on file size.

# 

# \## ✨ What It Does

# \* \*\*Peer-to-Peer File Transfer\*\* - Download files from multiple peers simultaneously in a swarm-like fashion

# \* \*\*Network Mesh Discovery\*\* - Automatically discovers and connects to peers via JSON configuration

# \* \*\*Dijkstra-Based Routing\*\* - Selects optimal peers using shortest-path algorithms based on measured latency

# \* \*\*Dynamic Chunking\*\* - Adjusts chunk sizes automatically:

# &nbsp; - Small files (<100MB): 64 KB chunks

# &nbsp; - Medium files (100MB-1GB): 512 KB chunks  

# &nbsp; - Large files (>1GB): 2 MB chunks

# \* \*\*GUI Network Manager\*\* - Launch and monitor multiple peers with a graphical interface

# \* \*\*Live Transfer Monitoring\*\* - Real-time console logs showing chunk downloads and peer contributions

# 

# \## 🛠️ Built With

# \* \*\*Python 3\*\* - Core language

# \* \*\*Tkinter\*\* - GUI framework

# \* \*\*Socket Programming\*\* - Network communication

# \* \*\*Threading\*\* - Concurrent chunk downloads

# \* \*\*JSON\*\* - Network configuration

# 

# \## 🚀 How to Run

# 1\. Launch the network manager:

# &nbsp;  ```bash

# &nbsp;  python main.py

# &nbsp;  ```

# 2\. Configure the number of peers and select a file to share

# 3\. Choose which peers start with the file (seeders)

# 4\. Click "Launch Network Environment"

# 5\. Use the peer GUIs to initiate swarm downloads

# 

# \## 📁 Project Structure

# ```

# ├── main.py          # Network launcher GUI

# ├── gui.py           # Individual peer interface

# ├── peer.py          # Core P2P logic and swarm download

# ├── network.py       # Network graph and latency measurement

# ├── dijkstra.py      # Shortest path algorithm

# └── network\_config.json  # Auto-generated peer mesh config

# ```

# 

# \## 🎯 Learning Outcomes

# This project helped me understand:

# \- Socket programming and TCP communication

# \- Multi-threaded file transfers

# \- Network graph algorithms (Dijkstra)

# \- GUI development with Tkinter

# \- File I/O and chunked data handling

# 

# \## 🔧 Future Improvements

# \* Error recovery for incomplete downloads

# \* Support for resume/pause functionality

# \* NAT traversal for internet-wide P2P

# \* Encrypted peer communication

# \* More sophisticated peer selection (availability, bandwidth)

# \* Better handling of peer disconnections mid-transfer

# 

# \## 👥 Contributors

# \* \*\***Mahathir Mohammad**\*\* - Primary development

# \* \*\***Ahmad Ibrahim Nahian**\*\* - Logic refinement and debugging

# 

# 

