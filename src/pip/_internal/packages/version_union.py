from typing import List

from .empty_constraint import EmptyConstraint
from .version_constraint import VersionConstraint

class VersionUnion(VersionConstraint):
    """
    use to represent version like <2.0.0 && >3.0.0
    """
    def __init__(self, *ranges):
        self._ranges = list(ranges)

    @property
    def ranges(self):
        return self._ranges