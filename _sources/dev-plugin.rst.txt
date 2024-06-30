Plugin development
------------------

The *alexandria3k* system is structured around plugins that provide access
to data sources and data processing functionality.
New plugins can be developed and contributed by adding a Python
file in the `data_sources` or `processes` source code directory.
Plugins are made automagically available to the *a3k* :doc:`cli`
and can also be used through the *alexandria3k* :doc:`user-api`.

All plugins shall start with a docstring describing the plugin's
functionality.

Data source plugins
~~~~~~~~~~~~~~~~~~~

To create a new data source plugin you need to perform a number
of steps.
The employed modules and classes are documented in the
:doc:`plugin-api`.

* Create a file in ``src/alexandria3k/data_sources/`` that implements the
  data source access.
  There you need to define the data's class, their schema,
  cursors for fetching the data items, and, optionally, a method for
  downloading the data.
  The data source's name for the CLI is all lowercase (e.g. ``datacite``),
  for the class name with an initial capital (e.g. ``Datacite``), and in
  the documentation and schema's as formally spelled (e.g. ``DataCite``).

  The simplest case involves adding plugins for data available in CSV
  format (see e.g. the implementations for ``asjcs``, ``journal_names``,
  ``doaj``, and ``funder_names``).
  In this case only the following steps are needed.

  * Create the plugin in the ``src/alexandria3k/data_sources`` directory.
  * Define the data schema in a ``tables`` global variable
    through the ``TableMeta`` and ``ColumnMeta`` classes.
    Use the ``CsvCursor`` as the table's cursor.
    Unless column values are obtained in order from a CSV
    file, each column must define a function that will provide its
    value.
    Example:

  .. code:: py

          tables = [
              TableMeta(
                  "funder_names",
                  cursor_class=CsvCursor,
                  columns=[
                      ColumnMeta("id"),
                      ColumnMeta("url"),
                      ColumnMeta("name"),
                      ColumnMeta("replaced", lambda row:
                                 row[2] if len(row[2]) else None),
                  ],
              )
          ]

  * Define a URL for fetching the data source, if none is provided, as
    the global constant ``DEFAULT_SOURCE``.
    If no such exists, set the constant to ``None``.
  * Define the data source's class by subclassing the ``DataSource`` class.
    Example (for a single table):

  .. code:: py

          class FunderNames(DataSource):
              def __init__(
                  self,
                  data_source,
                  sample=lambda n: True,
                  attach_databases=None,
              ):
                  super().__init__(
                      VTSource(table, data_source, sample),
                      [table], attach_databases
                  )

  Data sources with with multiple tables, need the defition of a more
  complex schema.
  In these cases you must also define:

  * an SQLite virtual table data source ``VTSource``,
  * a cursor to iterate over the records of each table,
  * and possibly a partitioning scheme to handle interrelated tables
    that are streamed concurrently (e.g. a work and its authors).

  The virtual table and cursor classes are documented in the
  `APSW Virtual Tables chapter <https://rogerbinns.github.io/apsw/vtable.html>`__.
  It is easiest to base this on an existing data source:

  * The data sources ``asjcs``, ``doaj``, ``funder_names``, ``journal_names``
    map a single CSV dataset into a single relational table.
  * ``crossref`` maps a set of compressed JSON files, all residing in
    a single directory, and each containing multiple works.
  * ``datacite`` maps a compressed tar file, containing files residing
    in a non-flat structure.  Each file contains 1000 JSON records, separated
    by newlines.
  * ``orcid`` maps a compressed tar file that has in nested directories one
    XML file for each person.
  * ``pubmed`` maps a set of compressed XML files, all residing in
    a single directory, and each containing multiple works.
  * ``ror`` maps a single compressed JSON file into several tables.
  The ``crossref``, ``ror``, and ``orcid`` data sources implement partitioning.
  In addition, the ``crossref``, ``orcid`, and ``datacite`` data sources
  implement indexing over partitions,
  which allows efficient sampling by skipping unneeded containers.
  All table rows have an ``id`` field, with a unique identifier for that
  table across all table rows.
  As detail table indices are reset for each record, the identifier
  typically incorporates also the identifiers of the parent tables.

* Add a small subset of the data in the ``tests/data/`` directory.
* Create a file with unit and integration tests in ``tests/data_sources/``.
* Create a `Graphviz <https://graphviz.org/>`_ file with the data source's
  schema in ``docs/schema/``.
  Use a color associated with the data source's logo.
* Add a legend for the schema's tables in ``docs/schema/other.dot``.
* Add the schema's SVG in ``docs/schema.rst``.
* Add the schema in ``bin/update-schema``, run it to regenerate the schema
  diagrams, and, after they are correct, add the generated SVG file, and
  commit the new and updated files.
* Update the plugin documentation and the schema diagrams as documented
  elsewhere in this guide.
* Add a motivating example in the ``examples`` directory.


Data processing plugins
~~~~~~~~~~~~~~~~~~~~~~~
To create a data processing plugin follow these steps.

* Create the plugin in the ``src/alexandria3k/plugins`` directory.
* Define the schema of the generated tables in a ``tables`` global variable
  through the ``TableMeta`` and ``ColumnMeta`` classes.
  There is not need to define cursors or accessor functions.
* Define a function named ``process``, which takes as an argument a
  path to a populated SQLite database,
  and performs the processing associated with the plugin.
* Add unit tests in the ``tests/processes`` directory.
* Add a motivating example in the ``examples`` directory.
