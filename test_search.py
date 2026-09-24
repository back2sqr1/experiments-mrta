"""Checks for search.py, phase 1 (plain python, no pytest).

Run: python3 test_search.py
"""

from formula import Formula
from generate import situations, allowed_worlds
from world import InvestigationSpace
from search import dist, toward, along, open_properties, next_question, sites_for, step

V = lambda s: Formula("var", s)


def make(sites, robots):
    """sites: name -> ((x, y), [properties])."""
    return InvestigationSpace(list(sites), {s: xy for s, (xy, _) in sites.items()},
                              {s: ps for s, (_, ps) in sites.items()}, robots)


AC = make({"A": ((10, 0), ["a"]), "C": ((22, 0), ["c"])},
          {"R1": (0, 0), "R2": (20, 0)})
NAMES = ["a", "c"]
ALL = situations(NAMES)


def by_values(branches):
    return {tuple(sorted(v.items())): w for w, v, _ in branches}


def test_toward():
    assert toward((0, 0), (10, 0), 3) == (3.0, 0.0)
    assert toward((0, 0), (10, 0), 30) == (10, 0)  # stops at the target
    p = toward((0, 0), (3, 4), 2.5)
    assert abs(dist((0, 0), p) - 2.5) < 1e-12 and abs(dist(p, (3, 4)) - 2.5) < 1e-12


def test_along():
    assert along((0, 0), (10, 0), (4, 0)) == 4
    assert along((0, 0), (10, 0), (0, 0)) == 0      # start counts
    assert along((0, 0), (10, 0), (10, 0)) == 10    # end counts
    assert along((0, 0), (10, 0), (11, 0)) is None  # past the end
    assert along((0, 0), (10, 0), (-1, 0)) is None  # behind the start
    assert along((0, 0), (10, 0), (4, 1)) is None   # off the path
    assert along((0, 0), (6, 8), (3, 4)) == 5       # diagonal
    assert along((2, 2), (2, 2), (2, 2)) == 0       # staying put, on the point
    assert along((2, 2), (2, 2), (3, 2)) is None


def test_open_properties():
    assert open_properties(ALL) == {0, 1}
    assert open_properties([w for w in ALL if w[0]]) == {1}


def test_sites_for():
    assert sites_for(AC, NAMES, 0) == [(10, 0)]
    sp = make({"X": ((0, 5), ["a"]), "Y": ((9, 9), ["a", "c"])}, {"R1": (0, 0)})
    assert sites_for(sp, NAMES, 0) == [(0, 5), (9, 9)]


def test_robot_cannot_start_on_a_site():
    for start in [(10, 0), (10, 1e-12)]:
        try:
            make({"A": ((10, 0), ["a"])}, {"R1": start})
        except ValueError:
            continue
        raise AssertionError("robot starting on a site was accepted: %s" % (start,))
    make({"A": ((10, 0), ["a"])}, {"R1": (10, 0.001)})  # close by is fine


def test_step_refuses_a_robot_on_an_open_site():
    try:
        step(AC, NAMES, ALL, {"R1": (10, 0), "R2": (20, 0)},
             {"R1": (22, 0), "R2": (22, 0)})
    except AssertionError as e:
        assert "open property" in str(e)
        return
    raise AssertionError("expected AssertionError")


def test_first_arrival_ends_the_moment():
    dt, after, learners, branches = step(AC, NAMES, ALL, AC.robots,
                                         {"R1": (10, 0), "R2": (22, 0)})
    assert dt == 2 and learners == ["R2"]
    assert after == {"R1": (2.0, 0.0), "R2": (22, 0)}
    assert by_values(branches) == {((1, False),): 0.5, ((1, True),): 0.5}


def test_passing_a_site_learns_there():
    # R1 is sent to C and passes A on the way: it learns a at A, not c
    dt, after, learners, branches = step(AC, NAMES, ALL, AC.robots,
                                         {"R1": (22, 0), "R2": (20, 0)})
    assert dt == 10 and learners == ["R1"]
    assert after == {"R1": (10, 0), "R2": (20, 0)}
    assert by_values(branches) == {((0, False),): 0.5, ((0, True),): 0.5}


def test_passing_a_known_site_does_not_stop():
    a_true = [w for w in ALL if w[0]]  # a already learned: true
    dt, after, learners, branches = step(AC, NAMES, a_true, AC.robots,
                                         {"R1": (22, 0), "R2": (20, 0)})
    assert dt == 22 and learners == ["R1"] and after["R1"] == (22, 0)
    assert by_values(branches) == {((1, False),): 0.5, ((1, True),): 0.5}


def test_passing_a_site_on_a_diagonal():
    sp = make({"M": ((3, 4), ["a"]), "C": ((50, 50), ["c"])},
              {"R1": (0, 0), "R2": (50, 0)})
    dt, after, learners, _ = step(sp, NAMES, ALL, sp.robots,
                                  {"R1": (6, 8), "R2": (50, 0)})
    assert dt == 5 and learners == ["R1"] and after["R1"] == (3, 4)


def test_near_miss_is_not_passing():
    # M sits 0.001 off R1's path: R1 goes past it and waits at (6, 8)
    sp = make({"M": ((3, 4.001), ["a"]), "C": ((50, 50), ["c"])},
              {"R1": (0, 0), "R2": (50, 0)})
    dt, after, learners, _ = step(sp, NAMES, ALL, sp.robots,
                                  {"R1": (6, 8), "R2": (50, 50)})
    assert dt == 50 and learners == ["R2"] and after["R1"] == (6, 8)


