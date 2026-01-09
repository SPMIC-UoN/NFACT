
Inputs
======

Required before running NFACT PP:
    - Crossing-fibre diffusion modelled data (bedpostX)
    - Seeds (either surfaces or volumes)

NFACT PP has three modes: surface , volume, and filestree.

Required input:
    - List of subjects (absolute path)
    - Output directory (absolute path)

Input needed for filetree mode:
    - .tree file (NFACT_PP comes with some defaults for the hcp)

Input needed for both surface and volume mode:
    - Seeds path inside folder (relative path, must be same across subjects)
    - Warps path inside a subjects folder (relative path, must be same across subjects)
    - bedpostx folder path inside a subjects folder (relative path, must be same across subjects)
   
Input for surface seed mode:
    - Seeds as surfaces (relative path, must be same across subjects)
    - ROI as surfaces. This is files to restrict seeding to (for example surface files that exclude medial wall, this is a relative path, must be same across subjects)

Input needed for volume mode:
    - Seeds as volumes (relative path, must be same across subjects)

Warps must be ordered Standard2diff and Diff2standard. If your target fdt paths doesn't match up to the template then it is most likely the warps being the wrong way around.

Optional NFACT_PP inputs:
- A seed reference space to define seed space used by probtrackx. Default is Human MNI. 
- Target image. Can be a whole brain or an ROI. Recommend to downsampled (or else matrix is huge!!) see below for downsampling. Default is seed reference space. 


Input folder
------------


NFACT pp can be used in a folder agnostic way by providing the paths to seeds/bedpostX/target inside a subject folder (i.e --seeds seeds/amygdala.nii.gz).
However, NFACT pp does have an  --absolute option which will treat the seeds (and rois) as absolute paths. This way one set of seeds and rois can be passed to all subjects

Filetrees
^^^^^^^^^^

nfact_pp can accept filetrees via the --file_tree command. The filetree has specific paths for seeds/rois/bedpostx etc in it so that these do not need to be specified when calling nfact_pp. For example:  

.. code-block:: text

    nfact_pp --file_tree hcp --list_of_subjects /home/study/list_of_subjects


nfact_pp prebuilt filetrees:
  - ``hcp``: standard hcp folder structure with seeds as L/R white.32k_fs_LR.surf.gii boundary and atlasroi.32k_fs_LR.shape.gii as rois. stop/wtstop files specified along with high res sphere for downsampling.
  - ``hcp_cifti``: Same as hcp but with subcortical volumes labelled for cifti support (See CIFTI support)

Building custom filetrees 
"""""""""""""""""""""""""

nfact_pp also allows for custom filetrees. These can be passed in by giving the full path to the ``--file_tree``. 

Filetree labels:
  - ``(seed)``: This is complusory and is the filepath to a seed. A seed must also have the following naming structure {sub}.{hemi}.filename.gii/nii.gz
  - ``(bedpostX)``: This is complusory and is the filepath to a bedpostx directory
  - ``(diff2std)``: and (std2diff) Another complusory argument. Relative paths to diff2std and std2diff warp files
  - ``(roi)``: This is complusory for surface mode. Must be named {sub}.{hemi}.filename.gii/nii.gz
  - ``(add_seed1)``, ``(add_seed2)``: etc additional seeds and can have as many as you want, as long as they have a a number suffix at the end. This is used to add cifti structures/subcortical volumes 
  - ``(wtstop1)``, ``(wtstop2)``: etc wtstop files. Again can have as many you want as long as they have a number suffix
  - ``(stop1)``, ``(stop2)``, etc: Stop files. Same as approach as wtstop and add_seed
  - ``(sphere)``: Path to high resolution sphere needed for downsampling surfaces.


Please see https://open.win.ox.ac.uk/pages/fsl/file-tree/index.html for further details on filetrees.

Example file tree
""""""""""""""""""

Below is the HCP filetree for cifti.

