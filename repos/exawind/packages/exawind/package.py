# Copyright (c) 2022, National Technology & Engineering Solutions of Sandia,
# LLC (NTESS). Under the terms of Contract DE-NA0003525 with NTESS, the U.S.
# Government retains certain rights in this software.
#
# This software is released under the BSD 3-clause license. See LICENSE file
# for more details.

from spack import *
from spack.pkg.builtin.exawind import Exawind as bExawind
from spack.pkg.exawind.ctest_package import *


class Exawind(bExawind, CtestPackage):
    variant("asan", default=False, description="Turn on address sanitizer")

    def cmake_args(self):
        spec = self.spec

        args = super(Exawind, self).cmake_args()

        if spec.satisfies("dev_path=*"):
            args.append(self.define("CMAKE_EXPORT_COMPILE_COMMANDS",True))

        return args

    def setup_build_environment(self, env):
        spec = self.spec
        super().setup_build_environment(env)
        if spec.satisfies("+asan"):
            env.append_flags("CXXFLAGS", "-fsanitize=address -fno-omit-frame-pointer -fsanitize-blacklist={0}".format(join_path(self.package_dir, "blacklist.asan")))
            env.set("LSAN_OPTIONS", "verbosity=1:log_threads=1:suppressions={0}".format(join_path(self.package_dir, "sup.asan")))
            env.set("ASAN_OPTIONS", "detect_container_overflow=0")
