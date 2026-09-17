"""The Query class: a boolean formula over properties.

A situation is one True/False assignment of all properties. A query is
built from AND, OR, XOR, NOT over those properties.
"""


class Query:
    """A boolean formula. kind is one of 'var', 'not', 'and', 'or', 'xor'.
    A 'var' node holds a property name string; other nodes hold sub-queries."""

    def __init__(self, kind, *children):
        self.kind = kind
        self.children = children

    def evaluate(self, situation):
        """situation: dict mapping property name -> bool."""
        if self.kind == "var":
            return situation[self.children[0]]
        if self.kind == "not":
            return not self.children[0].evaluate(situation)
        a = self.children[0].evaluate(situation)
        b = self.children[1].evaluate(situation)
        if self.kind == "and":
            return a and b
        if self.kind == "or":
            return a or b
        if self.kind == "xor":
            return a != b
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
        op = {"and": "&", "or": "|", "xor": "^"}[self.kind]
        return "(" + str(self.children[0]) + " " + op + " " + str(self.children[1]) + ")"

    __repr__ = __str__
