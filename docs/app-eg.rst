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

The following examples are available.

-  `“Hello world” example: number of authors by
   decade <https://github.com/dspinellis/alexandria3k/tree/main/examples/authors-by-decade>`__
-  `Tally number of research synthesis
   studies <https://github.com/dspinellis/alexandria3k/tree/main/examples/research-synthesis>`__
-  `Generate and study the entities’ graph
   structure <https://github.com/dspinellis/alexandria3k/tree/main/examples/graph>`__
-  `Examine the evolution and impact of open access journal
   papers <https://github.com/dspinellis/alexandria3k/tree/main/examples/open-access>`__
-  `Report metrics associated with ORCID
   data <https://github.com/dspinellis/alexandria3k/tree/main/examples/orcid>`__
-  `Obtain measures associated with COVID-19
   research <https://github.com/dspinellis/alexandria3k/tree/main/examples/covid>`__
-  `Calculate the 2021 journal impact
   factor <https://github.com/dspinellis/alexandria3k/tree/main/examples/impact-factor-2021>`__
-  `Calculate the h5-index of
   journals <https://github.com/dspinellis/alexandria3k/tree/main/examples/journal-h5>`__
-  `Calculate the h5-index of software engineering research
   venues <https://github.com/dspinellis/alexandria3k/tree/main/examples/soft-eng-h5>`__
-  `Calculate h5-index of persons and study their citation
   graph <https://github.com/dspinellis/alexandria3k/tree/main/examples/person-h5>`__
-  `Report metrics associated with the Crossref data
   set <https://github.com/dspinellis/alexandria3k/tree/main/examples/crossref-standalone>`__
-  `Calculate relative yearly author
   productivity <https://github.com/dspinellis/alexandria3k/tree/main/examples/author-productivity>`__
-  `Calculate the average size of an article’s pages each
   year <https://github.com/dspinellis/alexandria3k/tree/main/examples/yearly-numpages>`__
-  `Calculate the works’ CD-5 index using the Python API or a
   pre-populated
   database <https://github.com/dspinellis/alexandria3k/tree/main/examples/cdindex>`__
-  `Investigate the CD-5 index of Dan Tawfik’s
   works <https://github.com/dspinellis/alexandria3k/tree/main/examples/tawfik>`__
-  `Fully-indexed Crossref database
   sample <https://github.com/dspinellis/alexandria3k/tree/main/examples/sample>`__
-  `Top five US Patent Office applications by country and year  
   <https://github.com/dspinellis/alexandria3k/tree/main/examples/uspto>`__
