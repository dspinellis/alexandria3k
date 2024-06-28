Development processes
---------------------

For software development purposes *alexandria3k* can also be installed
and used through its `Github
repository <https://github.com/dspinellis/alexandria3k>`__, rather than
as a Python package.

.. _installation-1:

Installation
~~~~~~~~~~~~

.. code:: sh

   git clone https://github.com/dspinellis/alexandria3k.git
   cd alexandra3k/src
   pipenv install

Development environment
~~~~~~~~~~~~~~~~~~~~~~~

Perform the following steps for setting up a virtual environment
with the required development dependencies.

.. code:: sh

   # While in alexandria3k/src directory

   # Install development dependencies
   pipenv install --dev

   # Launch a shell in the virtual environment
   pipenv shell

You can then run the command-line version from the source distribution on the
top-level directory as follows:

.. code:: sh

   bin/a3k --help


Continuous integration
~~~~~~~~~~~~~~~~~~~~~~

GitHub actions are used for running unit tests, linting, verifying the
code's format, as well as building the package and the documentation
when a new commit is pushed to GitHub.
Before doing so, it's advisable to perform these actions locally,
as detailed in the following sections.
In addition, testing, formatting, and linting can be easilly configured
to be run as a fast Git pre-commit hook by running the following commands
at the top-level directory.

.. code:: sh

   printf '#!/bin/sh\nbin/pre-commit\n' >.git/hooks/pre-commit
   chmod +x .git/hooks/pre-commit


Debugging and logging
~~~~~~~~~~~~~~~~~~~~~

Much of the *alexandria3k* code is executed by means of callbacks
through the *SQLite* *apsw* module.
This makes it difficult to trace and debug.
The liberal use of ``print`` statements is your friend.
In addition, *alexandria3k* offers many debug options,
which you should be using for troubleshooting.
Run ``a3k --help`` to see which options are available.


Testing
~~~~~~~

Python unit and integration tests
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code:: sh

   # While in the top-level directory
   python3 -m unittest discover -s .

SQL unit tests
^^^^^^^^^^^^^^

To run SQL unit tests install
`rdbunit <https://github.com/dspinellis/rdbunit>`__ and the
`SQLite <https://www.sqlite.org/index.html>`__ command-line tool.

.. code:: sh

   # While in the top-level directory
   for t in tests/*.rdbu; do rdbunit --database=sqlite $t | sqlite3 ; done

Code formatting
~~~~~~~~~~~~~~~

.. code:: sh

   # While in the top-level directory
   find src -name '*.py' | xargs black -l 79

Linting
~~~~~~~

.. code:: sh

   # While in the top-level directory
   find src -name '*.py' | xargs python -m pylint --rcfile .pylintrc

Plugin documentation
~~~~~~~~~~~~~~~~~~~~

When data source or processing plugins are added the Python API
documentation must be updated as follows.

.. code:: sh

   # While in the top-level directory
   bin/update-python-api

For users on MacOS, this might require installing the
`GNU sed <https://formulae.brew.sh/formula/gnu-sed>`__ package.

Application examples documentation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When new application examples are added in the ``examples`` directory
documentation must be updated as follows.

.. code:: sh

   # While in the top-level directory
   bin/update-app-eg

This requires an installed version of `Pandoc <https://pandoc.org/>`__.

Database schema diagrams
~~~~~~~~~~~~~~~~~~~~~~~~

After the database schema has changed, its relational diagrams in the
documentation must be updated as follows.

.. code:: sh

   # While in the top-level directory
   bin/update-schema


This requires an installed version of the `GraphViz <https://graphviz.org/>`__
*dot* command.

Building
~~~~~~~~

.. code:: sh

   # While in the top-level directory
   hatch build dist/

This will result in built files being placed in the ``dist`` directory.

Documentation building
~~~~~~~~~~~~~~~~~~~~~~

The process for converting the documentation into HTML and a Unix *man* page
is documented in the
:doc:`installation instructions <installation>`.

Adding a new data source
~~~~~~~~~~~~~~~~~~~~~~~~
Adding a new data source plugin to *alexandria3k* involves the following steps.

* Create a file in ``src/alexandria3k/data_sources/`` that implements the
  data source access.
  There you need to define the data's class, its schema,
  cursors for fetching the data items, and, optionally, a method for
  downloading its data.
  The data source's name for the CLI is all lowercase (e.g. ``datacite``),
  for the class name with an initial capital (e.g. ``Datacite``), and in
  the documentation and schema's as formally spelled (e.g. ``DataCite``).
  All table rows have an ``id`` field, with a unique identifier for that
  table across all table rows.
  As detail table indices are reset for each record, the identifier
  typically incorporates also the identifiers of the parent tables.
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
* Add a small subset of the data in ``tests/data/``.
* Create a file with unit and integration tests in ``tests/data_sources/``.
* Create a file with the data source's schema in ``docs/schema/``.
  Use a color associated with the data source's logo.
* Add a legend for the schema's tables in ``docs/schema/other.dot``.
* Add the schema's SVG in ``docs/schema.rst``.
* Add the schema in ``bin/update-schema``, run it to regenerate the schema
  diagrams, and, after they are correct, add the generated SVG file, and
  commit the new and updated files.
* Update the plugin documentation and the schema diagrams as documented
  elsewhere in this guide.
