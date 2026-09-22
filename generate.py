"""Query and world-model generator for the MRTA problem (problem.md).

A property is a boolean fact a robot can learn at a location. A query
is a boolean formula over properties, built from AND, OR, XOR, NOT.
A situation is one True/False assignment of all properties. A world
model is a formula every real situation obeys; a world is a situation
the model allows.

Usage:
  python3 generate.py 4           # 4 properties, random seed (printed)
  python3 generate.py 4 42        # 4 properties, seed 42
  python3 generate.py 4 42 3      # ... query with 3 repeated properties
  python3 generate.py 4 42 3 2    # ... and world model with 2
"""

import random

from formula import Formula


def generate_query(num_properties, seed, repeats=None):
    """Random query over properties p0..p{n-1}, using AND, OR, XOR, NOT.

    Every property appears at least once; `repeats` is how many extra
    leaves are added on top of that (random 0..n if not given). A
    candidate with a dead property or a redundant part (see those
    functions) is thrown away and rebuilt.
    """
    if num_properties < 1:
        raise ValueError("need at least 1 property")
    rng = random.Random(seed)
    names = ["p%d" % i for i in range(num_properties)]
    if repeats is None:
        repeats = rng.randrange(num_properties + 1)
    for attempt in range(1000):
        q = random_formula(rng, names, repeats, ["and", "or", "xor"])
        if not dead_properties(q, names) and not redundant_parts(q, names):
            return q
    raise ValueError("no clean query in 1000 tries; lower repeats")


def generate_world(query, seed, repeats=None):
    """Random world model for `query`: a formula over the query's
    properties, built like the query but also using IMPLIES. (forall and
    exists are in Formula for hand-written models; the model with no
    constraints is Formula("forall").)

    Besides no dead property and no redundant part, a candidate is
    rejected unless the instance is worth planning for:
      - every property still varies across worlds (a fixed one is known
        without visiting it)
      - the model does not already decide the query
      - the model cuts the worst-case number of observations, but not
        below n/2, and some worlds are decided sooner than others, so
        the plan has to branch
    Brute force over all 2^n situations; fine up to n = 8.
    """
    names = sorted(query.variables(), key=lambda s: int(s[1:]))
    n = len(names)
    if n < 3:
        # With 2 properties a model that saves an observation leaves
        # exactly one to check, so the plan cannot branch.
        raise ValueError("need at least 3 properties")
    # Own random stream, so the model's shape is not tied to the query's.
    rng = random.Random("world %d" % seed)
    if repeats is None:
        repeats = rng.randrange(n + 1)
    every = situations(names)
    answer = {w: query.evaluate(dict(zip(names, w))) for w in every}
    free_worst, _ = observations_needed(every, answer)

    for attempt in range(1000):
        model = random_formula(rng, names, repeats, ["and", "or", "xor", "implies"])
        if dead_properties(model, names) or redundant_parts(model, names):
            continue
        worlds = allowed_worlds(model, names)
        if any(len({w[i] for w in worlds}) < 2 for i in range(n)):
            continue
        if len({answer[w] for w in worlds}) < 2:
            continue
        worst, best = observations_needed(worlds, answer)
        if best < worst < free_worst and worst >= n / 2:
            return model
    raise ValueError("no interesting world model in 1000 tries; change repeats")


def random_formula(rng, names, repeats, ops):
    """Random formula with every name as a leaf, plus `repeats` extra
    leaves. Each operator splits the leaves it owns at a random point,
    so tree shape and depth fall out of the splits instead of a cap."""
    leaves = names + [rng.choice(names) for _ in range(repeats)]
    rng.shuffle(leaves)

    def build(leaves):
        if len(leaves) == 1:
            node = Formula("var", leaves[0])
        else:
            k = rng.randrange(1, len(leaves))
            node = Formula(rng.choice(ops), build(leaves[:k]), build(leaves[k:]))
        # Negation is a coin flip on a finished node, not a recursive
        # step, so ~~x cannot occur.
        return Formula("not", node) if rng.random() < 0.3 else node

    return build(leaves)


