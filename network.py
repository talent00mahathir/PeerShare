import socket
import time
from dijkstra import dijkstra  

class NetworkManager:
    def __init__(self):
        self.peers = {}
        self.graph = {}
        self.last_update_time = 0
        self.update_interval = 2.0 

    def add_peer(self, peer_name, host, port):
        if peer_name not in self.peers:
            self.peers[peer_name] = (host, port)

    def remove_peer(self, peer_name):
        if peer_name in self.peers:
            del self.peers[peer_name]

    def _measure_latency(self, peer_name_a, peer_name_b):
        try:
            addr_b = self.peers[peer_name_b]
        except KeyError:
            return float('inf')

        if peer_name_a == peer_name_b: return 0

        ping_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ping_socket.settimeout(0.2) 

        try:
            start_time = time.perf_counter()
            ping_socket.connect(addr_b)
            ping_socket.sendall(b'__PING__')
            data = ping_socket.recv(8)
            end_time = time.perf_counter()

            if data == b'__PONG__':
                return (end_time - start_time) * 1000
            else:
                return float('inf')
        except:
            return float('inf')
        finally:
            ping_socket.close()

    def update_network_graph(self):
        current_time = time.time()
        if current_time - self.last_update_time < self.update_interval:
            return

        new_graph = {}
        all_peer_names = list(self.peers.keys())

        for peer_name in all_peer_names:
            new_graph[peer_name] = {}
            for other_peer_name in all_peer_names:
                if peer_name == other_peer_name: continue
                cost = self._measure_latency(peer_name, other_peer_name)
                if cost != float('inf'):
                    new_graph[peer_name][other_peer_name] = cost
        
        self.graph = new_graph
        self.last_update_time = current_time 

    def get_shortest_route(self, start_peer_name, end_peer_name):
        self.update_network_graph()
        
        if start_peer_name not in self.graph or end_peer_name not in self.graph:
            if not self.graph:
                 self.last_update_time = 0 
                 self.update_network_graph()
            if start_peer_name not in self.graph or end_peer_name not in self.graph:
                return None, float('inf')

        return dijkstra(self.graph, start_peer_name, end_peer_name)