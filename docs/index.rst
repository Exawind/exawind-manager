================
 Exawind-Manager
================

Exawind-Manager is a project specialization of `Spack-Manager <https://github.com/sandialabs/spack-manager>`_.
Spack-Manager is a light-weight extension to 
`Spack <https://spack.io>`_ that is intended to streamline the software development and deployment cycle
for software projects on specific machines.
A given software project, especially in high performance computing (HPC), typically requires managing multiple software dependencies using multiple compilers and processing devices across many machines.
Spack-Manager is quite literal in its name, in that it provides a way to manage and organize these configurations
across multiple machines, and multiple projects. Exawind-Manager is specialized towards the `ExaWind <https://github.com/exawind>`_ project, which is a set of complex coupled applications for modeling the physics of entire wind farms at high fidelities.

More information on Spack-Manager itself can be found `here <https://github.com/sandialabs/spack-manager>`_. Features of Spack-Manager also generally continue to be developed in Spack itself by the Spack-Manager author. Spack-Manager itself is designed as a fully integrated extension of Spack.

Spack-Manager and Exawind-Manager also provide several shortcut commands for automating simple tasks of setting up environments and building and deploying them.

Tutorial
========
In this tutorial we will learn the most used features and workflows for doing development of HPC software using this framework. We will do so using an Apple Macbook Pro M1. To set up such a machine for using Exawind-Manager, we need to satisfy these requirements:

1. Install `Homebrew <https://brew.sh>`_
2. `brew install gcc` for gfortran
3. `brew install make` for using depfiles
4. Install Python 3.12 if requiring use of SSL_CERT_FILE

Next, we start by cloning exawind-manager:

