Crossref publication data
=========================

.. Automatically generated file. Do not modify by hand.

.. code:: py

   from alexandria3k.data_sources import crossref

.. autoclass:: data_sources.crossref.Crossref
   :members: query, populate

Generated schema
----------------

.. code:: sql

    CREATE TABLE works(
      id,
      container_id,
      doi,
      title,
      published_year,
      published_month,
      published_day,
      short_container_title,
      container_title,
      publisher,
      abstract,
      type,
      subtype,
      page,
      volume,
      article_number,
      journal_issue,
      issn_print,
      issn_electronic,
      update_count,
      references_count,
      is_referenced_by_count
    );
    
    CREATE TABLE work_authors(
      id,
      container_id,
      work_id,
      orcid,
      suffix,
      given,
      family,
      name,
      authenticated_orcid,
      prefix,
      sequence
    );
    
    CREATE TABLE author_affiliations(
      author_id,
      container_id,
      name
    );
    
    CREATE TABLE work_references(
      work_id,
      container_id,
      issn,
      standards_body,
      issue,
      key,
      series_title,
      isbn_type,
      doi_asserted_by,
      first_page,
      isbn,
      doi,
      component,
      article_title,
      volume_title,
      volume,
      author,
      standard_designator,
      year,
      unstructured,
      edition,
      journal_title,
      issn_type
    );
    
    CREATE TABLE work_updates(
      work_id,
      container_id,
      label,
      doi,
      timestamp
    );
    
    CREATE TABLE work_subjects(
      work_id,
      container_id,
      name
    );
    
    CREATE TABLE work_licenses(
      work_id,
      container_id,
      url,
      start_timestamp,
      delay_in_days
    );
    
    CREATE TABLE work_links(
      work_id,
      container_id,
      url,
      content_type
    );
    
    CREATE TABLE work_funders(
      id,
      container_id,
      work_id,
      doi,
      name
    );
    
    CREATE TABLE funder_awards(
      funder_id,
      container_id,
      name
    );
    
