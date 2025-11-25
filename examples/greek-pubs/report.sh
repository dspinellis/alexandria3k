#!/bin/sh

set -eu

cat <<\EOF
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>Analysis of Greek-titled publications in Crossref</title>

    <style>
      body { font-family: sans-serif; line-height: 1.4; margin: 2rem; }
      table { border-collapse: collapse; margin-top: 1rem; }
      th, td { padding: 0.35rem 0.6rem; border-bottom: 1px solid #ccc; }
      th { text-align: left; font-weight: 600; }
      td.num, th.num { text-align: right; }
    </style>

  </head>
  <body>
    <h1>Analysis of Greek-titled publications in Crossref</h1>
      <p>
        This is a report of Greek-titled publications
        included in <a href="https://www.nature.com/articles/d41586-022-02926-y">Crossref</a>.
        It provides an analysis all publications with at least
        three lowercase modern Greek letters in their title.
        The selection method is a rough-and-ready approximation
        of all Crossref-indexed scientific publications written in Greek.
        However, it is not perfect, as it includes some papers from
        disciplines that use Greek terms,
        such as <a href="https://doi.org/10.1016/s0370-1573(02)00274-0">this one</a>,
        and it may also exclude titles consisting mostly of Ancient Greek
        polytonic letters.
      </p><p>
        The report has been created with
        <a href="https://dspinellis.github.io/alexandria3k/">Alexandria3k</a>.
        It can be reproduced with the queries and scripts found in the
        corresponding <a href="https://github.com/dspinellis/alexandria3k/tree/main/examples/greek-pubs">examples directory</a>.
      </p>
EOF

for sql in \
  metrics.sql \
  types.sql \
  top-publishers.sql \
  top-venues.sql \
  top-affiliations.sql \
  top-rors.sql \
  top-orcid-authors.sql \
  top-named-authors.sql \
  top-cited.sql \
  top-funders.sql \
  decades.sql \
  stratified-by-publisher.sql \
  ; do
    report=reports/$(basename $sql .sql).txt
cat <<EOF
$(sed -n '1s,-- \(.*\),<h2>\1</h2>,p' $sql)
<table>
<tr>
    $(sed -n '2{s,^-- ,<th>,;s,|,</th><th>,g;s,$,</th>,;p;}' $sql)
</tr>
$(sed '/^--/d;s,^,<tr><td>,;s,|,</td><td>,g;s,$,</td></tr>,;s,<td>\([0-9]*\)</td>,<td class="num">\1</td>,g;s,>\(10\.[^<]*/[^<]*\),><a href="https://doi.org/\1">\1</a>,g' $report)
</table>
EOF
done

cat <<\EOF
  </body>
</html>
EOF
