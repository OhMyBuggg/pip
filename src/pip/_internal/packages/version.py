import re

from typing import List
from typing import Optional
from typing import Union

from .empty_constraint import EmptyConstraint
from .patterns import COMPLETE_VERSION
from .version_constraint import VersionConstraint
from .version_range import VersionRange
from .version_union import VersionUnion

class Version(VersionConstraint):
    def __init__(
        self,
        major,  # type: int
        minor=None,  # type: Optional[int]
        patch=None,  # type: Optional[int]
        # rest=None,  # type: Optional[int]
        # pre=None,  # type: Optional[str]
        # build=None,  # type: Optional[str]
        text=None,  # type: Optional[str]
        precision=None,  # type: Optional[int]
    ):
        self._major = int(major)
        self._precision = None
        if precision is None:
            self._precision = 1

        if minor is None:
            minor = 0
        else:
            if self._precision is not None:
                self._precision += 1

        self._minor = int(minor)

        if patch is None:
            patch = 0
        else:
            if self._precision is not None:
                self._precision += 1

        if precision is not None:
            self._precision = precision

        self._patch = int(patch)

        if text is None:
            parts = [str(major)]
            if self._precision >= 2 or minor != 0:
                parts.append(str(minor))

                if self._precision >= 3 or patch != 0:
                    parts.append(str(patch))

                # if self._precision >= 4 or rest != 0:
                #    parts.append(str(rest))

            text = ".".join(parts)
            # if pre:
            #     text += "-{}".format(pre)

            # if build:
            #     text += "+{}".format(build)

        self._text = text


    @property
    def __str__(self):
        return self._text

    def __repr__(self):
        return "<Version {}>".format(str(self))

    @classmethod
    def parse(cls, text):  # type: (str) -> Version
        try:
            match = COMPLETE_VERSION.match(text)
        except TypeError:
            match = None

        # if match is None:
        #     raise ParseVersionError('Unable to parse "{}".'.format(text))

        text = text.rstrip(".")

        major = int(match.group(1))
        minor = int(match.group(2)) if match.group(2) else None
        patch = int(match.group(3)) if match.group(3) else None
        # rest = int(match.group(4)) if match.group(4) else None

        # pre = match.group(5)
        # build = match.group(6)

        if build:
            build = build.lstrip("+")

        # return Version(major, minor, patch, rest, pre, build, text)
        return Version(major, minor, patch, text)
