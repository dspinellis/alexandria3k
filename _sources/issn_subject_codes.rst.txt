ISSN Subject Codes data processing
==================================

.. Automatically generated file. Do not modify by hand.

.. code:: py

   from alexandria3k.data_sources import issn_subject_codes

.. autoclass:: data_sources.issn_subject_codes.IssnSubjectCodes
   :members: query, populate

Generated schema
----------------

.. code:: sql

    CREATE TABLE issn_subject_codes(
      id INTEGER PRIMARY KEY,
      issn,
      subject_code INTEGER
    );
    
