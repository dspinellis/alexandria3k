Installation
------------

The easiest way to install *alexandria3k* and its dependencies is
through `PyPI <https://pypi.org/>`__.

.. code:: sh

   python3 -m pip install --use-pep517 alexandria3k

or

.. code:: sh

   pip install --use-pep517 alexandria3k

The installation requires at least Python version 3.9 and is tested
with Python versions 3.9 to 3.12.
The best practice is to
`perform the installation in a Python virtual environment <https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/>`__.

Local documentation
~~~~~~~~~~~~~~~~~~~

The documentation of *alexandria3k*
`is available online <https://dspinellis.github.io/alexandria3k/>`__
If you want a local copy, you can create the HTML files by
cloning the *alexandria3k* 
`repository <https://github.com/dspinellis/alexandria3k>`__,
installing the required development dependencies,
and running `make html` in the `docs` directory.
The HTML files will be made available in the `docs/_build` directory.

Similarly, if you want to install a Unix manual page for the *a3k*
command-line interface, you can run `make manpage` (kudos to you BTW).
You can then install the man page made available at `docs/_build/a3k.1`
in your preferred man page source file location, e.g.
`/usr/local/share/man/man1` or `$HOME/man/man1`.
