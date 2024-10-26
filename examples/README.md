This directory contains proof-of-concept studies
that were conducted with _alexandria3k_ as examples of its use.

They are structured to use Makefiles based on
[simple-rolap](https://github.com/dspinellis/simple-rolap)
for orchestrating the queries (it is installed automatically) and
[rdbunit](https://github.com/dspinellis/rdbunit) for unit testing them
(it needs to be manually installed for running the tests).
Running (GNU) `make` in a directory will produce the expected results in a
`reports` sub-directory.
Many of the studies can take hours or days to run.
When running the scripts on a shared Unix/Linux computer,
running _make_ as `nohup nice make` will
log the operation in the file `nohup.out` (use `tail -f nohup.out` to view it),
prevent the command from terminating when a session is disconnected, and
decrease the priority of the tasks to minimize their burden on
interactive users.
When modifying existing studies or creating one ones,
run `make help` in a study directory
to see some potentially useful _make_ targets.

The [common](common) directory contains Makefile rules for satisfying
data dependencies common to more than one study.
It also hosts downloaded data sets to minimize useless replication.
The `Makefile` residing in it can be used to tailor the running
of all other studies.

## Examples by directory
The following examples are available.

### Templates
* ["Hello world" example: number of authors by decade](authors-by-decade)
* [Fully-indexed Crossref database sample](sample)

### Studies
* [Tally number of research synthesis studies](research-synthesis)
* [Generate and study the entities' graph structure](graph)
* [Obtain data associated with COVID-19 research](covid)
* [Calculate the average size of an article's pages each year](yearly-numpages)
* [Calculate the works' CD-5 index using the Python API or a pre-populated database](cdindex)
* [Investigate the CD-5 index of Dan Tawfik's works](tawfik)
* [Top five US Patent Office applications by country and year](uspto)
* [Replication study on software used in PubMed articles](pubmed-software)

### Data source examples and metric measurements
* [Report metrics associated with the Crossref data set](crossref-standalone)
* [Report metrics associated with ORCID data](orcid)
* [Report metrics associated with DataCite data](datacite)
* [Report research organization registry metrics](ror-metrics)

### Impact and productivity calculations
* [Calculate the 2021 journal impact factor](impact-factor-2021)
* [Calculate the h5-index of journals](journal-h5)
* [Calculate the h5-index of software engineering research venues](soft-eng-h5)
* [Calculate h5-index of persons and study their citation graph](person-h5)
* [Examine the evolution and impact of open access journal papers](open-access)
* [Calculate relative yearly author productivity](author-productivity)


## Published results
The following queries have been used to publish derived figures and tables.

* [Yearly availability of Crossref elements](https://doi.org/10.1371/journal.pone.0294946.g001) derived from
  * [crossref-standalone/yearly-abstracts.sql](./crossref-standalone/yearly-abstracts.sql)
  * [graph/yearly-work-subjects.sql](./graph/yearly-work-subjects.sql)
  * [graph/yearly-work-funders.sql](./graph/yearly-work-funders.sql)
  * [graph/yearly-work-links.sql](./graph/yearly-work-links.sql)
  * [graph/yearly-work-references.sql](./graph/yearly-work-references.sql)
  * [graph/yearly-work-authors.sql](./graph/yearly-work-authors.sql)
  * [graph/yearly-authors-orcid.sql](./graph/yearly-authors-orcid.sql)
  * [graph/yearly-author-affiliations.sql](./graph/yearly-author-affiliations.sql)
  * [graph/yearly-references-doi.sql](./graph/yearly-references-doi.sql)
  * [graph/yearly-funders-doi.sql](./graph/yearly-funders-doi.sql)
  * [graph/yearly-funder-awards.sql](./graph/yearly-funder-awards.sql)
* [Number and properties of Crossref records](https://doi.org/10.1371/journal.pone.0294946.t001) derived from [graph/metrics.sql](./graph/metrics.sql)
* [Number of ORCID records](https://doi.org/10.1371/journal.pone.0294946.t002) derived from [graph/metrics.sql](./graph/metrics.sql)
* [ Evolution of scientific publishing metrics in the post-WW2 period](https://doi.org/10.1371/journal.pone.0294946.g002) derived from
  * [graph/yearly-authors-per-work.sql](./graph/yearly-authors-per-work.sql)
  * [author-productivity/author-productivity.sql](./author-productivity/author-productivity.sql)
  * [graph/yearly-works.sql](./graph/yearly-works.sql)
  * [open-access/yearly-oa-journal-works.sql](./open-access/yearly-oa-journal-works.sql)
  * [graph/yearly-citations-per-paper.sql](./graph/yearly-citations-per-paper.sql)
  * [graph/yearly-references-per-paper.sql](./graph/yearly-references-per-paper.sql)
  * [crossref-standalone/yearly-journals.sql](./crossref-standalone/yearly-journals.sql)
  * [yearly-numpages/yearly-numpages.sql](./yearly-numpages/yearly-numpages.sql)
  * [graph/yearly-proportion-of-cited-papers.sql](./graph/yearly-proportion-of-cited-papers.sql)
  * [graph/yearly-2y-impact-factor.sql](./graph/yearly-2y-impact-factor.sql)
  * [graph/yearly-20y-impact-factor.sql](./graph/yearly-20y-impact-factor.sql)
  * [cdindex/yearly-cdindex.sql](./cdindex/yearly-cdindex.sql)
* [Number of research synthesis studies published each year in the period 1971–2021](https://doi.org/10.1371/journal.pone.0294946.g003) derived from [research-synthesis/a3k-queries/research-synthesis.sql](./research-synthesis/a3k-queries/research-synthesis.sql)
* [Evolution of subject coverage and publications 1945–2021](https://doi.org/10.1371/journal.pone.0294946.g004) derived from [graph/general-field-publications-list.sql](./graph/general-field-publications-list.sql)
* [Citations from COVID research to COVID research over time](https://doi.org/10.1371/journal.pone.0294946.g005) derived from [covid/inner-citations.sql](./covid/inner-citations.sql)
