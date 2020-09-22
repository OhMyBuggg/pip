from typing import Any
from typing import Dict
from typing import Hashable
from typing import List
from typing import Optional

from pip._internal.packages.version import Version
from pip._internal.packages.version_range import VersionRange
from pip._internal.packages.dependency import Dependency

from pip._vendor.resolvelib.mix.package_source import PackageSource as BasePackageSource
from pip._vendor.resolvelib.mix.range import Range
from pip._vendor.resolvelib.mix.constraint import Constraint
from pip._vendor.resolvelib.mix.union import Union
from pip._internal.packages.package import Package

class PackageSource(BasePackageSource):
    def __init__(self, provider):
        self._root_version = Version.parse("0.0.0")
        self._root_dependencies = []
        self._packages = {}
        self._provider = provider

        super(PackageSource, self).__init__()

    @property
    def root_version(self):
        return self._root_version

    def add(
        self, name, version, deps=None
    ):  # type: (str, str, Optional[Dict[str, str]]) -> None
        if deps is None:
            deps = {}

        version = Version.parse(version)
        if name not in self._packages:
            self._packages[name] = {}

        if version in self._packages[name]:
            raise ValueError("{} ({}) already exists".format(name, version))

        dependencies = []
        for dep_name, spec in deps.items():
            dependencies.append(Dependency(dep_name, spec))

        self._packages[name][version] = dependencies

    def root_dep(self, name, constraint):  # type: (str, str) -> None
        self._root_dependencies.append(Dependency(name, constraint))

    def _versions_for(self, package, constraint=None):
        if package not in self._packages:
            return []

        versions = []
        for version in self._packages[package].keys():
            if not constraint or constraint.allows_any(
                Range(version, version, True, True)
            ):
                versions.append(version)

        return sorted(versions, reverse=True)

    def dependencies_for(self, package, version):
        if package == self.root:
            return self._root_dependencies
        
        return self._packages[package][version]

    def convert_dependency(self, dependency): 
        ranges = [
                Range(
                    range.min,
                    range.max,
                    range.include_min,
                    range.include_max,
                    str(range),
                )
                for range in dependency.constraint.ranges
            ]
        constraint = Union.of(ranges)

        return Constraint(dependency.name, constraint)

    def convert_requirements(self, requirements):
        # change requirement -> criterion -> candidate -> _package
        # call add
        self._candidate = self._provider.find_matches(requirements)
        
        