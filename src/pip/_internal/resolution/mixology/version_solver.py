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
from pip._vendor.mixology.failure import SolverFailure
from pip._vendor.mixology.incompatibility import Incompatibility
from pip._vendor.mixology.incompatibility_cause import ConflictCause
from pip._vendor.mixology.incompatibility_cause import NoVersionsCause
from pip._vendor.mixology.incompatibility_cause import RootCause
from pip._internal.resolution.mixology.package_source import PackageSource
from pip._vendor.mixology.partial_solution import PartialSolution
from pip._vendor.mixology.range import Range
from pip._internal.resolution.mixology.result import SolverResult
from pip._vendor.mixology.set_relation import SetRelation
from pip._vendor.mixology.term import Term

from pip._vendor.resolvelib.structs import DirectedGraph


logger = logging.getLogger(__name__)

_conflict = object()


class VersionSolver:
    """
    The version solver that finds a set of package versions that satisfy the
    root package's dependencies.

    See https://github.com/dart-lang/pub/tree/master/doc/solver.md for details
    on how this solver works.
    """

    def __init__(
        self, source,  # type: PackageSource
    ):
        self._source = source

        self._incompatibilities = {}  # type: Dict[Hashable, List[Incompatibility]]
        self._solution = PartialSolution()

    @property
    def solution(self):  # type: () -> PartialSolution
        return self._solution

    def is_solved(self):  # type: () -> bool
        return not self._solution.unsatisfied

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

    def _run(self):  # type: () -> bool
        if self.is_solved():
            return False

        next_package = self._choose_package_version()
        # add the assignment if only-if-needed

        self._propagate(next_package)

        if self.is_solved():
            return False

        return True

    def _propagate(self, package):  # type: (Hashable) -> None
        """
        Performs unit propagation on incompatibilities transitively
        related to package to derive new assignments for _solution.
        """
        changed = set()
        changed.add(package)

        while changed:
            package = changed.pop()

            # Iterate in reverse because conflict resolution tends to produce more
            # general incompatibilities as time goes on. If we look at those first,
            # we can derive stronger assignments sooner and more eagerly find
            # conflicts.
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
                    root_cause = self._resolve_conflict(incompatibility)

                    # Back jumping erases all the assignments we did at the previous
                    # decision level, so we clear [changed] and refill it with the
                    # newly-propagated assignment.
                    changed.clear()
                    changed.add(str(self._propagate_incompatibility(root_cause)))
                    break
                elif result is not None:
                    changed.add(result)

    def _propagate_incompatibility(
        self, incompatibility
    ):  # type: (Incompatibility) -> Union[str, _conflict, None]
        """
        If incompatibility is almost satisfied by _solution, adds the
        negation of the unsatisfied term to _solution.

        If incompatibility is satisfied by _solution, returns _conflict. If
        incompatibility is almost satisfied by _solution, returns the
        unsatisfied term's package name.

        Otherwise, returns None.
        """
        # The first entry in incompatibility.terms that's not yet satisfied by
        # _solution, if one exists. If we find more than one, _solution is
        # inconclusive for incompatibility and we can't deduce anything.
        unsatisfied = None

        for term in incompatibility.terms:
            relation = self._solution.relation(term)

            if relation == SetRelation.DISJOINT:
                # If term is already contradicted by _solution, then
                # incompatibility is contradicted as well and there's nothing new we
                # can deduce from it.
                return
            elif relation == SetRelation.OVERLAPPING:
                # If more than one term is inconclusive, we can't deduce anything about
                # incompatibility.
                if unsatisfied is not None:
                    return

                # If exactly one term in incompatibility is inconclusive, then it's
                # almost satisfied and [term] is the unsatisfied term. We can add the
                # inverse of the term to _solution.
                unsatisfied = term

        # If *all* terms in incompatibility are satisfied by _solution, then
        # incompatibility is satisfied and we have a conflict.
        if unsatisfied is None:
            return _conflict

        logger.info("derived: {}".format(unsatisfied.inverse))

        self._solution.derive(
            unsatisfied.constraint, not unsatisfied.is_positive(), incompatibility
        )

        return unsatisfied.package

    def _resolve_conflict(
        self, incompatibility
    ):  # type: (Incompatibility) -> Incompatibility
        """
        Given an incompatibility that's satisfied by _solution,
        The `conflict resolution`_ constructs a new incompatibility that encapsulates the root
        cause of the conflict and backtracks _solution until the new
        incompatibility will allow _propagate() to deduce new assignments.

        Adds the new incompatibility to _incompatibilities and returns it.

        .. _conflict resolution: https://github.com/dart-lang/pub/tree/master/doc/solver.md#conflict-resolution
        """
        logger.info("conflict: {}".format(incompatibility))
        logger.info("conflict: {}".format(incompatibility))

        new_incompatibility = False
        while not incompatibility.is_failure():
            # The term in incompatibility.terms that was most recently satisfied by
            # _solution.
            most_recent_term = None

            # The earliest assignment in _solution such that incompatibility is
            # satisfied by _solution up to and including this assignment.
            most_recent_satisfier = None

            # The difference between most_recent_satisfier and most_recent_term;
            # that is, the versions that are allowed by most_recent_satisfier and not
            # by most_recent_term. This is None if most_recent_satisfier totally
            # satisfies most_recent_term.
            difference = None

            # The decision level of the earliest assignment in _solution *before*
            # most_recent_satisfier such that incompatibility is satisfied by
            # _solution up to and including this assignment plus
            # most_recent_satisfier.
            #
            # Decision level 1 is the level where the root package was selected. It's
            # safe to go back to decision level 0, but stopping at 1 tends to produce
            # better error messages, because references to the root package end up
            # closer to the final conclusion that no solution exists.
            previous_satisfier_level = 1

            for term in incompatibility.terms:
                satisfier = self._solution.satisfier(term)

                if most_recent_satisfier is None:
                    most_recent_term = term
                    most_recent_satisfier = satisfier
                elif most_recent_satisfier.index < satisfier.index:
                    previous_satisfier_level = max(
                        previous_satisfier_level, most_recent_satisfier.decision_level
                    )
                    most_recent_term = term
                    most_recent_satisfier = satisfier
                    difference = None
                else:
                    previous_satisfier_level = max(
                        previous_satisfier_level, satisfier.decision_level
                    )

                if most_recent_term == term:
                    # If most_recent_satisfier doesn't satisfy most_recent_term on its
                    # own, then the next-most-recent satisfier may be the one that
                    # satisfies the remainder.
                    difference = most_recent_satisfier.difference(most_recent_term)
                    if difference is not None:
                        previous_satisfier_level = max(
                            previous_satisfier_level,
                            self._solution.satisfier(difference.inverse).decision_level,
                        )

            # If most_recent_identifier is the only satisfier left at its decision
            # level, or if it has no cause (indicating that it's a decision rather
            # than a derivation), then incompatibility is the root cause. We then
            # backjump to previous_satisfier_level, where incompatibility is
            # guaranteed to allow _propagate to produce more assignments.
            if (
                previous_satisfier_level < most_recent_satisfier.decision_level
                or most_recent_satisfier.cause is None
            ):
                self._solution.backtrack(previous_satisfier_level)
                if new_incompatibility:
                    self._add_incompatibility(incompatibility)

                return incompatibility

            # Create a new incompatibility by combining incompatibility with the
            # incompatibility that caused most_recent_satisfier to be assigned. Doing
            # this iteratively constructs an incompatibility that's guaranteed to be
            # true (that is, we know for sure no solution will satisfy the
            # incompatibility) while also approximating the intuitive notion of the
            # "root cause" of the conflict.
            new_terms = []
            for term in incompatibility.terms:
                if term != most_recent_term:
                    new_terms.append(term)

            for term in most_recent_satisfier.cause.terms:
                if term.package != most_recent_satisfier.package:
                    new_terms.append(term)

            # The most_recent_satisfier may not satisfy most_recent_term on its own
            # if there are a collection of constraints on most_recent_term that
            # only satisfy it together. For example, if most_recent_term is
            # `foo ^1.0.0` and _solution contains `[foo >=1.0.0,
            # foo <2.0.0]`, then most_recent_satisfier will be `foo <2.0.0` even
            # though it doesn't totally satisfy `foo ^1.0.0`.
            #
            # In this case, we add `not (most_recent_satisfier \ most_recent_term)` to
            # the incompatibility as well, See the `algorithm documentation`_ for
            # details.
            #
            # .. _algorithm documentation: https://github.com/dart-lang/pub/tree/master/doc/solver.md#conflict-resolution
            if difference is not None:
                new_terms.append(difference.inverse)

            incompatibility = Incompatibility(
                new_terms, ConflictCause(incompatibility, most_recent_satisfier.cause)
            )
            new_incompatibility = True

            partially = "" if difference is None else " partially"
            bang = "!"
            logger.info(
                "{} {} is{} satisfied by {}".format(
                    bang, most_recent_term, partially, most_recent_satisfier
                )
            )
            logger.info(
              '{} which is caused by "{}"'.format(bang, most_recent_satisfier.cause)
            )
            logger.info("{} thus: {}".format(bang, incompatibility))

        raise SolverFailure(incompatibility)

    def _next_term_to_try(self):  # type: () -> Optional[Term]
        unsatisfied = self._solution.unsatisfied
        if not unsatisfied:
            return

        # Prefer packages with as few remaining versions as possible,
        # so that if a conflict is necessary it's forced quickly.
        def _get_min(term):
            return len(
                self._source.versions_for(term.package, term.constraint.constraint)
            )

        if len(unsatisfied) == 1:
            term = unsatisfied[0]
        else:
            term = min(*unsatisfied, key=_get_min)

        return term

    def _choose_package_version(self):  # type: () -> Union[Hashable, None]
        """
        Tries to select a version of a required package.

        Returns the name of the package whose incompatibilities should be
        propagated by _propagate(), or None indicating that version solving is
        complete and a solution has been found.
        """
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
            self._solution.derive(constraint, True, None)
        
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
            logger.info("selecting {} ({})".format(term.package, str(version)))

        return term.package

    def _add_incompatibility(self, incompatibility):  # type: (Incompatibility) -> None
        # print("incompatibility")
        # print(type(incompatibility))
        # print(incompatibility.terms)

        # print(incompatibility)
        logger.info("fact: {}".format(incompatibility))

        for term in incompatibility.terms:
            if term.package not in self._incompatibilities:
                self._incompatibilities[term.package] = []

            if incompatibility in self._incompatibilities[term.package]:
                continue

            self._incompatibilities[term.package].append(incompatibility)

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