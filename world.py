"""The InvestigationSpace: sites, what is known there, and the robots.

Not to be confused with the world MODEL (the constraint formula from
generate.py that filters situations): the InvestigationSpace is the map
the robots move through. Sites are 2d points; each site holds a subset
of the properties; a property may be witnessed at several sites, and a
site may hold several properties (one stop resolves all of them). Site
information is static -- observing never changes it.

Robots start at coordinates (not on a site); the two-robot fleet is the
default. The class guarantees every query property has at least one
witness site -- an unobservable property would make some worlds forever
undecidable, so it is unrepresentable here.
"""


class InvestigationSpace:
    """A 2d map of investigation sites plus the robot fleet.

    sites: list of names (any strings).
    coords: dict site -> (x, y).
    site_props: dict site -> list of property names.
    robots: dict robot name -> (x, y). A robot starting exactly on a
    site learns that site's properties at t=0 for free (see
    initial_observations).
    """

    def __init__(self, sites, coords, site_props, robots):
        self.sites = list(sites)
        self.coords = dict(coords)
        self.site_props = {s: list(site_props[s]) for s in self.sites}
        self.robots = dict(robots)
        self.check()

    def check(self):
        seen = set()
        for s in self.sites:
            if s in seen:
                raise ValueError("duplicate site name: %s" % s)
            seen.add(s)
            if s not in self.coords:
                raise ValueError("site %s has no coordinates" % s)
            if s not in self.site_props:
                raise ValueError("site %s has no property list" % s)
            if len(self.site_props[s]) == 0:
                raise ValueError("site %s observes nothing" % s)
        for r, p in self.robots.items():
            if not isinstance(p, tuple) or len(p) != 2:
                raise ValueError("robot %s needs an (x, y) start" % r)

    def check_query(self, query):
        """Every property the query depends on must be observable
        somewhere; an unobservable property makes those worlds forever
        undecidable."""
        missing = sorted(query.variables()
                         - {p for s in self.sites for p in self.site_props[s]})
        if missing:
            raise ValueError("no site witnesses: %s" % ", ".join(missing))

    # --- lookups -----------------------------------------------------
    def props_at(self, site):
        """Properties a robot learns by visiting site."""
        return tuple(self.site_props[site])

    def sites_with(self, prop):
        """Every site where prop can be observed (witnesses)."""
        return [s for s in self.sites if prop in self.site_props[s]]

    def dist(self, a, b):
        """Euclidean distance."""
        (x1, y1), (x2, y2) = self.coords[a], self.coords[b]
        return ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5

    def leg(self, robot, dest):
        """Distance of one move: from the robot's current position (a
        point, possibly off-site) to dest's coordinates."""
        (x1, y1) = self.robots[robot]
        (x2, y2) = self.coords[dest]
        return ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5

    # --- initial observations ------------------------------------------
    def initial_observations(self):
        """Properties resolved at t=0 because a robot starts on a site
        that witnesses them. Returns dict prop -> bool is not decidable
        (the site's static value is unknown before a world is chosen), so
        this returns the set of properties learned, and the caller pairs
        it with the found values during execution."""
        covered = set()
        for r, pos in self.robots.items():
            for s in self.sites:
                if self.coords[s] == pos:
                    covered |= set(self.site_props[s])
        return covered

    def __str__(self):
        rows = ["sites:"]
        for s in self.sites:
            rows.append("  %s %s: %s" % (s, self.coords[s],
                                         ", ".join(self.site_props[s])))
        rows.append("robots: " + ", ".join(
            "%s at %s" % (r, p) for r, p in self.robots.items()))
        return "\n".join(rows)
