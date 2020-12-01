from typing import Any
from typing import Dict
from typing import Hashable

from pip._vendor.mixology.result import SolverResult as BaseSolverResult

class SolverResult(BaseSolverResult):
    def __init__(
        self, decisions, attempted_solutions, mapping, graph
    ):  # type: (Dict[Hashable, Any], int) -> None
        self._decisions = decisions
        self._attempted_solutions = attempted_solutions
        self._mapping = mapping
        self._graph = graph

    @property
    def mapping(self):
        return self._mapping

    @property
    def graph(self):
        return self._graph
