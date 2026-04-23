#!/bin/bash

module load aue/python
export KYNEMA_MANAGER=/projects/wind/kynema-manager
if hostname | grep -q "ecw"; then
  export NPROCS=60
else
  echo "Running on unsupported machine $(hostname)"
  exit 1
fi

${KYNEMA_MANAGER}/scripts/run-nightly-tests.sh | tee /projects/wind/testing-logs/cee/$(date -I)-tests.log
