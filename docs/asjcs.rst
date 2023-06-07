Scopus Subject Areas and All Science Journal Classification Codes (ASJC) data
=============================================================================

.. Automatically generated file. Do not modify by hand.

.. code:: py

   from alexandria3k.data_sources import asjcs

.. autoclass:: data_sources.asjcs.Asjcs
   :members: query, populate

Generated schema
----------------

.. code:: sql

    CREATE TABLE asjc_import(
      id,
      code,
      field,
      subject_area
    );
    
    CREATE TABLE asjc_general_fields(
      id,
      name
    );
    
    CREATE TABLE asjc_subject_areas(
      id,
      name
    );
    
    CREATE TABLE asjcs(
      id,
      field,
      subject_area_id,
      general_field_id
    );
    
