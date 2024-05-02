# Copyright (c) 2022, National Technology & Engineering Solutions of Sandia,
# LLC (NTESS). Under the terms of Contract DE-NA0003525 with NTESS, the U.S.
# Government retains certain rights in this software.
#
# This software is released under the BSD 3-clause license. See LICENSE file
# for more details.
import llnl.util.tty as tty
import importlib
import glob
import os
import shutil
import time

import llnl.util.filesystem as fs

from spack.builder import run_after
from spack.directives import depends_on, variant, requires
from spack.package import CMakePackage
find_machine = importlib.import_module("find-exawind-manager")


class CtestPackage(CMakePackage):

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

    def cmake_args(self):
        args = []
        if self.spec.variants["cdash_submit"].value:
            args.extend([
                        "-D",
                        "BUILDNAME={}".format(find_machine.cdash_build_name(self.spec)),
                        "-D",
                        "SITE={}".format(find_machine.cdash_host_name()),
            ])
        return args


    def build(self, spec, prefix):
        """
        override spack's default build to run through ctest if needed
        """
        if self.spec.variants["cdash_submit"].value:
            with fs.working_dir(self.build_directory):
                ctest = Executable(self.spec["cmake"].prefix.bin.ctest)
                ctest.add_default_env("CMAKE_BUILD_PARALLEL_LEVEL", str(make_jobs))
                ctest("-T", "Start", "-T", "Configure", "-T", "Build", "-V")
        else:
            super().build(spec, prefix)


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
            if not os.path.isdir(self.spec.variants["reference_golds"].value):
                tty.die("Supplied referenced golds path is not valid: {}".format(
                        self.spec.variants["reference_golds"].value)
                        )
            return self.spec.variants["reference_golds"].value
        else:
            return find_machine.reference_golds_default(self.spec)
            


    def ctest_args(self):
        args = ["-T", "Test", "--group", self.spec.name]
        args.append("--stop-time")
        overall_test_timeout=60*60*4 # 4 hours
        args.append(time.strftime("%H:%M:%S", time.localtime(time.time() + overall_test_timeout)))
        args.append("-VV")
        extra_args = self.spec.variants["ctest_args"].value
        if extra_args:
            args.extend(extra_args.split())
        return args


    @run_after("install")
    def test_regression(self):
        """
        This method will be used to run regression test
        TODO: workout how to get the track,build,site mapped correctly
        thinking of a call to super and writing logic into the packages
        and auxilary python lib
        """ 
        spec = self.spec

        test_env = os.environ.copy()
        with working_dir(self.builder.build_directory):
            args = self.ctest_args()
            tty.debug("{} running CTest".format(spec.name))
            tty.debug("Running:: ctest"+" ".join(args))
            ctest = Executable(self.spec["cmake"].prefix.bin.ctest)
            ctest.add_default_env("CTEST_PARALLEL_LEVEL", str(make_jobs))
            # We want the install to succeed even if some tests fail so pass
            # fail_on_error=False
            ctest(*args, env=test_env, fail_on_error=False)

            if self.spec.variants["cdash_submit"].value:
                ctest("-T", "Submit", "-V")
