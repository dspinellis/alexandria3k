#!/bin/sh
#
# Run all available SQL unit tests
#

set -e

# Obtain directories where tests reside
ls */*.rdbu |
  awk -F / '{print $1}' |
  sort -u |
  while read dir ; do
    cd $dir
    make test
    cd ..
  done
