#!/bin/bash

cd "$(dirname $0)"

sbatch acc.pbs train/instances.txt {seed}
