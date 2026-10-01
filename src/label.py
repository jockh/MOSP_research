class Label:
    _next_id = 0

    def __init__(
        self,
        node,
        costs,
        predecessor=None
    ):
        self.id = Label._next_id
        Label._next_id += 1

        self.node = node
        self.costs = tuple(costs)

        self.predecessor = predecessor

        self.active = True

    def cost(self):
        return self.costs

    def __repr__(self):
        return (
            f"Label("
            f"node={self.node}, "
            f"costs={self.costs}"
            f")"
        )