"""Query generator for the MRTA problem (problem.md).

A property is a boolean fact a robot can learn at a location. A query
is a boolean formula over properties, built from AND, OR, XOR, NOT.
A situation is one True/False assignment of all properties.

Usage:
  python3 generate.py 4           # 4 properties, random seed (printed)
  python3 generate.py 4 42        # 4 properties, seed 42
  python3 generate.py 4 42 3      # ... with 3 repeated properties
"""

import random

from query import Query


def generate_query(num_properties, seed, repeats=None):
    """Random boolean formula over properties p0..p{n-1}.

    Every property appears at least once; `repeats` is how many extra
    leaves are added on top of that (random 0..n if not given). Each
    operator splits the leaves it owns at a random point, so tree shape
    and depth fall out of the splits instead of a cap.

    A property is dead if flipping it never changes the answer (p0 ^ p0
    kills p0; p0 | (p0 & p1) kills p1). Repeats make that possible, so
    a formula with a dead property is thrown away and rebuilt.
    """
    if num_properties < 1:
        raise ValueError("need at least 1 property")
    rng = random.Random(seed)
    names = ["p%d" % i for i in range(num_properties)]
    if repeats is None:
        repeats = rng.randrange(num_properties + 1)

    def build(leaves):
        if len(leaves) == 1:
            node = Query("var", leaves[0])
        else:
            k = rng.randrange(1, len(leaves))
            op = rng.choice(["and", "or", "xor"])
            node = Query(op, build(leaves[:k]), build(leaves[k:]))
        # Negation is a coin flip on a finished node, not a recursive
        # step, so ~~x cannot occur.
        return Query("not", node) if rng.random() < 0.3 else node

    for attempt in range(1000):
        leaves = names + [rng.choice(names) for _ in range(repeats)]
        rng.shuffle(leaves)
        q = build(leaves)
        if not dead_properties(q, names):
            return q
    raise ValueError("no formula without dead properties in 1000 tries; lower repeats")


def dead_properties(q, names):
    """Properties whose value never changes q's answer, by truth table."""
    n = len(names)
    table = [q.evaluate({names[i]: bool(m >> i & 1) for i in range(n)})
             for m in range(1 << n)]
    return [names[i] for i in range(n)
            if all(table[m] == table[m ^ (1 << i)] for m in range(1 << n))]


if __name__ == "__main__":
    import sys

    n = int(sys.argv[1])
    if len(sys.argv) > 2:
        seed = int(sys.argv[2])
    else:
        seed = random.randrange(2**31)
        print("seed:", seed)
    repeats = int(sys.argv[3]) if len(sys.argv) > 3 else None
    q = generate_query(n, seed, repeats)
    print(q)
