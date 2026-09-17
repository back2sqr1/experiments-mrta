"""Differential check: Query.evaluate vs an independent evaluator."""
import random
import sys

sys.path.insert(0, ".")
from generate import make_query


def ref(q, w):
    k = q.kind
    if k == "var":
        return w[q.children[0]]
    if k == "not":
        return not ref(q.children[0], w)
    a, b = ref(q.children[0], w), ref(q.children[1], w)
    if k == "and":
        return a and b
    if k == "or":
        return a or b
    return a != b  # xor


ok = True
for n in range(1, 9):
    for seed in range(300):
        q = make_query(n, seed)
        vars_ = sorted(q.variables())
        assert len(vars_) == n, (n, seed, vars_)
        assert "~~" not in str(q), (n, seed, str(q))
        if n <= 10:
            situations = [
                {v: bool((i >> j) & 1) for j, v in enumerate(vars_)}
                for i in range(2 ** n)
            ]
        else:
            situations = [
                {v: random.random() < 0.5 for v in vars_} for _ in range(200)
            ]
        for s in situations:
            if q.evaluate(s) != ref(q, s):
                print("MISMATCH", n, seed, str(q))
                ok = False
print("differential check:", "PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)