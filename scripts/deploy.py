#! /usr/bin/env spack-python

import argparse
import os
import time
import spack.main
import spack.util.executable

from datetime import date

import spack.environment as ev

today = date.today()
daystr = today.isoformat()

manager = spack.main.SpackCommand("manager")
env = spack.main.SpackCommand("env")
config = spack.main.SpackCommand("config")
concretize = spack.main.SpackCommand("concretize")
fetch = spack.main.SpackCommand("fetch")
install = spack.main.SpackCommand("install")
module = spack.main.SpackCommand("module")
make = spack.util.executable.which("make")

parser = argparse.ArgumentParser()
parser.add_argument("--pre-fetch",
                          help="fetch all the source code prior to install",
                          action="store_true"
                    )
parser.add_argument("--slurm-args",
                    help=(
                        "slurm argurments submitted as a single string. spaces will be split "
                        "and #SBATCH directives will be added before each argument")
                    )
parser.add_argument("--ranks", type=int)
parser.add_argument("--tests", action="store_true")
parser.add_argument("--cdash", action="store_true")

def environment_setup(args):
    out=manager("find-machine")
    project, machine = out.strip().split()
    template = os.path.expandvars("$EXAWIND_MANAGER/templates/exawind_{}.yaml".format(machine))

    if not os.path.isfile(template):
        template = os.path.expandvars("$EXAWIND_MANAGER/templates/exawind_basic.yaml")

    if not ev.exists(daystr):
        manager("create-env", "-l", "-n", daystr, "-y", template)
    print("Using env:", ev.read(daystr).path)


def configure_env(args):
    with ev.read(daystr) as e:
        module_projection = '{name}-{version}/'+'{}'.format(daystr)+'/{hash:4}'
        config("add", "modules:default:tcl:projections:all:'{}'".format(module_projection))
        concretize("--force")
        env("depfile", "-o", os.path.join(e.path, "Makefile"))
        if args.pre_fetch:
            fetch()

def dependency_install_args(ranks):
    with ev.read(daystr) as e:
        dep_args = []
        for root in e.concrete_roots():
            make_args = [
                "-j{}".format(ranks),
                "install-deps/{}".format(root.format("{name}-{version}-{hash}")),
                "SPACK_INSTALL_FLAGS='{}'".format("--keep-stage"),
            ]
            dep_args.append(make_args)
        return dep_args

def install_deps(args):
    with ev.read(daystr) as e:
        os.chdir(e.path)
        dep_args = dependency_install_args(args.ranks)
        for make_args in dep_args:
            print("make",*make_args)
            make(*make_args)

def root_install_args(ranks, tests=False, cdash=False):
    with ev.read(daystr) as e:
        install_args = [
            "--keep-stage",
            "--only-concrete",
            ]
        if tests:
            install_args.extend([
                "--test-root"
            ])
        if cdash:
            install_args.extend([
                "--log-format", "cdash",
                "--log-file", os.path.join(e.path, "cdash_results"),
                "--cdash-site", "dummy",
                "--cdash-track", "track",
            ])
        all_args = []
        for root in e.concrete_roots():
            make_args = [
                "-j{}".format(ranks),
                "install/{}".format(root.format("{name}-{version}-{hash}")),
                "SPACK_INSTALL_FLAGS='{}'".format(" ".join(install_args)),
            ]
            all_args.append(make_args)
        return all_args

def install_roots(args):
    root_arg_set = root_install_args(args.ranks, args.test, args.cdash)
    for arg_set in root_arg_set:
        make(*arg_set)


def install_roots(args):
    with ev.read(daystr) as e:
        os.chdir(e.path)
        install(*install_args())


def create_slurm_file(args):
    e = ev.read(daystr)
    slurm_args = ["#SBATCH {}\n".format(a) for a in args.slurm_args.split()]
    with open(os.path.join(e.path, "submit.sh"), "w") as f:
        f.write("#!/bin/bash\n")

        for s in slurm_args:
            f.write(s)
        f.write("\n")

        dep_arg_set = dependency_install_args(args.ranks)
        for dep_args in dep_arg_set:
            f.write("make " + " ".join(dep_args)+"\n")

        root_arg_set = root_install_args(args.ranks, args.tests, args.cdash)
        for root_args in root_arg_set:
            f.write("make " + " ".join(root_args)+"\n")
        f.write("spack module tcl refresh -y")


def module_gen(args):
    with ev.read(daystr) as e:
        module("tcl", "refresh", "-y")


args = parser.parse_args()
environment_setup(args)
print("configure args")
configure_env(args)
if args.slurm_args:
    print("create slurm args")
    create_slurm_file(args)
else:
    print("install deps")
    install_deps(args)
    print("install roots")
    install_roots(args)
    module_gen(args)
