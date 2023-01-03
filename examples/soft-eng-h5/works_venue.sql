-- Associate DOIs with SE venues

CREATE INDEX IF NOT EXISTS works_issn_print_idx ON works(issn_print);
CREATE INDEX IF NOT EXISTS journal_names_issn_print_idx
  ON journal_names(issn_print);

CREATE TABLE rolap.works_venue AS
  SELECT works.doi AS doi, works.id as work_id,
  -- Most proceedings are easily found at https://dl.acm.org/proceedings
  CASE
    -- Index 1
    WHEN works.doi LIKE '10.1109/MODELS50736.2021.%' THEN 'MODELS'  -- 2021
    WHEN works.doi LIKE '10.1145/3365438.%' THEN 'MODELS'  -- 2020
    WHEN works.doi LIKE '10.1109/MODELS.2019.%' THEN 'MODELS'  -- 2019
    WHEN works.doi LIKE '10.1145/3239372.%' THEN 'MODELS'  -- 2018
    WHEN works.doi LIKE '10.1109/MODELS.2017.%' THEN 'MODELS'  -- 2017

    -- Index 3
    WHEN works.doi LIKE '10.1109/RE51729.2021.%' THEN 'RE'  -- 2021
    WHEN works.doi LIKE '10.1109/RE48521.2020.%' THEN 'RE'  -- 2020
    WHEN works.doi LIKE '10.1109/RE.2019.%' THEN 'RE'  -- 2019
    WHEN works.doi LIKE '10.1109/RE.2018.%' THEN 'RE'  -- 2018
    WHEN works.doi LIKE '10.1109/RE.2017.%' THEN 'RE'  -- 2017

    -- Index 4
    WHEN works.doi LIKE '10.1145/3475716.%' THEN 'ESEM'  -- 2021
    WHEN works.doi LIKE '10.1145/3382494.%' THEN 'ESEM'  -- 2020
    WHEN works.doi LIKE '10.1109/ESEM.2019.%' THEN 'ESEM'  -- 2019
    WHEN works.doi LIKE '10.1145/3239235.%' THEN 'ESEM'  -- 2018
    WHEN works.doi LIKE '10.1109/ESEM.2017.%' THEN 'ESEM'  -- 2017

    -- Index 7
    WHEN works.doi LIKE '10.1007/978-3-030-88106-1_%' THEN 'SSBSE'  -- 2021
    WHEN works.doi LIKE '10.1007/978-3-030-59762-7_%' THEN 'SSBSE'  -- 2020
    WHEN works.doi LIKE '10.1007/978-3-030-27455-9_%' THEN 'SSBSE'  -- 2019
    WHEN works.doi LIKE '10.1007/978-3-319-99241-9_%' THEN 'SSBSE'  -- 2018
    WHEN works.doi LIKE '10.1007/978-3-319-66299-2_%' THEN 'SSBSE'  -- 2017

    -- Index 8
    -- CSMR and WCRE are SANER from 2015 onward

    WHEN works.doi LIKE '10.1109/ICPC52881.2021.%' THEN 'ICPC'  -- 2021
    WHEN works.doi LIKE '10.1145/3387904.%' THEN 'ICPC'  -- 2020
    WHEN works.doi LIKE '10.1109/ICPC.2019.%' THEN 'ICPC'  -- 2019
    WHEN works.doi LIKE '10.1145/3196321.%' THEN 'ICPC'  -- 2018
    WHEN works.doi LIKE '10.1109/ICPC.2017.%' THEN 'ICPC'  -- 2017

    WHEN works.doi LIKE '10.1109/MSR52588.2021.%' THEN 'MSR'  -- 2021
    WHEN works.doi LIKE '10.1145/3379597.%' THEN 'MSR'  -- 2020
    WHEN works.doi LIKE '10.1109/MSR.2019.%' THEN 'MSR'  -- 2019
    WHEN works.doi LIKE '10.1145/3196398.%' THEN 'MSR'  -- 2018
    WHEN works.doi LIKE '10.1109/MSR.2017.%' THEN 'MSR'  -- 2017

    WHEN works.doi LIKE '10.1109/ICSME52107.2021.%' THEN 'ICSME'  -- 2021
    WHEN works.doi LIKE '10.1109/ICSME46990.2020.%' THEN 'ICSME'  -- 2020
    WHEN works.doi LIKE '10.1109/ICSME.2019.%' THEN 'ICSME'  -- 2019
    WHEN works.doi LIKE '10.1109/ICSME.2018.%' THEN 'ICSME'  -- 2018
    WHEN works.doi LIKE '10.1109/ICSME.2017.%' THEN 'ICSME'  -- 2017

    -- Index 9
    WHEN works.doi LIKE '10.1145/3460319.%' THEN 'ISSTA'  -- 2021
    WHEN works.doi LIKE '10.1145/3395363.%' THEN 'ISSTA'  -- 2020
    WHEN works.doi LIKE '10.1145/3293882.%' THEN 'ISSTA'  -- 2019
    WHEN works.doi LIKE '10.1145/3213846.%' THEN 'ISSTA'  -- 2018
    WHEN works.doi LIKE '10.1145/3092703.%' THEN 'ISSTA'  -- 2017

    WHEN works.doi LIKE '10.1109/ICST49551.2021.%' THEN 'ICST'  -- 2021
    WHEN works.doi LIKE '10.1109/ICST46399.2020.%' THEN 'ICST'  -- 2020
    WHEN works.doi LIKE '10.1109/ICST.2019.%' THEN 'ICST'  -- 2019
    WHEN works.doi LIKE '10.1109/ICST.2018.%' THEN 'ICST'  -- 2018
    WHEN works.doi LIKE '10.1109/ICST.2017.%' THEN 'ICST'  -- 2017

    -- Index 10
    WHEN works.doi LIKE '10.1109/ICSE43902.2021.%' THEN 'ICSE' -- 2021
    WHEN works.doi LIKE '10.1145/3377811.%' THEN 'ICSE'  -- 2020
    WHEN works.doi LIKE '10.1109/ICSE.2019.%' THEN 'ICSE'  -- 2019
    WHEN works.doi LIKE '10.1145/3180155.%' THEN 'ICSE'  -- 2018
    WHEN works.doi LIKE '10.1109/ICSE.2017.%' THEN 'ICSE'  -- 2017

    -- Created from combining WCRE and CSMR
    WHEN works.doi LIKE '10.1109/SANER50967.2021.%' THEN 'SANER'  -- 2021
    WHEN works.doi LIKE '10.1109/SANER48275.2020.%' THEN 'SANER'  -- 2020
    WHEN works.doi LIKE '10.1109/SANER.2019.%' THEN 'SANER'  -- 2019
    WHEN works.doi LIKE '10.1109/SANER.2018.%' THEN 'SANER'  -- 2018
    WHEN works.doi LIKE '10.1109/SANER.2017.%' THEN 'SANER'  -- 2017

    -- Index 11
    WHEN works.doi LIKE '10.1145/3468264.%' THEN 'ESEC/FSE'  -- 2021
    WHEN works.doi LIKE '10.1145/3368089.%' THEN 'ESEC/FSE'  -- 2020
    WHEN works.doi LIKE '10.1145/3338906.%' THEN 'ESEC/FSE'  -- 2019
    WHEN works.doi LIKE '10.1145/3236024.%' THEN 'ESEC/FSE'  -- 2018
    WHEN works.doi LIKE '10.1145/3106237.%' THEN 'ESEC/FSE'  -- 2017

    WHEN works.doi LIKE '10.1109/ASE51524.2021.%' THEN 'ASE'  -- 2021
    WHEN works.doi LIKE '10.1145/3324884.%' THEN 'ASE'  -- 2020
    WHEN works.doi LIKE '10.1109/ASE.2019.%' THEN 'ASE'  -- 2019
    WHEN works.doi LIKE '10.1145/3238147.%' THEN 'ASE'  -- 2018
    WHEN works.doi LIKE '10.1109/ASE.2017.%' THEN 'ASE'  -- 2017

    -- Index 13
    WHEN works.doi LIKE '10.1109/SCAM52516.2021.%' THEN 'SCAM'  -- 2021
    WHEN works.doi LIKE '10.1109/SCAM51674.2020.%' THEN 'SCAM'  -- 2020
    WHEN works.doi LIKE '10.1109/SCAM.2019.%' THEN 'SCAM'  -- 2019
    WHEN works.doi LIKE '10.1109/SCAM.2018.%' THEN 'SCAM'  -- 2018
    WHEN works.doi LIKE '10.1109/SCAM.2017.%' THEN 'SCAM'  -- 2017

    WHEN works.doi LIKE '10.1145/3486609.%' THEN 'GPCE'  -- 2021
    WHEN works.doi LIKE '10.1145/3425898.%' THEN 'GPCE'  -- 2020
    WHEN works.doi LIKE '10.1145/3357765.%' THEN 'GPCE'  -- 2019
    WHEN works.doi LIKE '10.1145/3278122.%' THEN 'GPCE'  -- 2018
    WHEN works.doi LIKE '10.1145/3136040.%' THEN 'GPCE'  -- 2017

    WHEN works.doi LIKE '10.1007/978-3-030-71500-7_%' THEN 'FASE'  -- 2021
    WHEN works.doi LIKE '10.1007/978-3-030-45234-6_%' THEN 'FASE'  -- 2020
    WHEN works.doi LIKE '10.1007/978-3-030-16722-6_%' THEN 'FASE'  -- 2019
    WHEN works.doi LIKE '10.1007/978-3-319-89363-1_%' THEN 'FASE'  -- 2018
    WHEN works.doi LIKE '10.1007/978-3-662-54494-5_%' THEN 'FASE'  -- 2017

    ELSE
            Coalesce(journal_names.title, works.issn_print)
  END venue
  FROM works
  LEFT JOIN journal_names ON works.issn_print = journal_names.issn_print;
