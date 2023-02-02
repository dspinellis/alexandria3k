Use overview
------------

After downloading the Crossref data you can use *alexandria3k* through
its Python API or as a command-line tool.

These are the things you can do with *alexandria3k*.

-  Directly run ad hoc SQL queries on the Crossref data
-  Populate SQLite databases with Crossref, ORCID, DOAJ, and other data

   -  Select a horizontal subset of Crossref records

      -  Through an SQL expression
      -  By sampling a subset of the 26 thousand containers in the data
         set

   -  Select a horizontal subset of ORCID records by only loading those
      associated with already populated Crossref records
   -  Select a vertical subset of Crossref or ORCID columns

      -  Using the ``Table.Column`` or ``Table.*`` notation

Populating a database can take minutes (for a small, e.g. experimental,
subset), a few hours (to traverse the whole Crossref data set and obtain
a few thousands of records), or a couple of days (to produce a large
set, e.g. by selecting some columns).

After your populate an SQLite database and create suitable indexes, SQL
queries often run in seconds.

You can find many complete proof-of-concept example studies
conducted with command-line invocations in the
`examples <https://github.com/dspinellis/alexandria3k/tree/main/examples>`__
directory. Consider using the
`hello world <https://github.com/dspinellis/alexandria3k/tree/main/examples/authors-by-decade>`__ (work authors by decade) example as a starting point.
