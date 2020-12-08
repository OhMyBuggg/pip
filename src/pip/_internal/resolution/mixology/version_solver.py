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


logger = logging.getLogger(__name__)

_conflict = object()


class VersionSolver(BaseVersionSolver):
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
            if not self._run() or i > 10:
                break
            i += 1

        logger.info("Version solving took {:.3f} seconds.\n")
        logger.info(
            "Tried {} solutions.".format(
                time.time() - start, self._solution.attempted_solutions
            )
        )

        mapping = self._build_mapping()
        graph = self._build_graph(mapping)

        print()
        print("content", graph._vertices)
        print("mapping", mapping)
        print()
        return SolverResult(
            self._solution.decisions, self._solution.attempted_solutions, mapping, graph
        )
        # return SolverResult(
        #     None, None, mapping, graph
        # )

    def _choose_package_version(self):  # type: () -> Union[Hashable, None]
        """
        Tries to select a version of a required package.

        Returns the name of the package whose incompatibilities should be
        propagated by _propagate(), or None indicating that version solving is
        complete and a solution has been found.
        """
        print("\nin choose")
        term = self._next_term_to_try()
        if not term:
            return

        versions = self._source.versions_for(term.package, term.constraint.constraint)
        if not versions:
            # If there are no versions that satisfy the constraint,
            # add an incompatibility that indicates that.
            self._add_incompatibility(Incompatibility([term], NoVersionsCause()))

            return term.package

        version = versions[0]
        conflict = False
        # print("term.package", term.package, "version", version)
        incompatibilities, constraints = self._source.incompatibilities_for(term.package, version)
        for constraint in constraints:
            # self._solution.derive(constraint, True, None)
            # 5 should be replace by a meaningful object
            self._solution.derive(constraint, True, 5)
        
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
            logger.info("selecting {} ({})".format(term.package, str(version)))

        return term.package

    def _build_mapping(self):
        logger.info("build mapping")
        logger.info(self._solution.decisions)
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