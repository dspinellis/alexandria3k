Use overview
------------

After downloading the Crossref data you can use *alexandria3k* through
its Python API or as a command-line tool.

With *alexandria3k* you can process diverse sources of bibliographic
data, such as Crossref, ORCID, USPTO, DOAJ, and ROR.
Specifically, you can perform the following actions.

- Directly run ad hoc SQL queries on any of the supported data sets.
- Populate SQLite databases with selected elements of the supported
  data sets.

  - Select a horizontal subset of a data set's records.

    - Through an SQL expression.
    - By sampling a subset of the data set's elements or containers.
      (For example sampling some of the 26 thousand containers in the
      Crossref data set.)

  - Select a horizontal subset of a data set's records by only loading
    those associated with already populated records or records available
    in another database.
  - Select a vertical subset of a data set's columns

    - Using the ``Table.Column`` or ``Table.*`` notation

- Process already populated databases to cross-link or normalize their
  elements.

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
