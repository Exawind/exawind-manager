# Copyright (c) 2022, National Technology & Engineering Solutions of Sandia,
# LLC (NTESS). Under the terms of Contract DE-NA0003525 with NTESS, the U.S.
# Government retains certain rights in this software.
#
# This software is released under the BSD 3-clause license. See LICENSE file
# for more details.

from spack import *
from shutil import copyfile
import os
from spack.pkg.exawind.ctest_package import *


class Exawind(CtestPackage, CudaPackage, ROCmPackage):
    """Multi-application driver for Exawind project."""

    homepage = "https://github.com/Exawind/exawind-driver"
    git = "https://github.com/Exawind/exawind-driver.git"

    maintainers = ["jrood-nrel"]

    tags = ["ecp", "ecp-apps"]

    license("Apache-2.0")

    version("master", branch="main", submodules=True, preferred=True)
    version("multiphase", branch="multiphase_dev", submodules=True)
    version("1.0.0", tag="v1.0.0", submodules=True)

    variant("asan", default=False,
            description="turn on address sanitizer")
    variant("amr_wind_gpu", default=False,
            description="Enable AMR-Wind on the GPU")
    variant("nalu_wind_gpu", default=False,
            description="Enable Nalu-Wind on the GPU")
    variant("umpire", default=False,
            description="Enable Umpire")
    variant("sycl", default=False,
            description="Enable SYCL backend for AMR-Wind")
    variant("gpu-aware-mpi", default=False,
            description="gpu-aware-mpi")

    for arch in CudaPackage.cuda_arch_values:
        depends_on("amr-wind+cuda cuda_arch=%s" % arch, when="+amr_wind_gpu+cuda cuda_arch=%s" % arch)
        depends_on("nalu-wind+cuda cuda_arch=%s" % arch, when="+nalu_wind_gpu+cuda cuda_arch=%s" % arch)
        depends_on("trilinos+cuda cuda_arch=%s" % arch, when="+nalu_wind_gpu+cuda cuda_arch=%s" % arch)

    for arch in ROCmPackage.amdgpu_targets:
        depends_on("amr-wind+rocm amdgpu_target=%s" % arch, when="+amr_wind_gpu+rocm amdgpu_target=%s" % arch)
        depends_on("nalu-wind+rocm amdgpu_target=%s" % arch, when="+nalu_wind_gpu+rocm amdgpu_target=%s" % arch)
        depends_on("trilinos+rocm amdgpu_target=%s" % arch, when="+nalu_wind_gpu+rocm amdgpu_target=%s" % arch)

    depends_on("nalu-wind+ninja+hypre+fsi+openfast+tioga")
    depends_on("amr-wind+ninja~hypre+netcdf+mpi+tiny_profile")
    depends_on("trilinos+ninja")
    depends_on("yaml-cpp@0.6:")
    depends_on("tioga~nodegid")
    depends_on("openfast+cxx@2.6.0:")
    depends_on("amr-wind+sycl", when="+amr_wind_gpu+sycl")
    depends_on("nalu-wind@multiphase", when="@multiphase")
    depends_on("amr-wind@multiphase", when="@multiphase")
    depends_on("kokkos-nvcc-wrapper", type="build", when="+cuda")
    depends_on("mpi")
    depends_on("nalu-wind+umpire", when="+umpire")
    depends_on("amr-wind+umpire", when="+umpire")
    depends_on("nalu-wind+gpu-aware-mpi", when="+gpu-aware-mpi")
    depends_on("amr-wind+gpu-aware-mpi", when="+gpu-aware-mpi")
    depends_on("nalu-wind@2.0.0:", when="@1.0.0:")
    depends_on("amr-wind@0.9.0:", when="@1.0.0:")
    depends_on("tioga@1.0.0:", when="@1.0.0:")

    conflicts("+cuda", when="~amr_wind_gpu~nalu_wind_gpu")
    conflicts("+rocm", when="~amr_wind_gpu~nalu_wind_gpu")
    conflicts("+sycl", when="~amr_wind_gpu~nalu_wind_gpu")
    conflicts("+amr_wind_gpu", when="~cuda~rocm~sycl")
    conflicts("+nalu_wind_gpu", when="~cuda~rocm")
    conflicts("+nalu_wind_gpu", when="+sycl")
    conflicts("^nalu-wind+cuda", when="~nalu_wind_gpu")
    conflicts("^nalu-wind+rocm", when="~nalu_wind_gpu")
    conflicts("^amr-wind+cuda", when="~amr_wind_gpu")
    conflicts("^amr-wind+rocm", when="~amr_wind_gpu")
    conflicts("^amr-wind+sycl", when="~amr_wind_gpu")
    conflicts("+sycl", when="+cuda")
    conflicts("+rocm", when="+cuda")
    conflicts("+sycl", when="+rocm")

    def cmake_args(self):
        spec = self.spec

        args = [self.define("MPI_HOME", spec["mpi"].prefix)]

        if spec.satisfies("dev_path=*"):
            args.append(self.define("CMAKE_EXPORT_COMPILE_COMMANDS",True))

        if spec.satisfies("+umpire"):
            args.append(self.define_from_variant("EXAWIND_ENABLE_UMPIRE", "umpire"))
            args.append(self.define("UMPIRE_DIR", self.spec["umpire"].prefix))

        if spec.satisfies("+cuda"):
            args.append(self.define("CMAKE_CXX_COMPILER", spec["mpi"].mpicxx))
            args.append(self.define("CMAKE_C_COMPILER", spec["mpi"].mpicc))
            args.append(self.define("EXAWIND_ENABLE_CUDA", True))
            args.append(self.define("CUDAToolkit_ROOT", self.spec["cuda"].prefix))
            args.append(self.define("EXAWIND_CUDA_ARCH", self.spec.variants["cuda_arch"].value))

        if spec.satisfies("+rocm"):
            targets = self.spec.variants["amdgpu_target"].value
            args.append(self.define("EXAWIND_ENABLE_ROCM", True))
            args.append("-DCMAKE_CXX_COMPILER={0}".format(self.spec["hip"].hipcc))
            args.append("-DCMAKE_HIP_ARCHITECTURES=" + ";".join(str(x) for x in targets))
            args.append("-DAMDGPU_TARGETS=" + ";".join(str(x) for x in targets))
            args.append("-DGPU_TARGETS=" + ";".join(str(x) for x in targets))

        if spec.satisfies("^amr-wind+hdf5"):
            args.append(self.define("H5Z_ZFP_USE_STATIC_LIBS", True))

        return args

    def setup_build_environment(self, env):
        env.append_flags("CXXFLAGS", "-DUSE_STK_SIMD_NONE")
        if "+asan" in self.spec:
            env.append_flags("CXXFLAGS", "-fsanitize=address -fno-omit-frame-pointer -fsanitize-blacklist={0}".format(join_path(self.package_dir, "blacklist.asan")))
            env.set("LSAN_OPTIONS", "suppressions={0}".format(join_path(self.package_dir, "sup.asan")))
            env.set("ASAN_OPTIONS", "detect_container_overflow=0")
        if "+rocm+amr_wind_gpu~nalu_wind_gpu" in self.spec:
            # Manually turn off device self.defines to solve Kokkos issues in Nalu-Wind headers
            env.append_flags("CXXFLAGS", "-U__HIP_DEVICE_COMPILE__ -DDESUL_HIP_RDC")
        if "+cuda" in self.spec:
            env.set("OMPI_CXX", self.spec["kokkos-nvcc-wrapper"].kokkos_cxx)
            env.set("MPICH_CXX", self.spec["kokkos-nvcc-wrapper"].kokkos_cxx)
            env.set("MPICXX_CXX", self.spec["kokkos-nvcc-wrapper"].kokkos_cxx)
            if "+nalu_wind_gpu" in self.spec:
                env.set("CUDA_LAUNCH_BLOCKING", "1") 
                env.set("CUDA_MANAGED_FORCE_DEVICE_ALLOC", "1")
        if "+rocm" in self.spec:
            env.set("OMPI_CXX", self.spec["hip"].hipcc)
            env.set("MPICH_CXX", self.spec["hip"].hipcc)
            env.set("MPICXX_CXX", self.spec["hip"].hipcc)