.. code-block:: text

  MNINonLinear
    fsaverage_LR32k
        {sub}.{hemi}.atlasroi.32k_fs_LR.shape.gii (roi)
        {sub}.{hemi}.white.32k_fs_LR.surf.gii (seed)
        {sub}.{hemi}.sphere.32k_fs_LR.surf.gii (sphere)
    xfms
        acpc_dc2standard.nii.gz (diff2std)
        standard2acpc_dc.nii.gz (std2diff)
    Results
        Tractography
            CIFTI_STRUCTURE_ACCUMBENS_LEFT.nii.gz (add_seed1)
            CIFTI_STRUCTURE_ACCUMBENS_RIGHT.nii.gz (add_seed2)
            CIFTI_STRUCTURE_AMYGDALA_LEFT.nii.gz (add_seed3)
            CIFTI_STRUCTURE_AMYGDALA_RIGHT.nii.gz (add_seed4)
            CIFTI_STRUCTURE_CAUDATE_LEFT.nii.gz (add_seed5)
            CIFTI_STRUCTURE_CAUDATE_RIGHT.nii.gz (add_seed6)
            CIFTI_STRUCTURE_HIPPOCAMPUS_LEFT.nii.gz (add_seed7)
            CIFTI_STRUCTURE_HIPPOCAMPUS_RIGHT.nii.gz (add_seed8)
            CIFTI_STRUCTURE_PALLIDUM_LEFT.nii.gz (add_seed9)
            CIFTI_STRUCTURE_PALLIDUM_RIGHT.nii.gz (add_seed10)
            CIFTI_STRUCTURE_PUTAMEN_LEFT.nii.gz (add_seed11)
            CIFTI_STRUCTURE_PUTAMEN_RIGHT.nii.gz (add_seed12)
            CIFTI_STRUCTURE_THALAMUS_LEFT.nii.gz (add_seed13)
            CIFTI_STRUCTURE_THALAMUS_RIGHT.nii.gz (add_seed14)
            CIFTI_STRUCTURE_DIENCEPHALON_VENTRAL_LEFT.nii.gz  (add_seed15)
            CIFTI_STRUCTURE_DIENCEPHALON_VENTRAL_RIGHT.nii.gz (add_seed16)
            CIFTI_STRUCTURE_ACCUMBENS_LEFT.nii.gz (wtstop1)
            CIFTI_STRUCTURE_ACCUMBENS_RIGHT.nii.gz (wtstop2)
            CIFTI_STRUCTURE_AMYGDALA_LEFT.nii.gz (wtstop3)
            CIFTI_STRUCTURE_AMYGDALA_RIGHT.nii.gz (wtstop4)
            CIFTI_STRUCTURE_CAUDATE_LEFT.nii.gz (wtstop5)
            CIFTI_STRUCTURE_CAUDATE_RIGHT.nii.gz (wtstop6)
            CIFTI_STRUCTURE_CEREBELLUM_LEFT.nii.gz (wtstop7)
            CIFTI_STRUCTURE_CEREBELLUM_RIGHT.nii.gz (wtstop8)
            CIFTI_STRUCTURE_HIPPOCAMPUS_LEFT.nii.gz (wtstop9)
            CIFTI_STRUCTURE_HIPPOCAMPUS_RIGHT.nii.gz (wtstop10)
            CIFTI_STRUCTURE_PALLIDUM_LEFT.nii.gz (wtstop11)
            CIFTI_STRUCTURE_PALLIDUM_RIGHT.nii.gz (wtstop12)
            CIFTI_STRUCTURE_PUTAMEN_LEFT.nii.gz (wtstop13)
            CIFTI_STRUCTURE_PUTAMEN_RIGHT.nii.gz (wtstop14)
            CIFTI_STRUCTURE_THALAMUS_LEFT.nii.gz (wtstop15)
            CIFTI_STRUCTURE_THALAMUS_RIGHT.nii.gz (wtstop16)
            pial.L.asc (stop1)
            pial.R.asc (stop2)
            white.L.asc (wtstop17)
            white.R.asc (wtstop18)
  T1w
      Diffusion.bedpostX (bedpostX)

Downsampling
==============
Given that decomposition at with high resolution is computationally expensive and may not be beneficial, inputs can be downsampled to lower resolutions. 
nfact_pp has the ability to downsample surfaces and volumes using the ``--downsample`` option. Resolution can be controlled by ``--vertex`` and ``--voxel`` and 
the defaults are 10,000 and 3mm respectively. To downsample nfact_pp needs a filetree specified (see above) and to downsample surfaces a high resolution sphere 
with workbench installed.

