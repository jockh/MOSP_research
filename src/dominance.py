def dominates(a, b, stats=None):

    if len(a.costs) != len(b.costs):
        raise ValueError(
            "Labels have different numbers of objectives."
        )

    if stats is not None:
        stats["dominance_checks"] += 1

    no_worse = all(
        x <= y
        for x, y in zip(a.costs, b.costs)
    )

    strictly_better = any(
        x < y
        for x, y in zip(a.costs, b.costs)
    )

    return no_worse and strictly_better


def same_cost(a, b):
    return a.costs == b.costs


def insert_label(new_label, labels, stats=None):

    # Check whether new label should be pruned
    for old_label in labels:

        if dominates(
            old_label,
            new_label,
            stats
        ):
            new_label.active = False

            if stats is not None:
                stats["pruned_labels"] += 1

            return False

        if same_cost(old_label, new_label):
            new_label.active = False

            if stats is not None:
                stats["pruned_labels"] += 1

            return False

    # Remove old labels dominated by new label
    surviving_labels = []

    for old_label in labels:

        if dominates(
            new_label,
            old_label,
            stats
        ):
            old_label.active = False

        else:
            surviving_labels.append(old_label)

    surviving_labels.append(new_label)

    labels[:] = surviving_labels

    if stats is not None:
        stats["kept_labels"] += 1

    return True