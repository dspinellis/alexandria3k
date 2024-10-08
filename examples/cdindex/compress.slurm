#!/bin/bash

#SBATCH --job-name=cdindex-compress
#SBATCH --output=cdindex-compress.out
#SBATCH --error=cdindex-compress.err
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=16G
#SBATCH --time=40:00:00
#SBATCH --partition=compute
#SBATCH --account=pa240702

# Compress the reports

set -eu

cd reports
xz --threads=8 --keep --verbose cd5index-all.txt
