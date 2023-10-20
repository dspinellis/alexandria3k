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


Application examples documentation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When new application examples are added in the ``examples`` directory
documentation must be updated as follows.

.. code:: sh

   # While in the top-level directory
   bin/update-app-eg


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
   python3 -m build

Documentation building
~~~~~~~~~~~~~~~~~~~~~~

The process for converting the documentation into HTML and a Unix *man* page
is documented in the
:doc:`installation instructions <installation>`.
