from pip._vendor.mixology.package_source import PackageSource as BasePackageSource
from pip._vendor.poetry_semver.version import Version
from pip._vendor.poetry_semver.constraint import Constraint
from pip._vendor.poetry_semver.range import Range
from pip._vendor.poetry_semver.union import Union


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
        # type: (Hashable, Any) -> List[dependency]
        if package == self.root:
            requirements = self.root_requirement
        else:
            candidate = self.package[package.name][version.version]
            requirements = self.provider._get_dependencies(candidate)

        # put candidate in requirement to self.package
        # in this way may take a lot of time in provider.find_match()
        # the better way is that check self.package first if what requirement want
        # is already in self.package we would not call provider.find_match
        # if not call provider.find_match
        for requirement in requirements:
            if requirement.name not in self.package:
                self.package[requirement.name] = {}
            candidates = self.provider.find_match(requirement)
            for candidate in candidates:
                self.package[requirement.name][candidate.version] = candidate

        # change requirement to dependency (specifier to constraint)
        # and return dependency 

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