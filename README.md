# Validation pipeline for integrative and hybrid models

## Project objective 
- `1.` Develop a validation pipeline (including data validation, model validation, fit of input to model, fit of data not used for modeling and uncertainty of the model) for assessing IHM structures deposited to [PDB-Dev](https://pdb-dev.wwpdb.org/index.html)

## List of files and directories:
- `docs` documentation for all classes and functions (sphinx)

- `src`  relevant source code for execution

## List of classes:

- `WriteReport`  class to write dictionary for jinja2, HTML and PDF outputs

- `plots`  plots from analysis

- `get_excluded_volume` class to calculate excluded volume and other relevant statistics   

- `get_molprobity_information` class to get data from molprobity, used only for atomistic models

- `sas_validation` class to perform validation of models built using SAS datasets

- `cx_validation`  class to perform validation of models built using CX-MS datasets  

- `em_validation`  class to perform validation of models built using EM datasets

- `sas_validation_plots`  class to plot results from validation of models built using SAS datasets

## Test site
- [`test web page`](https://modbase.compbio.ucsf.edu/pdbdev-test/) 

## Information

_Author(s)_: Sai J. Ganesan


