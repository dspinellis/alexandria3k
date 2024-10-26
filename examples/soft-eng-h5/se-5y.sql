-- SQL expression for selecting 5 years of software engineering venues

-- Based on the venues given in Table 2 of the following paper.
-- G. Mathew, A. Agrawal and T. Menzies, "Finding Trends in Software
-- Research," in IEEE Transactions on Software Engineering,
-- doi: 10.1109/TSE.2018.2870388.

works.published_year BETWEEN 2017 AND 2021 AND (
  works.issn_print IN (
    -- Index 1
    '16191366', -- Software & Systems Modeling

    -- Index 2
    '07407459', -- IEEE Software

    -- Index 3
    '09473602', -- Requirements Engineering

    -- Index 4
    '13823256', -- Empirical Software Engineering

    -- Index 5
    '20477473', -- Journal of Software Evolution and Process
    '09639314', -- Software Quality Journal
    '09505849', -- Information and Software Technology

    -- Index 6
    '16145046', -- Innovations in Systems and Software Engineering
    '02181940', -- International Journal of Software Engineering and Knowledge Engineering
    '01635948', -- ACM SIGSOFT Software Engineering Notes

    -- Index 7
    '01641212', -- Journal of Systems and Software
    '00380644', -- Software: Practice and Experience

    -- Index 9
    '09600833', -- Software Testing Verification and Reliability

    -- Index 12
    '09288910', -- Automated Software Engineering
    '00985589', -- IEEE Transactions on Software Engineering
    '1049331X' -- ACM Transactions on Software Engineering and Methodology
  )
  -- Conferences
  -- These are created from se-metrics.sql with the following command:
  -- sed -n '/CASE/,/ELSE/{;s/WHEN doi/OR works.doi/;s/ THEN .* -/ -/;p;}'

  -- Index 1
  OR works.doi LIKE '10.1109/MODELS50736.2021.%' -- 2021
  OR works.doi LIKE '10.1145/3365438.%' -- 2020
  OR works.doi LIKE '10.1109/MODELS.2019.%' -- 2019
  OR works.doi LIKE '10.1145/3239372.%' -- 2018
  OR works.doi LIKE '10.1109/MODELS.2017.%' -- 2017

  -- Index 3
  OR works.doi LIKE '10.1109/RE51729.2021.%' -- 2021
  OR works.doi LIKE '10.1109/RE48521.2020.%' -- 2020
  OR works.doi LIKE '10.1109/RE.2019.%' -- 2019
  OR works.doi LIKE '10.1109/RE.2018.%' -- 2018
  OR works.doi LIKE '10.1109/RE.2017.%' -- 2017

  -- Index 4
  OR works.doi LIKE '10.1145/3475716.%' -- 2021
  OR works.doi LIKE '10.1145/3382494.%' -- 2020
  OR works.doi LIKE '10.1109/ESEM.2019.%' -- 2019
  OR works.doi LIKE '10.1145/3239235.%' -- 2018
  OR works.doi LIKE '10.1109/ESEM.2017.%' -- 2017

  -- Index 7
  OR works.doi LIKE '10.1007/978-3-030-88106-1_%' -- 2021
  OR works.doi LIKE '10.1007/978-3-030-59762-7_%' -- 2020
  OR works.doi LIKE '10.1007/978-3-030-27455-9_%' -- 2019
  OR works.doi LIKE '10.1007/978-3-319-99241-9_%' -- 2018
  OR works.doi LIKE '10.1007/978-3-319-66299-2_%' -- 2017

  -- Index 8
  -- CSMR and WCRE are SANER from 2015 onward

  OR works.doi LIKE '10.1109/ICPC52881.2021.%' -- 2021
  OR works.doi LIKE '10.1145/3387904.%' -- 2020
  OR works.doi LIKE '10.1109/ICPC.2019.%' -- 2019
  OR works.doi LIKE '10.1145/3196321.%' -- 2018
  OR works.doi LIKE '10.1109/ICPC.2017.%' -- 2017

  OR works.doi LIKE '10.1109/MSR52588.2021.%' -- 2021
  OR works.doi LIKE '10.1145/3379597.%' -- 2020
  OR works.doi LIKE '10.1109/MSR.2019.%' -- 2019
  OR works.doi LIKE '10.1145/3196398.%' -- 2018
  OR works.doi LIKE '10.1109/MSR.2017.%' -- 2017

  OR works.doi LIKE '10.1109/ICSME52107.2021.%' -- 2021
  OR works.doi LIKE '10.1109/ICSME46990.2020.%' -- 2020
  OR works.doi LIKE '10.1109/ICSME.2019.%' -- 2019
  OR works.doi LIKE '10.1109/ICSME.2018.%' -- 2018
  OR works.doi LIKE '10.1109/ICSME.2017.%' -- 2017

  -- Index 9
  OR works.doi LIKE '10.1145/3460319.%' -- 2021
  OR works.doi LIKE '10.1145/3395363.%' -- 2020
  OR works.doi LIKE '10.1145/3293882.%' -- 2019
  OR works.doi LIKE '10.1145/3213846.%' -- 2018
  OR works.doi LIKE '10.1145/3092703.%' -- 2017

  OR works.doi LIKE '10.1109/ICST49551.2021.%' -- 2021
  OR works.doi LIKE '10.1109/ICST46399.2020.%' -- 2020
  OR works.doi LIKE '10.1109/ICST.2019.%' -- 2019
  OR works.doi LIKE '10.1109/ICST.2018.%' -- 2018
  OR works.doi LIKE '10.1109/ICST.2017.%' -- 2017

  -- Index 10
  OR works.doi LIKE '10.1109/ICSE43902.2021.%' -- 2021
  OR works.doi LIKE '10.1145/3377811.%' -- 2020
  OR works.doi LIKE '10.1109/ICSE.2019.%' -- 2019
  OR works.doi LIKE '10.1145/3180155.%' -- 2018
  OR works.doi LIKE '10.1109/ICSE.2017.%' -- 2017

  -- Created from combining WCRE and CSMR
  OR works.doi LIKE '10.1109/SANER50967.2021.%' -- 2021
  OR works.doi LIKE '10.1109/SANER48275.2020.%' -- 2020
  OR works.doi LIKE '10.1109/SANER.2019.%' -- 2019
  OR works.doi LIKE '10.1109/SANER.2018.%' -- 2018
  OR works.doi LIKE '10.1109/SANER.2017.%' -- 2017

  -- Index 11
  OR works.doi LIKE '10.1145/3468264.%' -- 2021
  OR works.doi LIKE '10.1145/3368089.%' -- 2020
  OR works.doi LIKE '10.1145/3338906.%' -- 2019
  OR works.doi LIKE '10.1145/3236024.%' -- 2018
  OR works.doi LIKE '10.1145/3106237.%' -- 2017

  OR works.doi LIKE '10.1109/ASE51524.2021.%' -- 2021
  OR works.doi LIKE '10.1145/3324884.%' -- 2020
  OR works.doi LIKE '10.1109/ASE.2019.%' -- 2019
  OR works.doi LIKE '10.1145/3238147.%' -- 2018
  OR works.doi LIKE '10.1109/ASE.2017.%' -- 2017

  -- Index 13
  OR works.doi LIKE '10.1109/SCAM52516.2021.%' -- 2021
  OR works.doi LIKE '10.1109/SCAM51674.2020.%' -- 2020
  OR works.doi LIKE '10.1109/SCAM.2019.%' -- 2019
  OR works.doi LIKE '10.1109/SCAM.2018.%' -- 2018
  OR works.doi LIKE '10.1109/SCAM.2017.%' -- 2017

  OR works.doi LIKE '10.1145/3486609.%' -- 2021
  OR works.doi LIKE '10.1145/3425898.%' -- 2020
  OR works.doi LIKE '10.1145/3357765.%' -- 2019
  OR works.doi LIKE '10.1145/3278122.%' -- 2018
  OR works.doi LIKE '10.1145/3136040.%' -- 2017

  OR works.doi LIKE '10.1007/978-3-030-71500-7_%' -- 2021
  OR works.doi LIKE '10.1007/978-3-030-45234-6_%' -- 2020
  OR works.doi LIKE '10.1007/978-3-030-16722-6_%' -- 2019
  OR works.doi LIKE '10.1007/978-3-319-89363-1_%' -- 2018
  OR works.doi LIKE '10.1007/978-3-662-54494-5_%' -- 2017
)
