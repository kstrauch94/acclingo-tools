#!/bin/bash

cd "$(dirname $0)"

sbatch acc.pbs {instance_file} {seed}
