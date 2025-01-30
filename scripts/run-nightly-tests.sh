#!/bin/bash -l

#Example crontab:
#1 0 * * * /bin/bash -l -c "export EXAWIND_MANAGER=/data/ssd1/home/jrood/exawind/exawind-manager && mkdir -p \${EXAWIND_MANAGER}/logs && cd \${EXAWIND_MANAGER} && (cd \${EXAWIND_MANAGER}/spack && git checkout lib && cd - && git fetch --all && git reset --hard origin/main && git submodule update && git clean -df && git status -uno) &> \${EXAWIND_MANAGER}/logs/exawind-manager-repo-update-$(date -I).txt && sed -i 's/timeout=60/timeout=7200/' \${EXAWIND_MANAGER}/spack/lib/spack/spack/stage.py && NRANKS=36 nice -n19 ionice -c3 \${EXAWIND_MANAGER}/scripts/run-nightly-tests.sh &> \${EXAWIND_MANAGER}/logs/exawind-tests-log-$(date -I).txt"

cmd() {
  echo "+ $@"
  eval "$@"
}

cmd "source ${EXAWIND_MANAGER}/start.sh"
cmd "spack-start"

days_to_keep=${DAYS_TO_KEEP:-30}
nranks=${NRANKS:-8}

date_spack_envs() {
  env_output=$(spack env ls)
  env_list=$(echo "${env_output}" | awk '{print $1}' | grep -E '^[0-9]{4}-[0-9]{2}-[0-9]{2}$')
  echo "${env_list}"
}

prune_envs() {
  for env in $(date_spack_envs); do
    date_diff=$(( ($(date +%s) - $(date --date="$env" +%s)) / 86400 ))
    if [ "${date_diff}" -gt "${days_to_keep}" ]; then
     echo "Spack env ${env} is older than ${days_to_keep} days"
     cmd "spack -e ${env} uninstall --all --dependents --force -y"
     cmd "spack env remove ${env} -y"
    fi
  done
}

cmd "prune_envs"

packages_to_test="exawind amr-wind nalu-wind"
cmd "time ${EXAWIND_MANAGER}/scripts/deploy.py --depfile --daily --cdash ${packages_to_test} --ranks ${nranks} --overwrite --regression_tests ${packages_to_test}"