.. code-block:: console

   jrood@jrood-38508s ~ % git clone -c feature.manyFiles=true --depth=1 --shallow-submodules --recursive https://github.com/Exawind/exawind-manager.git
   Cloning into 'exawind-manager'...
   remote: Enumerating objects: 167, done.
   remote: Counting objects: 100% (167/167), done.
   remote: Compressing objects: 100% (135/135), done.
   remote: Total 167 (delta 15), reused 110 (delta 7), pack-reused 0 (from 0)
   Receiving objects: 100% (167/167), 2.00 MiB | 3.49 MiB/s, done.
   Resolving deltas: 100% (15/15), done.
   Submodule 'spack' (https://github.com/spack/spack) registered for path 'spack'
   Submodule 'spack-manager' (https://github.com/sandialabs/spack-manager.git) registered for path 'spack-manager'
   Cloning into '/Users/jrood/exawind-manager/spack'...
   remote: Enumerating objects: 21263, done.        
   remote: Counting objects: 100% (21263/21263), done.        
   remote: Compressing objects: 100% (12210/12210), done.        
   remote: Total 21263 (delta 980), reused 13494 (delta 917), pack-reused 0 (from 0)        
   Receiving objects: 100% (21263/21263), 14.82 MiB | 7.91 MiB/s, done.
   Resolving deltas: 100% (980/980), done.
   Cloning into '/Users/jrood/exawind-manager/spack-manager'...
   remote: Enumerating objects: 98, done.        
   remote: Counting objects: 100% (98/98), done.        
   remote: Compressing objects: 100% (92/92), done.        
   remote: Total 98 (delta 5), reused 37 (delta 0), pack-reused 0 (from 0)        
   Receiving objects: 100% (98/98), 2.02 MiB | 3.33 MiB/s, done.
   Resolving deltas: 100% (5/5), done.
   remote: Total 0 (delta 0), reused 0 (delta 0), pack-reused 0 (from 0)
   remote: Enumerating objects: 4354, done.
   remote: Counting objects: 100% (4354/4354), done.
   remote: Compressing objects: 100% (1866/1866), done.
   remote: Total 2760 (delta 596), reused 1171 (delta 31), pack-reused 0 (from 0)
   Receiving objects: 100% (2760/2760), 2.39 MiB | 9.54 MiB/s, done.
   Resolving deltas: 100% (596/596), completed with 552 local objects.
   From https://github.com/spack/spack
    * branch              313b7d4cdbbf0610b9b449d5855cb0f52c6df1eb -> FETCH_HEAD
   Submodule path 'spack': checked out '313b7d4cdbbf0610b9b449d5855cb0f52c6df1eb'
   Submodule path 'spack-manager': checked out '9a02da44788c943c1f1d4fcbe85b7397abe0a724'


To invoke Exawind-Manager we merely `source shortcut.sh` which sets the `EXAWIND_MANAGER` environment variable and also invokes Spack's shell support through our own `spack-start` command:

.. code-block:: console

   jrood@jrood-38508s ~ % cd exawind-manager 
   jrood@jrood-38508s exawind-manager % source shortcut.sh 
   /Users/jrood/exawind-manager/.bootstrap
   ==> Added repo with namespace 'exawind'.
   ==> Added 2 new compilers to /Users/jrood/exawind-manager/.spack/darwin/compilers.yaml
       gcc@14.2.0  apple-clang@15.0.0
   ==> Compilers are defined in the following files:
       /Users/jrood/exawind-manager/.spack/darwin/compilers.yaml

Next, we can probe the machine to see what Exawind-Manager thinks the machine is. Note for our project we have a set list of machines in which we curate our own configurations. They are defined and queried in the `find-exawind-manager.py <https://github.com/Exawind/exawind-manager/blob/main/find-exawind-manager.py>`_ file. Here we query which configuration files Exawind-Manager will choose:

.. code-block:: console

   jrood@jrood-38508s exawind-manager % spack manager find-machine
   exawind-manager darwin

Therefore Exawind-Manager will include the `yaml` files from the `darwin` (MacOS) `configuration <https://github.com/Exawind/exawind-manager/tree/main/configs/darwin>`_. Note the `base <https://github.com/Exawind/exawind-manager/tree/main/configs/base>`_ configuration files will always be used, with the machine-specific configuration taking precedence. The base files set many preferences as defaults such as where downloads are cached, the build stage is located, etc. Any of these can be overidden by the machine-specific configuration.

Within the machine-specific config or the base config, we have a `template.yaml` file which contains the default `spack.yaml` file that will be used for that machine if none is created or specified by the user. The `spack.yaml` file generally contains the spec or specs that will be built for the project on that machine by default. For the base template we see the default `template.yaml` below:

.. code-block:: console

   jrood@jrood-38508s exawind-manager % cat configs/base/template.yaml 
   spack:
     specs:
     - exawind

The first thing we could do is then easily build our entire project using the `deploy.py <https://github.com/Exawind/exawind-manager/blob/main/scripts/deploy.py>`_ script.

.. code-block:: console

   jrood@jrood-38508s exawind-manager % nice deploy.py --ranks 32 --depfile --overwrite --name exawind-env
   exawind-manager darwin
   Using env: /Users/jrood/exawind-manager/environments/exawind-env
   configure args
   ==> Using cached archive: /Users/jrood/.spack_downloads/blobs/sha256/8b3d4926c5fa7a6e4fc5834a3e7783a0b53b174eb77ef36ade87f423891f8331
   ==> Using cached archive: /Users/jrood/.spack_downloads/blobs/sha256/91214626a86c21fc0d76918884ec819050d4d52b4f78df7cc9769a83fbee2f71
   ==> Installing "clingo-bootstrap@=spack~docs+ipo+optimized+python build_system=cmake build_type=Release generator=make arch=darwin-bigsur-aarch64 %apple-clang@=15.0.0" from a buildcache
   ==> Starting concretization
   ==> Concretized 1 spec:
    -   mz2hzbn  exawind@1.2.0~amr_wind_gpu~asan~cdash_submit~cuda~gpu-aware-mpi~ipo~nalu_wind_gpu~ninja~rocm~sycl~tests build_system=cmake build_type=Release ctest_args='-R unit' generator=make reference_golds=default arch=darwin-ventura-m1 %apple-clang@15.0.0
    -   u433tbl      ^amr-wind@3.4.0~asan~ascent~cdash_submit~clangtidy~cuda~fft~gpu-aware-mpi~hdf5~helics~hypre~ipo~masa+mpi+netcdf~ninja~openfast~openmp~rocm+shared~sycl+tests+tiny_profile~umpire~waves2amr build_system=cmake build_type=Release ctest_args='-R unit' generator=make reference_golds=default arch=darwin-ventura-m1 %apple-clang@15.0.0
    -   dw42jis          ^netcdf-c@4.9.2~blosc~byterange~dap~fsync~hdf4~ipo~jna~logging+mpi~nczarr_zip+optimize+parallel-netcdf+pic+shared+szip+zstd build_system=cmake build_type=Release generator=make patches=0161eb8,3b09181 arch=darwin-ventura-m1 %apple-clang@15.0.0
    -   gi2hasa              ^bzip2@1.0.8~debug~pic+shared build_system=generic arch=darwin-ventura-m1 %apple-clang@15.0.0
    -   gxvu2tm                  ^diffutils@3.10 build_system=autotools arch=darwin-ventura-m1 %apple-clang@15.0.0
    -   yki3nbw              ^libaec@1.0.6~ipo+shared build_system=cmake build_type=Release generator=make arch=darwin-ventura-m1 %apple-clang@15.0.0
    -   ibpjfs4              ^m4@1.4.19+sigsegv build_system=autotools patches=9dc5fbd,bfdffa7 arch=darwin-ventura-m1 %apple-clang@15.0.0
    -   t23m7na                  ^libsigsegv@2.14 build_system=autotools arch=darwin-ventura-m1 %apple-clang@15.0.0
    -   rfxwvue              ^zstd@1.5.6~ipo+programs build_system=cmake build_type=Release compression=none generator=make libs=shared,static arch=darwin-ventura-m1 %apple-clang@15.0.0
    -   uzbwlhe          ^py-netcdf4@1.7.2+mpi build_system=python_pip patches=255b5ae arch=darwin-ventura-m1 %apple-clang@15.0.0
    -   6bapthx              ^py-certifi@2023.7.22 build_system=python_pip arch=darwin-ventura-m1 %apple-clang@15.0.0
    -   suuwb2d              ^py-cftime@1.0.3.4 build_system=python_pip arch=darwin-ventura-m1 %apple-clang@15.0.0
    -   vfvyi7m              ^py-cython@3.0.11 build_system=python_pip arch=darwin-ventura-m1 %apple-clang@15.0.0
    -   i4beywl              ^py-mpi4py@4.0.1 build_system=python_pip arch=darwin-ventura-m1 %apple-clang@15.0.0
    -   vxkadm6              ^py-pip@24.3.1 build_system=generic arch=darwin-ventura-m1 %apple-clang@15.0.0
    -   wjp6i5i              ^py-setuptools@76.0.0 build_system=generic arch=darwin-ventura-m1 %apple-clang@15.0.0
    -   vz7m6ie              ^py-setuptools-scm@8.2.0+toml build_system=python_pip arch=darwin-ventura-m1 %apple-clang@15.0.0
    -   w36stuz                  ^git@2.48.1+man+nls+perl+subtree~svn~tcltk build_system=autotools arch=darwin-ventura-m1 %apple-clang@15.0.0
    -   msnafax                      ^libidn2@2.3.7 build_system=autotools arch=darwin-ventura-m1 %apple-clang@15.0.0
    -   7jp2pqk                          ^libunistring@1.2 build_system=autotools arch=darwin-ventura-m1 %apple-clang@15.0.0
    -   ct2nxkp                      ^openssh@9.9p1+gssapi build_system=autotools patches=3f06fc0,d886b98 arch=darwin-ventura-m1 %apple-clang@15.0.0
    -   l6kpiuw                          ^krb5@1.21.3+shared build_system=autotools arch=darwin-ventura-m1 %apple-clang@15.0.0
    -   vtcfqx4                              ^bison@3.8.2~color build_system=autotools arch=darwin-ventura-m1 %apple-clang@15.0.0
    -   i4iecug                          ^libedit@3.1-20240808 build_system=autotools arch=darwin-ventura-m1 %apple-clang@15.0.0
    -   eixygxn                          ^libxcrypt@4.4.38~obsolete_api build_system=autotools arch=darwin-ventura-m1 %apple-clang@15.0.0
    -   ljjtffp                      ^pcre2@10.44~ipo~jit+multibyte+pic build_system=cmake build_type=Release generator=make arch=darwin-ventura-m1 %apple-clang@15.0.0
    -   orpxu2p                  ^py-packaging@24.2 build_system=python_pip arch=darwin-ventura-m1 %apple-clang@15.0.0
    -   whtq7h4                      ^py-flit-core@3.10.1 build_system=python_pip arch=darwin-ventura-m1 %apple-clang@15.0.0
    -   h5zy43v              ^py-wheel@0.45.1 build_system=generic arch=darwin-ventura-m1 %apple-clang@15.0.0
    -   n77pkqq              ^python@3.13.2+bz2+ctypes+dbm~debug+libxml2+lzma~optimizations+pic+pyexpat+pythoncmd+readline+shared+sqlite3+ssl~tkinter+uuid+zlib build_system=generic arch=darwin-ventura-m1 %apple-clang@15.0.0
   [e]  4aj5ju7                  ^apple-libuuid@1353.100.2 build_system=bundle arch=darwin-ventura-m1 %apple-clang@15.0.0
    -   iavpy4q                  ^expat@2.7.0~ipo~libbsd+shared build_system=cmake build_type=Release generator=make arch=darwin-ventura-m1 %apple-clang@15.0.0
    -   wgw4owk                  ^gdbm@1.23 build_system=autotools arch=darwin-ventura-m1 %apple-clang@15.0.0
    -   ctx5ou3                  ^libffi@3.4.6 build_system=autotools arch=darwin-ventura-m1 %apple-clang@15.0.0
    -   dnnt63f                  ^openssl@3.4.1~docs+shared build_system=generic certs=mozilla arch=darwin-ventura-m1 %apple-clang@15.0.0
    -   qrsyolz                      ^ca-certificates-mozilla@2025-02-25 build_system=generic arch=darwin-ventura-m1 %apple-clang@15.0.0
    -   gesbmde                  ^readline@8.2 build_system=autotools patches=1ea4349,24f587b,3d9885e,5911a5b,622ba38,6c8adf8,758e2ec,79572ee,a177edc,bbf97f1,c7b45ff,e0013d9,e065038 arch=darwin-ventura-m1 %apple-clang@15.0.0
    -   zkmnisf                  ^sqlite@3.46.0+column_metadata+dynamic_extensions+fts~functions+rtree build_system=autotools arch=darwin-ventura-m1 %apple-clang@15.0.0
    -   ofkc2ky              ^python-venv@1.0 build_system=generic arch=darwin-ventura-m1 %apple-clang@15.0.0
    -   7vw44na          ^py-numpy@2.2.4 build_system=python_pip patches=873745d arch=darwin-ventura-m1 %apple-clang@15.0.0
    -   soxm3iy              ^py-meson-python@0.16.0 build_system=python_pip arch=darwin-ventura-m1 %apple-clang@15.0.0
    -   klvlhcu                  ^meson@1.7.0 build_system=python_pip patches=0f0b1bd arch=darwin-ventura-m1 %apple-clang@15.0.0
    -   qfkcsvl                  ^py-pyproject-metadata@0.7.1 build_system=python_pip arch=darwin-ventura-m1 %apple-clang@15.0.0
    -   2vdjg64      ^cmake@3.31.6~doc+ncurses+ownlibs~qtgui build_system=generic build_type=Release arch=darwin-ventura-m1 %apple-clang@15.0.0
    -   k6bl6kl          ^curl@8.11.1~gssapi~ldap~libidn2~librtmp~libssh~libssh2+nghttp2 build_system=autotools libs=shared,static tls=secure_transport arch=darwin-ventura-m1 %apple-clang@15.0.0
    -   uzkvaxu              ^nghttp2@1.65.0 build_system=autotools arch=darwin-ventura-m1 %apple-clang@15.0.0
    -   usixkny          ^ncurses@6.5~symlinks+termlib abi=none build_system=autotools patches=7a351bc arch=darwin-ventura-m1 %apple-clang@15.0.0
    -   kcwseep          ^zlib@1.3.1+optimize+pic+shared build_system=makefile arch=darwin-ventura-m1 %apple-clang@15.0.0
    -   uf5swtz      ^gmake@4.4.1~guile build_system=generic arch=darwin-ventura-m1 %apple-clang@15.0.0
    -   fizesdu      ^mpich@4.3.0~argobots~cuda+fortran+hwloc+hydra~level_zero+libxml2~pci~rocm+romio~slurm~vci~verbs+wrapperrpath~xpmem build_system=autotools datatype-engine=auto device=ch4 netmod=ofi pmi=default arch=darwin-ventura-m1 %apple-clang@15.0.0
    -   bmwf3ok          ^findutils@4.10.0 build_system=autotools patches=440b954 arch=darwin-ventura-m1 %apple-clang@15.0.0
    -   rvxt5uj              ^gettext@0.23.1+bzip2+curses+git~libunistring+libxml2+pic+shared+tar+xz build_system=autotools arch=darwin-ventura-m1 %apple-clang@15.0.0
    -   qqcbb3h                  ^tar@1.35 build_system=autotools zip=pigz arch=darwin-ventura-m1 %apple-clang@15.0.0
    -   qenbi55                      ^pigz@2.8 build_system=makefile arch=darwin-ventura-m1 %apple-clang@15.0.0
    -   eabkdvh          ^gnuconfig@2024-07-27 build_system=generic arch=darwin-ventura-m1 %apple-clang@15.0.0
    -   4qnym3z          ^hwloc@2.11.1~cairo~cuda~gl~level_zero~libudev+libxml2~nvml~opencl~pci~rocm build_system=autotools libs=shared,static arch=darwin-ventura-m1 %apple-clang@15.0.0
    -   q2e7eap          ^libfabric@1.22.0~cuda~debug~kdreg~level_zero~uring build_system=autotools fabrics=sockets,tcp,udp arch=darwin-ventura-m1 %apple-clang@15.0.0
    -   7pky2zc          ^libxml2@2.13.5~http+pic~python+shared build_system=autotools arch=darwin-ventura-m1 %apple-clang@15.0.0
    -   ak6dl2i              ^libiconv@1.17 build_system=autotools libs=shared,static arch=darwin-ventura-m1 %apple-clang@15.0.0
    -   w3qd4kf              ^xz@5.6.3~pic build_system=autotools libs=shared,static arch=darwin-ventura-m1 %apple-clang@15.0.0
    -   d7h3rch          ^pkgconf@2.3.0 build_system=autotools arch=darwin-ventura-m1 %apple-clang@15.0.0
    -   qtf7ks6          ^yaksa@0.3~cuda~level_zero~rocm build_system=autotools arch=darwin-ventura-m1 %apple-clang@15.0.0
    -   y4sqkw4              ^autoconf@2.72 build_system=autotools arch=darwin-ventura-m1 %apple-clang@15.0.0
    -   zy2tzr5              ^automake@1.16.5 build_system=autotools arch=darwin-ventura-m1 %apple-clang@15.0.0
    -   3wntdqx              ^libtool@2.4.7 build_system=autotools arch=darwin-ventura-m1 %apple-clang@15.0.0
    -   i7zbc3h      ^nalu-wind@2.2.2~asan~boost~catalyst~cdash_submit~cuda~fftw~gpu-aware-mpi+hypre~ipo~ninja+openfast+pic~rocm+shared~tests+tioga~trilinos-solvers~umpire+unit-tests~wind-utils abs_tol=1e-15 build_system=cmake build_type=Release ctest_args='-R unit' generator=make reference_golds=default rel_tol=1e-12 arch=darwin-ventura-m1 %apple-clang@15.0.0
    -   766qr5m          ^hypre@2.32.0~caliper~complex~cublas~cuda~debug+fortran~gptune~gpu-aware-mpi~int64~internal-superlu+lapack~magma~mixedint+mpi~openmp~rocblas~rocm+shared~superlu-dist~sycl~umpire~unified-memory build_system=autotools precision=double arch=darwin-ventura-m1 %apple-clang@15.0.0
    -   nf4zr5p          ^nccmp@1.9.1.0~ipo build_system=cmake build_type=Release generator=make arch=darwin-ventura-m1 %apple-clang@15.0.0
    -   ty2mskn      ^openfast@4.0.2+cxx+dll-interface+double-precision~fastfarm~fpe-trap~ipo+netcdf~openmp+pic~rosco+shared build_system=cmake build_type=Release generator=make arch=darwin-ventura-m1 %apple-clang@15.0.0
    -   jbhwbxt          ^hdf5@1.14.5+cxx~fortran+hl~ipo~java~map+mpi+shared~subfiling~szip~threadsafe+tools api=default build_system=cmake build_type=Release generator=make arch=darwin-ventura-m1 %apple-clang@15.0.0
    -   ctwlu4y          ^openblas@0.3.29~bignuma~consistent_fpcsr+dynamic_dispatch+fortran~ilp64~ipo+locking+pic+shared build_system=cmake build_type=Release generator=make symbol_suffix=none threads=none arch=darwin-ventura-m1 %apple-clang@15.0.0
    -   bycpw22      ^tioga@1.3.0~asan~cdash_submit~ipo~ninja~nodegid+pic~shared~stats~timers build_system=cmake build_type=Release ctest_args='-R unit' generator=make reference_golds=default arch=darwin-ventura-m1 %apple-clang@15.0.0
    -   vbl5o4p      ^trilinos@16.1.0~adelus~adios2~amesos~amesos2~anasazi~asan~aztec~basker~belos~boost~chaco~complex~cuda~cuda_constexpr~cuda_rdc~debug~dtk~epetra~epetraext~epetraextbtf~epetraextexperimental~epetraextgraphreorderings+exodus+explicit_template_instantiation~float~fortran+gtest+hdf5~hypre~ifpack~ifpack2~intrepid~intrepid2~ipo~isorropia+kokkos~mesquite~minitensor~ml+mpi~muelu~mumps~nox~openmp~pamgen~panzer~phalanx~piro~python~rocm~rocm_rdc~rol~rythmos~sacado~scorec+shards+shared~shylu+stk~stokhos~stratimikos~strumpack~suite-sparse~superlu~superlu-dist~teko~tempus~test~thyra+tpetra~trilinoscouplings~wrapper~x11+zoltan~zoltan2 build_system=cmake build_type=Release cxxstd=17 generator=ninja gotype=long patches=99c3bba arch=darwin-ventura-m1 %apple-clang@15.0.0
    -   yd6qek7          ^cgns@4.5.0~base_scope~fortran+hdf5~int64~ipo~legacy~mem_debug+mpi~pic+scoping+shared~static~testing~tools build_system=cmake build_type=Release generator=make patches=0ecd9e4 arch=darwin-ventura-m1 %apple-clang@15.0.0
    -   slxmf5f          ^kokkos@4.5.01~aggressive_vectorization~cmake_lang~compiler_warnings~complex_align~cuda~debug~debug_bounds_check~debug_dualview_modify_check~deprecated_code~examples~hip_relocatable_device_code~hpx~hpx_async_dispatch~hwloc~ipo~memkind~numactl~openmp~openmptarget~pic~rocm+serial+shared~sycl~tests~threads~tuning~wrapper build_system=cmake build_type=Release cxxstd=17 generator=make intel_gpu_arch=none arch=darwin-ventura-m1 %apple-clang@15.0.0
    -   65fkmqo          ^kokkos-kernels@4.5.01~blas~cblas~cublas~cuda~cusolver~cusparse~execspace_cuda~execspace_openmp~execspace_serial~execspace_threads~ipo~lapack~lapacke~memspace_cudaspace~memspace_cudauvmspace~mkl~openmp~rocblas~rocsolver~rocsparse~serial+shared~superlu~threads build_system=cmake build_type=Release generator=make layouts=left offsets=int,size_t ordinals=int scalars=double arch=darwin-ventura-m1 %apple-clang@15.0.0
    -   jdd4vep          ^matio@1.5.26+hdf5+shared+zlib build_system=autotools arch=darwin-ventura-m1 %apple-clang@15.0.0
    -   umlhq5t          ^metis@5.1.0~gdb~int64~ipo~no_warning~real64+shared build_system=cmake build_type=Release generator=make patches=4991da9,93a7903 arch=darwin-ventura-m1 %apple-clang@15.0.0
    -   jdqogi7          ^ninja@1.12.1~re2c build_system=generic patches=93f4bb3 arch=darwin-ventura-m1 %apple-clang@15.0.0
    -   goytec6          ^parallel-netcdf@1.14.0~burstbuffer+cxx~examples+fortran+pic+shared build_system=autotools arch=darwin-ventura-m1 %apple-clang@15.0.0
    -   yptps6s              ^perl@5.40.0+cpanm+opcode+open+shared+threads build_system=generic arch=darwin-ventura-m1 %apple-clang@15.0.0
    -   z4kj4bw                  ^berkeley-db@18.1.40+cxx~docs+stl build_system=autotools patches=26090f4,b231fcc arch=darwin-ventura-m1 %apple-clang@15.0.0
    -   jdxgzi3          ^parmetis@4.0.3~gdb~int64~ipo+shared build_system=cmake build_type=Release generator=make patches=4f89253,50ed208,704b84f arch=darwin-ventura-m1 %apple-clang@15.0.0
    -   mnnwkyp      ^yaml-cpp@0.6.3~ipo+pic+shared~tests build_system=cmake build_type=Release generator=make arch=darwin-ventura-m1 %apple-clang@15.0.0
   
   install
   make -j32 SPACK_INSTALL_FLAGS='--show-log-on-error'
   /Users/jrood/exawind-manager/spack/bin/spack -c config:install_status:false -e '/Users/jrood/exawind-manager/environments/exawind-env' install  '--show-log-on-error' --only-concrete --only=package /uf5swtz56kty36hs6uhs3w26x7ho2myn # gmake@4.4.1~guile build_system=generic arch=darwin-ventura-m1 %apple-clang@=15.0.0
   /Users/jrood/exawind-manager/spack/bin/spack -c config:install_status:false -e '/Users/jrood/exawind-manager/environments/exawind-env' install  '--show-log-on-error' --only-concrete --only=package /eabkdvhseshxsuukgi4pznupmuwhrtmh # gnuconfig@2024-07-27 build_system=generic arch=darwin-ventura-m1 %apple-clang@=15.0.0
   /Users/jrood/exawind-manager/spack/bin/spack -c config:install_status:false -e '/Users/jrood/exawind-manager/environments/exawind-env' install  '--show-log-on-error' --only-concrete --only=package /4aj5ju7jryr7qtawfjfruuw5yngib3gq # apple-libuuid@1353.100.2 build_system=bundle arch=darwin-ventura-m1 %apple-clang@=15.0.0
   /Users/jrood/exawind-manager/spack/bin/spack -c config:install_status:false -e '/Users/jrood/exawind-manager/environments/exawind-env' install  '--show-log-on-error' --only-concrete --only=package /qrsyolzjhfza5njdvr6l66y3kcc332ag # ca-certificates-mozilla@2025-02-25 build_system=generic arch=darwin-ventura-m1 %apple-clang@=15.0.0
   [+] /Library/Developer/CommandLineTools/SDKs/MacOSX.sdk (external apple-libuuid-1353.100.2-4aj5ju7jryr7qtawfjfruuw5yngib3gq)
   ==> Installing gnuconfig-2024-07-27-eabkdvhseshxsuukgi4pznupmuwhrtmh
   ==> No binary for gnuconfig-2024-07-27-eabkdvhseshxsuukgi4pznupmuwhrtmh found: installing from source
   ==> Updating view at /Users/jrood/exawind-manager/environments/exawind-env/.spack-env/view
   ==> Installing ca-certificates-mozilla-2025-02-25-qrsyolzjhfza5njdvr6l66y3kcc332ag
   ==> No binary for ca-certificates-mozilla-2025-02-25-qrsyolzjhfza5njdvr6l66y3kcc332ag found: installing from source
   ==> Installing gmake-4.4.1-uf5swtz56kty36hs6uhs3w26x7ho2myn
   ==> No binary for gmake-4.4.1-uf5swtz56kty36hs6uhs3w26x7ho2myn found: installing from source
   ==> Using cached archive: /Users/jrood/.spack_downloads/_source-cache/archive/11/1135044961853c7f116145cee9bb15c3d29b1b081cf8293954efd0f05d801a7c.tar.gz
   ==> Using cached archive: /Users/jrood/.spack_downloads/_source-cache/archive/50/50a6277ec69113f00c5fd45f09e8b97a4b3e32daa35d3a95ab30137a55386cef
   ==> No patches needed for ca-certificates-mozilla
   ==> Using cached archive: /Users/jrood/.spack_downloads/_source-cache/archive/dd/dd16fb1d67bfab79a72f5e8390735c49e3e8e70b4945a15ab1f81ddb78658fb3.tar.gz
   ==> ca-certificates-mozilla: Executing phase: 'install'
   ==> ca-certificates-mozilla: Successfully installed ca-certificates-mozilla-2025-02-25-qrsyolzjhfza5njdvr6l66y3kcc332ag
     Stage: 0.00s.  Install: 0.00s.  Post-install: 0.01s.  Total: 0.07s
   [+] /Users/jrood/exawind-manager/opt/exawind-env/darwin-ventura-m1/apple-clang-15.0.0/ca-certificates-mozilla-2025-02-25-qrsyolzjhfza5njdvr6l66y3kcc332ag

   ... lots more building

   ==> Installing exawind-1.2.0-mz2hzbnhcqnrrqnxqch2guw53ep3fi4a
   ==> No binary for exawind-1.2.0-mz2hzbnhcqnrrqnxqch2guw53ep3fi4a found: installing from source
   ==> Using cached archive: /Users/jrood/.spack_downloads/_source-cache/git//Exawind/exawind-driver.git/4c49c7775c580b6bd2556e6c00fd13c08737d5eb.tar.gz
   ==> No patches needed for exawind
   ==> exawind: Executing phase: 'cmake'
   ==> exawind: Executing phase: 'build'
   ==> exawind: Executing phase: 'install'
   ==> exawind: Executing phase: 'analysis'
   ==> exawind: Successfully installed exawind-1.2.0-mz2hzbnhcqnrrqnxqch2guw53ep3fi4a
     Stage: 1.38s.  Cmake: 9.12s.  Build: 6.24s.  Install: 0.33s.  Analysis: 0.05s.  Post-install: 0.07s.  Total: 17.47s
   [+] /Users/jrood/exawind-manager/opt/exawind-env/darwin-ventura-m1/apple-clang-15.0.0/exawind-1.2.0-mz2hzbnhcqnrrqnxqch2guw53ep3fi4a
