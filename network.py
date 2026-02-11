import socket
import time
from dijkstra import dijkstra  

class NetworkManager:
    def __init__(self):
        self.peers = {}
        self.graph = {}
        self.last_update_time = 0
        self.update_interval = 3.0 # Update map every 3 seconds

    def add_peer(self, peer_name, host, port):
        self.peers[peer_name] = (host, port)

    def _measure_latency(self, peer_name_a, peer_name_b):
        if peer_name_a == peer_name_b: return 0
        addr_b = self.peers.get(peer_name_b)
        if not addr_b: return float('inf')

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.3)
        try:
            start = time.perf_counter()
            s.connect(addr_b)
            s.sendall(b'__PING__')
            if s.recv(8) == b'__PONG__':
                return (time.perf_counter() - start) * 1000
        except: return float('inf')
        finally: s.close()
        return float('inf')

    def update_network_graph(self):
        if time.time() - self.last_update_time < self.update_interval: return
        new_g = {}
        names = list(self.peers.keys())
        for p in names:
            new_g[p] = {}
            for other in names:
                if p == other: continue
                lat = self._measure_latency(p, other)
                if lat != float('inf'): new_g[p][other] = lat
        self.graph = new_g
        self.last_update_time = time.time()

    def get_shortest_route(self, start, end):
        self.update_network_graph()
        if start not in self.graph or end not in self.graph:
            return None, float('inf')
        return dijkstra(self.graph, start, end)