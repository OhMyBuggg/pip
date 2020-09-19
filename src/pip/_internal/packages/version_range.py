from typing import List

from .empty_constraint import EmptyConstraint
from .version_constraint import VersionConstraint
from .version_union import VersionUnion

class VersionRange(VersionConstraint):
    def __init__(
        self,
        min=None,
        max=None,
        include_min=False,
        include_max=False,
    ):
        self._min = min
        self._max = max
        self._inclde_min = include_min
        self._inclde_max = include_max
    