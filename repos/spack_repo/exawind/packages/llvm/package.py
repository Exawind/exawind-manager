import os
from spack.package import *
from spack_repo.builtin.packages.llvm.package import Llvm as bLlvm


class Llvm(bLlvm):
     patch("lldb_python_exe_relative_path.patch", when="@16:+lldb+python")
     depends_on("python@3.8:3.12", when="@:19 +python")
