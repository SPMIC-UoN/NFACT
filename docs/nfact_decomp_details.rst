
How nfact_decomp does decomposition 
====================================

NFACT uses an iterative NMF process, where several NMFs (usually 20) are ran to avoid local optimas and ensure robustness. This process is called SSO (taken by icasso). The ouput is then clustered and the results used to initiate a final NMF.
NFACT provides information on this clusters so that uses can explore robustness of connectivity patterns.

Output
======

Decomposition patterns are saved as ``W_`` (white matter decomposition) ``G_`` (grey matter decompostion). 
White matter components are saved as nii.gz while grey matter decompositions are saved depending on seed type.
Multiple ``W_`` and ``G_`` can be saved in the decomp folder assuming that the number of dimensions differs between what is already saved. i.e running nfact_decomp with ``--dim 100`` will save a W_NMF_dim100.nii.gz. If nfact_decomp ``--dim 50`` is ran then a W_NMF_dim50.nii.gz will also be saved. However, if nfact_decomp ``--dim 100`` is run again it will overwrite the orginal file.

SSO ouput
""""""""""
The iterative process produces a number of output files so users can interrogate output.

Outputs:
    - similarity_matrix.tiff: A heatmap of components similairty
    - dissimilarity_matrix.tff: A heatmap of components dis-similairty 
    - cluster_stats.tiff: Plots of stability score of clusters and number of components in a cluster
    - cluster_stats.csv: Stability score, number of components in a cluster and cluster number in csv format
    - cluster_network.tiff: Clusters projected to a 2D plane. 
      Pale red is centroid of component of cluster, blue is components, grey is edges between all cluster and black are edges in the top 95th centile. Red lines indicate which components belong wo which cluster.

Other save options
------------------
Components can also be saved directly as .npz files by giving the ``--disk``` argument. 
The grey component can be saved as a cifti as long as seeds are named in a set way (see `CIFTI support <nfact_pp_details.html#cifti-support>`_). 

If saving failed
------------------
By default if nfact_decomp can't save decomposition to imaging files then they will be saved to disk.
If nfact_decomp can't save files as ciftis (assuming the ``-cifti`` is given) then it will save files as corresponding gii/nii files depending on seed type.


Other decomposition options 
===========================
By default nfact_decomp will threshold components to remove noise. nfact_decomp will consider noise values less than a zscore value (default is 3). 
In some cases this might be too liberal and might need to be adjusted or turned  off by the ``-t``, ``--threshold``

White and Grey matter connectivity components can also be normalised with the zscore maps saved, which is useful for visualization. Normalised output coverts output into z-scores
Winner takes all maps can be created with the brain represented by which components are the "winner" in that region. 

GPU acceleration
================
NFACT decomp supports GPUs to speed up the process using torchnmf. This is done using the ``-G``, ``--gpu`` argument.
Depedning on your CUDA environment you might need to install a version of pytorch that supports your CUDA version. See `pytorch website <https://pytorch.org/get-started/locally/>`_ for more information.

**NOTE**
The FDT matrix can be really big (GBs). If running with GPU, and getting errors about memory errors then try and specify a GPU that has larger memory limits by setting the env varible `CUDA_VISIBLE_DEVICES` to a specific GPU. 
If this doesn't work or there isn't a bigger GPU memory, try reducing the number of components (``--dim``, ``-d``) or consider re running the nfact_pp with lower resolution seeds/target and less seeds. 
If neither of these are possible, and you are running sso, try parallelization (``--n_cores``, ``-n``) to distribute the work over multiple CPUs/ reduce the number of iterations. 

Usage
=====

.. code-block:: text

    nfact_decomp [-h] [-hh] [-O] [-l LIST_OF_SUBJECTS][-o OUTDIR] [-G] [--seeds SEEDS] 
    [--roi ROI] [-f CONFIG] [-a ALGO] [-d DIM] [-i ITERATIONS] [-n N_CORES] 
    [-X NO_SSO] [-C] [-D] [-W] [-z WTA_ZTHR] [-N] [-t THRESHOLD] [-c COMPONENTS]
    [-p PCA_TYPE] [-S]

General Options:
  -h, --help 
    Shows help message and exit
  -hh, --verbose_help 
    Verbose help message. Prints help message and example usages
  -O, --overwrite 
    Overwrites previous file structure

Set Up options:
  -l, --list_of_subjects 
    Filepath to a list of subjects
  -o, --outdir 
    Path to output directory

Decomposition inputs:
  -G, --gpu
    Use GPU for NMF decomposition
  -s, --seeds 
    Absolute path to a text file of seed(s) used in nfact_pp/probtrackx. If used nfact_pp this is the seeds_for_decomp.txt in the nfact_pp directory.
  -r, --roi 
    Absolute path to a text file containing the absolute path ROI(s) paths to restrict seeding to (e.g. medial wall masks). This is not needed if seeds are not surfaces. 
    If used nfact_pp then this is the roi_for_decomp.txt file in the nfact_pp directory.
  -m, --matrix 
    Absolute path to a previously averaged group folder. NFACT will use this matrix, average_matrix2, coords_for_fdt_matrix2, tract_space_coords and lookup_tractspace.nii.gz files in the decomposition.
  -f, --config_file 
    Absolute path to a configuration file. Congifuration file provides available hyperparameters for ICA and NMF. 
    Use nfact_config -D to create a config file. Please see sckit learn documentation for NMF and FASTICA for further details

Decomposition options:
  -a, --algo 
    Which decomposition algorithm. Options are: NMF (default), or ICA. This is case insensitive
  -d, --dim 
    Number of dimensions to retain after running NMF/ICA. If using NMF-sso the dimensions of the final analysis
    won't be this. Default is 200 as this provides the best coverage for whole brain seeds. May not work for all data
  -i, --iterations 
    Number of iterations of NMF for the NMF-sso. Default is 20
  -n, --n_cores 
    To parallelize NMF-sso and with how many cores. Default is not to.
  -w  --wm_matrix 
    Previous wm matrix to initiate NMF with. Default is false (see sckit learn NMF for further details on initialisation). If this option is given then --gm_matrix needed.
  -g, --gm_matrix 
    Previous gm matrix to initiate NMF with. Default is false (see sckit learn NMF for further details on initialisation). If this option is given then --wm_matrix needed.
  -X, --exclude_sso 
    Don't do NMF-sso. Just do a single NMF. Default is False

Output options:
  -C, --cifti 
    Option to save GM as a cifti dscalar. Seeds must be left and right surfaces with an optional nifti for subcortical structures.
  -D, --disk 
    Save the decomposition matrices directly to disk rather than as nii/gii files
  -W, --wta 
    Option to create and save winner-takes-all maps.
  -z, --wta_zthr 
    Winner-takes-all threshold. Default is 0
  -N, --normalise 
    Convert component values into Z scores and saves map. This is useful for visualization
  -t, --threshold 
    Value at which to threshold Components at. Default is to not do thresholding.
  -CS, --cluster_save 
    When doing sso save each cluster as nifti/gifti/cifti as 4D files with each 4D point as a single NMF run
  -I, --initialisation_matrices 
    Option to save initialisation matrices


ICA options:
  -c, --components 
    Number of component to be retained following the PCA. Default is 1000
  -p, --pca_type 
    Which type of PCA to do before ICA. Options are 'pca' which is sckit learns default PCA or 'migp' 
    (MELODIC's Incremental Group-PCA dimensionality). Default is 'pca' as for most cases 'migp' is slow and not needed. Option is case insensitive.
  -S, --sign_flip 
    nfact_decomp by default sign flips the ICA distribution to reduce the number of negative values. Use this option to stop the sign_flip.

Example Usage
--------------

Basic NMF with volume seeds usage:
  .. code-block:: text

    nfact_decomp --list_of_subjects /absolute path/sub_list \
                 --seeds /absolute path/seeds.txt \


Basic NMF usage with surface seeds:
  .. code-block:: text
    
    nfact_decomp --list_of_subjects /absolute path/sub_list \
                 --seeds /absolute path/seeds.txt \
                 --roi /absolute path/rois

NMF usage with surface seeds with different dims and reduced NMF-sso iterations:
  .. code-block:: text

    nfact_decomp --list_of_subjects /absolute path/sub_list \
                 --seeds /absolute path/seeds.txt \
                 --roi /absolute path/rois
                 --dim 50
                 --iterations 10

ICA with config file usage:
  .. code-block:: text

    nfact_decomp --list_of_subjects /absolute path/sub_list \
                 --seeds /absolute path/seeds.txt \
                 --outdir /absolute path/study_directory \
                 --algo ICA \
                 --nfact_config /absolute path/nfact_config.decomp

Advanced ICA Usage:
  .. code-block:: text

    nfact_decomp --list_of_subjects /absolute path/sub_list \
                 --seeds /absolute path/seeds.txt \
                 --outdir /absolute path/study_directory \
                 --algo ICA \
                 --components 1000 \
                 --pca_type mipg
                 --dim 100 \
                 --normalise \
                 --wta \
                 --wta_zthr 0.5