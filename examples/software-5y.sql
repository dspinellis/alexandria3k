-- SQL expression for selecting 5 years of software engineering venues

works.published_year BETWEEN 2017 AND 2021 AND (
  works.issn_print IN (
    -- Google Scholar List
    -- Journal of Systems and Software
    '01641212',
    -- Information and Software Technology
    '09505849',
    -- Software: Practice and Experience
    '00380644',

    -- All titleFile.csv lines containing "Soft.*Eng"
    -- ACM SIGSOFT Software Engineering Notes
    '01635948',
    -- ACM Transactions on Software Engineering and Methodology
    '1049331X',
    -- Advances in Software Engineering
    '16878655',
    -- American Journal of Software Engineering and Applications
    '23272473',
    -- Annals of Software Engineering
    '10227091',
    -- Automated Software Engineering
    '09288910',
    -- Bonfring International Journal of Software Engineering and Soft Computing
    '22501045',
    -- Bulletin of the South Ural State University Series Computational Mathematics and Software Engineering
    '23059052',
    -- e-Informatica Software Engineering Journal
    '18977979',
    -- Electronic Systems and Software
    '14798336',
    -- Empirical Software Engineering
    '13823256',
    -- i-manager’s Journal on Software Engineering
    '09735151',
    -- IEE Proceedings - Software
    '14625970',
    -- IEE Proceedings - Software Engineering
    '13645080',
    -- IEEE Software
    '07407459',
    -- IEEE Transactions on Software Engineering
    '00985589',
    -- IET Software
    '17518806',
    -- Indian Journal of Software Engineering and Project Management
    '',
    -- Indonesian Journal on Software Engineering (IJSE)
    '24610690',
    -- Information Technology Computer Science Software Engineering and Cyber Security
    '2786507X',
    -- Innovations in Systems and Software Engineering
    '16145046',
    -- International Journal of Advanced Research in Computer Science and Software Engineering
    '22776451',
    -- International Journal of Agent-Oriented Software Engineering
    '17461375',
    -- International Journal of Computer Systems & Software Engineering
    '22898522',
    -- International Journal of Forensic Software Engineering
    '17435099',
    -- International Journal of Secure Software Engineering
    '19473036',
    -- International Journal of Software Engineering
    '2162934X',
    -- International Journal of Software Engineering & Applications
    '09762221',
    -- International Journal of Software Engineering and Its Applications
    '17389984',
    -- International Journal of Software Engineering and Knowledge Engineering
    '02181940',
    -- International Journal of Software Engineering and Technologies (IJSET)
    '23024038',
    -- International Journal of Software Engineering for Smart Device
    '22058494',
    -- International Journal of Software Engineering Technology and Applications
    '20532466',
    -- International Journal Software Engineering and Computer Science (IJSECS)
    '27764869',
    -- Journal of Software Engineering
    '18194311',
    -- Journal of Software Engineering Research and Development
    '21951721',
    -- KIPS Transactions on Software and Data Engineering
    '22875905',
    -- Lecture Notes on Software Engineering
    '23013559',
    -- Software & Microsystems
    '02613182',
    -- Software Development Digital Business Intelligence and Computer Engineering
    '',
    -- Software Engineering
    '19257902',
    -- Software Engineering
    '23768029',
    -- Software Engineering and Applications
    '23252286',
    -- Software Engineering Journal
    '02686961',
    -- Syntax Journal of Software Engineering Computer Science and Information Technology
    '27767027',
    -- The Open Software Engineering Journal
    '1874107X',
    -- VFAST Transactions on Software Engineering
    '24116246'
  )
  -- https://scholar.google.com/citations?view_op=top_venues&hl=en&vq=eng_softwaresystems
  -- apart from PLDI, SOSP
  -- Includes all from https://www.sigsoft.org/events.html
  -- Most proceedings are easily found at https://dl.acm.org/proceedings

  -- SIGSOFT sponsored, Goodle Scholar Software Systems
  OR works.doi LIKE '10.1109/ASE51524.2021.%' -- 2021
  OR works.doi LIKE '10.1145/3324884.%' -- 2020
  OR works.doi LIKE '10.1109/ASE.2019.%' -- 2019
  OR works.doi LIKE '10.1145/3238147.%' -- 2018
  OR works.doi LIKE '10.1109/ASE.2017.%' -- 2017

  -- Goodle Scholar Software Systems
  OR works.doi LIKE '10.1109/COMPSAC51774.2021.%' -- 2021
  OR works.doi LIKE '10.1109/COMPSAC48688.2020.%' -- 2020
  OR works.doi LIKE '10.1109/COMPSAC.2019.%' -- 2019
  OR works.doi LIKE '10.1109/COMPSAC.2018.%' -- 2018
  OR works.doi LIKE '10.1109/COMPSAC.2017.%' -- 2017

  -- SIGSOFT sponsored
  OR works.doi LIKE '10.1145/3465480.%' -- 2021
  OR works.doi LIKE '10.1145/3401025.%' -- 2020
  OR works.doi LIKE '10.1145/3328905.%' -- 2019
  OR works.doi LIKE '10.1145/3210284.%' -- 2018
  OR works.doi LIKE '10.1145/3093742.%' -- 2017

  -- SIGSOFT sponsored, Goodle Scholar Software Systems
  OR works.doi LIKE '10.1145/3468264.%' -- 2021
  OR works.doi LIKE '10.1145/3368089.%' -- 2020
  OR works.doi LIKE '10.1145/3338906.%' -- 2019
  OR works.doi LIKE '10.1145/3236024.%' -- 2018
  OR works.doi LIKE '10.1145/3106237.%' -- 2017

  -- SIGSOFT sponsored, Goodle Scholar Software Systems
  OR works.doi LIKE '10.1145/3475716.%' -- 2021
  OR works.doi LIKE '10.1145/3382494.%' -- 2020
  OR works.doi LIKE '10.1109/ESEM.2019.%' -- 2019
  OR works.doi LIKE '10.1145/3239235.%' -- 2018
  OR works.doi LIKE '10.1109/ESEM.2017.%' -- 2017

  -- SIGSOFT sponsored
  OR works.doi LIKE '10.1145/3427921.%' -- 2021
  OR works.doi LIKE '10.1145/3358960.%' -- 2020
  OR works.doi LIKE '10.1145/3297663.%' -- 2019
  OR works.doi LIKE '10.1145/3185768.%' -- 2018
  OR works.doi LIKE '10.1145/3030207.%' -- 2017

  -- SIGSOFT sponsored, Goodle Scholar Software Systems
  OR works.doi LIKE '10.1109/ICSE43902.2021.%' -- 2021
  OR works.doi LIKE '10.1145/3377811.%' -- 2020
  OR works.doi LIKE '10.1109/ICSE.2019.%' -- 2019
  OR works.doi LIKE '10.1145/3180155.%' -- 2018
  OR works.doi LIKE '10.1109/ICSE.2017.%' -- 2017

  -- SIGSOFT sponsored, Goodle Scholar Software Systems
  OR works.doi LIKE '10.1145/3460319.%' -- 2021
  OR works.doi LIKE '10.1145/3395363.%' -- 2020
  OR works.doi LIKE '10.1145/3293882.%' -- 2019
  OR works.doi LIKE '10.1145/3213846.%' -- 2018
  OR works.doi LIKE '10.1145/3092703.%' -- 2017


  -- Goodle Scholar Software Systems
  OR works.doi LIKE '10.1109/ICSME52107.2021.%' -- 2021
  OR works.doi LIKE '10.1109/ICSME46990.2020.%' -- 2020
  OR works.doi LIKE '10.1109/ICSME.2019.%' -- 2019
  OR works.doi LIKE '10.1109/ICSME.2018.%' -- 2018
  OR works.doi LIKE '10.1109/ICSME.2017.%' -- 2017

  -- SIGSOFT sponsored
  OR works.doi LIKE '10.1109/MobileSoft52590.2021.%' -- 2021
  OR works.doi LIKE '10.1145/3387905.%' -- 2020
  OR works.doi LIKE '10.1109/MOBILESoft.2019.%' -- 2019
  OR works.doi LIKE '10.1145/3197231.%' -- 2018
  OR works.doi LIKE '10.1109/MOBILESoft.2017.%' -- 2017

  -- SIGSOFT sponsored
  OR works.doi LIKE '10.1109/MODELS50736.2021.%' -- 2021
  OR works.doi LIKE '10.1145/3365438.%' -- 2020
  OR works.doi LIKE '10.1109/MODELS.2019.%' -- 2019
  OR works.doi LIKE '10.1145/3239372.%' -- 2018
  OR works.doi LIKE '10.1109/MODELS.2017.%' -- 2017

  -- Goodle Scholar Software Systems
  OR works.doi LIKE '10.1109/MSR52588.2021.%' -- 2021
  OR works.doi LIKE '10.1145/3379597.%' -- 2020
  OR works.doi LIKE '10.1109/MSR.2019.%' -- 2019
  OR works.doi LIKE '10.1145/3196398.%' -- 2018
  OR works.doi LIKE '10.1109/MSR.2017.%' -- 2017

  -- Goodle Scholar Software Systems
  OR works.doi LIKE '10.1109/RE51729.2021.%' -- 2021
  OR works.doi LIKE '10.1109/RE48521.2020.%' -- 2020
  OR works.doi LIKE '10.1109/RE.2019.%' -- 2019
  OR works.doi LIKE '10.1109/RE.2018.%' -- 2018
  OR works.doi LIKE '10.1109/RE.2017.%' -- 2017

  -- Goodle Scholar Software Systems
  OR works.doi LIKE '10.1109/SANER50967.2021.%' -- 2021
  OR works.doi LIKE '10.1109/SANER48275.2020.%' -- 2020
  OR works.doi LIKE '10.1109/SANER.2019.%' -- 2019
  OR works.doi LIKE '10.1109/SANER.2018.%' -- 2018
  OR works.doi LIKE '10.1109/SANER.2017.%' -- 2017

  -- Goodle Scholar Software Systems
  OR works.doi LIKE '10.1007/978-3-030-72016-2_%' -- 2021
  OR works.doi LIKE '10.1007/978-3-030-45190-5_%' -- 2020
  OR works.doi LIKE '10.1007/978-3-030-17462-0_%' -- 2019
  OR works.doi LIKE '10.1007/978-3-319-89960-2_%' -- 2018
  OR works.doi LIKE '10.1007/978-3-662-54577-5_%' -- 2017
)
