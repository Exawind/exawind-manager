#!/bin/bash -e

if [[ $# -ne 1 ]] ; then
  echo error: please specify the commit to use
  echo "usage: $0 <commit>"
  exit 1
fi

COMMIT=$1

cmd() {
  echo "+ $@"
  eval "$@"
}

BUILD_DATE=$(printf '%(%Y-%m-%d)T' -1)
REGISTRY=${REGISTRY:-ecpe4s}
OUTPUT_IMAGE_REPO="${REGISTRY}/exawind-snapshot"
DATED_IMAGE="${OUTPUT_IMAGE_REPO}:${BUILD_DATE}"
LATEST_IMAGE="${OUTPUT_IMAGE_REPO}:latest"

cmd time docker build --no-cache --build-arg COMMIT=$COMMIT --build-arg BUILD_DATE="${BUILD_DATE}" -t ${DATED_IMAGE} .
cmd docker tag ${DATED_IMAGE} ${LATEST_IMAGE}

echo $DOCKER_PASSWORD | docker login --username esw123 --password-stdin
cmd docker push ${DATED_IMAGE}
cmd docker push ${LATEST_IMAGE}
cmd docker logout

