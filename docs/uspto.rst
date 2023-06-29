US patent grant publication data
================================

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
        type,
        series_code,
        invention_title,
        botanic_name,
        botanic_variety,
        claims_number,
        figures_number,
        drawings_number,
        microform_number,
        primary_examiner_firstname,
        primary_examiner_lastname,
        assistant_examiner_firstname,
        assistant_examiner_lastname,
        authorized_officer_firstname,
        authorized_officer_lastname,
        hague_filing_date,
        hague_reg_pub_date,
        hague_reg_date,
        hague_reg_num,
        sir_flag,
        cpa_flag,
        rule47_flag
    );

    CREATE TABLE icpr_classifications(
        id,
        container_id,
        patent_id,
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