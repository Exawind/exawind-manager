#!/bin/bash
#
# Copyright (c) 2022, National Technology & Engineering Solutions of Sandia,
# LLC (NTESS). Under the terms of Contract DE-NA0003525 with NTESS, the U.S.
# Government retains certain rights in this software.
#
# This software is released under the BSD 3-clause license. See LICENSE file
# for more details.
#

cmd() {
  echo "+ $@"
  eval "$@"
}

########################################################
# Tests
########################################################
if [[ -z ${EXAWIND_MANAGER} ]]; then
  echo "Env variable EXAWIND_MANAGER not set. You must set this variable."
  return 125
fi

if [[ ! -x $(which python3) ]]; then
  echo "Warning: spack-manager is only designed to work with python 3."
  echo "You may use spack, but spack-manager specific commands will fail."
fi

# convenience function for getting to the spack-manager directory
function cd-sm(){
  if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    echo "Convenience function for navigating to the spack-manager directory"
    return
  fi
  cd ${EXAWIND_MANAGER}
}

# function to initialize spack-manager's spack instance
function spack-start() {
  if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    echo "This function loads spack into your active shell"
    return
  fi
  function install_spack_manager(){
    git clone --branch develop https://github.com/sandialabs/spack-manager $SPACK_ROOT/../spack-manager
    spack -E config --scope site add "config:extensions:[${EXAWIND_MANAGER}/spack-manager]"
    spack -E manager add ${EXAWIND_MANAGER}
  }

  if ! $(type '_spack_start_called' 2>/dev/null | grep -q 'function'); then
    export SPACK_ROOT=${EXAWIND_MANAGER}/spack
    export SPACK_USER_CACHE_PATH=${EXAWIND_MANAGER}/.cache
    export SPACK_USER_CONFIG_PATH=${EXAWIND_MANAGER}/.spack

    if [ -n "$SPACK_ENV" ]; then 
      OLD_SPACK_ENV=${SPACK_ENV}
      unset SPACK_ENV
    fi

    source ${SPACK_ROOT}/share/spack/setup-env.sh

    # Clean Spack misc caches
    # Put this back in if outdated caches directory still causes problems when updating Spack submodule
    #spack clean -m
    
    # move the bootstrap store outside the user config path
    if [[ -z $(spack config blame bootstrap | grep "root: ${EXAWIND_MANAGER}/.bootstrap") ]]; then
      spack -E bootstrap root ${EXAWIND_MANAGER}/.bootstrap
    fi

    if [[ -z $(spack config --scope site blame config | grep "environments_root: ${EXAWIND_MANAGER}/environments") ]]; then
      spack -E config --scope site add config:environments_root:${EXAWIND_MANAGER}/environments
    fi

    if [[ -z $(spack config --scope site blame config | grep spack-manager) ]]; then
      install_spack_manager
    fi

    if [[ -z $(spack config --scope site blame concretizer | grep 'unify:false') ]]; then
      spack -E config --scope site add "concretizer:unify:false"
    fi

    if [[ -z $(spack repo list | awk '{print $1" "$2}' | grep "exawind $EXAWIND_MANAGER") ]]; then
      spack -E repo add ${EXAWIND_MANAGER}/repos/exawind
    fi
    
    if [[ -z $(spack config --scope site blame bootstrap | grep spack-bootstrap-store) ]]; then
      if [[ "${EXAWIND_MANAGER_MACHINE}" == "cee" ]]; then
        spack -E bootstrap add --scope site --trust wind-binaries /projects/wind/spack-bootstrap-store/metadata/binaries
      fi
    fi

    if [[ "${EXAWIND_MANAGER_MACHINE}" == "darwin" && ! -f ${SPACK_CONFIG_USER_PATH}/darwin/compilers.yaml ]]; then
      spack -E compiler find --mixed-toolchain
    fi

    source ${EXAWIND_MANAGER}/spack-manager/scripts/quick_commands.sh
    export PATH=${PATH}:${EXAWIND_MANAGER}/scripts
    # needed for package imports
    export PYTHONPATH=${PYTHONPATH}:${EXAWIND_MANAGER}
    # define a function since environment variables are sometimes preserved in a subshell but functions aren't
    # see https://github.com/psakievich/spack-manager/issues/210
    function _spack_start_called(){
      echo "TRUE"
    }
    if [ -n "${OLD_SPACK_ENV}" ]; then
      export SPACK_ENV=${OLD_SPACK_ENV}
    fi
  fi
}
