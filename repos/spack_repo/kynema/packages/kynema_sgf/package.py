from spack.package import *
from spack_repo.builtin.packages.kynema_sgf.package import KynemaSGF as bKynemaSGF
from spack_repo.kynema.packages.ctest_package.package import *
find_machine = importlib.import_module("find-kynema-manager")

class KynemaSGF(bKynemaSGF, CtestPackage):
    variant("asan", default=False, description="Turn on address sanitizer")
    variant("clangtidy", default=False, description="Turn on clang-tidy")

    depends_on("netcdf-c+mpi", when="+netcdf")
    requires("+tests", when="+cdash_submit")
    requires("+mpi", when="+kynema-fmb")
    requires("+mpi", when="+openfast")

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
        cmake_options = super(KynemaSGF, self).cmake_args()

        if spec.satisfies("dev_path=*"):
            cmake_options.append(self.define("CMAKE_EXPORT_COMPILE_COMMANDS", True))

        if spec.satisfies("+clangtidy"):
            cmake_options.append(self.define("KYNEMA_SGF_ENABLE_CLANG_TIDY", True))

        if spec.satisfies("+tests"):
            cmake_options.append(self.define("KYNEMA_SGF_TEST_WITH_FCOMPARE", True))
            cmake_options.append(self.define("KYNEMA_SGF_SAVE_GOLDS", True))
            cmake_options.append(self.define("KYNEMA_SGF_SAVED_GOLDS_DIRECTORY", super().saved_golds_dir))
            cmake_options.append(self.define("KYNEMA_SGF_REFERENCE_GOLDS_DIRECTORY", super().reference_golds_dir))

        return cmake_options
