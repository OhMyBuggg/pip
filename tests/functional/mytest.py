import json
import os
import sys
import textwrap

import pytest
from pip._vendor.packaging.utils import canonicalize_name

from tests.lib import (
    create_basic_sdist_for_package,
    create_basic_wheel_for_package,
    create_test_package_with_setup,
)
from tests.lib.wheel import make_wheel

def assert_installed(script, **kwargs):
    ret = script.pip('list', '--format=json')
    # 成功也會應出來
    # print("\n\n\n\nstdout\n\n\n\n")
    print(ret.stdout)
    installed = set(
        (canonicalize_name(val['name']), val['version'])
        for val in json.loads(ret.stdout)
    )
    expected = set((canonicalize_name(k), v) for k, v in kwargs.items())
    assert expected <= installed, \
        "{!r} not all in {!r}".format(expected, installed)

def test_silde_example(script):
    # root dependency
    depends=["icons == 1.0.0"]
    depends.append("menu >= 1.0.0")
    create_basic_wheel_for_package(script, "root", "0.0.0", depends=depends)
    
    # menu dependency
    for i in range(1,6):
        depends=["dropdown >= 2.0.0"]
        version = "1.{index}.0".format(index=i)
        create_basic_wheel_for_package(script, "menu", version, depends=depends)
    create_basic_wheel_for_package(script, "menu", "1.0.0", depends=["dropdown == 1.8.0"])

    # dropdown
    for index in range(0,4):
        depends=["icons == 2.0.0"]
        version = "2.{index}.0".format(index=index)
        create_basic_wheel_for_package(script, "dropdown", version, depends=depends)
    create_basic_wheel_for_package(script, "dropdown", "1.8.0")

    #icons
    create_basic_wheel_for_package(script, "icons", "2.0.0")
    create_basic_wheel_for_package(script, "icons", "1.0.0")

    script.pip(
        "install",
        "--no-cache-dir",
        "--no-index",
        "--find-links", script.scratch_path,
        "root"
    )

    assert_installed(script, root="0.0.0", menu="1.0.0", icons="1.0.0", dropdown="1.8.0")