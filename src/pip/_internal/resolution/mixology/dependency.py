from pip._vendor.mixology.constraint import Constraint

class Dependency(object):
    def __init__(self, name, constraints):
        self._name = name
        self._constraints = constraints
    
    def __eq__(self, other):
        if isinstance(other, Dependency):
            return NotImplemented

        return (self._name == other.name
            and self._constraints == other.constraints)