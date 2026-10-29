# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

#pylint: disable=line-too-long

from __future__ import print_function

import os
import tempfile
import argparse
from subprocess import check_call

from .version_patcher import VersionPatcher
from ..utilities.path import get_core_modules_paths, get_command_modules_paths

def build(pkg_path, dest):
    """
    pkg_path - Full path to directory of the package to build
    dest - Destination for the built package
    """
    check_call(['python', 'setup.py', 'sdist', '-d', dest, 'bdist_wheel', '-d', dest], cwd=pkg_path)

def release(pkg_dir, repo, username, password):
    """Release all packages in a directory"""
    pkgs = [os.path.join(pkg_dir, f) for f in os.listdir(pkg_dir)]
    for pkg in pkgs:
        check_call(['twine', 'register', '--repository-url', repo, '--username', username,
                    '--password', password, pkg])
        check_call(['twine', 'upload', '--repository-url', repo, '--username', username,
                    '--password', password, pkg])

def run_build_release(component_name, repo, repo_username, repo_password, use_version_patch=True):
    """
    component_name - The full component name (e.g. azure-cli, azure-cli-core, azure-cli-vm, etc.)
    """
    available = list(get_core_modules_paths()) + \
                    get_command_modules_paths(include_prefix=True)
    for comp_name, comp_path in available:
        if comp_name == component_name:
            pkg_dir = tempfile.mkdtemp()
            patcher = VersionPatcher(use_version_patch, component_name, comp_path)
            patcher.patch()
            build(comp_path, pkg_dir)
            patcher.unpatch()
            print("Built '{}' to '{}'".format(comp_name, pkg_dir))
            if repo and repo_username and repo_password:
                release(pkg_dir, repo, repo_username, repo_password)
            return
    raise ValueError("No component found with name '{}'".format(component_name))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Automated build and release of a component. To only build, don't specify the repo parameters.")
    parser.add_argument('--component', '-c', required=True,
                        help='Component name (e.g. azure-cli, azure-cli-vm, etc.)')
    parser.add_argument('--no-version-patch', action='store_false',
                        help="By default, we patch the version number of the package to remove '+dev' if it exists.")
    parser.add_argument('--repo', '-r',
                        help='Repository URL for release (e.g. https://pypi.python.org/pypi, https://testpypi.python.org/pypi)')
    parser.add_argument('--repo-username', '-u',
                        help='The username to authenticate to the repository as')
    parser.add_argument('--repo-password', '-p',
                        help='The password to authenticate to the repository with')
    args = parser.parse_args()
    run_build_release(args.component,
                      args.repo,
                      args.repo_username,
                      args.repo_password,
                      args.no_version_patch)
