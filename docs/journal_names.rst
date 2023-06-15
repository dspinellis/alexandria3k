Crossref journal names
======================

.. Automatically generated file. Do not modify by hand.

.. code:: py

   from alexandria3k.data_sources import journal_names

.. autoclass:: data_sources.journal_names.JournalNames
   :members: query, populate

Generated schema
----------------

.. code:: sql

    CREATE TABLE journal_names(
      id,
      title,
      crossref_id,
      publisher,
      issn_print,
      issn_eprint,
      issns_additional,
      doi,
      volume_info
    );
    
    CREATE TABLE journals_issns(
      journal_id,
      issn,
      issn_type
    );
    
