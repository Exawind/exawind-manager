# Copyright (c) 2022, National Technology & Engineering Solutions of Sandia,
# LLC (NTESS). Under the terms of Contract DE-NA0003525 with NTESS, the U.S.
# Government retains certain rights in this software.
#
# This software is released under the BSD 3-clause license. See LICENSE file
# for more details.

from spack import *
from spack.pkg.builtin.nalu_wind import NaluWind as bNaluWind
from spack.pkg.builtin.kokkos import Kokkos
import os
import importlib
import inspect
import time
from spack.pkg.exawind.ctest_package import *


class NaluWind(CtestPackage, bNaluWind, ROCmPackage):
    version("master", branch="master", submodules=True, preferred=True)
    version("multiphase", branch="multiphase_dev", submodules=True)

    variant("asan", default=False,
            description="Turn on address sanitizer")
    variant("fsi", default=False,
            description="Use FSI branch of openfast")
    variant("shared", default=True,
            description="Build shared libraries")
    variant("umpire", default=False,
            description="Enable Umpire")
    variant("gpu-aware-mpi", default=False,
            description="gpu-aware-mpi")
    variant("tests", default=True, description="Activate regression tests")
    variant("unit-tests", default=True, description="Activate unit tests")

    depends_on("hypre+gpu-aware-mpi", when="+gpu-aware-mpi")
    depends_on("hypre+umpire", when="+umpire")
    depends_on("trilinos gotype=long cxxstd=17")
    depends_on("trilinos~shared", when="+trilinos-solvers")
    depends_on("trilinos+wrapper", when="+cuda")
    depends_on("openfast@develop+netcdf+cxx", when="+fsi")

    for _arch in ROCmPackage.amdgpu_targets:
        depends_on("trilinos@13.4.0.2022.10.27: ~shared+exodus+tpetra+zoltan+stk~superlu-dist~superlu+hdf5+shards~hypre+gtest+rocm amdgpu_target={0}".format(_arch),
                   when="+rocm amdgpu_target={0}".format(_arch))
        depends_on("hypre+rocm amdgpu_target={0}".format(_arch), when="+hypre+rocm amdgpu_target={0}".format(_arch))

    conflicts("+cuda", when="+rocm")
    conflicts("^hypre+cuda", when="~cuda")
    conflicts("^hypre+rocm", when="~rocm")
    conflicts("^trilinos+cuda", when="~cuda")
    conflicts("^trilinos+rocm", when="~rocm")
    conflicts("+shared", when="+cuda",
             msg="invalid device functions are generated with shared libs and cuda")
    conflicts("+shared", when="+rocm",
             msg="invalid device functions are generated with shared libs and rocm")

    def setup_build_environment(self, env):
        super().setup_build_environment(env)
        env.append_flags("CXXFLAGS", "-DUSE_STK_SIMD_NONE")
        if "+asan" in self.spec:
            env.append_flags("CXXFLAGS", "-fsanitize=address -fno-omit-frame-pointer -fsanitize-blacklist={0}".format(join_path(self.package_dir, "blacklist.asan")))
            env.set("LSAN_OPTIONS", "suppressions={0}".format(join_path(self.package_dir, "sup.asan")))
            env.set("ASAN_OPTIONS", "detect_container_overflow=0")
        if "+cuda" in self.spec:
            env.set("CUDA_LAUNCH_BLOCKING", "1")
            env.set("CUDA_MANAGED_FORCE_DEVICE_ALLOC", "1")
            env.set("OMPI_CXX", self.spec["kokkos-nvcc-wrapper"].kokkos_cxx)
            env.set("MPICH_CXX", self.spec["kokkos-nvcc-wrapper"].kokkos_cxx)
            env.set("MPICXX_CXX", self.spec["kokkos-nvcc-wrapper"].kokkos_cxx)
        if "+rocm" in self.spec:
            env.append_flags('CXXFLAGS', '-fgpu-rdc')

    def cmake_args(self):
        spec = self.spec

        cmake_options = super(CtestPackage, self).cmake_args()
        cmake_options.extend(super(NaluWind, self).cmake_args())
        cmake_options.append(self.define("CMAKE_CXX_STANDARD", "17"))
        cmake_options.append(self.define_from_variant("BUILD_SHARED_LIBS", "shared"))

        if spec.satisfies("dev_path=*"):
            cmake_options.append(self.define("CMAKE_EXPORT_COMPILE_COMMANDS",True))
            cmake_options.append(self.define("ENABLE_TESTS", True))

        if "+umpire" in spec:
            cmake_options.append(self.define_from_variant("ENABLE_UMPIRE", "umpire"))
            cmake_options.append(self.define("UMPIRE_DIR", spec["umpire"].prefix))

        if "+rocm" in spec:
            cmake_options.append(self.define("CMAKE_CXX_COMPILER", spec["hip"].hipcc))
            cmake_options.append(self.define("ENABLE_ROCM", True))
            targets = spec.variants["amdgpu_target"].value
            cmake_options.append(self.define("GPU_TARGETS", ";".join(str(x) for x in targets)))

        cmake_options.append(self.define_from_variant("ENABLE_OPENFAST_FSI", "fsi"))
        if "+fsi" in spec:
            cmake_options.append(self.define("OpenFAST_DIR", spec["openfast"].prefix))
            cmake_options.append(self.define("ENABLE_OPENFAST", True))

        if spec.satisfies("+tests") or self.run_tests or spec.satisfies("dev_path=*"):
            cmake_options.append(self.define("ENABLE_TESTS", True))
            cmake_options.append(self.define("NALU_WIND_SAVE_GOLDS", True))
            cmake_options.append(self.define("NALU_WIND_SAVED_GOLDS_DIR", super().saved_golds_dir))
            cmake_options.append(self.define("NALU_WIND_REFERENCE_GOLDS_DIR", super().reference_golds_dir))

        return cmake_options
