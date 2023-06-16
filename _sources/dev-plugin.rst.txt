Plugin development
------------------

The *alexandria3k* is structured around plugins that provide access
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
The simplest case involves adding plugins for data available in CSV
format (see e.g. the implementations for `asjcs`, `journal_names`,
`doaj`, and `funder_names`).
In this case only the following steps are needed.

* Create the plugin in the `src/alexandria3k/data_sources` directory.
* Define the data schema in a `tables` global variable
  through the `TableMeta` and `ColumnMeta` classes.
  Use the `CsvCursor` as the table's cursor.
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
  the global constant `DEFAULT_SOURCE`.
  If no such exists, set the constant to `None`.
* Define the data source's class by subclassing the `DataSource` class.
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

* Add a small subset of the data in the `tests/data` directory.
* Add unit tests in the `tests/data_sources` directory.
* Add a motivating example in the `examples` directory.

For data sources available in more complex forms you must also define.

* an SQLite virtual table data source `VTSource`,
* a cursor to iterate over the records of each table,
* and possibly a partitioning scheme to handle interrelated tables
  that are streamed concurrently (e.g. a work and its authors).

The virtual table and cursor classes are documented in the
`APSW Virtual Tables chapter <https://rogerbinns.github.io/apsw/vtable.html>`__.
As examples of their use in *alexandria3k* see the data source modules
`crossref` (this uses compressed containers of JSON files,
each containing multiple works),
`orcid` (a compressed *tar* file containing an XML file for each author),
and `ror` (a single compressed JSON file).
All these data sources implement partitioning.
In addition, the `crossref` and `orcid` data sources implement indexing
over partitions that allows efficient sampling by skipping unneeded
containers.

Data processing plugins
~~~~~~~~~~~~~~~~~~~~~~~
To create a data processing plugin follow these steps.

* Create the plugin in the `src/alexandria3k/plugins` directory.
* Define the schema of the generated tables in a `tables` global variable
  through the `TableMeta` and `ColumnMeta` classes.
  There is not need to define cursors or accessor functions.
* Define a function named `process`, which takes as an argument a
  path to a populated SQLite database,
  and performs the processing associated with the plugin.
* Add unit tests in the `tests/processes` directory.
* Add a motivating example in the `examples` directory.
