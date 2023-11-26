Link USPTO non-patent literature citations with their DOI
=========================================================

.. Automatically generated file. Do not modify by hand.

.. code:: py

   from alexandria3k.processes import link_uspto_doi

.. autofunction:: processes.link_uspto_doi.process

Generated schema
----------------

.. code:: sql

    CREATE TABLE usp_nplcit_dois(
      patent_id,
      nplcit_num,
      doi
    );
    
