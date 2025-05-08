# Copyright (c) 2022, National Technology & Engineering Solutions of Sandia,
# LLC (NTESS). Under the terms of Contract DE-NA0003525 with NTESS, the U.S.
# Government retains certain rights in this software.
#
# This software is released under the BSD 3-clause license. See LICENSE file
# for more details.

from spack import *
from spack.package import *
from spack_repo.builtin.packages.amr_wind.package import AmrWind as bAmrWind
from spack.pkg.exawind.ctest_package import *
find_machine = importlib.import_module("find-exawind-manager")

class AmrWind(bAmrWind, CtestPackage):

    version(
        "3.4.2", tag="v3.4.2", commit="ed475a0533dfacf1fdff0b707518ccf99040d9f9", submodules=True
    )
    version(
        "3.4.1", tag="v3.4.1", commit="effe63ca9061e6d2bd5c5e84b690d29c0869f029", submodules=True
    )

    variant("asan", default=False, description="Turn on address sanitizer")
    variant("clangtidy", default=False, description="Turn on clang-tidy")

    # For some reason numpy tends to concretize to a 1.X version
    # and doesn't build
    depends_on("py-numpy@2:", when="+netcdf")
    # New versions of HDF5 have CMake problems finding ZLIB::ZLIB targets
    # during amr-wind configure
    depends_on("hdf5@:1.14.4-3", when="+hdf5")

    requires("+tests", when="+cdash_submit")

    def setup_build_environment(self, env):
        spec = self.spec
        super().setup_build_environment(env)
        if spec.satisfies("+asan"):
            env.append_flags("CXXFLAGS", "-fsanitize=address -fno-omit-frame-pointer")
            env.set("LSAN_OPTIONS", "suppressions={0}".format(join_path(self.package_dir, "sup.asan")))

        machine_name, _ = find_machine.get_current_machine()
        if spec.satisfies("+gpu-aware-mpi+rocm") and machine_name == "frontier":
            env.set("MPICH_GPU_SUPPORT_ENABLED", "1")
            env.append_flags("LDFLAGS", "-I" + os.path.join(os.getenv("MPICH_DIR"), "include"))
            env.append_flags("LDFLAGS", "-L" + os.path.join(os.getenv("MPICH_DIR"), "lib"))
            env.append_flags("LDFLAGS", "-lmpi")
            env.append_flags("LDFLAGS", os.getenv("CRAY_XPMEM_POST_LINK_OPTS"))
            env.append_flags("LDFLAGS", "-lxpmem")
            env.append_flags("LDFLAGS", os.getenv("PE_MPICH_GTL_DIR_amd_gfx90a"))
            env.append_flags("LDFLAGS", os.getenv("PE_MPICH_GTL_LIBS_amd_gfx90a"))
        if spec.satisfies("+gpu-aware-mpi+cuda") and machine_name == "kestrel-gpu":
            env.set("MPICH_GPU_SUPPORT_ENABLED", "1")
            env.append_flags("CXXFLAGS", "-I" + os.path.join(os.getenv("MPICH_DIR"), "include"))
            env.append_flags("CXXFLAGS", "-L" + os.path.join(os.getenv("MPICH_DIR"), "lib"))
            env.append_flags("CXXFLAGS", "-lmpi")
            env.append_flags("CXXFLAGS", os.getenv("PE_MPICH_GTL_DIR_nvidia90"))
            env.append_flags("CXXFLAGS", os.getenv("PE_MPICH_GTL_LIBS_nvidia90"))

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

        return cmake_options
