# -*- coding: utf-8 -*-
import logging
import time
import collections
import sys
import warnings

from typing import Dict
from typing import Hashable
from typing import List
from typing import Optional
from typing import Union

from pip._vendor.mixology.constraint import Constraint
from pip._vendor.mixology.incompatibility import Incompatibility
from pip._vendor.mixology.incompatibility_cause import NoVersionsCause
from pip._vendor.mixology.incompatibility_cause import RootCause
from pip._vendor.mixology.range import Range
from pip._internal.resolution.mixology.result import SolverResult
from pip._vendor.mixology.term import Term

from pip._vendor.resolvelib.structs import DirectedGraph

from pip._vendor.mixology.version_solver import VersionSolver as BaseVersionSolver
from pip._vendor.mixology.version_solver import _conflict
from .partial_solution import PartialSolution

logger = logging.getLogger(__name__)

# _conflict = object()


class VersionSolver(BaseVersionSolver):
    def __init__(self, source):
        super(VersionSolver, self).__init__(source)
        self._solution = PartialSolution()
        self._lock = set()
        
    
    def solve(self):  # type: () -> SolverResult
        """
        Finds a set of dependencies that match the root package's constraints,
        or raises an error if no such set is available.
        """
        start = time.time()
        
        self._add_incompatibility(
            Incompatibility(
                [Term(Constraint(self._source.root, Range()), False)], RootCause()
            )
        )
        self._propagate(self._source.root)

        i = 0
        while not self.is_solved():
            if not self._run() or i > 100:
                break
            i += 1

        # logger.info("Version solving took {:.3f} seconds".format(
        #         time.time() - start
        #     ))
        # logger.info(
        #     "Tried {} solutions.".format(
        #         self._solution.attempted_solutions
        #     )
        # )

        end = time.time()
        cost = end - start
        for i in range(0,len(self.timelist)-1):
            cost = cost - self.timelist[i+1] + self.timelist[i]
            i += 2
        print("Version solving took {} seconds".format(
                cost
            ))
        
        mapping = self._build_mapping()
        graph = self._build_graph(mapping)

        
        return SolverResult(
            self._solution.decisions, self._solution.attempted_solutions, mapping, graph
        )
        # return SolverResult(
        #     None, None, mapping, graph
        # )

    def _propagate(self, package):  # type: (Hashable) -> None
        """
        Performs unit propagation on incompatibilities transitively
        related to package to derive new assignments for _solution.
        """
        # start_start = time.time()
        # print("\nin propagate")
        # print(package)
        changed = set()
        changed.add(package)
        # print("init", changed)
        while changed:
            # print("set", changed)
            package = changed.pop()
            # print(package)
            # Iterate in reverse because conflict resolution tends to produce more
            # general incompatibilities as time goes on. If we look at those first,
            # we can derive stronger assignments sooner and more eagerly find
            # conflicts.
            # print("size", len(changed))
            # print("package",package)
            # print(package)
            for incompatibility in reversed(self._incompatibilities[package]):
                result = self._propagate_incompatibility(incompatibility)

                if result is _conflict:
                    # If the incompatibility is satisfied by the solution, we use
                    # _resolve_conflict() to determine the root cause of the conflict as a
                    # new incompatibility.
                    #
                    # It also backjumps to a point in the solution
                    # where that incompatibility will allow us to derive new assignments
                    # that avoid the conflict.
                    # root_cause = self._resolve_conflict(incompatibility)

                    # Back jumping erases all the assignments we did at the previous
                    # decision level, so we clear [changed] and refill it with the
                    # newly-propagated assignment.
                    # changed.clear()
                    # changed.add(str(self._propagate_incompatibility(root_cause)))
                    # print("conflict")
                    while True :
                        root_cause = self._resolve_conflict(incompatibility)
                        changed.clear()
                        temp_result = self._propagate_incompatibility(root_cause)
                        # print(root_cause)
                        if temp_result is _conflict:
                            # print("back conflict")
                            incompatibility = root_cause
                            
                        elif temp_result is None:
                            break
                        else :
                            changed.add(str(temp_result))
                            break

                    break
                elif result is not None:
                    changed.add(result)

    def _choose_package_version(self):  # type: () -> Union[Hashable, None]
        """
        Tries to select a version of a required package.

        Returns the name of the package whose incompatibilities should be
        propagated by _propagate(), or None indicating that version solving is
        complete and a solution has been found.
        """
        # print("\nin choose")
        term = self._next_term_to_try()
        if not term:
            return
        self.timelist.append(time.time())
        versions = self._source.versions_for(term.package, term.constraint.constraint)
        self.timelist.append(time.time())
        if not versions:
            # If there are no versions that satisfy the constraint,
            # add an incompatibility that indicates that.
            self._add_incompatibility(Incompatibility([term], NoVersionsCause()))

            return term.package

        version = versions[0]
        conflict = False
        # print("term.package", term.package, "version", version)
        self.timelist.append(time.time())
        incompatibilities, constraints = self._source.incompatibilities_for(term.package, version)
        self.timelist.append(time.time())

        # for constraint in constraints:
        #     # self._solution.derive(constraint, True, None)
        #     # 5 should be replace by a meaningful object
        #     print("\n eager!!!")
        #     for constraint, incompatibility in constraint.items():
        #         self._solution.derive(constraint, True, incompatibility)
        #         print("derivedd: {}".format(constraint))
        
        for incompatibility in incompatibilities:
            self._add_incompatibility(incompatibility)

            # If an incompatibility is already satisfied, then selecting version
            # would cause a conflict.
            #
            # We'll continue adding its dependencies, then go back to
            # unit propagation which will guide us to choose a better version.
            conflict = conflict or all(
                [
                    iterm.package == term.package or self._solution.satisfies(iterm)
                    for iterm in incompatibility.terms
                ]
            )

        if not conflict:
            self._solution.decide(term.package, version)
            # logger.info("selecting {} ({})".format(term.package, str(version)))

            for constraint in constraints:
                # self._solution.derive(constraint, True, None)
                # 5 should be replace by a meaningful object
                # print("\n eager!!!")
                for constraint, incompatibility in constraint.items():
                    record = constraint.package.name + str(constraint.constraint.min)
                    if record not in self._lock:
                        self._lock.add(record)
                        # print("constraint", constraint)
                        # print("incompatibility", incompatibility)
                        self._solution.derive(constraint, True, incompatibility)
                        # print("derivedd: {}".format(constraint))
                    else:
                        continue

            

        return term.package

    def _build_mapping(self):
        # logger.info("build mapping")
        # logger.info(self._solution.decisions)
        mapping = collections.OrderedDict() #str : candidate
        for package, version in self._solution.decisions.items():
            # print(package)
            # print(version)
            # print(1)
            # 如果不把_root_拿掉下面的search_candidate()會出現error
            # 因為_root_本來就不是真的存在的package
            # if package._name == "_root_":
            #     continue
            #version = self._solution.decisions[package]
            # if _root_ then None
            candidate = self._source.search_candidate(package, version)
            mapping[package.name] = candidate
            

        return mapping

    # 因為我在 _build_mapping() 把root拿掉了所以現在會出錯
    # 它找不到root在哪裡
    def _build_graph(self, mapping):
        graph = DirectedGraph()
        # print(mapping)
        for package, _ in self._solution.decisions.items():
            candidate = mapping[package.name]
            package = package.name
            #candidate = mapping[package]
            #print(package)
            if package not in graph:
                # print(package)
                if package == "_root_":
                    package = None
                graph.add(package)
            # else:
            #     print("already in", package)
            
            for requirement in self._source.get_dependencies(candidate):
                if requirement.name not in graph:
                    graph.add(requirement.name)
                
                graph.connect(package, requirement.name)
        
        mapping.pop("_root_")
        # print("length", len(graph))
        # print("content", graph._vertices)
        # print("mapping", mapping)
        return graph