def test_two_sites_at_one_point_are_learned_together():
    sp = make({"X": ((5, 0), ["a"]), "Y": ((5, 0), ["c"])}, {"R1": (0, 0)})
    dt, _, learners, branches = step(sp, NAMES, ALL, sp.robots, {"R1": (9, 0)})
    assert dt == 5 and learners == ["R1"] and len(branches) == 4


def test_waiting_point_does_not_end_the_moment():
    dt, after, learners, _ = step(AC, NAMES, ALL, AC.robots,
                                  {"R1": (10, 0), "R2": (15, 0)})
    assert dt == 10 and learners == ["R1"]
    assert after["R2"] == (15, 0)  # got there at t=5 and waited


def test_simultaneous_arrivals_both_learn():
    sp = make({"A": ((-5, 0), ["a"]), "B": ((5, 0), ["b"])},
              {"R1": (0, 0), "R2": (0, 0)})
    names = ["a", "b"]
    dt, _, learners, branches = step(sp, names, situations(names), sp.robots,
                                     {"R1": (-5, 0), "R2": (5, 0)})
    assert dt == 5 and learners == ["R1", "R2"] and len(branches) == 4


def test_staying_off_site_just_waits():
    # R2 is told to stay at (20, 0), where there is no site: it does not move
    dt, after, learners, _ = step(AC, NAMES, ALL, AC.robots,
                                  {"R1": (10, 0), "R2": (20, 0)})
    assert dt == 10 and learners == ["R1"] and after["R2"] == (20, 0)


def test_staying_on_a_known_site_just_waits():
    # R1 learns a at A; in the a=true branch it stays on A (nothing open
    # there now) while R2 heads to C
    dt, after, _, branches = step(AC, NAMES, ALL, AC.robots,
                                  {"R1": (10, 0), "R2": (20, 0)})
    assert dt == 10 and after["R1"] == (10, 0)
    a_true = [g for _, v, g in branches if v == {0: True}][0]
    dt, after, learners, _ = step(AC, NAMES, a_true, after,
                                  {"R1": (10, 0), "R2": (22, 0)})
    assert dt == 2 and learners == ["R2"] and after["R1"] == (10, 0)


def test_branches_split_the_worlds():
    _, _, _, branches = step(AC, NAMES, ALL, AC.robots, {"R1": (10, 0), "R2": (22, 0)})
    assert abs(sum(w for w, _, _ in branches) - 1) < 1e-12
    parts = [set(g) for _, _, g in branches]
    assert set().union(*parts) == set(ALL) and sum(map(len, parts)) == len(ALL)
    for _, values, g in branches:
        assert all(w[i] == v for w in g for i, v in values.items())


def test_site_with_two_properties_splits_on_combinations_that_exist():
    names = ["a", "b", "c"]
    worlds = allowed_worlds(Formula("implies", V("b"), V("c")), names)  # 6 of 8
    sp = make({"S": ((3, 4), ["b", "c"]), "A": ((9, 9), ["a"])},
              {"R1": (0, 0), "R2": (9, 0)})
    _, _, _, branches = step(sp, names, worlds, sp.robots, {"R1": (3, 4), "R2": (9, 0)})
    combos = sorted(tuple(v[i] for i in (1, 2)) for _, v, _ in branches)
    assert combos == [(False, False), (False, True), (True, True)]  # b=T, c=F ruled out
    assert all(abs(w - 2 / 6) < 1e-12 for w, _, _ in branches)


def test_known_property_does_not_end_the_moment():
    c_true = [w for w in ALL if w[1]]  # c already learned: true
    dt, _, learners, _ = step(AC, NAMES, c_true, AC.robots,
                              {"R1": (10, 0), "R2": (22, 0)})
    assert dt == 10 and learners == ["R1"]


def test_redraw_settles_as_soon_as_the_answer_is_known():
    q = Formula("and", V("a"), V("c"))
    ans = {w: q.evaluate(dict(zip(NAMES, w))) for w in ALL}
    assert next_question(ALL, ans, [0, 1]) == 0                             # asks a first
    assert next_question([w for w in ALL if not w[1]], ans, [0, 1]) is None  # c=F: settled
    assert next_question([w for w in ALL if w[1]], ans, [0, 1]) == 0         # c=T: still a


def test_redraw_uses_the_world_model():
    # query a & c, model b -> c; with b=T and a=T known, c must be true
    names = ["a", "b", "c"]
    q = Formula("and", V("a"), V("c"))
    worlds = allowed_worlds(Formula("implies", V("b"), V("c")), names)
    ans = {w: q.evaluate(dict(zip(names, w))) for w in situations(names)}
    assert next_question([w for w in worlds if w[0] and w[1]], ans, [0, 2, 1]) is None


def test_no_useful_destination_is_an_error():
    try:
        step(AC, NAMES, ALL, AC.robots, {"R1": (1, 1), "R2": (2, 2)})
    except ValueError:
        return
    raise AssertionError("expected ValueError")


if __name__ == "__main__":
    tests = [f for name, f in sorted(globals().items()) if name.startswith("test_")]
    for f in tests:
        f()
        print("ok ", f.__name__)
    print("%d checks passed" % len(tests))
