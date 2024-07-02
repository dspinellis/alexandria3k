#!/bin/sh
#
# Tabulate the scheme results in Markdown
#

# Fail on command errors and unset variables
set -eu


SCHEMES=reports/schemes.txt

for scheme in $(awk -F\| '{print $1}' $SCHEMES | sort -u) ; do
  cat <<EOF

## $scheme

| Value | Count |
|:------|------:|
EOF
  grep $scheme\| $SCHEMES |
    sort -t\| -k3rn |
    head -10 |
    awk -F\| '$2 == "" {$2 = "(none)"} {print "|" $2 "|" $3 "|"}' |
    sed 's/_/\\_/g' |
    ../../bin/decimal.sed
done

