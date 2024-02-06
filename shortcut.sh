#
# Copyright (c) 2022, National Technology & Engineering Solutions of Sandia,
# LLC (NTESS). Under the terms of Contract DE-NA0003525 with NTESS, the U.S.
# Government retains certain rights in this software.
#
# This software is released under the BSD 3-clause license. See LICENSE file
# for more details.
#
#---------------------------------------------------
# This script is an easy entry point for using 
# the exawind manager in the current directory
# and makes it easier to manager multiple instances
# of exawind-manager
#---------------------------------------------------
export EXAWIND_MANAGER=`pwd`
source ${EXAWIND_MANAGER}/start.sh
spack-start
