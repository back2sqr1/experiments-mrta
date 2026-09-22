"""The Formula class: a boolean formula over properties.

A situation is one True/False assignment of all properties. Both the
query (what the robots must decide) and the world model (what every
real situation obeys) are formulas, built from AND, OR, XOR, NOT,
IMPLIES (->), FORALL (all of the sub-formulas hold) and EXISTS (at
least one holds).
"""


class Formula:
    """A boolean formula. kind is one of 'var', 'not', 'and', 'or', 'xor',
    'implies', 'forall', 'exists'. A 'var' node holds a property name
    string; other nodes hold sub-formulas ('forall' and 'exists' take
    any number of them)."""

    def __init__(self, kind, *children):
        self.kind = kind
        self.children = children

    def evaluate(self, situation):
        """situation: dict mapping property name -> bool."""
        if self.kind == "var":
            return situation[self.children[0]]
        if self.kind == "not":
            return not self.children[0].evaluate(situation)
        if self.kind == "forall":
            return all(c.evaluate(situation) for c in self.children)
        if self.kind == "exists":
            return any(c.evaluate(situation) for c in self.children)
        a = self.children[0].evaluate(situation)
        b = self.children[1].evaluate(situation)
        if self.kind == "and":
            return a and b
        if self.kind == "or":
            return a or b
        if self.kind == "xor":
            return a != b
        if self.kind == "implies":
            return (not a) or b
        raise ValueError(self.kind)

    def variables(self):
        if self.kind == "var":
            return {self.children[0]}
        out = set()
        for c in self.children:
            out |= c.variables()
        return out

    def __str__(self):
        if self.kind == "var":
            return self.children[0]
        if self.kind == "not":
            return "~" + str(self.children[0])
        if self.kind in ("forall", "exists"):
            return self.kind + "(" + ", ".join(str(c) for c in self.children) + ")"
        op = {"and": "&", "or": "|", "xor": "^", "implies": "->"}[self.kind]
        return "(" + str(self.children[0]) + " " + op + " " + str(self.children[1]) + ")"

    __repr__ = __str__
