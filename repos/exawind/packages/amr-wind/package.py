# Copyright (c) 2022, National Technology & Engineering Solutions of Sandia,
# LLC (NTESS). Under the terms of Contract DE-NA0003525 with NTESS, the U.S.
# Government retains certain rights in this software.
#
# This software is released under the BSD 3-clause license. See LICENSE file
# for more details.

from spack import *
from spack.pkg.builtin.amr_wind import AmrWind as bAmrWind
from spack.pkg.exawind.ctest_package import *

class AmrWind(bAmrWind, CtestPackage):
    variant("asan", default=False, description="Turn on address sanitizer")
    variant("clangtidy", default=False, description="Turn on clang-tidy")

    requires("+tests", when="+cdash_submit")

    def setup_build_environment(self, env):
        spec = self.spec
        super().setup_build_environment(env)
        if spec.satisfies("+asan"):
            env.append_flags("CXXFLAGS", "-fsanitize=address -fno-omit-frame-pointer")
            env.set("LSAN_OPTIONS", "verbosity=1:log_threads=1:suppressions={0}".format(join_path(self.package_dir, "sup.asan")))

        if spec.satisfies("+cuda"):
            env.set("CUDAHOSTCXX", spack_cxx)
        if spec.satisfiles("+gpu-aware-mpi") and find_machine(verbose=False, full_machine_name=False) == "frontier":
            env.set("MPICH_GPU_SUPPORT_ENABLED", "1")

    def flag_handler(self, name, flags):
        if find_machine(verbose=False, full_machine_name=False) == "frontier" and name == "cxxflags" and "+gpu-aware-mpi" in self.spec and "+rocm" in self.spec:
            flags.append("-I" + os.path.join(os.getenv("MPICH_DIR"), "include"))
            flags.append("-L" + os.path.join(os.getenv("MPICH_DIR"), "lib"))
            flags.append("-lmpi")
            flags.append(os.getenv("CRAY_XPMEM_POST_LINK_OPTS"))
            flags.append("-lxpmem")
            flags.append(os.getenv("PE_MPICH_GTL_DIR_amd_gfx90a"))
            flags.append(os.getenv("PE_MPICH_GTL_LIBS_amd_gfx90a"))

    def cmake_args(self):
        spec = self.spec
        cmake_options = super(AmrWind, self).cmake_args()

        if spec.satisfies("dev_path=*"):
            cmake_options.append(self.define("CMAKE_EXPORT_COMPILE_COMMANDS", True))

        if spec.satisfies("+clangtidy"):
            cmake_options.append(self.define("AMR_WIND_ENABLE_CLANG_TIDY", True))

        if spec.satisfies("+tests"):
            cmake_options.append(self.define("AMR_WIND_TEST_WITH_FCOMPARE", True))
            cmake_options.append(self.define("AMR_WIND_SAVE_GOLDS", True))
            cmake_options.append(self.define("AMR_WIND_SAVED_GOLDS_DIRECTORY", super().saved_golds_dir))
            cmake_options.append(self.define("AMR_WIND_REFERENCE_GOLDS_DIRECTORY", super().reference_golds_dir))

        if spec.satisfies("+mpi"):
            cmake_options.append(self.define("MPI_CXX_COMPILER", spec["mpi"].mpicxx))
            cmake_options.append(self.define("MPI_C_COMPILER", spec["mpi"].mpicc))

        return cmake_options
