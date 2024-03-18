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


class CmakeExtension(CMakePackage):

    variant("cdash_submit", default=False, description="Submit results to cdash")
    variant("ninja", default=False, description="Shortcut for generator=ninja")

    requires("generator=ninja", when="+ninja")

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
                ctest("-T", "Start", "-T", "Configure", "-T", "Build", "-V")
        else:
            super().build(spec, prefix)


    def ctest_args(self):
        args = ["-T", "Test"]
        args.append("--stop-time")
        overall_test_timeout=60*60*4 # 4 hours
        args.append(time.strftime("%H:%M:%S", time.localtime(time.time() + overall_test_timeout)))
        args.append("-VV")
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
        if not self.spec.variants["cdash_submit"].value:
            return

        with working_dir(self.builder.build_directory):
            args = self.ctest_args()
            tty.debug("{} running CTest".format(spec.name))
            tty.debug("Running:: ctest"+" ".join(args))
            ctest = Executable(self.spec["cmake"].prefix.bin.ctest)
            # We want the install to succeed even if some tests fail so pass
            # fail_on_error=False
            ctest(*args, fail_on_error=False)
            # submit 
            ctest("-T", "Submit", "-V")

