# Copyright 2013-2024 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack.package import *
from spack.pkg.exawind.ctest_package import *


class Pelelmex(CtestPackage, CMakePackage, CudaPackage, ROCmPackage):
    """An AMR code for compressible reacting flow simulations."""

    homepage = "https://github.com/AMReX-Combustion/PeleLMeX"
    git = "https://github.com/AMReX-Combustion/PeleLMeX.git"

    maintainers("jrood-nrel")

    tags = ["ecp", "ecp-apps"]

    license("BSD-3-Clause")

    version("main", branch="development", submodules=True)

    variant("asan", default=False, description="Turn on address sanitizer")
    variant("clangtidy", default=False, description="Turn on clang-tidy")
    variant(
        "dim",
        default="3",
        description="Phyiscal dimensions",
        values=["2", "3"],
        multi=False
    )
    variant(
        "precision",
        default="DOUBLE",
        description="Precision: DOUBLE or FLOAT",
        values=["DOUBLE", "FLOAT"],
        multi=False
    )
    variant("ascent", default=False, description="Enable Ascent integration")
    variant("eb", default=True, description="Enable embedded boundaries")
    variant("masa", default=False, description="Enable MASA integration")
    variant("mpi", default=True, description="Enable MPI support")
    variant("openmp", default=False, description="Enable OpenMP for CPU builds")
    variant("particles", default=False, description="Enable AMReX particles")
    variant("shared", default=True, description="Build shared libraries")
    variant("tests", default=False, description="Enable some things for testing")
    variant("tiny_profile", default=True, description="Activate tiny profile")
    variant("hdf5", default=False, description="Enable HDF5 plots with ZFP compression")
    variant("sycl", default=False, description="Enable SYCL backend")
    variant("hypre", default=False, description="Enable hypre integration")

    depends_on("mpi", when="+mpi")
    depends_on("hdf5~mpi", when="+hdf5~mpi")
    depends_on("hdf5+mpi", when="+hdf5+mpi")
    depends_on("h5z-zfp", when="+hdf5")
    depends_on("zfp", when="+hdf5")
    depends_on("masa", when="+masa")
    depends_on("ascent~mpi", when="+ascent~mpi")
    depends_on("ascent+mpi", when="+ascent+mpi")
    depends_on("py-matplotlib", when="+masa")
    depends_on("py-pandas", when="+masa")
    depends_on("hypre@2.20.0:", when="+hypre")
    depends_on("hypre+mpi", when="+hypre+mpi")
    depends_on("hypre+sycl", when="+hypre+sycl")

    for arch in CudaPackage.cuda_arch_values:
        depends_on("ascent+cuda cuda_arch=%s" % arch, when="+ascent+cuda cuda_arch=%s" % arch)
    for arch in CudaPackage.cuda_arch_values:
        depends_on("hypre+cuda cuda_arch=%s" % arch, when="+cuda+hypre cuda_arch=%s" % arch)
    for arch in ROCmPackage.amdgpu_targets:
        depends_on(
            "hypre+rocm amdgpu_target=%s" % arch, when="+rocm+hypre amdgpu_target=%s" % arch
        )

    conflicts("+openmp", when="+cuda")
    conflicts("+openmp", when="+rocm")
    conflicts("+openmp", when="+sycl")

    requires("+tests", when="+cdash_submit")

    def setup_build_environment(self, env):
        spec = self.spec
        super().setup_build_environment(env)
        if spec.satisfies("+asan"):
            env.append_flags("CXXFLAGS", "-fsanitize=address -fno-omit-frame-pointer")
            env.set("LSAN_OPTIONS", "suppressions={0}".format(join_path(self.package_dir, "sup.asan")))

    def cmake_args(self):
        define = self.define
        spec = self.spec

        vs = [
            "ascent",
            "cuda",
            "eb",
            "masa",
            "mpi",
            "openmp",
            "particles",
            "rocm",
            "sycl",
            "hypre",
            "tiny_profile",
        ]
        args = [self.define_from_variant("PELE_ENABLE_%s" % v.upper(), v) for v in vs]

        args += [
            self.define_from_variant("BUILD_SHARED_LIBS", "shared"),
            self.define_from_variant("PELE_DIM", "dim"),
            self.define_from_variant("PELE_PRECISION", "precision"),
            self.define_from_variant("PELE_ENABLE_CLANG_TIDY", "clangtidy"),
        ]

        if spec.satisfies("+mpi"):
            args.append(define("MPI_HOME", spec["mpi"].prefix))

        if spec.satisfies("+hdf5"):
            args.append(define("PELE_ENABLE_HDF5", True))
            args.append(define("PELE_ENABLE_HDF5_ZFP", True))
            # Help AMReX understand if HDF5 is parallel or not.
            # Building HDF5 with CMake as Spack does, causes this inspection to break.
            args.append(define("HDF5_IS_PARALLEL", spec.satisfies("+mpi")))

        if spec.satisfies("+cuda"):
            amrex_arch = [
                "{0:.1f}".format(float(i) / 10.0) for i in spec.variants["cuda_arch"].value
            ]
            if amrex_arch:
                args.append(define("AMReX_CUDA_ARCH", amrex_arch))

        if spec.satisfies("+rocm"):
            args.append(define("CMAKE_CXX_COMPILER", spec["hip"].hipcc))
            targets = spec.variants["amdgpu_target"].value
            args.append("-DAMReX_AMD_ARCH=" + ";".join(str(x) for x in targets))

        if spec.satisfies("+sycl"):
            requires(
                "%dpcpp",
                "%oneapi",
                policy="one_of",
                msg=(
                    "AMReX's SYCL GPU Backend requires DPC++ (dpcpp) "
                    "or the oneAPI CXX (icpx) compiler."
                ),
            )

        if spec.satisfies("dev_path=*"):
            cmake_options.append(self.define("CMAKE_EXPORT_COMPILE_COMMANDS", True))

        if spec.satisfies("+tests"):
            cmake_options.append(self.define("PELE_ENABLE_FCOMPARE_FOR_TESTS", True))
            cmake_options.append(self.define("PELE_SAVE_GOLDS", True))
            cmake_options.append(self.define("PELE_SAVED_GOLDS_DIRECTORY", self.saved_golds_dir))
            cmake_options.append(self.define("PELE_REFERENCE_GOLDS_DIRECTORY", self.reference_golds_dir))

        return args
