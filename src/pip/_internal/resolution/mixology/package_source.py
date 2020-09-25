import re
import sys
if __name__ == "__main__":
    sys.path[0] = ('/mnt/c/Users/wchiung.cs06/Desktop/graduate_project/pip-develop/src/')
from pip._internal.resolution.resolvelib.provider import PipProvider
from pip._internal.resolution.resolvelib.requirements import (
    ExplicitRequirement,
    SpecifierRequirement,
    RequiresPythonRequirement,
)
from pip._internal.resolution.mixology.dependency import Dependency
from pip._internal.resolution.mixology.package import Package

from pip._vendor.poetry_semver.version import Version
from pip._vendor.poetry_semver.version_range import VersionRange
from pip._vendor.poetry_semver import parse_constraint
from pip._vendor.mixology.package_source import PackageSource as BasePackageSource
from pip._vendor.mixology.constraint import Constraint
from pip._vendor.mixology.range import Range
from pip._vendor.mixology.union import Union


class PackageSource(BasePackageSource):
    def __init__(self, provider, root_requirement):
        self._root_version = Version.parse("0.0.0")
        self.provider = provider
        self.package = {} # store candidate
        # must be list
        self.root_requirements = root_requirement # list[requirement] must be list

        super(PackageSource, self).__init__()

    @property
    def root_version(self):
        return self._root_version

    def _versions_for(self, package, constraint=None):
        if package not in self.package:
            return []

        versions = []
        for version in self.package[package].keys():
            if not constraint or constraint.allows_any(
                Range(version, version, True, True)
            ):
                versions.append(version)

        return sorted(versions, reverse=True)

    def dependencies_for(self, package, version):  # type: (Hashable, Any) -> List[dependency]
        
        if package == self.root:
            requirements = self.root_requirements
        else:
            candidate = self.package[package.name][version.version]
            requirements = self.provider._get_dependencies(candidate)
        
        # put candidate in requirement to self.package
        # in this way may take a lot of time in provider.find_match()
        # the better way is that chaeck self.package first if what requirement want
        # is already in self.package we would not call provider.find_match
        # if not call provider.find_match

        dependencies = [] # Constraint
        for requirement in requirements:

            if requirement.name not in self.package:
                self.package[requirement.name] = {}
            candidates = self.provider.find_match(requirement)
            for candidate in candidates:
                self.package[requirement.name][candidate.version] = candidate

            # change requirement to dependency (specifier to constraint)
            # and return dependency
            # requirements
            dependencies.append(self.convert_requirement(requirement))

        return dependencies

    def convert_dependency(self, dependency): 
        return dependency

    def convert_requirement(self, requirement):
        constraints = []
        if isinstance(requirement, ExplicitRequirement):
            # may occur problem because of unclean specifier
            #for_constraint = re.split(r'(===|==|~=|!=|>=|>|<=|<)', requirement.candidate.version)
            return Constraint(
                Package(requirement.name),
                Range(
                    Version.parse(requirement.candidate.version), 
                    Version.parse(requirement.candidate.version), True, True))
        
        elif isinstance(requirement, SpecifierRequirement):
            
            specs = requirement._ireq.req.specifier
            ranges = []
            for spec in specs:
                s = spec.__str__()
                temp_range = self.parse_specifier(s)
                ranges.append(temp_range)
            
            constraints.append(Constraint(Package(requirement.name), Union(*ranges)))
        
        elif isinstance(requirement, RequiresPythonRequirement):
            pass
        else :
            pass

        return constraints
    # Version.parse will return a Version
    def parse_specifier(self, spec):
        
        op_and_version = re.split(r'(===|==|~=|!=|>=|>|<=|<)', spec) #list of str
        if op_and_version[1] == '===':
            print()
        elif op_and_version[1] == '==':
            return Range(
                Version.parse(op_and_version[2]), 
                Version.parse(op_and_version[2]), True, True)

        elif op_and_version[1] == '~=':
            return Range(
                Version.parse(op_and_version[2]), 
                Version.parse(op_and_version[2]), True, True)
        elif op_and_version[1] == '!=':
            print()
        elif op_and_version[1] == '>=':
            print()
        elif op_and_version[1] == '>':
            print()
        elif op_and_version[1] == '<=':
            print()
        elif op_and_version[1] == '<':
            print()
        else :
            print("error")
        
        return 0
