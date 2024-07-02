.. WARNING: Automatically generated file. Do not modify by hand.

Application examples
====================

The source distribution ``examples`` directory contains proof-of-concept
studies that were conducted with *alexandria3k* as examples of its use.

They are structured to use Makefiles based on
`simple-rolap <https://github.com/dspinellis/simple-rolap>`__ for
orchestrating the queries (it is installed automatically) and
`rdbunit <https://github.com/dspinellis/rdbunit>`__ for unit testing
them (it needs to be manually installed for running the tests). Running
(GNU) ``make`` in a directory will produce the expected results in a
``reports`` sub-directory. Many of the studies can take hours or days to
run. When running the scripts on a shared Unix/Linux computer, running
*make* as ``nohup nice make`` will log the operation in the file
``nohup.out`` (use ``tail -f nohup.out`` to view it), prevent the
command from terminating when a session is disconnected, and decrease
the priority of the tasks to minimize their burden on interactive users.
When modifying existing studies or creating one ones, run ``make help``
in a study directory to see some potentially useful *make* targets.

The
`common <https://github.com/dspinellis/alexandria3k/tree/main/examples/common>`__
directory contains Makefile rules for satisfying data dependencies
common to more than one study. It also hosts downloaded data sets to
minimize useless replication. The ``Makefile`` residing in it can be
used to tailor the running of all other studies.

Examples by directory
---------------------

The following examples are available.

Templates
~~~~~~~~~

-  `“Hello world” example: number of authors by
   decade <https://github.com/dspinellis/alexandria3k/tree/main/examples/authors-by-decade>`__
-  `Fully-indexed Crossref database
   sample <https://github.com/dspinellis/alexandria3k/tree/main/examples/sample>`__

Studies
~~~~~~~

-  `Tally number of research synthesis
   studies <https://github.com/dspinellis/alexandria3k/tree/main/examples/research-synthesis>`__
-  `Generate and study the entities’ graph
   structure <https://github.com/dspinellis/alexandria3k/tree/main/examples/graph>`__
-  `Obtain data associated with COVID-19
   research <https://github.com/dspinellis/alexandria3k/tree/main/examples/covid>`__
-  `Calculate the average size of an article’s pages each
   year <https://github.com/dspinellis/alexandria3k/tree/main/examples/yearly-numpages>`__
-  `Calculate the works’ CD-5 index using the Python API or a
   pre-populated
   database <https://github.com/dspinellis/alexandria3k/tree/main/examples/cdindex>`__
-  `Investigate the CD-5 index of Dan Tawfik’s
   works <https://github.com/dspinellis/alexandria3k/tree/main/examples/tawfik>`__
-  `Top five US Patent Office applications by country and
   year <https://github.com/dspinellis/alexandria3k/tree/main/examples/uspto>`__
-  `Replication study on software used in PubMed
   articles <https://github.com/dspinellis/alexandria3k/tree/main/examples/pubmed-software>`__

Data source examples and metric measurements
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  `Report metrics associated with the Crossref data
   set <https://github.com/dspinellis/alexandria3k/tree/main/examples/crossref-standalone>`__
-  `Report metrics associated with ORCID
   data <https://github.com/dspinellis/alexandria3k/tree/main/examples/orcid>`__
-  `Report metrics associated with DataCite
   data <https://github.com/dspinellis/alexandria3k/tree/main/examples/datacite>`__
-  `Report research organization registry
   metrics <https://github.com/dspinellis/alexandria3k/tree/main/examples/ror-metrics>`__

Impact and productivitycalculations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  `Calculate the 2021 journal impact
   factor <https://github.com/dspinellis/alexandria3k/tree/main/examples/impact-factor-2021>`__
-  `Calculate the h5-index of
   journals <https://github.com/dspinellis/alexandria3k/tree/main/examples/journal-h5>`__
-  `Calculate the h5-index of software engineering research
   venues <https://github.com/dspinellis/alexandria3k/tree/main/examples/soft-eng-h5>`__
-  `Calculate h5-index of persons and study their citation
   graph <https://github.com/dspinellis/alexandria3k/tree/main/examples/person-h5>`__
-  `Examine the evolution and impact of open access journal
   papers <https://github.com/dspinellis/alexandria3k/tree/main/examples/open-access>`__
-  `Calculate relative yearly author
   productivity <https://github.com/dspinellis/alexandria3k/tree/main/examples/author-productivity>`__

Published results
-----------------

The following queries have been used to publish derived figures and
tables.

