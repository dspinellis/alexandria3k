#!/bin/sh

set -eu

cat <<EOF
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
    <div style="text-align:center">
      <h1>Analysis of Greek-titled publications in Crossref</h1>
      <p>
        Diomidis Spinellis<br/>
        Department of Management Science and Technology<br/>
        Athens University of Economics and Business<br/>
        $(date +"%d %B %Y")
      </p>
    </div>
      <p>
        This is a short report regarding Greek-titled publications
        included in <a href="https://www.nature.com/articles/d41586-022-02926-y">Crossref</a>
        ($(basename "$CROSSREF_DIR") edition).
        It provides a quantitative publication metadata analysis
        of all publications with at least
        three lowercase modern Greek letters in their title.
        The selection method is a rough-and-ready approximation
        of all Crossref-indexed scientific publications written in Greek.
        However, it is not perfect, as it includes some papers from
        disciplines that use terms written in Greek,
        such as <a href="https://doi.org/10.1016/s0370-1573(02)00274-0">this one</a>,
        papers with titles written with non-latin characters incorrectly
        transcribed into Greek characters,
        such as <a href="https://doi.org/10.1524/slaw.1975.20.1.788">this one written in Cyrillic</a>,
        and it may also exclude titles consisting mostly of Greek capital
        or Ancient Greek polytonic letters.
      </p><p>
        The report has been created with
        <a href="https://dspinellis.github.io/alexandria3k/">Alexandria3k</a>.
        Its methods and means of reproduction are documented through
        the queries and scripts found in the
        corresponding <a href="https://github.com/dspinellis/alexandria3k/tree/main/examples/greek-pubs">examples directory</a>.
      </p>
EOF

for sql in \
  metrics.sql \
  types.sql \
  issn-use.sql \
  top-publishers.sql \
  top-venues.sql \
  top-affiliations.sql \
  top-rors.sql \
  top-orcid-authors.sql \
  top-named-authors.sql \
  top-cited.sql \
  top-funders.sql \
  represented-periodicals.sql \
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
$(sed -E '/^--/d
  s,^,<tr><td>,
  s,\|,</td><td>,g
  s,$,</td></tr>,
  s,<td>([0-9]+)</td>,<td class="num">\1</td>,g
  s,>(10\.[^<]*/[^<]*),><a href="https://doi.org/\1">\1</a>,g
  s,(([0-9]{4}-){3}[0-9X]{4}),<a href="https://orcid.org/\1">\1</a>,g
  ' $report)
</table>
EOF
done

cat <<\EOF
  <p>
    <a href="https://www.spinellis.gr/pubs/tr/2025-Greek-titled-pubs/html/">Analysis of Greek-titled publications in Crossref</a> © 2025 by <a href="https://www.spinellis.gr/">Diomidis Spinellis</a> is licensed under <a href="https://creativecommons.org/licenses/by/4.0/">Creative Commons Attribution 4.0 International</a><img src="https://mirrors.creativecommons.org/presskit/icons/cc.svg" alt="" style="max-width: 1em;max-height:1em;margin-left: .2em;"><img src="https://mirrors.creativecommons.org/presskit/icons/by.svg" alt="" style="max-width: 1em;max-height:1em;margin-left: .2em;">
  </p>
  </body>
</html>
EOF
