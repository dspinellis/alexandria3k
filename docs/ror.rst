Research Organization Registry (ROR) data
=========================================

.. Automatically generated file. Do not modify by hand.

.. code:: py

   from alexandria3k.data_sources import ror

.. autoclass:: data_sources.ror.Ror
   :members: query, populate

Generated schema
----------------

.. code:: sql

    CREATE TABLE research_organizations(
      id INTEGER PRIMARY KEY,
      ror_path,
      name,
      status,
      established,
      grid,
      address_city,
      address_state,
      address_postcode,
      address_country_code,
      address_lat,
      address_lng
    );
    
    CREATE TABLE ror_types(
      id,
      ror_id,
      type
    );
    
    CREATE TABLE ror_links(
      id,
      ror_id,
      link
    );
    
    CREATE TABLE ror_aliases(
      id,
      ror_id,
      alias
    );
    
    CREATE TABLE ror_acronyms(
      id,
      ror_id,
      acronym
    );
    
    CREATE TABLE ror_relationships(
      id,
      ror_id,
      type,
      ror_path
    );
    
    CREATE TABLE ror_funder_ids(
      id,
      ror_id,
      funder_id
    );
    
    CREATE TABLE ror_wikidata_ids(
      id,
      ror_id,
      wikidata_id
    );
    
    CREATE TABLE ror_isnis(
      id,
      ror_id,
      isni
    );
    