-  `Yearly availability of Crossref
   elements <https://doi.org/10.1371/journal.pone.0294946.g001>`__
   derived from

   -  `crossref-standalone/yearly-abstracts.sql <https://github.com/dspinellis/alexandria3k/tree/main/examples/./crossref-standalone/yearly-abstracts.sql>`__
   -  `graph/yearly-work-subjects.sql <https://github.com/dspinellis/alexandria3k/tree/main/examples/./graph/yearly-work-subjects.sql>`__
   -  `graph/yearly-work-funders.sql <https://github.com/dspinellis/alexandria3k/tree/main/examples/./graph/yearly-work-funders.sql>`__
   -  `graph/yearly-work-links.sql <https://github.com/dspinellis/alexandria3k/tree/main/examples/./graph/yearly-work-links.sql>`__
   -  `graph/yearly-work-references.sql <https://github.com/dspinellis/alexandria3k/tree/main/examples/./graph/yearly-work-references.sql>`__
   -  `graph/yearly-work-authors.sql <https://github.com/dspinellis/alexandria3k/tree/main/examples/./graph/yearly-work-authors.sql>`__
   -  `graph/yearly-authors-orcid.sql <https://github.com/dspinellis/alexandria3k/tree/main/examples/./graph/yearly-authors-orcid.sql>`__
   -  `graph/yearly-author-affiliations.sql <https://github.com/dspinellis/alexandria3k/tree/main/examples/./graph/yearly-author-affiliations.sql>`__
   -  `graph/yearly-references-doi.sql <https://github.com/dspinellis/alexandria3k/tree/main/examples/./graph/yearly-references-doi.sql>`__
   -  `graph/yearly-funders-doi.sql <https://github.com/dspinellis/alexandria3k/tree/main/examples/./graph/yearly-funders-doi.sql>`__
   -  `graph/yearly-funder-awards.sql <https://github.com/dspinellis/alexandria3k/tree/main/examples/./graph/yearly-funder-awards.sql>`__

-  `Number and properties of Crossref
   records <https://doi.org/10.1371/journal.pone.0294946.t001>`__
   derived from `graph/metrics.sql <./graph/metrics.sql>`__
-  `Number of ORCID
   records <https://doi.org/10.1371/journal.pone.0294946.t002>`__
   derived from `graph/metrics.sql <./graph/metrics.sql>`__
-  `Evolution of scientific publishing metrics in the post-WW2
   period <https://doi.org/10.1371/journal.pone.0294946.g002>`__ derived
   from

   -  `graph/yearly-authors-per-work.sql <https://github.com/dspinellis/alexandria3k/tree/main/examples/./graph/yearly-authors-per-work.sql>`__
   -  `author-productivity/author-productivity.sql <https://github.com/dspinellis/alexandria3k/tree/main/examples/./author-productivity/author-productivity.sql>`__
   -  `graph/yearly-works.sql <https://github.com/dspinellis/alexandria3k/tree/main/examples/./graph/yearly-works.sql>`__
   -  `open-access/yearly-oa-journal-works.sql <https://github.com/dspinellis/alexandria3k/tree/main/examples/./open-access/yearly-oa-journal-works.sql>`__
   -  `graph/yearly-citations-per-paper.sql <https://github.com/dspinellis/alexandria3k/tree/main/examples/./graph/yearly-citations-per-paper.sql>`__
   -  `graph/yearly-references-per-paper.sql <https://github.com/dspinellis/alexandria3k/tree/main/examples/./graph/yearly-references-per-paper.sql>`__
   -  `crossref-standalone/yearly-journals.sql <https://github.com/dspinellis/alexandria3k/tree/main/examples/./crossref-standalone/yearly-journals.sql>`__
   -  `yearly-numpages/yearly-numpages.sql <https://github.com/dspinellis/alexandria3k/tree/main/examples/./yearly-numpages/yearly-numpages.sql>`__
   -  `graph/yearly-proportion-of-cited-papers.sql <https://github.com/dspinellis/alexandria3k/tree/main/examples/./graph/yearly-proportion-of-cited-papers.sql>`__
   -  `graph/yearly-2y-impact-factor.sql <https://github.com/dspinellis/alexandria3k/tree/main/examples/./graph/yearly-2y-impact-factor.sql>`__
   -  `graph/yearly-20y-impact-factor.sql <https://github.com/dspinellis/alexandria3k/tree/main/examples/./graph/yearly-20y-impact-factor.sql>`__
   -  `cdindex/yearly-cdindex.sql <https://github.com/dspinellis/alexandria3k/tree/main/examples/./cdindex/yearly-cdindex.sql>`__

-  `Number of research synthesis studies published each year in the
   period
   1971–2021 <https://doi.org/10.1371/journal.pone.0294946.g003>`__
   derived from
   `research-synthesis/a3k-queries/research-synthesis.sql <./research-synthesis/a3k-queries/research-synthesis.sql>`__
-  `Evolution of subject coverage and publications
   1945–2021 <https://doi.org/10.1371/journal.pone.0294946.g004>`__
   derived from
   `graph/general-field-publications-list.sql <./graph/general-field-publications-list.sql>`__
-  `Citations from COVID research to COVID research over
   time <https://doi.org/10.1371/journal.pone.0294946.g005>`__ derived
   from `covid/inner-citations.sql <./covid/inner-citations.sql>`__
