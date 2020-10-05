import pytest
import sys
import  os
import sys

import  os
#myPath = os.path.dirname(os.path.abspath(__file__))
#sys.path.insert(1, myPath + '/../')
if __name__ == "__main__":
    sys.path[0] = ('C:\\Users\\chunw\\OneDrive\\桌面\\專題\\bug_pip_main\\pip\\src\\')
#from .. import package_source
#from pip._internal.package_source import PackageSource as pkg_src
from pip._internal.resolution.resolvelib.provider import PipProvider
from pip._internal.resolution.mixology.package_source import PackageSource
from pip._internal.resolution.mixology.package import Package

from pip._vendor.poetry_semver.version import Version

from pip._vendor.mixology.constraint import Constraint
from pip._vendor.mixology.range import Range
from pip._vendor.mixology.union import Union

from typing import Union as _Union


class my_pkg_source(PackageSource):

	def init_pkg(self,package):
		self.package=package


def test_version_for():

	p=my_pkg_source(PipProvider,None)
	pkg_name="numpy"

	assert p._versions_for(pkg_name,None) == []
	#test package not in packagesource

	version_1=Version(1,2,0)
	version_2=Version(1,5,1)
	test_package={pkg_name:{version_1:"candidate",version_2:"candidate2"}}
	p.init_pkg(test_package)
	
	set_result=set(p._versions_for(pkg_name,None))
	set_expect=set( [version_1,version_2] )
	assert set_result == set_expect
	#test package without constraint

	constraint_version_1=Version(1,2,0)
	constraint_version_2=Version(1,3,1)
	pkg_range_1=Range(constraint_version_1,constraint_version_2,True,True)

	constraint_version_3=Version(2,2,0)
	constraint_version_4=Version(2,3,1)
	pkg_range_2=Range(constraint_version_3,constraint_version_4,True,True)

	constraint_version_5=Version(3,2,0)
	constraint_version_6=Version(3,3,1)
	pkg_range_3=Range(constraint_version_5,constraint_version_6,True,True)

	pkg_union=Union([pkg_range_1,pkg_range_2])
	#pkg_Unions=_Union(pkg_range_3,pkg_union)

	numpy_constraint=Constraint(pkg_name,pkg_union)
	set_result=set(p._versions_for(pkg_name,numpy_constraint))

	set_expect=set([version_1])

	assert set_result == set_expect
	#test with constraint

	