DataCite publication data
=========================

.. Automatically generated file. Do not modify by hand.

.. code:: py

   from alexandria3k.data_sources import datacite

.. autoclass:: data_sources.datacite.Datacite
   :members: query, populate

Generated schema
----------------

.. code:: sql

    CREATE TABLE dc_works(
      id,
      container_id,
      identifier,
      identifier_type,
      doi,
      publisher,
      publication_year,
      resource_type,
      resource_type_general,
      language,
      sizes,
      formats,
      schema_version,
      metadata_version,
      url,
      created,
      registered,
      published,
      updated
    );
    
    CREATE TABLE dc_work_creators(
      id,
      container_id,
      work_id,
      name,
      name_type,
      given_name,
      family_name
    );
    
    CREATE TABLE dc_creator_name_identifiers(
      creator_id,
      container_id,
      name_identifier,
      name_identifier_scheme,
      scheme_uri
    );
    
    CREATE TABLE dc_creator_affiliations(
      creator_id,
      container_id,
      name
    );
    
    CREATE TABLE dc_work_titles(
      work_id,
      container_id,
      title,
      title_type
    );
    
    CREATE TABLE dc_work_subjects(
      work_id,
      container_id,
      subject,
      subject_scheme,
      scheme_uri,
      value_uri
    );
    
    CREATE TABLE dc_work_contributors(
      id,
      container_id,
      work_id,
      contributor_type,
      name,
      family_name,
      given_name
    );
    
    CREATE TABLE dc_contributor_name_identifiers(
      contributor_id,
      container_id,
      name_identifier,
      name_identifier_scheme,
      scheme_uri
    );
    
    CREATE TABLE dc_contributor_affiliations(
      contributor_id,
      container_id,
      name
    );
    
    CREATE TABLE dc_work_dates(
      work_id,
      container_id,
      date,
      date_type
    );
    
    CREATE TABLE dc_work_related_identifiers(
      work_id,
      container_id,
      related_identifier,
      related_identifier_type,
      relation_type,
      related_metadata_scheme,
      scheme_uri,
      scheme_type
    );
    
    CREATE TABLE dc_work_rights(
      work_id,
      container_id,
      rights,
      lang,
      rights_uri,
      rights_identifier,
      rights_identifier_scheme,
      scheme_uri
    );
    
    CREATE TABLE dc_work_descriptions(
      work_id,
      container_id,
      description,
      description_type
    );
    
    CREATE TABLE dc_work_geo_locations(
      work_id,
      container_id,
      geo_location_place,
      geo_location_point,
      geo_location_box
    );
    
    CREATE TABLE dc_work_funding_references(
      work_id,
      container_id,
      funder_name,
      funder_identifier,
      funder_identifier_type,
      award_number,
      award_uri,
      award_title
    );
    
