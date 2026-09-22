"""The OLD construction, on our small world: build two separate BDDs
(one for the query over all situations, one for the world model), then
walk them in lockstep to form the product graph -- the way
form_product_graph did it in MRTA_Search. No situation table crosses
into the walk; the two diagrams carry all the structure.

Sifting is NOT the old kind: the old code reshaped BDDs in place by
swapping adjacent levels (the ~2900-line machinery we dropped). Here the
sift is our rebuild-per-order loop, scoring the PRODUCT built this old
way -- which is also what the old code evaluated at every swept
position, so this isolates exactly the construction difference.

Usage:
  python3 bdd_old.py 6 1
"""

from generate import generate_query, generate_world, allowed_worlds, situations
from bdd import build, evaluate, size, sift


def function_bdd(formula, names, order):
    """Plain BDD of a formula over ALL situations, in `order`. (The old
    code got this from the dd library's ite machine; the reduced result
    is the same object either way.)"""
    every = situations(names)
    answer = {s: formula.evaluate(dict(zip(names, s))) for s in every}
    return build(every, answer, order)


def product(qbdd, wbdd, order):
    """Old-style combination: walk the query BDD and the world BDD in
    lockstep from their roots. Each product node is a PAIR of nodes, one
    from each diagram; the variable asked is whichever side sits earlier
    in `order`. If the world side dies on a branch (constraint violated),
    the branch is pruned; if one value of the variable is infeasible, the
    variable is skipped -- the query continues on the feasible side only.
    Returns (root, nodes) with the same representation as bdd.build."""
    qnodes, wnodes = qbdd[1], wbdd[1]
    level = {v: i for i, v in enumerate(order)}
    ids, nodes, memo = {}, {}, {}

    def walk(qn, wn):
        if wn == 0:                     # world false here: no allowed world
            return None
        if qn < 2:                      # query decided
            return qn
        if (qn, wn) in memo:
            return memo[(qn, wn)]
        qv = qnodes[qn][0]
        w_steps = wn >= 2 and level[wnodes[wn][0]] < level[qv]
        both = wn >= 2 and level[wnodes[wn][0]] == level[qv]
        if w_steps:                     # world asks first; query waits
            lo = walk(qn, wnodes[wn][1])
            hi = walk(qn, wnodes[wn][2])
            v = wnodes[wn][0]
        elif both:                      # both ask the same variable
            lo = walk(qnodes[qn][1], wnodes[wn][1])
            hi = walk(qnodes[qn][2], wnodes[wn][2])
            v = qv
        else:                           # query asks; world already true
            lo = walk(qnodes[qn][1], wn)
            hi = walk(qnodes[qn][2], wn)
            v = qv
        if lo is None and hi is None:
            out = None
        elif lo is None:                # v must be 1: skip it
            out = hi
        elif hi is None:                # v must be 0: skip it
            out = lo
        elif lo == hi:
            out = lo
        else:
            if (v, lo, hi) not in ids:
                ids[(v, lo, hi)] = len(ids) + 2
                nodes[ids[(v, lo, hi)]] = (v, lo, hi)
            out = ids[(v, lo, hi)]
        memo[(qn, wn)] = out
        return out

    root = walk(qbdd[0], wbdd[0])
    if root is None:                    # no world at all satisfies the model
        root = 0
    return root, nodes


def sift_old(q, w, names, order=None, verbose=False):
    """Rudell's loop scoring the old construction: for each trial order,
    rebuild the query BDD, the world BDD, and their product."""
    n = len(names)
    order = list(range(n)) if order is None else list(order)

    def cost(ordr):
        p = product(function_bdd(q, names, ordr), function_bdd(w, names, ordr), ordr)
        return size(p)

    best = cost(order)
    for v in range(n):
        at = order.index(v)
        rest = order[:at] + order[at + 1:]
        for pos in range(n):
            trial = rest[:pos] + [v] + rest[pos:]
            c = cost(trial)
            if c < best:
                best, at = c, pos
        order = rest[:at] + [v] + rest[at:]
        if verbose:
            print("  sifted %s -> %d nodes" % (names[v], best))
    return order, best


if __name__ == "__main__":
    import sys

    n = int(sys.argv[1])
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    names = ["p%d" % i for i in range(n)]
    q = generate_query(n, seed)
    w = generate_world(q, seed)
    worlds = allowed_worlds(w, names)
    answer = {s: q.evaluate(dict(zip(names, s))) for s in situations(names)}
    print("query:", q)
    print("world:", w)
    print("worlds: %d of %d" % (len(worlds), 1 << n))
    order, _ = sift(worlds, answer)
    qbdd = function_bdd(q, names, order)
    wbdd = function_bdd(w, names, order)
    p = product(qbdd, wbdd, order)
    combined = build(worlds, answer, order)
    print("query BDD %d nodes | world BDD %d nodes | product %d nodes | "
          "one-shot build %d nodes" % (size(qbdd), size(wbdd), size(p), size(combined)))
    ok = all(evaluate(p, s) == answer[s] for s in worlds)
    print("product agrees with the query on every allowed world:", ok)
    o_old, c_old = sift_old(q, w, names, verbose=True)
    o_new, c_new = sift(worlds, answer)
    print("sift old construction: %s -> %d nodes" % (o_old, c_old))
    print("sift one-shot build:   %s -> %d nodes" % (o_new, c_new))