NFACT can also downsample the target image using the ``-mm_res`` argument. Current default is 3mm.

**WARNING** If using wtstop and stop files NFACT does not downsample these!

CIFTI support
==============

NFACT can save files as cifti dscalars. However, seeds must be in the following order: left_hemisphere.gii (complusory), right hemisphere.nii (complusory), follwed by optional nifti files as subcortical structures (can also have no subcortical files)

If there are subcortical structures, they must be named as standard cifti structures (i.e CIFTI_STRUCTURE_ACCUMBENS_LEFT.nii.gz) or subcortical data is put as the CIFTI structure OTHER. 

Examples are: 


.. list-table::
   :header-rows: 1
   :widths: 20 15 65

   * - Structure
     - Hemisphere
     - Filename
   * - Accumbens
     - Left
     - ``CIFTI_STRUCTURE_ACCUMBENS_LEFT.nii.gz``
   * - Accumbens
     - Right
     - ``CIFTI_STRUCTURE_ACCUMBENS_RIGHT.nii.gz``
   * - Amygdala
     - Left
     - ``CIFTI_STRUCTURE_AMYGDALA_LEFT.nii.gz``
   * - Amygdala
     - Right
     - ``CIFTI_STRUCTURE_AMYGDALA_RIGHT.nii.gz``
   * - Caudate
     - Left
     - ``CIFTI_STRUCTURE_CAUDATE_LEFT.nii.gz``
   * - Caudate
     - Right
     - ``CIFTI_STRUCTURE_CAUDATE_RIGHT.nii.gz``
   * - Cerebellum
     - Left
     - ``CIFTI_STRUCTURE_CEREBELLUM_LEFT.nii.gz``
   * - Cerebellum
     - Right
     - ``CIFTI_STRUCTURE_CEREBELLUM_RIGHT.nii.gz``
   * - Hippocampus
     - Left
     - ``CIFTI_STRUCTURE_HIPPOCAMPUS_LEFT.nii.gz``
   * - Hippocampus
     - Right
     - ``CIFTI_STRUCTURE_HIPPOCAMPUS_RIGHT.nii.gz``
   * - Pallidum
     - Left
     - ``CIFTI_STRUCTURE_PALLIDUM_LEFT.nii.gz``
   * - Pallidum
     - Right
     - ``CIFTI_STRUCTURE_PALLIDUM_RIGHT.nii.gz``
   * - Putamen
     - Left
     - ``CIFTI_STRUCTURE_PUTAMEN_LEFT.nii.gz``
   * - Putamen
     - Right
     - ``CIFTI_STRUCTURE_PUTAMEN_RIGHT.nii.gz``
   * - Thalamus
     - Left
     - ``CIFTI_STRUCTURE_THALAMUS_LEFT.nii.gz``
   * - Thalamus
     - Right
     - ``CIFTI_STRUCTURE_THALAMUS_RIGHT.nii.gz``


HPC clusters
==============
NFACT can directly submit jobs to high performance computing enviorments and monitor queues to let you know when they are finished. 
Cluster arguments require ``--cluster`` and a queue to submit to via ``--cluster_qos``. 
This will make NFACT search for a HPC cluster enviorment and the queue to check that NFACT can submit to the cluster. 
NFACT by default allocates time and ram to the job, however, these may need to be changed depending on the data by the ``--cluster_ram`` and ``--cluster_time`` arguments.


Usage
======


.. code-block:: text

  nfact_pp [-h] [-hh] [-O] [-l LIST_OF_SUBJECTS] [-o OUTDIR] [-G] [-D] 
  [-vx VERTEX] [-vl VOXEL] [-f FILE_TREE] [-s SEED [SEED ...]] [-w WARPS [WARPS ...]] 
  [-b BPX_PATH] [-r ROI [ROI ...]] [-sr SEEDREF] [-t TARGET2] [-ns NSAMPLES] 
  [-mm MM_RES] [-p PTX_OPTIONS] [-e EXCLUSION] [-S [STOP ...]] [-A] [-F] 
  [-n N_CORES] [-C] [-cq CLUSTER_QUEUE] [-cr CLUSTER_RAM] [-ct CLUSTER_TIME] 
  [-cqos CLUSTER_QOS]
 
   

