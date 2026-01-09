import argparse
from NFACT.base.utils import colours, no_args, verbose_help_message
from NFACT.base.base_args import (
    cluster_args,
    parallel_args,
    set_up_args,
    base_arguments,
)


def nfact_pp_args() -> dict:
    """
    Function to get arguements
    to run NFACT pre-processing

    Parameters
    -----------
    None

    Returns
    -------
    dict: dictionary object
        dict of arguments
    """
    base_args = argparse.ArgumentParser(
        prog="nfact_pp",
        description=print(nfact_pp_splash()),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    col = colours()
    base_arguments(base_args)
    set_up_args(base_args, col)
    base_args.add_argument(
        "-G",
        "--gpu",
        dest="gpu",
        action="store_true",
        default=False,
        help="""
        To use the GPU version of probtrackx2.
        """,
    )

    downsample_input = base_args.add_argument_group(
        f"{col['lav']}Downsample options{col['reset']}"
    )
    downsample_input.add_argument(
        "-D",
        "--downsample",
        dest="downsample",
        action="store_true",
        default=False,
        help="""Should the seeds be downsampled. Sufaces need workbench installed to work.
        Default is False""",
    )
    downsample_input.add_argument(
        "-vx",
        "--vertex",
        dest="vertex",
        default=10000,
        help="Value to downsample vertexes in a single suface seed to. Default is 10,000.",
    )
    downsample_input.add_argument(
        "-vl",
        "--voxel",
        dest="voxel",
        default=3,
        help="Value to downsample voxels in volume seeds to. Default is 3mm.",
    )
    file_tree_input = base_args.add_argument_group(
        f"{col['plum']}Filetree option{col['reset']}"
    )
    file_tree_input.add_argument(
        "-f",
        "--file_tree",
        dest="file_tree",
        default=False,
        help="""Use this option to provide name of a predefined file tree to 
        perform whole brain tractography. nfact_pp currently comes with a number of HCP filetrees,
        or can accept a custom filetree (provide abosulte path) 
        See documentation for further information.""",
    )
    tractography_input = base_args.add_argument_group(
        f"{col['pink']}Tractography options{col['reset']}"
    )
    tractography_input.add_argument(
        "-s",
        "--seed",
        nargs="+",
        dest="seed",
        help="""
        Relative path to either a single or multiple seeds. If multiple seeds given
        then include a space between paths. Path to file must be the same across subjects.
        """,
    )
    tractography_input.add_argument(
        "-w",
        "--warps",
        dest="warps",
        nargs="+",
        help="""Relative path to warps inside a subjects directory. 
        Include a space between paths. Path to file must be the same across subjects.
        Expects the order as Standard2diff and Diff2standard.
        """,
    )
    tractography_input.add_argument(
        "-b",
        "--bpx",
        dest="bpx_path",
        help="""Relative path to Bedpostx folder inside a subjects directory. 
        Path to file must be the same across subjects""",
    )
    tractography_input.add_argument(
        "-r",
        "--roi",
        dest="roi",
        nargs="+",
        help="""REQUIRED FOR SURFACE MODE: 
        Relative path to a single ROI or multiple ROIS to restrict seeding to (e.g. medial wall masks). 
        Must be the same across subject. ROIS must match number of seeds.
        """,
    )
    tractography_input.add_argument(
        "-sr",
        "--seedref",
        dest="seedref",
        default=False,
        help="""
        Absolute path to a reference volume to define seed space used by probtrackx. 
        Default is MNI space ($FSLDIR/data/standard/MNI152_T1_2mm.nii.gz).
        """,
    )
    tractography_input.add_argument(
        "-t",
        "--target",
        dest="target2",
        default=False,
        help="""
        Absolute path to a target image. 
        If not provided will use the seedref.
        """,
    )
    tractography_input.add_argument(
        "-ns",
        "--nsamples",
        dest="nsamples",
        default=1000,
        help="Number of samples per seed used in tractography. Default is 1000",
    )
    tractography_input.add_argument(
        "-mm",
        "--mm_res",
        dest="mm_res",
        default=3,
        help="""
        Resolution of target image. 
        Default is 3 mm
        """,
    )
    tractography_input.add_argument(
        "-p",
        "--ptx_options",
        dest="ptx_options",
        help="""
        Path to ptx_options file for additional options. 
        Currently doesn't override defaults
        """,
        default=False,
    )

    tractography_input.add_argument(
        "-e",
        "--exclusion",
        dest="exclusion",
        default=False,
        help="""
        Absolute path to an exclusion mask. 
        Will reject pathways passing through locations given by this mask
      """,
    )
    tractography_input.add_argument(
        "-S",
        "--stop",
        dest="stop",
        default=False,
        nargs="*",
        help="""
        Use wtstop and stop in the tractography. 
        Takes an absolute file path to a json file containing stop and wtstop masks, JSON keys must be stopping_mask and wtstop_mask.
        Argument can be used with the --filetree, in that case no json file is needed.
      """,
    )
    tractography_input.add_argument(
        "-A",
        "--absolute",
        action="store_true",
        default=False,
        dest="absolute",
        help="""
        Treat seeds and rois as absolute paths, 
        providing one set of seeds and rois for tractography
        across all subjects.
        """,
    )
    tractography_input.add_argument(
        "-F",
        "--fdt_img",
        action="store_true",
        default=False,
        dest="dont_save_fdt_img",
        help="""
        Don't save the fdt path as a nifti file. This is useful to save space
        """,
    )
    parallel_args(
        base_args,
        col,
        """
                  If should parallel process locally and with how many cores. 
                  This parallelizes the number of subjects. If n_cores exceeds
                  subjects nfact_pp sets this argument to be the number of subjects. 
                  If nfact_pp is being used on one subject then this may slow down
                  processing.
                  """,
    )
    cluster_args(base_args, col)

    no_args(base_args)
    args = base_args.parse_args()
    if args.verbose_help:
        verbose_help_message(base_args, nfact_pp_example_usage())

    return vars(args)


def nfact_pp_splash() -> str:
    """
    Function to return NFACT splash

    Parameters
    ----------
    None

    Returns
    -------
    str: splash
    """
    col = colours()
    return f"""
{col["pink"]} 
 _   _ ______   ___   _____  _____     ______ ______ 
| \ | ||  ___| /   \ /  __ \|_   _|    | ___ \| ___ \\
|  \| || |_   / /_\ \| /  \/  | |      | |_/ /| |_/ /
|     ||  _|  |  _  || |      | |      |  __/ |  __/ 
| |\  || |    | | | || \__/\  | |      | |    | |    
\_| \_/\_|    \_| |_/ \____/  \_/      \_|    \_|  
{col["reset"]} 
"""


def nfact_pp_example_usage() -> str:
    """
    Function to return example usage

    Parameters
    ----------
    None

    Returns
    -------
    str: str object
    """
    col = colours()
    return f"""
Example Usage:
    {col["purple"]}Surface mode:{col["reset"]}
           nfact_pp --list_of_subjects /absolute_path/study/sub_list
               --outdir absolute_path/study   
               --bpx_path /relative_path/.bedpostX 
               --seeds /relative_path/L.surf.gii /path_to/R.surf.gii 
               --roi /relative_path/L.exclude_medialwall.shape.gii /path_to/R.exclude_medialwall.shape.gii 
               --warps /relative_path/stand2diff.nii.gz /relative_path/diff2stand.nii.gz 
               --n_cores 3 

    {col["pink"]}Volume mode:{col["reset"]}
            nfact_pp --list_of_subjects /absolute_path/study/sub_list
                --outdir /absolute_path/study   
                --bpx_path /relative_path/.bedpostX 
                --seeds /relative_path/L.white.nii.gz /relative_path/R.white.nii.gz 
                --warps /relative_path/stand2diff.nii.gz /relative_path/diff2stand.nii.gz 
                --seedref absolute_path/MNI152_T1_1mm_brain.nii.gz 
                --target absolute_path/dlpfc.nii.gz

    {col["darker_pink"]}Filestree mode:{col["reset"]}
        nfact_pp --filestree hcp
            --list_of_subjects /absolute_path/study/sub_list  
            --outdir /absolute_path/study 
"""
