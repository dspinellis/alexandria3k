#!/bin/bash

#SBATCH --job-name=cdindex-make
#SBATCH --output=cdindex-make.out
#SBATCH --error=cdindex-make.err
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=16G
#SBATCH --time=40:00:00
#SBATCH --partition=compute
#SBATCH --account=pa240702

# Run make to compute the yearly cdindex

set -eu

# On ARIS cdindex-db can be compiled as follows:
# module load intel/18
# module load gnu/13
# SQLITE_DIR=$HOME/src/sqlite-amalgamation-3460000/ make cdindex-db

# /tmp is 2GB; redirect it here for 64GB
export TMP=$(mktemp -d /dev/shm/csmake.XXXXXX)
export TMPDIR="$TMP"

time make

rm -rf "$TMP"