def dead_properties(q, names):
    """Properties whose value never changes q's answer, e.g. p1 in
    (p0 ^ p1) ^ (p1 ^ p2)."""
    t = table(q, names)
    n = len(names)
    return [names[i] for i in range(n)
            if all((t >> m & 1) == (t >> (m ^ 1 << i) & 1) for m in range(1 << n))]


def redundant_parts(q, names):
    """Sub-formulas that can be replaced by True or False without
    changing q's answer anywhere: (p2 ^ p2) in p0 | (p2 ^ p2); either
    ~p1 in (~p1 | ~p1); (p0 & p1) in p0 | (p0 & p1)."""
    full = (1 << (1 << len(names))) - 1
    t = table(q, names)
    return [s for s in parts(q)
            if table(q, names, s, 0) == t or table(q, names, s, full) == t]


def parts(q):
    """q and every sub-formula inside it."""
    out = [q]
    if q.kind != "var":
        for c in q.children:
            out += parts(c)
    return out


def table(q, names, forced=None, value=0):
    """Truth table of q as an int: bit m is q's answer in situation m,
    where property i has the value of bit i of m. If `forced` is a node
    of q, it counts as the constant table `value` (0 or all ones)."""
    n = len(names)
    full = (1 << (1 << n)) - 1
    if forced is not None and q is forced:
        return value
    if q.kind == "var":
        i = names.index(q.children[0])
        return sum(1 << m for m in range(1 << n) if m >> i & 1)
    t = [table(c, names, forced, value) for c in q.children]
    if q.kind == "not":
        return full ^ t[0]
    if q.kind == "and":
        return t[0] & t[1]
    if q.kind == "or":
        return t[0] | t[1]
    if q.kind == "xor":
        return t[0] ^ t[1]
    if q.kind == "implies":
        return (full ^ t[0]) | t[1]
    if q.kind == "forall":
        out = full
        for x in t:
            out &= x
        return out
    if q.kind == "exists":
        out = 0
        for x in t:
            out |= x
        return out
    raise ValueError(q.kind)


def situations(names):
    """All True/False assignments, as tuples in `names` order; entry m
    is situation m in the sense of table()."""
    n = len(names)
    return [tuple(bool(m >> i & 1) for i in range(n)) for m in range(1 << n)]


def allowed_worlds(model, names):
    """Situations the world model allows."""
    t = table(model, names)
    return [w for m, w in enumerate(situations(names)) if t >> m & 1]


def observations_needed(worlds, answer):
    """(worst, best) number of properties an ideal plan must observe to
    decide the query over `worlds`. answer: world -> query value.
    Worst is over worlds for the best plan; best is the earliest any
    world can be decided."""
    memo = {}

    def rec(W):
        if W not in memo:
            if len({answer[w] for w in W}) == 1:
                memo[W] = (0, 0)
            else:
                worst, best = [], []
                for i in range(len(W[0])):
                    W0 = tuple(w for w in W if not w[i])
                    W1 = tuple(w for w in W if w[i])
                    if W0 and W1:  # observing a property already implied is wasted
                        (w0, b0), (w1, b1) = rec(W0), rec(W1)
                        worst.append(1 + max(w0, w1))
                        best.append(1 + min(b0, b1))
                memo[W] = (min(worst), min(best))
        return memo[W]

    return rec(tuple(worlds))


if __name__ == "__main__":
    import sys

    n = int(sys.argv[1])
    if len(sys.argv) > 2:
        seed = int(sys.argv[2])
    else:
        seed = random.randrange(2**31)
        print("seed:", seed)
    repeats = int(sys.argv[3]) if len(sys.argv) > 3 else None
    world_repeats = int(sys.argv[4]) if len(sys.argv) > 4 else None
    q = generate_query(n, seed, repeats)
    print("query:", q)
    if n >= 3:
        names = ["p%d" % i for i in range(n)]
        w = generate_world(q, seed, world_repeats)
        print("world:", w)
        print("worlds: %d of %d" % (len(allowed_worlds(w, names)), 1 << n))
