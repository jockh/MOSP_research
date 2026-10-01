from src.label import Label
from src.dominance import dominates


def add_costs(a, b):
    if len(a) != len(b):
        raise ValueError(
            "Cost vectors have different dimensions."
        )

    return tuple(
        x + y
        for x, y in zip(a, b)
    )


def enumerate_paths(
    graph,
    source,
    target,
    num_objectives
):
    """
    Enumerate all simple paths from source to target.
    """

    results = []

    zero_cost = (0,) * num_objectives

    def dfs(node, path, total_cost):

        if node == target:
            results.append(
                (
                    path.copy(),
                    total_cost
                )
            )
            return

        for edge in graph.neighbors(node):

            # Only enumerate simple paths
            if edge.to in path:
                continue

            if len(edge.costs) != num_objectives:
                raise ValueError(
                    "Edge cost dimension does not match."
                )

            path.append(edge.to)

            dfs(
                edge.to,
                path,
                add_costs(
                    total_cost,
                    edge.costs
                )
            )

            path.pop()

    dfs(
        source,
        [source],
        zero_cost
    )

    return results


def brute_force_pareto(
    graph,
    source,
    target,
    num_objectives
):
    """
    Find true Pareto-optimal paths by
    exhaustive simple-path enumeration.
    """

    paths = enumerate_paths(
        graph,
        source,
        target,
        num_objectives
    )

    pareto_paths = []

    for i, (path_i, costs_i) in enumerate(paths):

        label_i = Label(
            target,
            costs_i
        )

        dominated = False

        for j, (path_j, costs_j) in enumerate(paths):

            if i == j:
                continue

            label_j = Label(
                target,
                costs_j
            )

            if dominates(
                label_j,
                label_i
            ):
                dominated = True
                break

        if not dominated:
            pareto_paths.append(
                (
                    path_i,
                    costs_i
                )
            )

    return pareto_paths