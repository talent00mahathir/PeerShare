import heapq

def dijkstra(graph, start, end):
    costs = {node: float('inf') for node in graph}
    costs[start] = 0
    previous_nodes = {}
    priority_queue = [(0, start)]
    
    while priority_queue:
        current_cost, current_node = heapq.heappop(priority_queue)
        
        if current_node == end: break
        if current_cost > costs[current_node]: continue
        if current_node not in graph: continue
            
        for neighbor, weight in graph[current_node].items():
            new_cost = current_cost + weight
            if new_cost < costs[neighbor]:
                costs[neighbor] = new_cost
                previous_nodes[neighbor] = current_node
                heapq.heappush(priority_queue, (new_cost, neighbor))
                
    if costs[end] == float('inf'): return None, float('inf')
        
    path = []
    current_node = end
    while current_node in previous_nodes:
        path.append(current_node)
        current_node = previous_nodes[current_node]
    path.append(start)
    path.reverse()
    return path, costs[end]