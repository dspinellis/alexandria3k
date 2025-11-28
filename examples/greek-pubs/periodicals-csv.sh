#!/bin/sh
#
# Create a CSV file from the specified URL.
# The URL must be a GET query to the Greek periodical database.
#

set -eu

curl "$1" |
  # Clean up raw file
  jq '.aaData | map({ id: (.DT_RowId | tonumber), title: .["0"], issn: .["1"] })' |

  # Remove embedded CR LFs, e.g. "issn": "1010-4577\r\n"
  sed 's/\\[rn]//g' |

  # Convert raw file into CSV format
  jq -r '.  | map(select(.issn != null)) | (.[] | [.id, .issn, .title]) | @csv'
