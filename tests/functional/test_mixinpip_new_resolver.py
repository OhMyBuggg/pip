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
    installed = set(
        (canonicalize_name(val['name']), val['version'])
        for val in json.loads(ret.stdout)
    )
    expected = set((canonicalize_name(k), v) for k, v in kwargs.items())
    assert expected <= installed, \
        "{!r} not all in {!r}".format(expected, installed)


def assert_not_installed(script, *args):
    ret = script.pip("list", "--format=json")
    installed = set(
        canonicalize_name(val["name"])
        for val in json.loads(ret.stdout)
    )
    # None of the given names should be listed as installed, i.e. their
    # intersection should be empty.
    expected = set(canonicalize_name(k) for k in args)
    assert not (expected & installed), \
        "{!r} contained in {!r}".format(expected, installed)


def assert_editable(script, *args):
    # This simply checks whether all of the listed packages have a
    # corresponding .egg-link file installed.
    # TODO: Implement a more rigorous way to test for editable installations.
    egg_links = set("{}.egg-link".format(arg) for arg in args)
    assert egg_links <= set(os.listdir(script.site_packages_path)), \
        "{!r} not all found in {!r}".format(args, script.site_packages_path)


def test_new_resolver_picks_installed_version_extened(script):
    create_basic_wheel_for_package(
        script,
        "simple",
        "0.1.0",
    )
    create_basic_wheel_for_package(
        script,
        "simple",
        "0.2.0",
    )
    create_basic_wheel_for_package(
        script,
        "simple",
        "0.3.0",
    )
    create_basic_wheel_for_package(
        script,
        "simple",
        "0.7.0",
    )
    
    script.pip(
        "install",
        "--no-cache-dir", "--no-index",
        "--find-links", script.scratch_path,
        "simple==0.2.0"
    )
    assert_installed(script, simple="0.2.0")

    result = script.pip(
        "install",
        "--no-cache-dir", "--no-index",
        "--find-links", script.scratch_path,
        "simple"
    )
    assert "Collecting" not in result.stdout, "Should not fetch new version"
    assert_installed(script, simple="0.2.0")


def test_new_resolver_picks_installed_version_extened_second(script):
    create_basic_wheel_for_package(
        script,
        "simple",
        "0.1.0",
    )
    create_basic_wheel_for_package(
        script,
        "simple",
        "0.2.0",
    )
    create_basic_wheel_for_package(
        script,
        "simple",
        "1.3.0",
    )
    create_basic_wheel_for_package(
        script,
        "simple",
        "0.7.0",
    )

    create_basic_wheel_for_package(
        script,
        "simple",
        "0.9.0",
    )
    
    script.pip(
        "install",
        "--no-cache-dir", "--no-index",
        "--find-links", script.scratch_path,
        "simple==0.9.0"
    )
    assert_installed(script, simple="0.9.0")

    result = script.pip(
        "install",
        "--no-cache-dir", "--no-index",
        "--find-links", script.scratch_path,
        "simple"
    )
    assert "Collecting" not in result.stdout, "Should not fetch new version"
    assert_installed(script, simple="0.9.0")