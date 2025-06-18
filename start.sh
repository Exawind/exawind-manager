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
  
  # https://stackoverflow.com/questions/4774054/reliable-way-for-a-bash-script-to-get-the-full-path-to-itself
  # for zsh we follow: https://stackoverflow.com/questions/9901210/bash-source0-equivalent-in-zsh
  export EXAWIND_MANAGER="$( cd -- "$(dirname "${BASH_SOURCE[0]:-${(%):-%x}}")" >/dev/null 2>&1 ; pwd -P )"

  function install_spack_manager(){
    export SPACK_ROOT=${EXAWIND_MANAGER}/spack
    ORIGINAL_DIR=$(pwd)
    cd "$EXAWIND_MANAGER"
    git submodule update ${SPACK_ROOT}/../spack-manager
    cd "$ORIGINAL_DIR"
    unset ORIGINAL_DIR
    spack -E config --scope site add "config:extensions:[${EXAWIND_MANAGER}/spack-manager]"
    spack -E manager add ${EXAWIND_MANAGER}
  }

  if ! $(type '_spack_start_called' 2>/dev/null | grep -q 'function'); then
    # The default python version on Kestrel does not work correctly
    if [[ "${NREL_CLUSTER}" == 'kestrel' ]]; then
      module load cray-python
    fi

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

    export PATH=${PATH}:${EXAWIND_MANAGER}/scripts
    export PYTHONPATH=${PYTHONPATH}:${EXAWIND_MANAGER}:${EXAWIND_MANAGER}/repos:${EXAWIND_MANAGER}/spack/var/spack/repos:${EXAWIND_MANAGER}/spack/lib/spack

    if [[ -z $(spack repo list | awk '{print $2" "$4}' | grep "exawind $EXAWIND_MANAGER") ]]; then
      spack -E repo add ${EXAWIND_MANAGER}/repos/spack_repo/exawind
    fi

    if [[ -z $(spack config --scope site blame bootstrap | grep spack-bootstrap-store) ]]; then
      if [[ "$(spack manager find-machine | awk '{print $2}')" == "cee" ]]; then
        spack -E bootstrap add --scope site --trust wind-binaries /projects/wind/spack-bootstrap-store/metadata/binaries
      fi
    fi

    if [[ "$(spack manager find-machine | awk '{print $2}')" == "darwin" && ! -f ${SPACK_USER_CONFIG_PATH}/darwin/compilers.yaml ]]; then
      spack -E compiler find
    fi

    source ${EXAWIND_MANAGER}/spack-manager/scripts/quick_commands.sh
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
