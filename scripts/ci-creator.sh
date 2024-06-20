#!/bin/bash

. ../shortcut.sh
deploy.py --name e4s-container --ranks=${NRANKS:-4} --depfile
spack clean -a
