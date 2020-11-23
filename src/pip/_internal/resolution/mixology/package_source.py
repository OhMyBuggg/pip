import re
import sys


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
        self.package = {} # store candidate {package(class)):{version(class):candidate}}
        # must be list
        self.root_requirements = root_requirement # list[requirement] must be list

        super(PackageSource, self).__init__()

    @property
    def root_version(self):
        return self._root_version
    
    # we do not need to process the condition of root_package, instead of
    # calling _versions_for directly, version solver call versions_for which is in BasePackageSource
    # and it will help us to deal the problem I mention above
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

    def dependencies_for(self, package, version):  # type: (Hashable(package(class)), Any(version(version))) -> List[dependency]
        
        if package == self.root:
            requirements = self.root_requirements
            # print("__root__")
        else:
            # print("not root")
            candidate = self.package[package][version]
            requirements = self.provider.get_dependencies(candidate)
        
        # put candidate in requirement to self.package
        # in this way may take a lot of time in provider.find_match()
        # the better way is that chaeck self.package first if what requirement want
        # is already in self.package we would not call provider.find_match
        # if not call provider.find_match
        # for i in requirements:
        #     print("requirement", i)
        dependencies = [] # Constraint
        for requirement in requirements:

            if requirement.name not in self.package:
                package = Package(requirement.name)
                self.package[package] = {}

            # import pdb
            # pdb.set_trace()
            candidates = self.provider.find_matches([requirement])
            
            for candidate in candidates:
                # print(type(candidate.version))
                # print(dir(candidate.version))
                # print(candidate.version.__str__)
                version = Version.parse(candidate.version.__str__())
                package = Package(requirement.name)
                self.package[requirement.name][version] = candidate

            # change requirement to dependency (specifier to constraint)
            # and return dependency
            # requirements
            dependencies.append(self.convert_requirement(requirement))

        return dependencies

    def convert_dependency(self, dependency): 
        return dependency

    def convert_requirement(self, requirement):
        # convert requirement to the type which mixology recongize
        # requirement -> constraint
    
        if isinstance(requirement, ExplicitRequirement):
            # may occur problem because of unclean specifier
            #for_constraint = re.split(r'(===|==|~=|!=|>=|>|<=|<)', requirement.candidate.version)
            print("ExplicitRequirement")
            print(type(requirement.candidate.version))
            print(requirement.candidate.version)
            return Constraint(
                Package(requirement.name),
                Range(
                    Version.parse(requirement.candidate.version.__str__()), 
                    Version.parse(requirement.candidate.version.__str__()), True, True))
        
        elif isinstance(requirement, SpecifierRequirement):
            
            print("SpecifierRequirement")
            specs = requirement._ireq.req.specifier
            # print("specifier", specs)
            # print("type", type(specs))
            # if specs.contains("0.1.0"):
            #     print("accept")
            # print("length", len(specs))
            ranges = []
            if len(specs) == 0:
                # print("0")
                ranges = Range()
                ranges = [ranges]
                # print("length", len(ranges))
            for spec in specs:
                # print("specifier", spec.__str__())
                s = spec.__str__()
                print(s)
                temp_ranges = self.parse_specifier(s)
                ranges = ranges + temp_ranges
            
            # if there is a range only, error may happen (this problem is from "union and range" )
            
            if len(ranges) == 1:
                # print("ranges == 1")
                constraint = (Constraint(Package(requirement.name), ranges[0]))
            else:
                constraint = (Constraint(Package(requirement.name), Union(*ranges)))
        
        elif isinstance(requirement, RequiresPythonRequirement):
            print("RequiresPythonRequirement")

            specs = requirement.specifier

            ranges = []
            if len(specs) == 0:
                # print("0")
                ranges = Range()
                ranges = [ranges]
                # print("length", len(ranges))
            for spec in specs:
                # print("specifier", spec.__str__())
                s = spec.__str__()
                temp_ranges = self.parse_specifier(s)
                ranges = ranges + temp_ranges
            
            # if there is a range only, error may happen (this problem is from "union and range" )
            
            if len(ranges) == 1:
                # print("ranges == 1")
                constraint = (Constraint(Package(requirement.name), ranges[0]))
            else:
                constraint = (Constraint(Package(requirement.name), Union(*ranges)))
            
        else :
            print("some error happen")

        return constraint
    # Version.parse will return list of Range
    def parse_specifier(self, spec):
        # import pdb
        # pdb.set_trace()
        op_and_version = re.split(r'(===|==|~=|!=|>=|>|<=|<|\*)', spec) #list of str
        if op_and_version[1] == '===':
            # I surrender. I think it can't be transformed to range
            return [Range()]
        
        elif op_and_version[1] == '==' and len(op_and_version) != 4:
            # print("in == operator")
            # print(op_and_version[2])
            min = Version.parse(op_and_version[2])
            max = Version.parse(op_and_version[2])
            return [ Range(min, max, True, True) ]

        elif op_and_version[1] == '~=' or ( op_and_version[1] == '==' and len(op_and_version) == 4):
            
            count = len(op_and_version[2].split('.'))
            
            min = Version.parse(op_and_version[2])
            max = Version.parse(op_and_version[2])

            if count == 2:
                max = max._increment_major()
            elif count == 3:
                max = max._increment_minor()
            # import pdb
            # pdb.set_trace()
            return [ Range(min, max, True, False) ]
        
        elif op_and_version[1] == '!=':
            # separate into two range
            
            version = Version.parse(op_and_version[2])
            return [Range(min=version, max=None, include_min=False, include_max=False),
            Range(min=None, max=version, include_min=False, include_max=False)]
            
        elif op_and_version[1] == '>=':
            
            version = Version.parse(op_and_version[2])
            return [Range(min=version, max=None, include_min=True, include_max=False)]
        
        elif op_and_version[1] == '>':
            
            version = Version.parse(op_and_version[2])
            return [Range(min=version, max=None, include_min=False, include_max=False)]
        
        elif op_and_version[1] == '<=':
            
            version = Version.parse(op_and_version[2])
            return [Range(min=None, max=version, include_min=False, include_max=True)]
        
        elif op_and_version[1] == '<':
            
            version = Version.parse(op_and_version[2])
            return [Range(min=None, max=version, include_min=False, include_max=False)]
        
        else :
            print("error")
        
        return 0

    # to build mapping in result 
    def search_candidate(self, package, version):
        if package == self.root:
            return None
        candidate = self.package[package][version]
        return candidate

    def get_dependencies(self, candidate):
        if candidate == None:
            return self.root_requirements
        else:
            return self.provider.get_dependencies(candidate)

    # str -> str
    def padding(self, version):
        count = version.split('.')
        count = len(count)

        if count == 3:
            version = version
        elif count == 2:
            version = version + '.0'
        elif count == 1:
            version = version + '.0.0'
        else:
            print("error in padding")        
        return version, count
