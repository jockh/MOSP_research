import heapq

from src.label import Label
from src.dominance import insert_label


def add_costs(a, b):

    if len(a) != len(b):
        raise ValueError(
            "Cost vectors have different dimensions."
        )

    return tuple(
        x + y
        for x, y in zip(a, b)
    )


def mosp(
    graph,
    source,
    num_objectives,
    return_stats=False
):

    labels = {
        node: []
        for node in graph.nodes()
    }

    stats = {
        "generated_labels": 0,
        "kept_labels": 0,
        "pruned_labels": 0,
        "dominance_checks": 0,
        "max_labels_per_node": 1
    }

    start_label = Label(
        node=source,
        costs=(0,) * num_objectives,
        predecessor=None
    )

    labels[source].append(start_label)

    pq = []

    heapq.heappush(
        pq,
        (
            start_label.costs,
            start_label.id,
            start_label
        )
    )

    while pq:

        _, _, current = heapq.heappop(pq)

        if not current.active:
            continue

        for edge in graph.neighbors(current.node):

            if len(edge.costs) != num_objectives:
                raise ValueError(
                    "Edge cost dimension does not match."
                )

            new_costs = add_costs(
                current.costs,
                edge.costs
            )

            new_label = Label(
                node=edge.to,
                costs=new_costs,
                predecessor=current
            )

            stats["generated_labels"] += 1

            kept = insert_label(
                new_label,
                labels[edge.to],
                stats
            )

            if kept:

                heapq.heappush(
                    pq,
                    (
                        new_label.costs,
                        new_label.id,
                        new_label
                    )
                )

                stats["max_labels_per_node"] = max(
                    stats["max_labels_per_node"],
                    len(labels[edge.to])
                )

    if return_stats:
        return labels, stats

    return labels


def reconstruct_path(label):

    path = []

    current = label

    while current is not None:
        path.append(current.node)
        current = current.predecessor

    path.reverse()

    return path