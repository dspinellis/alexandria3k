-- Calculate metrics of software engineering venues

ATTACH '5y-se.db' AS se_data;

CREATE TABLE works_venue AS
  SELECT doi AS doi,
  -- https://scholar.google.com/citations?view_op=top_venues&hl=en&vq=eng_softwaresystems
  -- apart from PLDI, SOSP
  -- Includes all from https://www.sigsoft.org/events.html
  -- Most proceedings are easily found at https://dl.acm.org/proceedings
  CASE
    -- SIGSOFT sponsored, Goodle Scholar Software Systems
    WHEN doi LIKE '10.1109/ASE51524.2021.%' THEN 'ASE'  -- 2021
    WHEN doi LIKE '10.1145/3324884.%' THEN 'ASE'  -- 2020
    WHEN doi LIKE '10.1109/ASE.2019.%' THEN 'ASE'  -- 2019
    WHEN doi LIKE '10.1145/3238147.%' THEN 'ASE'  -- 2018
    WHEN doi LIKE '10.1109/ASE.2017.%' THEN 'ASE'  -- 2017

    -- Goodle Scholar Software Systems
    WHEN doi LIKE '10.1109/COMPSAC51774.2021.%' THEN 'COMPSAC'  -- 2021
    WHEN doi LIKE '10.1109/COMPSAC48688.2020.%' THEN 'COMPSAC'  -- 2020
    WHEN doi LIKE '10.1109/COMPSAC.2019.%' THEN 'COMPSAC'  -- 2019
    WHEN doi LIKE '10.1109/COMPSAC.2018.%' THEN 'COMPSAC'  -- 2018
    WHEN doi LIKE '10.1109/COMPSAC.2017.%' THEN 'COMPSAC'  -- 2017

    -- SIGSOFT sponsored
    WHEN doi LIKE '10.1145/3465480.%' THEN 'DEBS'  -- 2021
    WHEN doi LIKE '10.1145/3401025.%' THEN 'DEBS'  -- 2020
    WHEN doi LIKE '10.1145/3328905.%' THEN 'DEBS'  -- 2019
    WHEN doi LIKE '10.1145/3210284.%' THEN 'DEBS'  -- 2018
    WHEN doi LIKE '10.1145/3093742.%' THEN 'DEBS'  -- 2017

    -- SIGSOFT sponsored, Goodle Scholar Software Systems
    WHEN doi LIKE '10.1145/3468264.%' THEN 'ESEC/FSE'  -- 2021
    WHEN doi LIKE '10.1145/3368089.%' THEN 'ESEC/FSE'  -- 2020
    WHEN doi LIKE '10.1145/3338906.%' THEN 'ESEC/FSE'  -- 2019
    WHEN doi LIKE '10.1145/3236024.%' THEN 'ESEC/FSE'  -- 2018
    WHEN doi LIKE '10.1145/3106237.%' THEN 'ESEC/FSE'  -- 2017

    -- SIGSOFT sponsored, Goodle Scholar Software Systems
    WHEN doi LIKE '10.1145/3475716.%' THEN 'ESEM'  -- 2021
    WHEN doi LIKE '10.1145/3382494.%' THEN 'ESEM'  -- 2020
    WHEN doi LIKE '10.1109/ESEM.2019.%' THEN 'ESEM'  -- 2019
    WHEN doi LIKE '10.1145/3239235.%' THEN 'ESEM'  -- 2018
    WHEN doi LIKE '10.1109/ESEM.2017.%' THEN 'ESEM'  -- 2017

    -- SIGSOFT sponsored
    WHEN doi LIKE '10.1145/3427921.%' THEN 'ICPE' -- 2021
    WHEN doi LIKE '10.1145/3358960.%' THEN 'ICPE' -- 2020
    WHEN doi LIKE '10.1145/3297663.%' THEN 'ICPE' -- 2019
    WHEN doi LIKE '10.1145/3185768.%' THEN 'ICPE' -- 2018
    WHEN doi LIKE '10.1145/3030207.%' THEN 'ICPE' -- 2017

    -- SIGSOFT sponsored, Goodle Scholar Software Systems
    WHEN doi LIKE '10.1109/ICSE43902.2021.%' THEN 'ICSE' -- 2021
    WHEN doi LIKE '10.1145/3377811.%' THEN 'ICSE'  -- 2020
    WHEN doi LIKE '10.1109/ICSE.2019.%' THEN 'ICSE'  -- 2019
    WHEN doi LIKE '10.1145/3180155.%' THEN 'ICSE'  -- 2018
    WHEN doi LIKE '10.1109/ICSE.2017.%' THEN 'ICSE'  -- 2017

    -- SIGSOFT sponsored, Goodle Scholar Software Systems
    WHEN doi LIKE '10.1145/3460319.%' THEN 'ISSTA'  -- 2021
    WHEN doi LIKE '10.1145/3395363.%' THEN 'ISSTA'  -- 2020
    WHEN doi LIKE '10.1145/3293882.%' THEN 'ISSTA'  -- 2019
    WHEN doi LIKE '10.1145/3213846.%' THEN 'ISSTA'  -- 2018
    WHEN doi LIKE '10.1145/3092703.%' THEN 'ISSTA'  -- 2017


    -- Goodle Scholar Software Systems
    WHEN doi LIKE '10.1109/ICSME52107.2021.%' THEN 'ICSME'  -- 2021
    WHEN doi LIKE '10.1109/ICSME46990.2020.%' THEN 'ICSME'  -- 2020
    WHEN doi LIKE '10.1109/ICSME.2019.%' THEN 'ICSME'  -- 2019
    WHEN doi LIKE '10.1109/ICSME.2018.%' THEN 'ICSME'  -- 2018
    WHEN doi LIKE '10.1109/ICSME.2017.%' THEN 'ICSME'  -- 2017

    -- SIGSOFT sponsored
    WHEN doi LIKE '10.1109/MobileSoft52590.2021.%' THEN 'MobileSoft'  -- 2021
    WHEN doi LIKE '10.1145/3387905.%' THEN 'MobileSoft'  -- 2020
    WHEN doi LIKE '10.1109/MOBILESoft.2019.%' THEN 'MobileSoft'  -- 2019
    WHEN doi LIKE '10.1145/3197231.%' THEN 'MobileSoft'  -- 2018
    WHEN doi LIKE '10.1109/MOBILESoft.2017.%' THEN 'MobileSoft'  -- 2017

    -- SIGSOFT sponsored
    WHEN doi LIKE '10.1109/MODELS50736.2021.%' THEN 'MODELS'  -- 2021
    WHEN doi LIKE '10.1145/3365438.%' THEN 'MODELS'  -- 2020
    WHEN doi LIKE '10.1109/MODELS.2019.%' THEN 'MODELS'  -- 2019
    WHEN doi LIKE '10.1145/3239372.%' THEN 'MODELS'  -- 2018
    WHEN doi LIKE '10.1109/MODELS.2017.%' THEN 'MODELS'  -- 2017

    -- Goodle Scholar Software Systems
    WHEN doi LIKE '10.1109/MSR52588.2021.%' THEN 'MSR'  -- 2021
    WHEN doi LIKE '10.1145/3379597.%' THEN 'MSR'  -- 2020
    WHEN doi LIKE '10.1109/MSR.2019.%' THEN 'MSR'  -- 2019
    WHEN doi LIKE '10.1145/3196398.%' THEN 'MSR'  -- 2018
    WHEN doi LIKE '10.1109/MSR.2017.%' THEN 'MSR'  -- 2017

    -- Goodle Scholar Software Systems
    WHEN doi LIKE '10.1109/RE51729.2021.%' THEN 'RE'  -- 2021
    WHEN doi LIKE '10.1109/RE48521.2020.%' THEN 'RE'  -- 2020
    WHEN doi LIKE '10.1109/RE.2019.%' THEN 'RE'  -- 2019
    WHEN doi LIKE '10.1109/RE.2018.%' THEN 'RE'  -- 2018
    WHEN doi LIKE '10.1109/RE.2017.%' THEN 'RE'  -- 2017

    -- Goodle Scholar Software Systems
    WHEN doi LIKE '10.1109/SANER50967.2021.%' THEN 'SANER'  -- 2021
    WHEN doi LIKE '10.1109/SANER48275.2020.%' THEN 'SANER'  -- 2020
    WHEN doi LIKE '10.1109/SANER.2019.%' THEN 'SANER'  -- 2019
    WHEN doi LIKE '10.1109/SANER.2018.%' THEN 'SANER'  -- 2018
    WHEN doi LIKE '10.1109/SANER.2017.%' THEN 'SANER'  -- 2017

    -- Goodle Scholar Software Systems
    WHEN doi LIKE '10.1007/978-3-030-72016-2_%' THEN 'TACAS'  -- 2021
    WHEN doi LIKE '10.1007/978-3-030-45190-5_%' THEN 'TACAS'  -- 2020
    WHEN doi LIKE '10.1007/978-3-030-17462-0_%' THEN 'TACAS'  -- 2019
    WHEN doi LIKE '10.1007/978-3-319-89960-2_%' THEN 'TACAS'  -- 2018
    WHEN doi LIKE '10.1007/978-3-662-54577-5_%' THEN 'TACAS'  -- 2017
    ELSE
            issn_print
  END venue
  FROM works;
