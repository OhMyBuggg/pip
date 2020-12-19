from typing import Any
from typing import Dict
from typing import Hashable
from typing import List

from pip._vendor.mixology._compat import OrderedDict
from pip._vendor.mixology.assignment import Assignment
from pip._vendor.mixology.constraint import Constraint
from pip._vendor.mixology.incompatibility import Incompatibility
from pip._vendor.mixology.package import Package
from pip._vendor.mixology.set_relation import SetRelation
from pip._vendor.mixology.term import Term

from pip._vendor.mixology.partial_solution import PartialSolution as BaseSolution

class PartialSolution(BaseSolution):
    def backtrack(self, decision_level):  # type: (int) -> None
        """
        Resets the current decision level to decision_level, and removes all
        assignments made after that level.
        """
        self._backtracking = True
        # print("backtracking")
        # print("decision", self._decisions)
        # print("before", self._assignments)
        packages = set()
        while self._assignments[-1].decision_level > decision_level:
            removed = self._assignments.pop(-1)
            packages.add(removed.package)
            # print(removed.package)
            # print(self._assignments)
            if removed.is_decision():
                # print(self._decisions[removed.package])
                del self._decisions[removed.package]
        # print("decision", self._decisions)

        # Re-compute _positive and _negative for the packages that were removed.
        for package in packages:
            if package in self._positive:
                del self._positive[package]

            if package in self._negative:
                del self._negative[package]

        for assignment in self._assignments:
            if assignment.package in packages:
                self._register(assignment)
        
        # print("after", self._assignments)