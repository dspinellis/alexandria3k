#!/bin/sh
#
# Fetch all USPTO bibliographic data for XML Version >= 4.0
#

# Fail on command errors and unset variables
set -eu

BASE=https://bulkdata.uspto.gov/data/patent/grant/redbook/bibliographic

mkdir uspto-data
cd uspto-data

for year in $(seq 2005 $(date +%Y)) ; do
  mkdir -p $year

  # Obtain list of weekly files
  curl --silent $BASE/$year/ |

  # Extract file names
  sed -n 's/.*href="\(ipgb[^"]*\)".*/\1/p' |

  # A date's revision appears after the original file, so overwrite it
  awk -F_ '{name[$1] = $0} END {for (date in name) print name[date]}' |

  sort |

  # Fetch each weekly zip file
  while read zip ; do
    if [ -r $year/$zip ] ; then
      echo "Skip existing file $year/$zip" 1>&2
      continue
    fi
    echo "Download file $year/$zip" 1>&2
    curl --silent $BASE/$year/$zip >$year/$zip
  done

done
