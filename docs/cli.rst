Command line interface
======================

The *a3k* command can be invoked from the shell as follows.

.. argparse::
   :ref: alexandria3k.__main__.get_cli_parser
   :prog: a3k

.. _shell-completion:

Shell completion
======================

The command line interface provides optional TAB completion (Bash, Zsh, Tcsh)
implemented in :mod:`alexandria3k.completion` via the optional dependency
`shtab <https://pypi.org/project/shtab/>`_.  When enabled it completes:

* Global options (``--debug``, ``--progress``, ``--version``)
* Subcommands (``populate``, ``query``, ``process``, ``download``,
  ``list-sources``, ``list-processes``, schema listing commands, ...)
* Data source names (``populate``, ``query``, ``download``)
* Process names (``process`` subcommand argument)
* Facility names (``list-source-schema`` / ``list-process-schema``)
* File / path arguments (``--query-file``, ``--row-selection-file``,
  ``--output``, positional ``data_location``, ``--attach-databases``)

Enabling
~~~~~~~~

Shell completion is provided by the `shtab <https://pypi.org/project/shtab/>`_
package.  This is installed automatically on non-Windows systems.
On Windows, or if it is missing, you can install it manually.

Install with the extra:

.. code-block:: bash

    pip install 'alexandria3k[completion]'

Or install the dependency directly (this is equivalent):

.. code-block:: bash

    pip install shtab

If ``--print-completion`` exits with an instruction to install the extra,
add it (or reinstall) and retry.

Generating a script
~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    a3k --print-completion SHELL   # SHELL = bash | zsh | tcsh

Bash
^^^^

System-wide (root):

.. code-block:: bash

    a3k --print-completion bash | sudo tee /etc/bash_completion.d/a3k > /dev/null

Per-user:

.. code-block:: bash

    mkdir -p ~/.local/share/bash-completion/completions
    a3k --print-completion bash > ~/.local/share/bash-completion/completions/a3k
    # Activate in the current shell (optional)
    source ~/.local/share/bash-completion/completions/a3k

Zsh
^^^

Ensure completion is initialized (normally already in ``~/.zshrc``):

.. code-block:: bash

    autoload -U compinit && compinit

Install function (Zsh expects leading underscore):

.. code-block:: bash

    a3k --print-completion zsh > "${fpath[1]}/_a3k"

If ``${fpath[1]}`` is not writable:

.. code-block:: bash

    mkdir -p ~/.zsh/completions
    a3k --print-completion zsh > ~/.zsh/completions/_a3k
    fpath=(~/.zsh/completions $fpath)
    autoload -U compinit && compinit

Tcsh
^^^^

.. code-block:: csh

    a3k --print-completion tcsh > ~/.a3k_completions.csh
    echo 'source ~/.a3k_completions.csh' >> ~/.tcshrc
    source ~/.a3k_completions.csh

Usage examples
~~~~~~~~~~~~~~

.. code-block:: console

    $ a3k popu<TAB>
    populate
    $ a3k populate db.sqlite <TAB>
    crossref-metadata datacite ...
    $ a3k process <TAB>
    link-works-asjcs ...
    $ a3k query -Q <TAB>
    (file suggestions...)

Regenerating after upgrades
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Re-run ``a3k --print-completion <shell>`` after upgrading if new data sources
or processes appear, overwriting the existing completion file.

Troubleshooting
~~~~~~~~~~~~~~~

===============================  =============================================================
Symptom                          Resolution
===============================  =============================================================
``--print-completion`` errors    ``pip install 'alexandria3k[completion]'``
Data sources not completing      Regenerate script; ensure new file was sourced
Zsh: no completion for ``a3k``   Confirm ``_a3k`` is on ``$fpath`` before ``compinit`` runs
Bash: script has no effect       Ensure system ``bash-completion`` installed; open new shell
===============================  =============================================================

Removing completion
~~~~~~~~~~~~~~~~~~~

Delete the installed file(s) and start a new shell:

* Bash system-wide: ``sudo rm /etc/bash_completion.d/a3k``
* Bash user: ``rm ~/.local/share/bash-completion/completions/a3k``
* Zsh: remove ``_a3k``; rerun ``compinit -u`` or restart shell
* Tcsh: remove the file and its ``source`` line from ``~/.tcshrc``

Implementation notes
~~~~~~~~~~~~~~~~~~~~

``completion.py`` adds ``--print-completion``. When ``shtab`` is present the
dynamic lists (data sources, processes, facilities) and file/path arguments are
annotated by assigning ``action.complete`` with either a dict of choices or a
file completion helper. If the dependency is missing a stub action prints
instructions and exits.