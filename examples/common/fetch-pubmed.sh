#!/bin/sh
#
# Fetch baseline PubMed bibliographic data
#

# Fail on command errors and unset variables
set -eu

BASE=https://ftp.ncbi.nlm.nih.gov/pubmed/baseline/

mkdir -p pubmed
cd pubmed

# Obtain last baseline file from README.txt
last=$(curl --silent https://ftp.ncbi.nlm.nih.gov/pubmed/baseline/README.txt |
  sed -n '/pubmed24n0001/s/.*pubmed24n\([^.]*\)\.xml.*/\1/p')

for n in $(seq 1 $last) ; do
  file_name=$(printf 'pubmed24n%04d.xml.gz' $n)

  test -r $file_name && continue

  curl --silent $BASE/$file_name >$file_name
done
