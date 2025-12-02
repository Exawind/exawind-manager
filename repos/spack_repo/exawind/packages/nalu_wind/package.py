# Copyright (c) 2022, National Technology & Engineering Solutions of Sandia,
# LLC (NTESS). Under the terms of Contract DE-NA0003525 with NTESS, the U.S.
# Government retains certain rights in this software.
#
# This software is released under the BSD 3-clause license. See LICENSE file
# for more details.

from spack.package import *
from spack_repo.builtin.packages.nalu_wind.package import NaluWind as bNaluWind
from spack_repo.exawind.packages.ctest_package.package import *
find_machine = importlib.import_module("find-exawind-manager")


class NaluWind(bNaluWind, CtestPackage):
    version("2.6.0", tag="v2.6.0", commit="9272856bb6b8dae54a369395654c7c0933e87457")

    variant("asan", default=False, description="Turn on address sanitizer")
    variant("unit-tests", default=True, description="Activate unit tests")

    depends_on("trilinos+mpi@16.2.0:", when="@2.6.0")
    requires("+hypre")

    requires("+tests", when="+cdash_submit")

    def flag_handler(self, name, flags):
        if name == "cxxflags":
            flags.append("-DUSE_STK_SIMD_NONE")
        return (flags, None, None)

    def setup_dependent_run_environment(self, env, dependent_spec):
        spec = self.spec
        super().setup_dependent_run_environment(env, dependent_spec)

    def setup_build_environment(self, env):
        spec = self.spec
        super(CtestPackage, self).setup_build_environment(env)
        if spec.satisfies("+asan"):
            env.append_flags("CXXFLAGS", "-fsanitize=address -fno-omit-frame-pointer -fsanitize-blacklist={0}".format(join_path(self.package_dir, "blacklist.asan")))
            env.set("LSAN_OPTIONS", "suppressions={0}".format(join_path(self.package_dir, "sup.asan")))
            env.set("ASAN_OPTIONS", "detect_container_overflow=0")

        machine_name, _ = find_machine.get_current_machine()
        if spec.satisfies("+gpu-aware-mpi+rocm") and machine_name == "frontier":
            env.set("MPICH_GPU_SUPPORT_ENABLED", "1")
            env.append_flags("CXXFLAGS", "--amdgpu-target=gfx90a")
            env.append_flags("CXXFLAGS", "-I" + os.path.join(os.getenv("MPICH_DIR"), "include"))
            env.append_flags("CXXFLAGS", "-L" + os.path.join(os.getenv("MPICH_DIR"), "lib"))
            env.append_flags("CXXFLAGS", "-lmpi")
            env.append_flags("CXXFLAGS", os.getenv("CRAY_XPMEM_POST_LINK_OPTS"))
            env.append_flags("CXXFLAGS", "-lxpmem")
            env.append_flags("CXXFLAGS", os.getenv("PE_MPICH_GTL_DIR_amd_gfx90a"))
            env.append_flags("CXXFLAGS", os.getenv("PE_MPICH_GTL_LIBS_amd_gfx90a"))
        if spec.satisfies("+gpu-aware-mpi+cuda") and machine_name == "kestrel-gpu":
            env.set("MPICH_GPU_SUPPORT_ENABLED", "1")
            env.append_flags("CXXFLAGS", "-I" + os.path.join(os.getenv("MPICH_DIR"), "include"))
            env.append_flags("CXXFLAGS", "-L" + os.path.join(os.getenv("MPICH_DIR"), "lib"))
            env.append_flags("CXXFLAGS", "-lmpi")
            env.append_flags("CXXFLAGS", os.getenv("PE_MPICH_GTL_DIR_nvidia90"))
            env.append_flags("CXXFLAGS", os.getenv("PE_MPICH_GTL_LIBS_nvidia90"))

    def cmake_args(self):
        spec = self.spec

        cmake_options = super().cmake_args()

        if spec.satisfies("+kynema"):
            cmake_options.append(self.define("ENABLE_KYNEMA_SIXDOF", True))

        if spec.satisfies("+tests") or self.run_tests or spec.satisfies("dev_path=*"):
            cmake_options.append(self.define("CMAKE_EXPORT_COMPILE_COMMANDS", True))
            cmake_options.append(self.define("ENABLE_TESTS", True))
            cmake_options.append(self.define("NALU_WIND_SAVE_GOLDS", True))
            cmake_options.append(self.define("NALU_WIND_SAVED_GOLDS_DIR", super().saved_golds_dir))
            cmake_options.append(self.define("NALU_WIND_REFERENCE_GOLDS_DIR", super().reference_golds_dir))
            if spec.satisfies("+cuda"):
                cmake_options.append(self.define("TEST_ABS_TOL", 1.0e-8))
                cmake_options.append(self.define("TEST_REL_TOL", 1.0e-6))

        return cmake_options
