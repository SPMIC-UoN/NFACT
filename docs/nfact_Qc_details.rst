Overview
=========
Each map contains the number of times that voxel/vertex appears in the decomposition. 
This is then saved as a hitmap with each voxel/vertex containing the number of times a component value is in that voxel or as a binary mask to demonstrate coverage.

Output
========
Output depends on what imging files are present in the decomp directory. As a minimum (due to how nfact works) there will be a nii.gz file. 
However, depending on if the grey component is nii.gz/gii/.dscalar.nii this will depend on the output.

Prefix:
  - ``hitmap_*.nii.gz``: Volume nii component. Components are not thresholded 
  - ``hitmap_threshold*_.nii.gz``: Volume nii component. Components are thresholded by zscoring to remove noise
  - ``mask_*.nii.gz: Volume nii component``. Binary mask of unthresholded components    
  - ``mask_threshold*.nii.gz``: Volume nii component. Binary mask of thresholded components
  - ``*.gii``: Surface gii component. Components are not thresholded
  - ``threshold_*.gii``: Surface gii component. Components are thresholded by zscoring to remove noise
  - ``*.dscalar.nii``: Cifti component, not thresholded 
  - ``threshold_*.dscalar.nii``: Cifti component. Components are thresholded by zscoring to remove noise


Note on output
--------------
If nfact_decomp has been run with thresholding then look at the _raw files as noise should have been filtered out. 
However, if not thresholding has been done at the decomp stage then look at the threshold images as this is a more accurate view of how many times a connectivity pattern at that vertex or voxel actually appears

Usage
========

.. code-block:: text
    
    nfact_Qc [-h] [-n NFACT_FOLDER] [-d DIM] [-a ALGO] [-t THRESHOLD] [-O]

NFACT QC options:
  -h, --help 
    Show help message
  -n, --nfact_folder 
    REQUIRED: Absolute path to nfact_decomp output folder. nfact_Qc folder is also saved within this folder.
  -d, --dim 
    REQUIRED: Number of dimensions/components that was used to generate nfact_decomp image
  -a, --algo 
    REQUIRED: Which algorithm to run qulatiy control on. Options are: NMF (default), or ICA.
  -t, --threshold 
    Threshold value for z scoring the number of times a component comes up in a voxel in the image. 
    Values below this z score are treated as noise and discarded in the non raw image.
  -O, --overwrite 
    Overwite previous QC
