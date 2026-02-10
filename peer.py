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
            print(f"[{self.name}] ✅ Connected to mesh: {count} peers.")
        except Exception as e:
            print(f"[{self.name}] ⚠️ Config load error: {e}")

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
            # FIX: Increased backlog from 15 to 100 to handle rapid chunk requests
            server_socket.listen(100) 
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
            if request_data == '__PING__':
                client_socket.sendall(b'__PONG__')
                return

            parts = request_data.split('|')
            if parts[0] == 'SIZE':
                filename = parts[1]
                size = self._get_file_size(filename)
                client_socket.sendall(str(size).encode())
                return

            if parts[0] == 'TRANSFER':
                target_peer = parts[1]
                filename = parts[2]
                start_byte = int(parts[3])
                length = int(parts[4])

                if target_peer == self.name:
                    self._send_file_content(client_socket, filename, start_byte, length)
                else:
                    self._relay_file_content(client_socket, target_peer, filename, start_byte, length)
        except Exception:
            pass
        finally:
            client_socket.close()

    def _get_file_size(self, filename):
        path1 = os.path.join(self.storage_folder, filename)
        if os.path.exists(path1): return os.path.getsize(path1)
        
        path2 = os.path.join(self.storage_folder, f"downloaded_{filename}")
        if os.path.exists(path2): return os.path.getsize(path2)
        return -1

    def _send_file_content(self, client_socket, filename, start_byte, length):
        path1 = os.path.join(self.storage_folder, filename)
        path2 = os.path.join(self.storage_folder, f"downloaded_{filename}")
        filepath = path1 if os.path.exists(path1) else (path2 if os.path.exists(path2) else None)
        
        if filepath:
            client_socket.sendall(b'OK')
            with open(filepath, 'rb') as f:
                f.seek(start_byte)
                bytes_to_send = length
                total_sent = 0
                while total_sent < bytes_to_send:
                    read_size = min(BUFFER_SIZE, bytes_to_send - total_sent)
                    data = f.read(read_size)
                    if not data: break
                    client_socket.sendall(data)
                    total_sent += len(data)
        else:
            client_socket.sendall(b'ERROR: File not found')

    def _relay_file_content(self, client_socket, target_peer, filename, start_byte, length):
        if target_peer not in self.network.peers:
            client_socket.sendall(b'ERROR: Peer unknown')
            return
        target_host, target_port = self.network.peers[target_peer]
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect((target_host, target_port))
            command = f"TRANSFER|{target_peer}|{filename}|{start_byte}|{length}"
            s.sendall(command.encode('utf-8'))
            response = s.recv(1024)
            if b'OK' in response:
                client_socket.sendall(b'OK')
                total_relayed = 0
                while total_relayed < length:
                    data = s.recv(BUFFER_SIZE)
                    if not data: break
                    client_socket.sendall(data)
                    total_relayed += len(data)
            else:
                client_socket.sendall(response)
        except: pass
        finally: s.close()

    def swarm_download(self, filename, seeder_list):
        print(f"[{self.name}] 🚀 Initiating Swarm for '{filename}'")
        
        file_size = 0
        for peer in seeder_list:
            if peer == self.name: continue
            try:
                if peer in self.network.peers:
                    host, port = self.network.peers[peer]
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(2)
                    s.connect((host, port))
                    s.sendall(f"SIZE|{filename}".encode())
                    resp = s.recv(1024).decode()
                    s.close()
                    if int(resp) > 0:
                        file_size = int(resp)
                        print(f"[{self.name}] 📄 Metadata from {peer}: {file_size} bytes")
                        break
            except: continue
                
        if file_size <= 0:
            print("❌ Error: File not found in swarm.")
            return

        save_path = os.path.join(self.storage_folder, f"downloaded_{filename}")
        with open(save_path, 'wb') as f:
            f.seek(file_size - 1)
            f.write(b'\0')

        # FIX: Increased chunk sizes to reduce total connection overhead
        limit_small = 100 * 1024 * 1024
        limit_large = 1024 * 1024 * 1024

        if file_size < limit_small:
            chunk_size = 512 * 1024      # 512 KB
            cat_str = "Small File (<100MB)"
        elif file_size < limit_large:
            chunk_size = 2 * 1024 * 1024     # 2 MB
            cat_str = "Medium File (100MB-1GB)"
        else:
            chunk_size = 8 * 1024 * 1024 # 8 MB
            cat_str = "Large File (>1GB)"

        job_queue = queue.Queue()
        num_pieces = (file_size + chunk_size - 1) // chunk_size
        
        print(f"[{self.name}] ℹ️  File Size: {file_size / (1024*1024):.2f} MB")
        print(f"[{self.name}] ℹ️  Mode: {cat_str}")
        print(f"[{self.name}] ℹ️  Chunk Size: {chunk_size / 1024:.0f} KB")
        print(f"[{self.name}] 🔢 Total Chunks: {num_pieces}")

        for i in range(num_pieces):
            start = i * chunk_size
            length = min(chunk_size, file_size - start)
            job_queue.put((start, length))

        threads = []
        file_lock = threading.Lock()
        stats = {peer: 0 for peer in seeder_list if peer != self.name}
        start_time = time.time()
        
        for peer in seeder_list:
            if peer != self.name:
                t = threading.Thread(target=self._peer_worker, args=(peer, filename, job_queue, file_lock, stats, chunk_size))
                t.start()
                threads.append(t)
            
        job_queue.join()
        for t in threads: t.join(timeout=1.0)
        
        duration = time.time() - start_time
        print("\n" + "="*40)
        print(f"   🎉 DOWNLOAD COMPLETE in {duration:.2f}s")
        print("="*40)
        print(f"{'Seeder Name':<15} | {'Bytes Sent':<12} | {'Chunks':<6}")
        print("-" * 40)
        
        total_bytes = 0
        for peer, bytes_sent in stats.items():
            chunks_sent = (bytes_sent + chunk_size - 1) // chunk_size if bytes_sent > 0 else 0
            print(f"{peer:<15} | {bytes_sent:<12} | {chunks_sent:<6}")
            total_bytes += bytes_sent
            
        print("-" * 40)
        print(f"Total Received: {total_bytes} bytes")
        print("="*40 + "\n")

    def _peer_worker(self, peer, filename, job_queue, file_lock, stats, chunk_size):
        while not job_queue.empty():
            try:
                start, length = job_queue.get(timeout=1)
            except queue.Empty: break

            success = False
            try:
                if peer in self.network.peers:
                    host, port = self.network.peers[peer]
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(5)
                    s.connect((host, port))
                    
                    req = f"TRANSFER|{peer}|{filename}|{start}|{length}"
                    s.sendall(req.encode())
                    
                    resp = s.recv(1024)
                    if b'OK' in resp:
                        data_buffer = b""
                        while len(data_buffer) < length:
                            packet = s.recv(BUFFER_SIZE)
                            if not packet: break
                            data_buffer += packet
                        
                        if len(data_buffer) == length:
                            with file_lock:
                                save_path = os.path.join(self.storage_folder, f"downloaded_{filename}")
                                with open(save_path, 'r+b') as f:
                                    f.seek(start)
                                    f.write(data_buffer)
                            
                            stats[peer] += length
                            success = True
                            chunk_id = (start // chunk_size) + 1
                            print(f"[{self.name}] ✅ Chunk {chunk_id} from {peer}")
                    s.close()
            except Exception as e:
                # print(f"[{self.name}] ⚠️ Peer {peer} busy, retrying chunk...")
                pass

            if success:
                job_queue.task_done()
            else:
                # FIX: Added sleep and task_done for failed tasks to prevent CPU spin
                time.sleep(1.0) 
                job_queue.put((start, length))
                job_queue.task_done()