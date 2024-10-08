#!/bin/bash

#SBATCH --job-name=cdindex-multi
#SBATCH --output=cdindex-multi.out
#SBATCH --error=cdindex-multi.err
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=40
#SBATCH --mem=256G
#SBATCH --time=40:00:00
#SBATCH --partition=fat
#SBATCH --account=pa240702

# Calculate the CD index up to 2023

set -eu

# On ARIS cdindex-db can be compiled as follows:
# module load intel/18
# module load gnu/13
# SQLITE_DIR=$HOME/src/sqlite-amalgamation-3460000/ make cdindex-db

# /tmp is 2GB; redirect it here for 64GB
export TMP=$(mktemp -d /dev/shm/csmake.XXXXXX)
export TMPDIR="$TMP"

time ./cdindex-db cdindex.db rolap.db

rm -rf "$TMP"
