class Edge:
    def __init__(self, to, costs):
        self.to = to
        self.costs = tuple(costs)

    def __repr__(self):
        return f"Edge(to={self.to}, costs={self.costs})"


class Graph:
    def __init__(self):
        self.adj = {}

    def add_node(self, node):
        if node not in self.adj:
            self.adj[node] = []

    def add_edge(self, u, v, costs):
        self.add_node(u)
        self.add_node(v)

        self.adj[u].append(
            Edge(v, costs)
        )

    def neighbors(self, node):
        return self.adj.get(node, [])

    def nodes(self):
        return list(self.adj.keys())