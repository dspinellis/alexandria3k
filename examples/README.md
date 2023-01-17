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

The following examples are available.

* ["Hello world" example: number of authors by decade](authors-by-decade)
* [Tally number of research synthesis studies](research-synthesis)
* [Generate and study the entities' graph structure](graph)
* [Report metrics associated with ORCID data](orcid)
* [Obtain measures associated with COVID-19 research](covid)
* [Calculate the 2021 journal impact factor](impact-factor-2021)
* [Calculate the h5-index of journals](journal-h5)
* [Calculate the h5-index of software engineering research venues](soft-eng-h5)
* [Calculate h5-index of persons and study their citation graph](person-h5)
* [Calculate relative yearly author productivity](author-productivity)
* [Calculate the average size of an article's pages each year](yearly-numpages)
* [Calculate the works' CD-5 index using the Python API or a pre-populated database](cdindex)
* [Fully-indexed Crossref database sample](sample)
