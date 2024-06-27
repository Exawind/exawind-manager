# Copyright 2013-2024 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack.package import *


class Pelec(CMakePackage, CudaPackage, ROCmPackage):
    """An AMR code for compressible reacting flow simulations."""

    homepage = "https://github.com/AMReX-Combustion/PeleC"
    git = "https://github.com/AMReX-Combustion/PeleC.git"

    maintainers("jrood-nrel")

    tags = ["ecp", "ecp-apps"]

    license("BSD-3-Clause")

    version("main", branch="development", submodules=True)

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
    variant("masa", default=False, description="Enable MASA integration")
    variant("mpi", default=True, description="Enable MPI support")
    variant("openmp", default=False, description="Enable OpenMP for CPU builds")
    variant("shared", default=True, description="Build shared libraries")
    variant("tiny_profile", default=True, description="Activate tiny profile")
    variant("hdf5", default=False, description="Enable HDF5 plots with ZFP compression")
    variant("sycl", default=False, description="Enable SYCL backend")

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

    for arch in CudaPackage.cuda_arch_values:
        depends_on("ascent+cuda cuda_arch=%s" % arch, when="+ascent+cuda cuda_arch=%s" % arch)

    conflicts("+openmp", when="+cuda")

    def cmake_args(self):
        define = self.define
        spec = self.spec

        vs = [
            "ascent",
            "cuda",
            "masa",
            "mpi",
            "openmp",
            "particles",
            "rocm",
            "sycl",
            "tiny_profile",
        ]
        args = [self.define_from_variant("PELE_ENABLE_%s" % v.upper(), v) for v in vs]

        args += [
            self.define_from_variant("BUILD_SHARED_LIBS", "shared"),
            self.define_from_variant("PELE_DIM", "dim"))
            self.define_from_variant("PELE_PRECISION", "precision"))
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

        return args
