Overview
=========

This pipleine runs pre-processing, group level decomposition, quality control and dual regression on data ready for processing.
It is fully customisable by the `configuration file <nfact_config_details.html#pipeline-configuration-filet>`_ or can be run using command line arguments.

Please see :doc:`nfact_pp`, :doc:`nfact_decomp`, :doc:`nfact_Qc` and :doc:`nfact_dr` for further details


Usage
======

.. code-block:: text

    nfact [-h] [-l LIST_OF_SUBJECTS] [-s SEED [SEED ...]] [-o OUTDIR] 
    [-n FOLDER_NAME] [-c CONFIG] [-P] [-Q] [-D] [-O] [-w WARPS [WARPS ...]] 
    [-b BPX_PATH] [-r ROI [ROI ...]] [-f FILE_TREE] [-sr SEEDREF] [-t TARGET2] 
    [-d DIM] [-a ALGO] [-rf ROI] [--threshold THRESHOLD]

General Options:
  -h, --help 
    Shows help message and exit

Pipeline inputs:
  -l, --list_of_subjects 
    Absolute filepath to a text file containing absolute path to subjects. Consider using nfact_config to create subject list.
  -s, --seed 
    Relative path to either a single or multiple seeds. If multiple seeds given then include a space between paths. Must be the same across subjects.
  -o, --outdir 
    Absolute path to a directory to save results in.
  -n, --folder_name 
    Name of output folder. That contains within it the nfact_pp, nfact_decomp and nfact_dr folders. Default is nfact
  -c, --config 
    Provide an nfact_config file instead of using command line arguements. Configuration files provide control over all parameters of modules and can be created using nfact_config -C. 
    If this is provided no other arguments are needed to run nfact as arguments are taken from config file rather than command line.
  -P, --pp_skip 
    Skips nfact_pp. Pipeline still assumes that data has been pre-processed with nfact_pp before. If data hasn't been pre-processed with nfact_pp consider runing modules seperately
  -Q, --qc_skip 
    Skips nfact_Qc.
  -D, --dr_skip 
    Skips nfact_dr so no dual regression is performed.
  -O, --overwrite 
    Overwirte existing file structure

nfact_pp inputs:
  -w, --warps 
    Relative path to warps inside a subjects directory. Include a space between paths. Must be the same across subjects.
  -b, --bpx 
    Relative path to Bedpostx folder inside a subjects directory. Must be the same across subjects
  -r, --roi 
    REQUIRED FOR SURFACE MODE: Relative path to a single ROI or multiple ROIS to restrict seeding to (e.g. medial wall masks). Must be the same across subject. ROIS must match number of seeds.
  -f, --file_tree 
    Use this option to provide name of predefined file tree to perform whole brain tractography. nfact_pp currently comes with HCP filetree. See documentation for further information.
  -sr, --seedref 
    Absolute path to a reference volume to define seed space used by probtrackx. Default is MNI152 T1 2mm.
  -t, --target 
    Absolute path to a target image. If not provided will use the seedref. 

nfact_decomp/nfact_dr inputs:
  -d, --dim 
    This is compulsory option. Number of dimensions/components to retain after running NMF/ICA.
  -a, --algo 
    Which decomposition algorithm to run. Options are: NMF (default), or ICA. This is case insensitive
  -rf, --rf_decomp 
    Absolute path to a text file containing the absolute path ROI(s) paths to restrict seeding to (e.g. medial wall masks). This is not needed if seeds are not surfaces. 
    If used nfact_pp then this is the roi_for_decomp.txt file in the nfact_pp directory. This option is not needed if the pipeline is being ran from nfact_pp onwards.

nfact_Qc inputs:
  --threshold
    Z score value to threshold hitmaps.


Example Usage
-------------

From command line::

  nfact --list_of_subject /absolute path/sub_list \
  --seed thalamus.nii.gz \
  --algo NMF \
  --dim 100 \
  --outdir /absolute path/save directory \
  --warps standard2acpc_dc.nii.gz acpc_dc2standard.nii.gz \
  --ref $FSLDIR/data/standard/MNI152_T1_2mm_brain.nii.gz \
  --bpx Diffusion.bedpostX 


With a config file::

    nfact –config /absolute path/nfact_config.config  
