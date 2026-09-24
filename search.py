"""Search over robot assignments (problem.md, The Search).

Phase 1: what happens in one decision moment.

At a decision moment every robot gets a destination point. Everyone
moves in a straight line at speed 1. A robot learns at every site with
an open property (one the remaining worlds still disagree on) that it
passes on the way or stops at. The moment ends at the first such site;
the robot there learns every property of the site, and the plan splits:
one branch per combination of values found among the remaining worlds,
weighted by its share of them, so every allowed world counts equally.
In each branch the diagram is redrawn from the worlds left, in the same
order: its top question is where the progressing robot goes next, or
there is no question and the answer is settled.

Worlds are tuples of bools in `names` order, as in generate.py.

Usage:
  python3 search.py     # the a & c example: head out early vs wait
"""

from bdd import build
from world import EPS


def dist(p, q):
    return ((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2) ** 0.5


def toward(p, q, d):
    """Where a robot at p is after moving d toward q; it stops at q."""
    L = dist(p, q)
    if L <= d:
        return q
    return (p[0] + (q[0] - p[0]) * d / L, p[1] + (q[1] - p[1]) * d / L)


def along(p, q, s):
    """How far a robot going straight from p to q travels before it is
    at s, or None if s is not on its path (both ends count)."""
    dx, dy = q[0] - p[0], q[1] - p[1]
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else ((s[0] - p[0]) * dx + (s[1] - p[1]) * dy) / L2
    t = max(0.0, min(1.0, t))  # the point of the path nearest s
    nearest = (p[0] + t * dx, p[1] + t * dy)
    return t * L2 ** 0.5 if dist(nearest, s) <= EPS else None


def open_properties(worlds):
    """Properties (indices) the remaining worlds disagree on."""
    return {i for i in range(len(worlds[0])) if len({w[i] for w in worlds}) == 2}


def next_question(worlds, answer, order):
    """Redraw the diagram from the remaining worlds and return its top
    question (a property index), or None if the answer is settled."""
    root, nodes = build(worlds, answer, order)
    return None if root < 2 else nodes[root][0]


def sites_for(space, names, i):
    """Coordinates of the sites where property i can be learned."""
    return [space.coords[s] for s in space.sites if names[i] in space.props_at(s)]


def first_stop(space, names, p, q, still_open):
    """The first site with an open property on the straight path from p
    to q (ends included). Returns (distance from p, its point, the open
    properties learned there), or None if the path reaches no such site."""
    best = None
    for s in space.sites:
        props = {names.index(x) for x in space.props_at(s) if x in names} & still_open
        d = along(p, q, space.coords[s]) if props else None
        if d is None:
            continue
        if best is None or d < best[0] - EPS:
            best = (d, space.coords[s], props)
        elif d <= best[0] + EPS:  # two sites at the same point
            best = (best[0], best[1], best[2] | props)
    return best


def step(space, names, worlds, positions, assignment):
    """Play one decision moment.

    positions, assignment: robot -> (x, y). Returns (dt, positions
    after dt, robots that learned, branches); each branch is (weight,
    {property: value}, worlds in the branch). Robots that learned stand
    at their site; the rest have moved dt toward their destination, or
    wait there if they arrived early.
    """
    assert set(assignment) == set(positions), "every robot needs a destination"
    still_open = open_properties(worlds)
    # No robot begins a moment on a site with an open property: robots
    # never start on a site, a robot that learns takes in every site at
    # its point, and the others stop short of their first open site. So
    # every moment takes time.
    for r, p in positions.items():
        assert first_stop(space, names, p, p, still_open) is None, \
            "robot %s begins on a site with an open property" % r
    stops = {}  # robot -> (distance to its first stop, point, properties)
    for r, p in positions.items():
        stop = first_stop(space, names, p, assignment[r], still_open)
        if stop is not None:
            stops[r] = stop
    if not stops:
        raise ValueError("no robot reaches a site with an open property")
    dt = min(d for d, _, _ in stops.values())
    learners = sorted(r for r, (d, _, _) in stops.items() if d <= dt + EPS)
    after = {r: stops[r][1] if r in learners else toward(p, assignment[r], dt)
             for r, p in positions.items()}
    learned = sorted(set().union(*(stops[r][2] for r in learners)))
    groups = {}
    for w in worlds:
        groups.setdefault(tuple(w[i] for i in learned), []).append(w)
    branches = [(len(g) / len(worlds), dict(zip(learned, values)), g)
                for values, g in groups.items()]
    return dt, after, learners, branches
    # learners - which robots learned new info
    # dt - minimum time taken among assignments (or just time taken)


if __name__ == "__main__":
    from formula import Formula
    from generate import situations
    from world import InvestigationSpace

    names = ["a", "c"]
    query = Formula("and", Formula("var", "a"), Formula("var", "c"))
    worlds = situations(names)  # no world model in this example
    answer = {w: query.evaluate(dict(zip(names, w))) for w in worlds}
    order = [0, 1]  # the diagram asks a, then c
    A, C = (10, 0), (22, 0)
    space = InvestigationSpace(["A", "C"], {"A": A, "C": C},
                               {"A": ["a"], "C": ["c"]},
                               {"R1": (0, 0), "R2": (20, 0)})

    def early(q, pos):  # R2 heads to c's site while R1 heads to a's
        return {"R1": A, "R2": C} if names[q] == "a" else {"R1": pos["R1"], "R2": C}

    def wait(q, pos):  # R2 stays until the diagram asks for c
        return {"R1": A, "R2": pos["R2"]} if names[q] == "a" else {"R1": pos["R1"], "R2": C}

    def play(policy, ws, pos, t, indent):
        """Follow a hand-written policy in every branch; return the
        average finish time over the worlds in `ws`."""
        q = next_question(ws, answer, order)
        if q is None:
            print("%sanswer %s at t=%.2f" % (indent, answer[ws[0]], t))
            return t
        dt, after, learners, branches = step(space, names, ws, pos, policy(q, pos))
        where = ", ".join("%s at %s" % (r, s) for r in learners
                          for s in space.sites if space.coords[s] == after[r])
        total = 0.0
        for weight, values, part in branches:
            found = ", ".join("%s=%s" % (names[i], v) for i, v in values.items())
            print("%st=%.2f %s learns %s (%d of %d worlds)"
                  % (indent, t + dt, where, found, len(part), len(ws)))
            total += weight * play(policy, part, after, t + dt, indent + "    ")
        return total

    for title, policy in (("R2 heads to c's site early", early),
                          ("R2 waits until the diagram asks for c", wait)):
        print(title)
        avg = play(policy, worlds, space.robots, 0.0, "  ")
        print("  average finish time %.2f\n" % avg)
