PubMed publication data
=======================

.. Automatically generated file. Do not modify by hand.

.. code:: py

   from alexandria3k.data_sources import pubmed

.. autoclass:: data_sources.pubmed.Pubmed
   :members: query, populate

Generated schema
----------------

.. code:: sql

    CREATE TABLE pubmed_articles(
      id,
      container_id,
      pubmed_id,
      doi,
      publisher_item_identifier_article_id,
      pmc_article_id,
      journal_title,
      journal_issn,
      journal_issn_type,
      journal_cited_medium,
      journal_volume INTEGER,
      journal_issue INTEGER,
      journal_year INTEGER,
      journal_month INTEGER,
      journal_day INTEGER,
      journal_medline_date,
      journal_ISO_abbreviation,
      article_date_year INTEGER,
      article_date_month INTEGER,
      article_date_day INTEGER,
      article_date_type,
      pagination,
      elocation_id,
      elocation_id_type,
      elocation_id_valid,
      language,
      title,
      vernacular_title,
      journal_country,
      medline_ta,
      nlm_unique_id,
      issn_linking,
      article_pubmodel,
      citation_subset,
      completed_year INTEGER,
      completed_month INTEGER,
      completed_day INTEGER,
      revised_year INTEGER,
      revised_month INTEGER,
      revised_day INTEGER,
      coi_statement,
      medline_citation_status,
      medline_citation_owner,
      medline_citation_version,
      medline_citation_indexing_method,
      medline_citation_version_date,
      keyword_list_owner,
      publication_status,
      abstract_copyright_information,
      other_abstract_copyright_information
    );
    
    CREATE TABLE pubmed_authors(
      id,
      container_id,
      article_id,
      given,
      family,
      suffix,
      initials,
      valid,
      identifier,
      identifier_source,
      collective_name
    );
    
    CREATE TABLE pubmed_author_affiliations(
      id,
      container_id,
      author_id,
      affiliation,
      identifier
    );
    
    CREATE TABLE pubmed_investigators(
      id,
      container_id,
      article_id,
      given,
      family,
      suffix,
      initials,
      valid,
      identifier,
      identifier_source
    );
    
    CREATE TABLE pubmed_investigator_affiliations(
      id,
      container_id,
      investigator_id,
      affiliation,
      identifier
    );
    
    CREATE TABLE pubmed_abstracts(
      id,
      container_id,
      article_id,
      label,
      text,
      nlm_category,
      copyright_information
    );
    
    CREATE TABLE pubmed_other_abstracts(
      id,
      container_id,
      article_id,
      abstract_type,
      language
    );
    
    CREATE TABLE pubmed_other_abstract_texts(
      id,
      container_id,
      abstract_id,
      text,
      label,
      nlm_category,
      copyright_information
    );
    
    CREATE TABLE pubmed_history(
      id,
      container_id,
      article_id,
      publication_status,
      year INTEGER,
      month INTEGER,
      day INTEGER,
      hour INTEGER,
      minute INTEGER
    );
    
    CREATE TABLE pubmed_chemicals(
      id,
      container_id,
      article_id,
      registry_number,
      name_of_substance,
      unique_identifier
    );
    
    CREATE TABLE pubmed_meshs(
      id,
      container_id,
      article_id,
      descriptor_name,
      descriptor_unique_identifier,
      descriptor_major_topic,
      descriptor_type,
      qualifier_name,
      qualifier_major_topic,
      qualifier_unique_identifier
    );
    
    CREATE TABLE pubmed_supplement_meshs(
      id,
      container_id,
      article_id,
      supplement_mesh_name,
      unique_identifier,
      mesh_type
    );
    
    CREATE TABLE pubmed_comments_corrections(
      id,
      container_id,
      article_id,
      ref_type,
      ref_source,
      pmid,
      pmid_version,
      note
    );
    
    CREATE TABLE pubmed_keywords(
      id,
      container_id,
      article_id,
      keyword,
      major_topic
    );
    
    CREATE TABLE pubmed_grants(
      id,
      container_id,
      article_id,
      grant_id,
      acronym,
      agency,
      country
    );
    
    CREATE TABLE pubmed_data_banks(
      id,
      container_id,
      article_id,
      data_bank_name
    );
    
    CREATE TABLE pubmed_data_bank_accessions(
      id,
      container_id,
      data_bank_id,
      accession_number
    );
    
    CREATE TABLE pubmed_references(
      id,
      container_id,
      article_id,
      citation
    );
    
    CREATE TABLE pubmed_reference_articles(
      id,
      container_id,
      reference_id,
      article_id,
      id_type
    );
    
    CREATE TABLE pubmed_publication_types(
      id,
      container_id,
      article_id,
      publication_type,
      unique_identifier
    );
    
