Directory of Open Access Journals
=================================

.. Automatically generated file. Do not modify by hand.

.. code:: py

   from alexandria3k.data_sources import doaj

.. autoclass:: data_sources.doaj.Doaj
   :members: query, populate

Generated schema
----------------

.. code:: sql

    CREATE TABLE open_access_journals(
      id,
      name,
      url,
      doaj_url,
      oaj_start,
      alternative_name,
      issn_print,
      issn_eprint,
      keywords,
      languages,
      publisher,
      pubisher_country,
      society,
      society_country,
      license,
      license_attributes,
      license_terms_url,
      license_embedded,
      example_license_embedded_url,
      author_copyright,
      copyright_info_url,
      review_process,
      review_process_url,
      plagiarism_screening,
      plagiarism_info_url,
      aims_scope_url,
      board_url,
      author_instructions_url,
      sub_pub_weeks,
      apc,
      apc_info_url,
      apc_amount,
      apc_waiver,
      apc_waiver_info_url,
      other_fees,
      other_fees_info_url,
      preservation_services,
      preservation_national_library,
      preservation_info_url,
      deposit_policy_directory,
      deposit_policy_directory_url,
      persistent_article_identifiers,
      orcid_in_metadata,
      i4oc_compliance,
      doaj_oa_compliance,
      oa_statement_url,
      continues,
      continued_by,
      lcc_codes,
      subjects,
      doaj_Seal,
      added_on,
      last_updated,
      article_records_number,
      most_recent_addition
    );
    
