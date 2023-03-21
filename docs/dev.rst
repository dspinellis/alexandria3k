Development
-----------

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

CLI use while developing
~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: sh

   # While in alexandria3k/src directory

   # Install development dependencies
   pipenv install --dev

   # Launch a shell in the virtual environment
   pipenv shell

   # Navigate to the top directory
   cd ..

   # Run the CLI
   bin/alexandria3k --help

Testing
~~~~~~~

Python unit and integration tests
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code:: sh

   # While in the top-level directory
   python3 -m unittest discover

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
   black -l 79 src/alexandria3k/*.py

Linting
~~~~~~~

.. code:: sh

   # While in the top-level directory
   python -m pylint src/alexandria3k/*.py

Database schema diagrams
~~~~~~~~~~~~~~~~~~~~~~~~

After the database schema has changed, its relational diagrams in the
documentation must be updated as follows.

.. code:: sh

   # While in the top-level directory
   bin/update-schema


Building
~~~~~~~~

.. code:: sh

   # While in the top-level directory
   python3 -m build


