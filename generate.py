"""Query generator for the MRTA problem (problem.md).

A property is a boolean fact a robot can learn at a location. A query
is a boolean formula over properties, built from AND, OR, XOR, NOT.
A situation is one True/False assignment of all properties.

Usage:
  python3 generate.py 4           # 4 properties, random seed (printed)
  python3 generate.py 4 42        # 4 properties, seed 42
"""

import random
import sys

from query import Query


def make_query(n, seed):
    """Random query over exactly n distinct properties, as a Query tree."""
    if n < 1:
        raise ValueError("n must be at least 1")
    rng = random.Random(seed)

    names = ["p%d" % i for i in range(n)]

    # Pair random nodes with random operators until one tree is left.
    nodes = [Query("var", name) for name in names]
    while len(nodes) > 1:
        a = nodes.pop(rng.randrange(len(nodes)))
        b = nodes.pop(rng.randrange(len(nodes)))
        nodes.append(Query(rng.choice(["and", "or", "xor"]), a, b))
    return _negate_some(nodes[0], rng)


def _negate_some(q, rng, p=0.15, wrap_ok=True):
    """Rebuild the tree, wrapping some nodes in NOT (never ~~)."""
    if q.kind == "not":
        return Query("not", _negate_some(q.children[0], rng, wrap_ok=False))
    if wrap_ok and rng.random() < p:
        return Query("not", _negate_some(q, rng, p, wrap_ok=False))
    if q.kind == "var":
        return q
    return Query(
        q.kind,
        _negate_some(q.children[0], rng),
        _negate_some(q.children[1], rng),
    )


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else random.randrange(10 ** 6)
    q = make_query(n, seed)
    print("seed:   ", seed)
    print("query:  ", q)
    print("vars:   ", " ".join(sorted(q.variables())))
    rng = random.Random(seed)
    for _ in range(4):
        situation = {v: rng.random() < 0.5 for v in q.variables()}
        bits = " ".join(v + "=" + ("T" if situation[v] else "F") for v in sorted(situation))
        print("situation:", bits, "-> ", q.evaluate(situation))
