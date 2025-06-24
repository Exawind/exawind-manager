# Copyright (c) 2022, National Technology & Engineering Solutions of Sandia,
# LLC (NTESS). Under the terms of Contract DE-NA0003525 with NTESS, the U.S.
# Government retains certain rights in this software.
#
# This software is released under the BSD 3-clause license. See LICENSE file
# for more details.

from spack.package import *
from spack_repo.builtin.packages.exawind.package import Exawind as bExawind
from spack_repo.exawind.packages.ctest_package.package import *
find_machine = importlib.import_module("find-exawind-manager")

class Exawind(bExawind, CtestPackage):
    variant("asan", default=False, description="Turn on address sanitizer")
    variant("tests", default=False, description="Activate regression tests")

    requires("+tests", when="+cdash_submit")

    def cmake_args(self):
        spec = self.spec
        cmake_options = super(Exawind, self).cmake_args()

        machine_name, _ = find_machine.get_current_machine()
        if machine_name == "kestrel-gpu":
            cmake_options.append(self.define("MPIEXEC_EXECUTABLE", "srun"))

        if spec.satisfies("dev_path=*"):
            cmake_options.append(self.define("CMAKE_EXPORT_COMPILE_COMMANDS", True))
            cmake_options.append(self.define("EXAWIND_ENABLE_TESTS", True))

        if spec.satisfies("+tests"):
            cmake_options.append(self.define("EXAWIND_ENABLE_TESTS", True))
            cmake_options.append(self.define("EXAWIND_TEST_WITH_FCOMPARE", True))
            cmake_options.append(self.define("EXAWIND_SAVE_GOLDS", True))
            cmake_options.append(self.define("EXAWIND_SAVED_GOLDS_DIRECTORY", super().saved_golds_dir))
            cmake_options.append(self.define("EXAWIND_REFERENCE_GOLDS_DIRECTORY", super().reference_golds_dir))
            cmake_options.append(self.define("FCOMPARE_EXE", join_path(spec["amr-wind"].prefix.bin, "amrex_fcompare")))

        return cmake_options

    def setup_build_environment(self, env):
        spec = self.spec
        super().setup_build_environment(env)
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
