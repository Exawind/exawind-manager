#!/bin/bash

cmd() {
  echo "+ $@"
  eval "$@"
}

cmd "source ${EXAWIND_MANAGER}/start.sh"
cmd "spack-start"

days_to_keep=${DAYS_TO_KEEP:-30}
nranks=${NRANKS:-8}

date_spack_envs() {
  # determine date spack env's from running deploy
  env_output=$(spack env ls)
  env_list=$(echo "${env_output}" | awk '{print $1}' | grep -E '^[0-9]{4}-[0-9]{2}-[0-9]{2}$')
  echo "${env_list}"
}

prune_envs() {
  # check for old  date spack env's and remove them
  today=$(date -I)

  for env in $(date_spack_envs); do

    date_diff=$(( ($(date -f "%Y-%m-%d" "$today" +%s) - $(date -f "%Y-%m-%d" "$env" +%s)) / 86400 ))

    if [ "${date_diff}" -gt "${days_to_keep}" ]; then
     echo "Spack env ${env} is older than ${days_to_keep} days"
     cmd "spack -e ${env} uninstall --all --dependents --force -y"
     cmd "spack env remove ${env} -y"
    fi
  done
}

cmd "prune_envs"

packages_to_test="exawind amr-wind nalu-wind"
# build the test environment and run the tests
cmd "${EXAWIND_MANAGER}/scripts/deploy.py --daily --cdash ${packages_to_test} --ranks ${nranks} --overwrite --regression_tests ${packages_to_test}"
