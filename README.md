# Biosphere-Functional-Integrity
This repository aims to make calculation of functional integrity - as defined in Mohamed and al. 2024 (https://doi.org/10.1016/j.oneear.2023.12.008) - easier, and readaptable, using QGIS models.

**MANDATORY:** Change the software (QGIS) translation language to US English.

## PREPARATION

### Necessary:
1) Vector: Layer of the studied territory
2) Raster: land use database (DB) and its nomenclature
3) A breakdown of the nomenclature between: semi-natural soils; non-semi-natural soils; not categorised (NULL)

### Optional :
4) Another land use DB, to requalify a category from the first DB

## USE OF THE MODULE

2 QGIS models: MODEL_Integ.model3; MODEL_Reclass.model3

### MODEL_Reclass
This model is used to reclassify a category from the initial land-use DB using a category from another land-use DB.
It produces 1 output map:
- A map of the studied territory with the initial DB including the new category (old category -> new category if superposition ; old category otherise)

### MODEL_Integ
This model is used to calculate the functional integrity of the study area, based on a land use DBD.
It produces 4 output maps:
- A map of the input DB on the territory only; 
- A map showing the distribution of the area between (semi-)natural and non-(semi-)natural spaces; 
- A map of the territory's functional integrity of the Biosphere (% of km² semi-natural); 
- A map showing the distribution of the territory between areas that respect the limit (>=25%) and areas that do not (<25%). The latter makes it easy to calculate the proportion of the territory that complies with the limit (Raster layer statistics).

Shield: [![CC BY-NC-SA 4.0][cc-by-nc-sa-shield]][cc-by-nc-sa]

This work is licensed under a
[Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License][cc-by-nc-sa].

[![CC BY-NC-SA 4.0][cc-by-nc-sa-image]][cc-by-nc-sa]

[cc-by-nc-sa]: http://creativecommons.org/licenses/by-nc-sa/4.0/
[cc-by-nc-sa-image]: https://licensebuttons.net/l/by-nc-sa/4.0/88x31.png
[cc-by-nc-sa-shield]: https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg
