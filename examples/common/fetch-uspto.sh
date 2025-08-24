#!/bin/sh
#
# Fetch all USPTO bibliographic data for XML Version >= 4.0
#

# Fail on command errors and unset variables
set -eu

DEST_DIR=uspto-data

if [ -z "${MYODP_KEY-}" ] ; then
  echo "$0: The MYODP_KEY environment variable is not set." 1>&2
  exit 1
fi

# Obtain list of available files in JSON format.
curl --silent -X GET \
  'https://api.uspto.gov/api/v1/datasets/products/ptblxml?fileDataFromDate=2001-12-31&includeFiles=true' \
  -H 'Accept: application/json' \
  -H 'Content-Type: application/json' \
  -H "x-api-key: $MYODP_KEY" |

# Obtain list of URLs.
jq -r '.bulkDataProductBag[0].productFileBag.fileDataBag[] | .fileDownloadURI' |

# Handle revisions.
# A date's revision appears after the original file, so overwrite it.
awk -F_ '/\/ipgb/ {url[$1] = $0} END {for (main in url) print url[main]}' |

sort |

# Input:
# https://api.uspto.gov/api/v1/datasets/products/files/PTBLXML/2005/ipgb20050118_wk03.zip
# Output a list of: URL year file.
awk -F/ '{print $0, $10, $11}' |

# Fetch each weekly zip file
while read url year file ; do
  if [ -r $DEST_DIR/$year/$file ] ; then
    echo "Skip existing file $year/$file" 1>&2
    continue
  fi
  mkdir -p $DEST_DIR/$year
  echo "Download file $year/$file" 1>&2
  curl --silent "$url" -H "x-api-key: $MYODP_KEY" >$DEST_DIR/$year/$file
done
