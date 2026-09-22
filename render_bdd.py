"""Render a BDD to PNG with graphviz (dot), for looking at diagrams.

Light theme, top-to-bottom. A node asks a property (diamond); the left
edge is False (red), the right edge True (green); terminals are small
boxes 0/1. Dashed edges are the world model at work — the property was
never asked because the worlds all agree on it there.

Usage:
  python3 render_bdd.py 5           # instance from generate.py, random seed
  python3 render_bdd.py 5 42        # ... seed 42
Writes <prefix>_bdd.png, <prefix>_dot.txt
"""

import html
import subprocess
import sys

from generate import generate_query, generate_world, allowed_worlds, situations
from bdd import build, evaluate, size, sift

GREEN, RED, AMBER = "#2e9e4f", "#d95f5f", "#c8961e"


def to_dot(bdd, names, order):
    """DOT source for the diagram. `order` is the asking order the
    diagram was built with; every node asking the same property goes on
    one horizontal row, in that order top to bottom."""
    root, nodes = bdd
    lines = [
        "digraph bdd {",
        "  bgcolor=white;",
        "  rankdir=TB;",
        "  node [shape=ellipse, style=filled, fillcolor=white, color=black,",
        "        fontname=Helvetica, fontsize=11];",
        "  edge [fontname=Helvetica, fontsize=9, arrowsize=0.7];",
    ]
    for i in sorted(nodes):
        v, lo, hi = nodes[i]
        lines.append('  %d [label=<%s>, style=filled, '
                     'fillcolor="#f0f3fa", color="#3b5aa8"];' % (i, html.escape(names[v])))
    lines.append('  0 [label="0", fillcolor="#f6dcdc"];')
    lines.append('  1 [label="1", fillcolor="#ddf0dd"];')
    for i, (v, lo, hi) in nodes.items():
        lines.append('  %d -> %d [label=<<font color="%s">0</font>>, '
                     'color="%s"];' % (i, lo, RED, RED))
        lines.append('  %d -> %d [label=<<font color="%s">1</font>>, '
                     'color="%s"];' % (i, hi, GREEN, GREEN))
    # one row per question: every node asking the same property shares a rank,
    # terminals share the bottom row. rank=same alone does NOT pin the rows'
    # relative order (an edge can skip a position when the world resolved a
    # property in that subtree, leaving nothing to force the rows apart), so
    # invisible edges chain each used row to the next.
    groups = {}
    for i, (v, lo, hi) in nodes.items():
        groups.setdefault(order.index(v), []).append(i)
    for r in sorted(groups):
        lines.append("  {rank=same; %s}" % " ".join(str(i) for i in sorted(groups[r])))
    lines.append("  {rank=same; 0; 1;}")
    used = sorted(groups)
    for a, b in zip(used, used[1:]):
        lines.append("  %d -> %d [style=invis, weight=10];" % (groups[a][0], groups[b][0]))
    lines.append("  newrank=true;")
    lines.append("  labelloc=t; labeljust=l;")
    lines.append('  label="asks: %s";' % " -> ".join(names[v] for v in order))
    lines.append("}")
    return "\n".join(lines)


def levels(bdd, names, order, dot_path):
    """Y coordinate of every node, from dot's own layout. Returns
    (rows, strict) where rows maps property name -> set of y values and
    strict is True iff each property has exactly one y and no two
    properties share one."""
    r = subprocess.run(["dot", "-Tplain", dot_path], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr)
    rows = {}
    for line in r.stdout.splitlines():
        parts = line.split()
        if parts and parts[0] == "node" and parts[1] in ("0", "1"):
            continue  # terminals share the bottom row on purpose
        if parts and parts[0] == "node":
            v = nodes_of(bdd)[int(parts[1])]
            rows.setdefault(names[v], set()).add(float(parts[3]))
    strict = (all(len(y) == 1 for y in rows.values())
              and len({next(iter(y)) for y in rows.values()}) == len(rows))
    return rows, strict


def nodes_of(bdd):
    root, nodes = bdd
    return {i: v for i, (v, lo, hi) in nodes.items()}


def render(bdd, names, path, order):
    dot = to_dot(bdd, names, order)
    src = path + ".dot"
    with open(src, "w") as f:
        f.write(dot)
    r = subprocess.run(["dot", "-Tpng", "-Gdpi=150", src, "-o", path],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("dot failed: %s\nDOT source:\n%s" % (r.stderr, dot[:2000]))
    return path


if __name__ == "__main__":
    n = int(sys.argv[1])
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else None
    if seed is None:
        import random
        seed = random.randrange(2**31)
        print("seed:", seed)
    names = ["p%d" % i for i in range(n)]
    q = generate_query(n, seed)
    w = generate_world(q, seed)
    worlds = allowed_worlds(w, names)
    answer = {s: q.evaluate(dict(zip(names, s))) for s in situations(names)}
    init = build(worlds, answer, list(range(n)))
    order, c = sift(worlds, answer)
    sifted = build(worlds, answer, order)
    print("query:", q)
    print("world:", w)
    print("worlds: %d of %d" % (len(worlds), 1 << n))
    print("before sift: %d nodes, after: %d nodes (order %s)" % (size(init), size(sifted), order))
    prefix = "bdd_n%d_s%d" % (n, seed)
    print(render(init, names, prefix + "_before.png", list(range(n))))
    print(render(sifted, names, prefix + "_after.png", order))