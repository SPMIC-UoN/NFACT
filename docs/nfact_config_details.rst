Overview
=========

NFACT config can create:
1. nfact_config.pipeline overview. This config JSON file is used in the nfact pipeline to have greater control over parameters.  
2. nfact_config.decomp. A config JSON file to control the hyper-parameters of the ICA and NMF functions.
3. nfact_config.sublist. A list of subjects(text file) in a folder. 

Additionally NFACT config can zip the fdt_matrix.dot files in the nfact_pp directory to save on space.

Pipeline configuration file
===========================

This is the config file for the nfact pipeline. 
Everything that says required must be given. Boolean arguments (true & false) must be given in lowercase not in strings

Rois, warps and seed must be given in python list format like this ``"seed": ["l_seed.nii.gz", "r_seed.nii.gz"]`` unless a filetree is used.

Please check the individual modules for further details on arguments.

.. code-block:: json

  {
      "global_input": {
          "list_of_subjects": "Required",
          "outdir": "Required",
          "seed": [
              "Required unless file_tree specified"
          ],
          "overwrite": false,
          "pp_skip": false,
          "dr_skip": false,
          "qc_skip": false,
          "folder_name": "nfact"
      },
      "cluster": {
          "cluster": false,
          "cluster_queue": "None",
          "cluster_ram": "60",
          "cluster_time": false,
          "cluster_qos": false
      },
      "nfact_pp": {
          "gpu": false,
          "file_tree": false,
          "warps": [],
          "bpx_path": false,
          "roi": [],
          "seedref": false,
          "target2": false,
          "nsamples": "1000",
          "mm_res": "3",
          "ptx_options": false,
          "exclusion": false,
          "stop": false,
          "absolute": false,
          "dont_save_fdt_img": false,
          "n_cores": false
      },
      "nfact_decomp": {
          "dim": "Required",
          "algo": "NMF",
          "roi": false,
          "config": false,
          "iterations": "20",
          "n_cores": "1",
          "no_sso": false,
          "cifti": false,
          "disk": false,
          "wta": false,
          "wta_zthr": "0.0",
          "normalise": false,
          "threshold": "3",
          "components": "1000",
          "pca_type": "pca",
          "sign_flip": true
      },
      "nfact_dr": {
          "normalise": false,
          "cifti": false,
          "threshold": "3",
          "n_cores": false
      },
      "nfact_qc": {
          "threshold": "2"
      }
  }

Decomposition configuration file
================================
NFACT does its decomposition using sckit-learn's NMF (https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.NMF.html) and FastICA (https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.FastICA.html).
Any of the hyperparameters of these functions can be altered by changing the values in the JSON file.

.. code-block:: json

  {
    "ica": {
        "algorithm": "parallel",
        "whiten": "unit-variance",
        "fun": "logcosh",
        "fun_args": null,
        "max_iter": 200,
        "tol": 0.0001,
        "w_init": null,
        "whiten_solver": "svd",
        "random_state": null
    },
    "nmf": {
        "init": null,
        "solver": "cd",
        "beta_loss": "frobenius",
        "tol": 0.0001,
        "max_iter": 200,
        "random_state": null,
        "alpha_W": 0.0,
        "alpha_H": "same",
        "l1_ratio": 0.0,
        "verbose": 0,
        "shuffle": false
    }
  }

Subject lists
==============

NFACT config will attempt to given a directory work out and write to a file all the subjects in that file. Though nfact will try and filter out 
folders that aren't subjects, it isn't perfect so please check the subject list.

NFACT config will also from the file path work out what type of subject list to create. If it is ran within the nfact_pp directory
if will add /omatrix2 onto the file path so this subject list can be used for decomposition. If it is ran within the nfact_dr/NMF directory
if will get the subjects from those files.

.. code-block:: text

    nfact_config -s /path/to/subs/dir

Zipping fdt matrix2
====================
The main output from NFACT Pre-processing is the fdt_matrix2.dot file which can be very large. nfact_config is able to zip this file into a lz4 file to significantly save on space.
NFACT is able to read the zipped files, however it may add to processing time. 

To zip files::

  nfact_config -z /path/to/nfact_pp

Usage
=====

.. code-block:: text
    
    nfact_config [-h] [-C] [-D] [-s SUBJECT_LIST] [-z ZIP] [-o OUTPUT_DIR] [-f FILE_NAME]

options:
  -h, --help 
    Shows help message
  -C, --config 
    Creates a config file for NFACT pipeline
  -D, --decomp_only 
    Creates a config file for hyperparameters for the NMF/ICA
  -s, --subject_list 
    Creates a subject list from a given directory Needs path to subjects directory. If ran inside an nfact_pp directory will make a subject list for decompoisition (adds on omatrix2 to file paths)
  -z, --zip 
    Zip fdt matrices from nfact_pp to save space. Needs a path to a nfact_pp directory
  -o, --output_dir 
    File path of where to save config file
  -f, --file_name 
    Name of the nfact config filename. Defaults is nfact_config