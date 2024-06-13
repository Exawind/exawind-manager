#!/bin/bash

cmd() {
  echo "+ $@"
  eval "$@"
}

source ../start.sh
cmd "spack-start"

date_spack_envs() {
  # determine date spack env's from running deploy
  env_output=$(spack env ls)
  env_list=$(echo "$env_output" | awk '{print $1}' | grep -E '^[0-9]{4}-[0-9]{2}-[0-9]{2}$')
  echo "$env_list"
}

prune_envs() {
  # check for old  date spack env's and remove them
  today=$(date -I)

  for env in $(date_spack_envs); do
    date_diff=$(( ($(date -d "$today" +%s) - $(date -d "$env" +%s)) / 86400 ))
    if [ "$date_diff" -gt 30 ]; then
     echo "Spack env ${env} is older than 30 days"
     spack -e "${env}" uninstall --all
     spack env remove "${env}"
    fi
  done
}

cmd "prune_envs"

# build the test environment and run the tests
cmd "deploy.py --daily --depfile --cdash exawind amr-wind nalu-wind --ranks $(NRANKS:-8) --overwrite --regression_tests"
