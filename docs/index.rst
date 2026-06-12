NFACT 
=====

.. image:: _static/thalamus_radiations.png
   :alt: description
   :class: spaced-figure

**NFACT** (Non-negative matrix Factorisation of Tractography data) is a set of modules (as well as an end to end pipeline) that decomposes 
tractography data using NMF/ICA.

NFACT pre-processes data ready for decomposition, performs group level decomposition and output then projects back to the subject level.
It is also able to produce quality control output, create spatialmaps and component loadings for further statistical testing as well as 
create confirguation files.

.. toctree::
   :maxdepth: 1
   :titlesonly:
   
   Install
   Examples

**It consists of three "main" decomposition modules**

.. toctree::
   :maxdepth: 1
   :titlesonly:

   nfact_pp
   nfact_decomp
   nfact_dr

**And three auxiliary modules**

.. toctree::
   :maxdepth: 1
   :titlesonly:

   nfact_Qc
   nfact_config
   nfact_stats

**and a pipeline wrapper**

.. toctree::
   :maxdepth: 1
   :titlesonly:

   nfact_pipeline

OHBM 2026 poster
-----------------
.. image:: _static/ohbm_2026.png
   :alt: description
   :class: spaced-figure

NFACT full pipeline
--------------------
.. image:: _static/pipeline.png
   :alt: description
   :class: spaced-figure

.. note::

   Wanting to contribute? Please check out the `contributing <https://github.com/SPMIC-UoN/NFACT/blob/main/CONTRIBUTING.md>`_
