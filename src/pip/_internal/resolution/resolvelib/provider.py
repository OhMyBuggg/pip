import time

from pip._vendor.resolvelib.providers import AbstractProvider

from pip._internal.utils.typing import MYPY_CHECK_RUNNING

from .base import Constraint

if MYPY_CHECK_RUNNING:
    from typing import Any, Dict, Iterable, Optional, Sequence, Set, Tuple, Union

    from .base import Candidate, Requirement
    from .factory import Factory

# Notes on the relationship between the provider, the factory, and the
# candidate and requirement classes.
#
# The provider is a direct implementation of the resolvelib class. Its role
# is to deliver the API that resolvelib expects.
#
# Rather than work with completely abstract "requirement" and "candidate"
# concepts as resolvelib does, pip has concrete classes implementing these two
# ideas. The API of Requirement and Candidate objects are defined in the base
# classes, but essentially map fairly directly to the equivalent provider
# methods. In particular, `find_matches` and `is_satisfied_by` are
# requirement methods, and `get_dependencies` is a candidate method.
#
# The factory is the interface to pip's internal mechanisms. It is stateless,
# and is created by the resolver and held as a property of the provider. It is
# responsible for creating Requirement and Candidate objects, and provides
# services to those objects (access to pip's finder and preparer).


class PipProvider(AbstractProvider):
    def __init__(
        self,
        factory,  # type: Factory
        constraints,  # type: Dict[str, Constraint]
        ignore_dependencies,  # type: bool
        upgrade_strategy,  # type: str
        user_requested,  # type: Set[str]
    ):
        # type: (...) -> None
        self._factory = factory
        self._constraints = constraints
        self._ignore_dependencies = ignore_dependencies
        self._upgrade_strategy = upgrade_strategy
        self._user_requested = user_requested

        self.time = []

    def identify(self, dependency):
        # type: (Union[Requirement, Candidate]) -> str
        return dependency.name

    def get_preference(
        self,
        resolution,  # type: Optional[Candidate]
        candidates,  # type: Sequence[Candidate]
        information  # type: Sequence[Tuple[Requirement, Candidate]]
    ):
        # type: (...) -> Any
        self.time.append(time.time())

        transitive = all(parent is not None for _, parent in information)

        self.time.append(time.time())

        return (transitive, bool(candidates))

    def find_matches(self, requirements):
        # type: (Sequence[Requirement]) -> Iterable[Candidate]
        self.time.append(time.time())

        if not requirements:
            return []
        name = requirements[0].name

        def _eligible_for_upgrade(name):
            # type: (str) -> bool
            """Are upgrades allowed for this project?

            This checks the upgrade strategy, and whether the project was one
            that the user specified in the command line, in order to decide
            whether we should upgrade if there's a newer version available.

            (Note that we don't need access to the `--upgrade` flag, because
            an upgrade strategy of "to-satisfy-only" means that `--upgrade`
            was not specified).
            """
            if self._upgrade_strategy == "eager":
                return True
            elif self._upgrade_strategy == "only-if-needed":
                return (name in self._user_requested)
            return False

        for_record = self._factory.find_candidates(
            requirements,
            constraint=self._constraints.get(name, Constraint.empty()),
            prefers_installed=(not _eligible_for_upgrade(name)),
            )

        self.time.append(time.time())
        return for_record

    def is_satisfied_by(self, requirement, candidate):
        # type: (Requirement, Candidate) -> bool
        self.time.append(time.time())
        for_record = requirement.is_satisfied_by(candidate)
        self.time.append(time.time())
        return for_record

    def get_dependencies(self, candidate):
        # type: (Candidate) -> Sequence[Requirement]
        self.time.append(time.time())
        with_requires = not self._ignore_dependencies
        for_record = [
            r 
            for r in candidate.iter_dependencies(with_requires)
            if r is not None
            ]
        self.time.append(time.time())
        return for_record
