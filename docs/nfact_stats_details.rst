Overview
========
This module creates either component loadings or statsmaps of merged components. 
Most of the output is needed after doing dual regression, however it can created statsmaps of group level components.

Component loadings
==================

This calculates loadings between individual subjects dual regression output and the group level components. 
Each loading is a pearson R of how similar an individual component is to the group level component.

Output
-------
Output is a csv file or a npy file of subject by component. 

Usage
-------
.. code-block:: text
    
    nfact_stats loadings [-h] [-O] [-l LIST_OF_SUBJECTS] 
    [-o OUTDIR] [-d DIM] [-n NFACT_FOLDER] [-a ALGO] [-C]


General options:
  -h, --help 
    Shows help message
  -O, --overwrite 
    Overwrites previous file structure

Set Up Arguments:
  -l, --list_of_subjects 
    Filepath to a list of subjects
  -o, --outdir 
    Path to output directory

Decomp args:
  -d, --dim 
    Number of dimensions/components that was used to generate nfact_decomp image
  -n, --nfact_folder 
    Absolute path to nfact_decomp output folder.
  -a, --algo 
    Which decomposition algorithm. Options are: NMF (default), or ICA. This is case insensitive

Stats args:
  -t, --threshold 
    Threshold components so that component loadings reflect connectivity patterns not noise.
  -C, --no_csv 
    Save Component Loadings as a npy file rather than as a csv file


Statsmap 
========

This creates statistical maps to be used in PALM or Randomise. 
The statistical maps are 3D niftis (white matter) and ciftis (grey matter) of combined combined components. 
This can be done on a group level or on a subject level. If it is done on a group level then images are 3D of just combined components. 
If it is done on a subject level then output is a 4D image with subject as the 4th dim (ready for palm/randomise)

**please note** statsmap can currently only accept ciftis for the grey matter.

Usage
-------

.. code-block:: text

    nfact_stats statsmap [-h] [-l LIST_OF_SUBJECTS] [-o OUTDIR] [-O] [-d DIM] 
    [-n NFACT_FOLDER] [-a ALGO] [-c COMPONENTS [COMPONENTS ...]] [-m MAP_NAME] [-G]

General options:
  -h, --help 
    Shows help message and exit
  -O, --overwrite 
    Overwrites previous file structure

Set Up options:
  -l, --list_of_subjects 
    Filepath to a list of subjects
  -o, --outdir 
    Path to output directory

Decomp options:
  -d, --dim 
    Number of dimensions/components that was used to generate nfact_decomp image
  -n, --nfact_folder 
    Absolute path to nfact_decomp output folder.
  -a, --algo 
    Which decomposition algorithm. Options are: NMF (default), or ICA. This is case insensitive

Statsmap options:
  -c, --components 
    Components to merge, Can accept any number
  -m, --map_name 
    Name to call the maps (i.e if merging components asscoiated with a network call it networkx)
  -G, --group-only 
    Only do group level stats map. Doesn't need a subject list