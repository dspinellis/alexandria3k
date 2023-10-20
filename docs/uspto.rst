Patent grant bibliographic (front page) text data (JAN 1976 - present)
======================================================================

.. Automatically generated file. Do not modify by hand.

.. code:: py

   from alexandria3k.data_sources import uspto

.. autoclass:: data_sources.uspto.Uspto
   :members: query, populate

Generated schema
----------------

.. code:: sql

    CREATE TABLE us_patents(
      id,
      container_id,
      language,
      status,
      country,
      filename,
      date_produced,
      date_published,
      publication_reference_doc_number,
      publication_reference_kind,
      publication_reference_name,
      type,
      application_reference_doc_number,
      application_reference_kind,
      application_reference_name,
      application_reference_date,
      locarno_edition,
      locarno_main_classification,
      locarno_further_classification,
      locarno_text,
      national_edition,
      national_main_classification,
      national_further_classification,
      national_additional_info,
      national_linked_indexing_code_group,
      national_unlinked_indexing_code,
      national_text,
      series_code,
      invention_title,
      botanic_name,
      botanic_variety,
      claims_number,
      exemplary_claim,
      figures_number,
      drawings_number,
      primary_examiner_firstname,
      primary_examiner_lastname,
      assistant_examiner_firstname,
      assistant_examiner_lastname,
      authorized_officer_firstname,
      authorized_officer_lastname,
      hague_reg_num,
      cpa_flag,
      rule47_flag
    );
    
    CREATE TABLE usp_icpr_classifications(
      patent_id,
      container_id,
      ipc_date,
      class_level,
      section,
      class,
      subclass,
      main_group,
      subgroup,
      symbol_position,
      class_value,
      action_date,
      generating_office,
      class_status,
      class_source
    );
    
    CREATE TABLE usp_cpc_classifications(
      patent_id,
      container_id,
      type,
      cpc_version_indicator,
      section,
      class,
      sub_class,
      main_group,
      sub_group,
      symbol_position,
      class_value,
      action_date,
      generating_office,
      class_status,
      class_data_source,
      scheme_origination_code,
      combination_group_number,
      combination_rank_number
    );
    
    CREATE TABLE usp_related_documents(
      patent_id,
      container_id,
      relation,
      parent_doc_number,
      parent_doc_kind,
      parent_doc_name,
      parent_doc_date,
      status,
      parent_grant_doc_number,
      parent_pct_doc_number,
      parent_filing_date,
      child_doc_number,
      child_doc_kind,
      child_doc_name,
      child_doc_date,
      child_filing_date,
      document_number,
      document_kind,
      document_name,
      document_date,
      provisional_application_status,
      corrected_document_doc_number,
      corrected_document_kind,
      corrected_document_name,
      corrected_document_date,
      type_of_correction,
      gazette_number,
      gazette_date,
      correction_text
    );
    
    CREATE TABLE usp_field_of_classification(
      patent_id,
      container_id,
      ipcr_classification,
      cpc_classification_text,
      cpc_classification_combination_text,
      national_edition,
      national_main,
      national_further,
      national_additional_info,
      national_linked_code_group,
      national_unlinked_code,
      national_text
    );
    
    CREATE TABLE usp_inventors(
      patent_id,
      container_id,
      sequence,
      name,
      first_name,
      middle_name,
      last_name,
      org_name,
      suffix,
      iid,
      role,
      department,
      synonym,
      registered_number,
      email,
      url,
      text,
      city,
      state,
      country,
      postcode,
      designation,
      designated_country,
      designated_region
    );
    
    CREATE TABLE usp_applicants(
      patent_id,
      container_id,
      sequence,
      name,
      first_name,
      middle_name,
      last_name,
      org_name,
      suffix,
      iid,
      role,
      department,
      synonym,
      registered_number,
      email,
      url,
      text,
      city,
      state,
      country,
      postcode,
      app_type,
      applicant_authority_category,
      designation,
      residence,
      us_rights,
      designated_country,
      designated_region,
      designated_country_inventor,
      designated_region_inventor
    );
    
    CREATE TABLE usp_agents(
      patent_id,
      container_id,
      sequence,
      name,
      first_name,
      middle_name,
      last_name,
      org_name,
      suffix,
      iid,
      role,
      department,
      synonym,
      registered_number,
      email,
      url,
      text,
      city,
      state,
      country,
      postcode,
      rep_type
    );
    
    CREATE TABLE usp_assignees(
      patent_id,
      container_id,
      name,
      first_name,
      middle_name,
      last_name,
      org_name,
      suffix,
      iid,
      role,
      department,
      synonym,
      registered_number,
      email,
      url,
      text,
      city,
      state,
      country,
      postcode
    );
    
    CREATE TABLE usp_citations(
      patent_id,
      container_id,
      patcit_num,
      nplcit_num,
      nplcit_othercit,
      patcit_doc_number,
      patcit_country,
      patcit_kind,
      patcit_date,
      patcit_rel_passage,
      patcit_rel_category,
      patcit_rel_claims,
      category,
      ipc_class_edition,
      ipc_class_main,
      ipc_class_further,
      cpc_class_text,
      national_class_country,
      national_class_edition,
      national_class_main,
      national_class_further
    );
    
    CREATE TABLE usp_patent_family(
      patent_id,
      container_id,
      priority_app_doc_number,
      priority_app_country,
      priority_app_kind,
      priority_app_name,
      priority_app_date,
      family_member_doc_number,
      family_member_country,
      family_member_kind,
      family_member_name,
      family_member_date,
      text
    );
    
