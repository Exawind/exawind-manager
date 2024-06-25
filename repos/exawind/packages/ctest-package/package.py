# Copyright (c) 2022, National Technology & Engineering Solutions of Sandia,
# LLC (NTESS). Under the terms of Contract DE-NA0003525 with NTESS, the U.S.
# Government retains certain rights in this software.
#
# This software is released under the BSD 3-clause license. See LICENSE file
# for more details.
import llnl.util.tty as tty
import importlib
import inspect
import glob
import os
import shutil
import time

import llnl.util.filesystem as fs

import spack.builder
import spack.build_systems.cmake
import spack.util.log_parse

from spack.builder import run_after
from spack.directives import depends_on, variant, requires
from spack.package import CMakePackage
find_machine = importlib.import_module("find-exawind-manager")

class CTestBuilder(spack.build_systems.cmake.CMakeBuilder):
    phases = ("cmake", "build", "install", "analysis")

    @property
    def std_cmake_args(self):
        args = super().std_cmake_args
        if self.spec.variants["cdash_submit"].value:
            args.extend([
                        "-D",
                        "BUILDNAME={}".format(find_machine.cdash_build_name(self.pkg.spec)),
                        "-D",
                        f"CTEST_BUILD_OPTIONS={self.pkg.spec.short_spec}",
                        "-D",
                        "SITE={}".format(find_machine.cdash_host_name()),
            ])
        return args

    def ctest_args(self):
        args = ["-T", "Test"]
        args.append("--stop-time")
        overall_test_timeout=60*60*4 # 4 hours
        args.append(time.strftime("%H:%M:%S", time.localtime(time.time() + overall_test_timeout)))
        args.append("-VV")
        extra_args = self.pkg.spec.variants["ctest_args"].value
        if extra_args:
            args.extend(extra_args.split())
        return args

    @property
    def build_args(self):
        args = [
            "--group",
            self.pkg.spec.name,
            "-T",
            "Start",
            "-T",
            "Configure",
            "-T",
            "Build",
            "-VV"
        ]
        return args

    @property
    def submit_args(self):
        args = [
            "-T",
            "Submit",
            "-v"
        ]
        return args

    def submit_cdash(self, pkg, spec, prefix):
        ctest = Executable(self.spec["cmake"].prefix.bin.ctest)
        ctest.add_default_env("CTEST_PARALLEL_LEVEL", str(make_jobs))
        build_env = os.environ.copy()
        ctest(*self.submit_args, env = build_env)


    def build(self, pkg, spec, prefix):
        if self.pkg.spec.variants["cdash_submit"].value:
            ctest = Executable(self.spec["cmake"].prefix.bin.ctest)
            ctest.add_default_env("CMAKE_BUILD_PARALLEL_LEVEL", str(make_jobs))
            with fs.working_dir(self.build_directory):
                 build_env = os.environ.copy()
                 output = ctest(*self.build_args, env=build_env, output=str.split, error=str.split).split("\n")
                 errors, warnings = spack.util.log_parse.parse_log_events(output)
                 if len(errors) > 0:
                     errs = [str(e) for e in errors]
                     tty.warn(f"Errors: {errs}")
                     tty.warn(f"returncode {ctest.returncode}")
                     self.submit_cdash(pkg, spec, prefix)
                     raise BaseException(f"{self.pkg.spec.name} had build errors")

        else:
            super().build(pkg, spec, prefix)

    def analysis(self, pkg, spec, prefix):
        """
        This method will be used to run regression test
        TODO: workout how to get the track,build,site mapped correctly
        thinking of a call to super and writing logic into the packages
        and auxilary python lib
        """

        with working_dir(self.build_directory):
            args = self.ctest_args()
            tty.debug("{} running CTest".format(self.pkg.spec.name))
            tty.debug("Running:: ctest"+" ".join(args))
            ctest = Executable(self.spec["cmake"].prefix.bin.ctest)
            ctest.add_default_env("CTEST_PARALLEL_LEVEL", str(make_jobs))
            ctest.add_default_env("CMAKE_BUILD_PARALLEL_LEVEL", str(make_jobs))
            build_env = os.environ.copy()
            ctest(*args, "-j", str(make_jobs),  env=build_env, fail_on_error=False)

            if self.pkg.spec.variants["cdash_submit"].value:
                self.submit_cdash(pkg, spec, prefix)


class CtestPackage(CMakePackage):

    CMakeBuilder = CTestBuilder
    variant("cdash_submit", default=False, description="Submit results to cdash")
    variant("ninja", default=False, description="Shortcut for generator=ninja")
    variant("reference_golds", default='default', description="gold directories to compare against")
    variant("ctest_args", default="-R unit", description="quoted string of arguments to send to ctest, default is run unit tests")

    requires("generator=ninja", when="+ninja")

    def setup_build_environment(self, env):
        env.prepend_path("PYTHONPATH", os.environ["EXAWIND_MANAGER"])

    def do_clean(self):
        super().do_clean()
        if not self.stage.managed_by_spack:
            build_artifacts = glob.glob(os.path.join(self.stage.source_path, "spack-*"))
            for f in build_artifacts:
                if os.path.isfile(f):
                    os.remove(f)
                if os.path.isdir(f):
                    shutil.rmtree(f)
            ccjson = os.path.join(self.stage.source_path, "compile_commands.json")

            if os.path.isfile(ccjson):
                os.remove(ccjson)

    @run_after("cmake")
    def copy_compile_commands(self):
        if self.spec.satisfies("dev_path=*"):
            target = os.path.join(self.stage.source_path, "compile_commands.json")
            source = os.path.join(self.build_directory, "compile_commands.json")
            if os.path.isfile(source):
                shutil.copyfile(source, target)

    @property
    def saved_golds_dir(self):
        """
        Save golds in the install directory if they are generated
        """
        saved_golds = os.path.join(self.prefix, "golds")
        os.makedirs(saved_golds, exist_ok=True)
        return saved_golds

    @property
    def reference_golds_dir(self):
        if self.spec.variants["reference_golds"].value != "default":
            gold_dir =  self.spec.variants["reference_golds"].value
        else:
            gold_dir = find_machine.reference_golds_default(self.spec)
        if not os.path.isdir(gold_dir):
            raise Exception(f"Supplied referenced golds path is not valid: {gold_dir}")
        return gold_dir


