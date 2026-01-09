Overview
=========
Which type of decomposition technique dictates  which dual regression technique will be used. 
To maintain non negativity in an NMF decomposition NFACT will use non-negative least squares regression. If ICA then it will be a least-squares regression.

Basic usage
===========

CIFTIs
-------
Similar to nfact_decomp nfact_dr can save components as cifti dscalars as well as accept cifti dscalars as inputs. 

Please see  `CIFTI support <nfact_pp_details.html#cifti-support>`_.

nfact_dr without nfact_decomp
------------------------------
nfact_dr can be ran independent from nfact_decomp, however, nfact_decomp expects a strict naming convention of files. 

The following files **MUST** be present and named like this:
  - Group components: ``W_dim`` and ``G_dim`` followed by the number of dimensions. For example ``W_NMF_dim50.nii.gz`` and ``G_NMF_dim50.dscalar.nii`` 
  - Output of probtrackx: Single files for ``coords_for_fdt_matrix2``, ``lookup_tractspace_fdt_matrix2.nii.gz`` and ``tract_space_coords_for_fdt_matrix2``

These files **MUST** be in a single folder

HPC
===
nfact_dr jobs can be sent to a high performance computing cluster. Please see `HPC clusters <nfact_pp_details.html#hpc-clusters>`_.

What is unquie about nfact_dr is it can submit jobs to a HPC cluster and parallel the dual regression within a job. 
The job sumitted is the individual subject but the dual regression within that subject can be parallelized.



Usage
=====

.. code-block:: text

    nfact_dr [-h] [-hh] [-O] [-l LIST_OF_SUBJECTS] [-o OUTDIR] [-a ALGO] [--seeds SEEDS] 
    [--roi ROI] [-d NFACT_DECOMP_DIR] [-dd DECOMP_DIR] [-N] [-D] [-n N_CORES] 
    [-C] [-cq CLUSTER_QUEUE] [-cr CLUSTER_RAM] [-ct CLUSTER_TIME] [-cqos CLUSTER_QOS]



General options:
  -h, --help 
    Show help message
  -hh, --verbose_help 
    Verbose help message. Prints help message and example usages
  -O, --overwrite 
    Overwrites previous file structure

Set Up options:
  -l, --list_of_subjects 
    Filepath to a list of subjects
  -o, --outdir 
    Path to output directory

Dual Regression options:
  -a, --algo 
    Which decomposition algorithm. Options are: NMF (default), or ICA. This is case insensitive.
  -s, --seeds 
    Absolute path to a text file of seed(s) used in nfact_pp/probtrackx. If used nfact_pp this is the seeds_for_decomp.txt in the nfact_pp directory.
  -r, --roi 
    Absolute path to a text file containing the absolute path ROI(s) paths to restrict seeding to (e.g. medial wall masks). This is not needed if seeds are not surfaces. If used nfact_pp then this is the roi_for_decomp.txt file in the nfact_pp directory.
  -d, --nfact_decomp_dir 
    Filepath to the NFACT_decomp directory. Use this if you have ran NFACT decomp.
  -dd, --decomp_dir 
    Filepath to decomposition directory if not using nfact_decomp.
  -N, --normalise 
    Normalise components by scaling.
  -D, --dscalar 
    Save GM as cifti dscalar. Seeds must be left and right surfaces with an optional nifti for subcortical structures

Parallel Processing options:
  -n, --n_cores 
    To parallelize dual regression

Cluster options:
  -C, --cluster 
    Use cluster enviornment
  -cq, --queue 
    Cluster queue to submit to
  -cr, --cluster_ram 
    Ram that job will take. Default is 60
  -ct, --cluster_time 
    Time that job will take. nfact will assign a time if none given
  -cqos, --cluster_qos 
    Set the qos for the cluster

Example Usage
--------------


Basic usage:
  .. code-block:: text

    nfact_dr --list_of_subjects /path/to/nfact_config_sublist \
        --seeds /path/to/seeds.txt \
        --nfact_decomp_dir /path/to/nfact_decomp \
        --outdir /path/to/output_directory \
        --algo NMF

ICA Dual regression usage:
  .. code-block:: text

    nfact_dr --list_of_subjects /path/to/nfact_config_sublist \
        --seeds /path/to//seeds.txt \
        --nfact_decomp_dir /path/to/nfact_decomp \
        --outdir /path/to/output_directory \
        --algo ICA

Dual regression with roi seeds usage:
  .. code-block:: text

    nfact_dr --list_of_subjects /path/to/nfact_config_sublist \
        --seeds /path/to/seeds.txt \
        --nfact_decomp_dir /path/to/nfact_decomp \
        --outdir /path/to/output_directory \
        --roi /path/to/roi.txt \
        --algo NMF
