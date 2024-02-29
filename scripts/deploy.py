#! /usr/bin/env spack-python

import argparse
import os
import time
import spack.main
import spack.util.executable
from spack.util.path import canonicalize_path as spack_path_resolve

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
parser.add_argument("--name", help="name of env for installing")
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
parser.add_argument("--overwrite", action="store_true")
parser.add_argument("--depfile", action="store_true")


def get_env_name(args):
    _env_name = daystr
    if args.name:
        _env_name = args.name
    return _env_name


def environment_setup(args, env_name):
    out=manager("find-machine")
    project, machine = out.strip().split()
    template = os.path.expandvars("$EXAWIND_MANAGER/configs/{}/template.yaml".format(machine))

    if not os.path.isfile(template):
        template = os.path.expandvars("$EXAWIND_MANAGER/configs/base/template.yaml")

    if args.overwrite and ev.exists(env_name):
        env("rm", env_name, "-y")

    if not ev.exists(env_name):
        manager("create-env", "-n", env_name, "-y", template)

    print("Using env:", ev.read(env_name).path)


def configure_env(args, env_name):
    with ev.read(env_name) as e:
        config("add", "config:install_tree:{}".format(
               spack_path_resolve("$EXAWIND_MANAGER/opt/$arch/{}".format(e.name))
               ))
        config("add", "modules:default:tcl:all:suffixes:all:'{}'".format(e.name))
        concretize("--force")
        if args.depfile:
            env("depfile", "-o", os.path.join(e.path, "Makefile"))
        if args.pre_fetch:
            fetch()

def dependency_make_args(env, ranks):
    dep_args = []
    for root in env.concrete_roots():
        make_args = [
            "-j{}".format(ranks),
            "install-deps/{}".format(root.format("{name}-{version}-{hash}")),
            "SPACK_INSTALL_FLAGS='{}'".format("--show-log-on-error"),
        ]
        dep_args.append(make_args)
    return dep_args

def install_deps(args, env_name):
    with ev.read(env_name) as e:
        os.chdir(e.path)
        if args.depfile:
            dep_args = dependency_make_args(e, args.ranks)
            for make_args in dep_args:
                print("make",*make_args)
                make(*make_args)
        else:
            install("--only", "dependencies")

def root_install_args(env, tests=False, cdash=False):
    install_args = [
        "--keep-stage",
        "--only-concrete",
        "--show-log-on-error",
        ]
    if tests:
        install_args.extend([
            "--test=root",
        ])
    if cdash:
        install_args.extend([
            "--log-format", "cdash",
            "--log-file", os.path.join(env.path, "cdash_results"),
            "--cdash-site", "darwin",
            "--cdash-track", "track",
            "--cdash-build", "test",
        ])
    return install_args

def root_make_args(env, ranks, tests=False, cdash=False):
    install_args = root_install_args(env, tests, cdash)
    all_args = []
    for root in env.concrete_roots():
        make_args = [
            "-j{}".format(ranks),
            "install/{}".format(root.format("{name}-{version}-{hash}")),
            "SPACK_INSTALL_FLAGS='{}'".format(" ".join(install_args)),
        ]
        all_args.append(make_args)
    return all_args


def install_roots(args, env_name):
    env = ev.read(env_name)
    if args.depfile:
        root_arg_set = root_make_args(env, args.ranks, args.tests, args.cdash)
        for arg_set in root_arg_set:
            make(*arg_set)
    else:
        install(*root_install_args(env, args.tests, args.cdash))


def create_slurm_file(args, env_name):
    e = ev.read(env_name)
    slurm_args = ["#SBATCH {}\n".format(a) for a in args.slurm_args.split()]
    with open(os.path.join(e.path, "submit.sh"), "w") as f:
        f.write("#!/bin/bash\n")

        for s in slurm_args:
            f.write(s)
        f.write("\n")

        if args.depfile:
            dep_arg_set = dependency_make_args(e, args.ranks)
            for dep_args in dep_arg_set:
                f.write("make " + " ".join(dep_args)+"\n")

            root_arg_set = root_make_args(e, args.ranks, args.tests, args.cdash)
            for root_args in root_arg_set:
                f.write("make " + " ".join(root_args)+"\n")
        else:
            f.write("\nsrun -N $SLURM_JOB_NUM_NODES -n {} spack -e {} install --only dependencies".format(args.ranks, env_name))
            f.write("\nsrun -N $SLURM_JOB_NUM_NODES -n {} spack -e {} install ".format(args.ranks, env_name) + " ".join(root_install_args(e, args.tests, args.cdash)))
        f.write("\nspack -e {} module tcl refresh -y".format(env_name))


def module_gen(args, env_name):
    with ev.read(env_name) as e:
        module("tcl", "refresh", "-y")


args = parser.parse_args()
env_name = get_env_name(args)
environment_setup(args, env_name)
print("configure args")
configure_env(args, env_name)
if args.slurm_args:
    print("create slurm args")
    create_slurm_file(args, env_name)
else:
    print("install deps")
    install_deps(args, env_name)
    print("install roots")
    install_roots(args, env_name)
    module_gen(args, env_name)
