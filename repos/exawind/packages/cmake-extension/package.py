# Copyright (c) 2022, National Technology & Engineering Solutions of Sandia,
# LLC (NTESS). Under the terms of Contract DE-NA0003525 with NTESS, the U.S.
# Government retains certain rights in this software.
#
# This software is released under the BSD 3-clause license. See LICENSE file
# for more details.
import argparse
import inspect
import llnl.util.tty as tty
import glob
import os
import shutil
import time

import llnl.util.filesystem as fs

from spack.builder import run_after
from spack.directives import depends_on, variant
from spack.package import CMakePackage
import spack.cmd.common.arguments as arguments


class CmakeExtension(CMakePackage):

    variant("cdash_submit", default=False, description="Submit results to cdash")

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
        if "+cdash_submit" in self.spec:
            args.extend([
                        "-D",
                        "BUILDNAME={}".format(self.spec.format("{name}@{compiler}")),
                        "-D",
                        "SITE={}".format("darwin-test-phil"),
            ])
        return args


    def build(self, spec, prefix):
        """
        override spack's default build to run through ctest if needed
        """
        if "+cdash_submit" in spec:
            with fs.working_dir(self.build_directory):
                ctest = Executable(self.spec["cmake"].prefix.bin.ctest)
                ctest("-T", "Start", "-T", "Configure", "-T", "Build", "-V")
        else:
            super().build(spec, prefix)


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

        cdash_args = {
            "site": "darwin",
            "build": "test",
            "track": "track",
            "timeout": 5*60,
            }

        with working_dir(self.builder.build_directory):
            ctest_args = ["-T", "Test"]
            ctest_args.append("--stop-time")
            overall_test_timeout=60*60*4 # 4 hours
            ctest_args.append(time.strftime("%H:%M:%S", time.localtime(time.time() + overall_test_timeout)))
            ctest_args.extend(["-VV", "-R", "unit"])
            # We want the install to succeed even if some tests fail so pass
            # fail_on_error=False
            tty.debug("{} running CTest".format(spec.name))
            tty.debug("Running:: ctest"+" ".join(ctest_args))
            print("Running:: ctest"+" ".join(ctest_args))
            ctest = Executable(self.spec["cmake"].prefix.bin.ctest)
            # ctest(*ctest_args)
            ctest(*ctest_args, fail_on_error=False)
            ctest("-T", "Submit")

