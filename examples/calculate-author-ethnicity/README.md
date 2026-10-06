# Populating Crossref by author ethnicity

Contains a [Makefile](Makefile) that populates a database with all works associated with authors whose name matches a given ethnicity. 

#### Steps: 
- Populates only id, given, family, work_id of the work_authors table.

- Classifies all authors based on given and family using the link-author-ethnicities process.

- Populates the rest of the tables only on the authors of the selected ethnicity

#### Usage:

```
make ETH=<ethincity>
```

#### Example:

```
make ETH=italian
```

### Available ethnicities:

``british`` ``norwegian`` ``indian`` ``hungarian`` ``spanish`` ``german`` ``zimbabwean`` ``portugese`` ``polish`` ``bulgarian`` ``bangladeshi`` ``turkish`` ``belgian`` ``pakistani`` ``italian`` ``romanian`` ``lithuanian`` ``french`` ``chinese`` ``swedish`` ``nigerian`` ``greek`` ``south african`` ``japanese`` ``dutch`` ``danish`` ``russian`` ``filipino``

### Classifier: 

The classifier model used to classify the names is n2e "28_nationalities_english_once"

For more details check: https://github.com/name-ethnicity-classifier/name-ethnicity-classifier/tree/main/model_configurations/28_nationalities_english_once#this-model-classifies-28-nationalities-of-which-only-one-is-english-speaking