Options
""""""""

General options:
  -h, --help 
    Show help message
  -hh, --verbose_help 
    Verbose help message. Prints help message and example usages
  -O, --overwrite 
    Overwrites previous file structure
  -G, --gpu 
    To use the GPU version of probtrackx2.

Set Up options:
  -l, --list_of_subjects 
    Filepath to a list of subjects
  -o, --outdir 
    Path to output directory

Downsample options:
  -D, --downsample 
    Should the seeds be downsampled. Sufaces need workbench installed to work. Default is False
  -vx, --vertex 
    Value to downsample vertexes in a single suface seed to. Default is 10,000.
  -vl, --voxel 
    Value to downsample voxels in volume seeds to. Default is 3mm.

Filetree option:
  -f, --file_tree 
    Use this option to provide name of a predefined file tree to perform whole brain tractography. nfact_pp currently comes with a number of HCP filetrees, or can accept a custom filetree (provide abosulte path).

Tractography options:
  -s, --seed 
    Relative path to either a single or multiple seeds. If multiple seeds given then include a space between paths. Path to file must be the same across subjects.
  -w, --warps 
    Relative path to warps inside a subjects directory. Include a space between paths. Path to file must be the same across subjects. Expects the order as Standard2diff and Diff2standard.
  -b, --bpx 
    Relative path to Bedpostx folder inside a subjects directory. Path to file must be the same across subjects.
  -r, --roi 
    REQUIRED FOR SURFACE MODE: Relative path to a single ROI or multiple ROIS to restrict seeding to (e.g. medial wall masks). Must be the same across subject. ROIS must match number of seeds.
  -sr, --seedref 
    Absolute path to a reference volume to define seed space used by probtrackx, default is MNI space MNI152 T1w 2mm.
  -t, --target 
    Absolute path to a target image. If not provided will use the seedref.
  -ns, --nsamples 
    Number of samples per seed used in tractography, default is 1000.
  -mm, --mm_res 
    Resolution of target image. Default is 3 mm.
  -p, --ptx_options 
    Path to ptx_options file for additional options. Doesn't override defaults.
  -e, --exclusion 
    Absolute path to an exclusion mask. Will reject pathways passing through locations given by this mask.
  -S, --stop 
    Use wtstop and stop in the tractography. Takes an absolute file path to a json file containing stop and wtstop masks, JSON keys must be stopping_mask and wtstop_mask. Argument can be used with the --filetree, in that case no json file is needed.
  -A, --absolute 
    Treat seeds and rois as absolute paths, providing one set of seeds and rois for tractography across all subjects.
  -F, --dont_save_fdt_img 
    Don't save the fdt path as a nifti file. This is useful to save space.

Parallel Processing option:
  -n N_CORES, --n_cores 
    If should parallel process locally and with how many cores. This parallelizes the number of subjects. If n_cores exceeds subjects nfact_pp sets this argument to be the number of subjects. If nfact_pp is being used on one subject then this may slow down processing.

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
"""""""""""""""""""
Surface mode:
  .. code-block:: text

    nfact_pp --list_of_subjects /absolute_path/study/sub_list
        --outdir absolute_path/study
        --bpx_path /relative_path/.bedpostX
        --seeds /relative_path/L.surf.gii /path_to/R.surf.gii
        --roi /relative_path/L.exclude_medialwall.shape.gii /path_to/R.exclude_medialwall.shape.gii
        --warps /relative_path/stand2diff.nii.gz /relative_path/diff2stand.nii.gz
        --n_cores 3

Volume mode:
  .. code-block:: text

    nfact_pp --list_of_subjects /absolute_path/study/sub_list
        --outdir /absolute_path/study
        --bpx_path /relative_path/.bedpostX
        --seeds /relative_path/L.white.nii.gz /relative_path/R.white.nii.gz
        --warps /relative_path/stand2diff.nii.gz /relative_path/diff2stand.nii.gz
        --seedref absolute_path/MNI152_T1_1mm_brain.nii.gz
        --target absolute_path/dlpfc.nii.gz

Filestree mode:
   .. code-block:: text
    
    nfact_pp --filestree hcp
        --list_of_subjects /absolute_path/study/sub_list
        --outdir /absolute_path/study

