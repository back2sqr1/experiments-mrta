"""BDD of the query under the world model, plus Rudell sifting.

The diagram asks about properties one at a time. A node is
( property index, child-if-false, child-if-true ); the terminals are
the ints 0 (False) and 1 (True). `build` makes the diagram by splitting
the set of allowed worlds on the next property in `order` — a property
the remaining worlds all agree on is already known and gets no node
(that is where the world model does its work). `sift` is Rudell's
search over property orders: slide each property through every
position, keep the one with the best score.

Usage:
  python3 bdd.py 5           # instance from generate.py, random seed
  python3 bdd.py 5 42        # ... seed 42
"""

from generate import generate_query, generate_world, allowed_worlds


def build(worlds, answer, order):
    """Diagram of the query restricted to `worlds`, asking properties in
    `order`. worlds: list of situations (tuples, property i is bit i);
    answer: situation -> bool; order: permutation of 0..n-1. Returns
    (root, nodes) where nodes maps id >= 2 -> (property, low, high)."""
    assert sorted(order) == list(range(len(worlds[0]))), "order must cover every property"
    nodes = {}   # id -> (property, low child, high child)
    ids = {}     # the same key -> id, so identical subtrees share one node

    def rec(W, k):
        answers = {answer[w] for w in W}
        if len(answers) == 1:
            return int(answers.pop())
        while True:
            v = order[k]
            W0 = [w for w in W if not w[v]]
            W1 = [w for w in W if w[v]]
            if W0 and W1:
                break
            k += 1  # no world has the other value: observing v teaches nothing
        lo, hi = rec(W0, k + 1), rec(W1, k + 1)
        if lo == hi:
            return lo
        if (v, lo, hi) not in ids:
            ids[(v, lo, hi)] = len(ids) + 2
            nodes[ids[(v, lo, hi)]] = (v, lo, hi)
        return ids[(v, lo, hi)]

    return rec(list(worlds), 0), nodes


def evaluate(bdd, w):
    """Follow the diagram for situation `w` down to its terminal."""
    root, nodes = bdd
    while root >= 2:
        v, lo, hi = nodes[root]
        root = hi if w[v] else lo
    return bool(root)


def size(bdd):
    """Number of decision nodes."""
    return len(bdd[1])


def sift(worlds, answer, order=None, cost=size):
    """Rudell's sifting, scored by `cost(built diagram)`. Starts from
    `order` (default 0..n-1); slides each property to its best position.
    Returns (order, best cost)."""
    n = len(worlds[0])
    order = list(range(n)) if order is None else list(order)
    best = cost(build(worlds, answer, order))
    for v in range(n):
        at = order.index(v)
        rest = order[:at] + order[at + 1:]
        for pos in range(n):
            trial = rest[:pos] + [v] + rest[pos:]
            c = cost(build(worlds, answer, trial))
            if c < best:
                best, at = c, pos
        order = rest[:at] + [v] + rest[at:]
    return order, best


if __name__ == "__main__":
    import random
    import sys

    n = int(sys.argv[1])
    if len(sys.argv) > 2:
        seed = int(sys.argv[2])
    else:
        seed = random.randrange(2**31)
        print("seed:", seed)
    world_repeats = int(sys.argv[3]) if len(sys.argv) > 3 else None
    names = ["p%d" % i for i in range(n)]
    q = generate_query(n, seed)
    w = generate_world(q, seed, world_repeats)
    worlds = allowed_worlds(w, names)
    answer = {s: q.evaluate(dict(zip(names, s))) for s in worlds}
    print("query:", q)
    print("world:", w)
    print("worlds: %d of %d" % (len(worlds), 1 << n))
    init = build(worlds, answer, list(range(n)))
    print("order %s -> %d nodes" % (list(range(n)), size(init)))
    order, c = sift(worlds, answer)
    print("order %s -> %d nodes  (sifted)" % (order, c))