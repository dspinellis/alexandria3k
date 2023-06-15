Open Researcher and Contributor ID (ORCID) data
===============================================

.. Automatically generated file. Do not modify by hand.

.. code:: py

   from alexandria3k.data_sources import orcid

.. autoclass:: data_sources.orcid.Orcid
   :members: query, populate

Generated schema
----------------

.. code:: sql

    CREATE TABLE persons(
      id INTEGER PRIMARY KEY,
      container_id,
      orcid,
      given_names,
      family_name,
      biography
    );
    
    CREATE TABLE person_researcher_urls(
      id,
      container_id,
      person_id,
      name,
      url
    );
    
    CREATE TABLE person_countries(
      id,
      container_id,
      person_id,
      country
    );
    
    CREATE TABLE person_keywords(
      id,
      container_id,
      person_id,
      keyword
    );
    
    CREATE TABLE person_external_identifiers(
      id,
      container_id,
      person_id,
      type,
      value,
      url
    );
    
    CREATE TABLE person_distinctions(
      id,
      container_id,
      person_id,
      organization_name,
      organization_city,
      organization_region,
      organization_country,
      organization_identifier,
      department_name,
      role_title,
      start_year,
      start_month,
      start_day,
      end_year,
      end_month,
      end_day
    );
    
    CREATE TABLE person_educations(
      id,
      container_id,
      person_id,
      organization_name,
      organization_city,
      organization_region,
      organization_country,
      organization_identifier,
      department_name,
      role_title,
      start_year,
      start_month,
      start_day,
      end_year,
      end_month,
      end_day
    );
    
    CREATE TABLE person_employments(
      id,
      container_id,
      person_id,
      organization_name,
      organization_city,
      organization_region,
      organization_country,
      organization_identifier,
      department_name,
      role_title,
      start_year,
      start_month,
      start_day,
      end_year,
      end_month,
      end_day
    );
    
    CREATE TABLE person_invited_positions(
      id,
      container_id,
      person_id,
      organization_name,
      organization_city,
      organization_region,
      organization_country,
      organization_identifier,
      department_name,
      role_title,
      start_year,
      start_month,
      start_day,
      end_year,
      end_month,
      end_day
    );
    
    CREATE TABLE person_memberships(
      id,
      container_id,
      person_id,
      organization_name,
      organization_city,
      organization_region,
      organization_country,
      organization_identifier,
      department_name,
      role_title,
      start_year,
      start_month,
      start_day,
      end_year,
      end_month,
      end_day
    );
    
    CREATE TABLE person_qualifications(
      id,
      container_id,
      person_id,
      organization_name,
      organization_city,
      organization_region,
      organization_country,
      organization_identifier,
      department_name,
      role_title,
      start_year,
      start_month,
      start_day,
      end_year,
      end_month,
      end_day
    );
    
    CREATE TABLE person_services(
      id,
      container_id,
      person_id,
      organization_name,
      organization_city,
      organization_region,
      organization_country,
      organization_identifier,
      department_name,
      role_title,
      start_year,
      start_month,
      start_day,
      end_year,
      end_month,
      end_day
    );
    
    CREATE TABLE person_fundings(
      id,
      container_id,
      person_id,
      title,
      type,
      short_description,
      amount,
      url,
      start_year,
      start_month,
      start_day,
      end_year,
      end_month,
      end_day,
      organization_name,
      organization_city,
      organization_region,
      organization_country,
      organization_identifier
    );
    
    CREATE TABLE person_peer_reviews(
      id,
      container_id,
      person_id,
      reviewer_role,
      review_type,
      subject_type,
      subject_name,
      subject_url,
      group_id,
      completion_year,
      completion_month,
      completion_day,
      organization_name,
      organization_city,
      organization_region,
      organization_country
    );
    
    CREATE TABLE person_research_resources(
      id,
      container_id,
      person_id,
      title,
      start_year,
      start_month,
      start_day,
      end_year,
      end_month,
      end_day
    );
    
    CREATE TABLE person_works(
      id,
      container_id,
      person_id,
      doi
    );
    
