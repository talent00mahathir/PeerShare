import socket
import threading
import os
import sys
import time
import queue
import json
from network import NetworkManager

BUFFER_SIZE = 32768  

class Peer:
    def __init__(self, name, port, storage_folder, ip='127.0.0.1'):
        self.name = name
        self.port = int(port)
        self.storage_folder = storage_folder
        self.ip = ip
        
        # Track what chunks other peers have: { 'PeerName': set([0, 1]) or 'ALL' }
        self.remote_chunks = {}
        
        if not os.path.exists(storage_folder):
            os.makedirs(storage_folder)

        self.network = NetworkManager()
        self.network.add_peer(self.name, self.ip, self.port)
        
        self.load_network_config()
        self.running = True

    def load_network_config(self):
        config_path = "network_config.json"
        for _ in range(5):
            if os.path.exists(config_path): break
            time.sleep(0.5)

        try:
            with open(config_path, 'r') as f:
                peers_list = json.load(f)
            count = 0
            for p in peers_list:
                if p['name'] != self.name:
                    self.network.add_peer(p['name'], p['ip'], int(p['port']))
                    count += 1
            print(f"[{self.name}] ✅ Mesh link: {count} peers discovered.")
        except Exception as e:
            print(f"[{self.name}] ⚠️ Config error: {e}")

    def start(self):
        server_thread = threading.Thread(target=self._listen_for_connections)
        server_thread.daemon = True
        server_thread.start()
        print(f"[{self.name}] Online at {self.ip}:{self.port}")

    def _listen_for_connections(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            server_socket.bind((self.ip, self.port))
            server_socket.listen(100) # Increased backlog
            while self.running:
                client_socket, addr = server_socket.accept()
                threading.Thread(target=self._handle_client, args=(client_socket,)).start()
        except OSError as e:
            print(f"[{self.name}] Server Error: {e}")
        finally:
            server_socket.close()

    def _handle_client(self, client_socket):
        try:
            request_data = client_socket.recv(1024).decode('utf-8')
            if not request_data: return
            
            parts = request_data.split('|')
            cmd = parts[0]

            if cmd == '__PING__':
                client_socket.sendall(b'__PONG__')
                return

            if cmd == 'HAVE':
                # Dynamic update from leechers
                p_name, c_idx = parts[3], int(parts[2])
                if p_name not in self.remote_chunks: self.remote_chunks[p_name] = set()
                if self.remote_chunks[p_name] != 'ALL':
                    self.remote_chunks[p_name].add(c_idx)
                return

            if cmd == 'SIZE':
                filename = parts[1]
                size = self._get_file_size(filename)
                client_socket.sendall(str(size).encode())
                return

            if cmd == 'TRANSFER':
                target_peer, filename, start, length = parts[1], parts[2], int(parts[3]), int(parts[4])
                if target_peer == self.name:
                    self._send_file_content(client_socket, filename, start, length)
                else:
                    self._relay_file_content(client_socket, target_peer, filename, start, length)
        except Exception:
            pass
        finally:
            client_socket.close()

    def _get_file_size(self, filename):
        p1 = os.path.join(self.storage_folder, filename)
        p2 = os.path.join(self.storage_folder, f"downloaded_{filename}")
        if os.path.exists(p1): return os.path.getsize(p1)
        if os.path.exists(p2): return os.path.getsize(p2)
        return -1

    def _send_file_content(self, client_socket, filename, start, length):
        p1 = os.path.join(self.storage_folder, filename)
        p2 = os.path.join(self.storage_folder, f"downloaded_{filename}")
        filepath = p1 if os.path.exists(p1) else (p2 if os.path.exists(p2) else None)
        
        if filepath:
            client_socket.sendall(b'OK')
            with open(filepath, 'rb') as f:
                f.seek(start)
                total_sent = 0
                while total_sent < length:
                    chunk = f.read(min(BUFFER_SIZE, length - total_sent))
                    if not chunk: break
                    client_socket.sendall(chunk)
                    total_sent += len(chunk)
        else:
            client_socket.sendall(b'ERROR: File not found')

    def _relay_file_content(self, client_socket, target_peer, filename, start, length):
        if target_peer not in self.network.peers: return
        host, port = self.network.peers[target_peer]
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect((host, port))
            s.sendall(f"TRANSFER|{target_peer}|{filename}|{start}|{length}".encode())
            if b'OK' in s.recv(1024):
                client_socket.sendall(b'OK')
                relayed = 0
                while relayed < length:
                    data = s.recv(BUFFER_SIZE)
                    if not data: break
                    client_socket.sendall(data)
                    relayed += len(data)
        except: pass
        finally: s.close()

    def broadcast_have(self, filename, chunk_index):
        for p_name, (host, port) in self.network.peers.items():
            if p_name == self.name: continue
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.5)
                s.connect((host, port))
                s.sendall(f"HAVE|{filename}|{chunk_index}|{self.name}".encode())
                s.close()
            except: pass

    def swarm_download(self, filename, seeder_list):
        print(f"[{self.name}] 🚀 Initiating Swarm for '{filename}'")
        
        file_size = 0
        for peer in seeder_list:
            if peer == self.name: continue
            try:
                host, port = self.network.peers[peer]
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(2); s.connect((host, port))
                s.sendall(f"SIZE|{filename}".encode())
                resp = int(s.recv(1024).decode())
                s.close()
                if resp > 0:
                    file_size = resp
                    self.remote_chunks[peer] = 'ALL'
                    print(f"[{self.name}] 📄 Metadata from {peer}: {file_size} bytes")
                else:
                    self.remote_chunks[peer] = set()
            except: continue

        if file_size <= 0: return

        save_path = os.path.join(self.storage_folder, f"downloaded_{filename}")
        with open(save_path, 'wb') as f:
            f.seek(file_size - 1); f.write(b'\0')

        # Dynamic chunk sizing
        if file_size < 100 * 1024 * 1024:
            chunk_size = 512 * 1024
        elif file_size < 1024 * 1024 * 1024:
            chunk_size = 2 * 1024 * 1024
        else:
            chunk_size = 8 * 1024 * 1024

        num_pieces = (file_size + chunk_size - 1) // chunk_size
        print(f"[{self.name}] 🔢 Total Chunks: {num_pieces}")

        job_queue = queue.Queue()
        for i in range(num_pieces):
            job_queue.put((i, i * chunk_size, min(chunk_size, file_size - i * chunk_size)))

        stats = {p: 0 for p in seeder_list if p != self.name}
        file_lock = threading.Lock()
        threads = []
        start_time = time.time()
        
        for peer in seeder_list:
            if peer != self.name:
                t = threading.Thread(target=self._peer_worker, args=(peer, filename, job_queue, file_lock, stats, chunk_size))
                t.start()
                threads.append(t)
            
        job_queue.join()
        
        # Restoration of detailed technical summary
        duration = time.time() - start_time
        print("\n" + "="*40)
        print(f"   🎉 DOWNLOAD COMPLETE in {duration:.2f}s")
        print("="*40)
        print(f"{'Source Name':<15} | {'Bytes Sent':<12} | {'Chunks':<6}")
        print("-" * 40)
        
        total_bytes = 0
        for p, b_sent in stats.items():
            c_sent = (b_sent + chunk_size - 1) // chunk_size if b_sent > 0 else 0
            print(f"{p:<15} | {b_sent:<12} | {c_sent:<6}")
            total_bytes += b_sent
            
        print("-" * 40)
        print(f"Total Received: {total_bytes} bytes")
        print("="*40 + "\n")

    def _peer_worker(self, peer, filename, job_queue, file_lock, stats, chunk_size):
        while not job_queue.empty():
            try:
                c_idx, start, length = job_queue.get(timeout=1)
            except queue.Empty: break

            # Availability verification
            peer_has_it = (peer in self.remote_chunks and (self.remote_chunks[peer] == 'ALL' or c_idx in self.remote_chunks[peer]))
            
            if not peer_has_it:
                job_queue.put((c_idx, start, length))
                job_queue.task_done()
                time.sleep(1.0)
                continue

            success = False
            try:
                host, port = self.network.peers[peer]
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(5); s.connect((host, port))
                s.sendall(f"TRANSFER|{peer}|{filename}|{start}|{length}".encode())
                
                if b'OK' in s.recv(1024):
                    data = b""
                    while len(data) < length:
                        pkt = s.recv(BUFFER_SIZE)
                        if not pkt: break
                        data += pkt
                    
                    if len(data) == length:
                        with file_lock:
                            with open(os.path.join(self.storage_folder, f"downloaded_{filename}"), 'r+b') as f:
                                f.seek(start); f.write(data)
                        
                        stats[peer] += length
                        success = True
                        # Restored live chunk logging
                        print(f"[{self.name}] ✅ Chunk {c_idx + 1} from {peer}")
                        threading.Thread(target=self.broadcast_have, args=(filename, c_idx)).start()
                s.close()
            except: pass

            if success:
                job_queue.task_done()
            else:
                job_queue.put((c_idx, start, length))
                job_queue.task_done()
                time.sleep(0.5)