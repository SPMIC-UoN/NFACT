import argparse
from NFACT.base.utils import colours, no_args, verbose_help_message
from NFACT.base.base_args import set_up_args, base_arguments, seed_roi_args, algo_arg


def nfact_decomp_args() -> dict:
    """
    Function to define cmd arguments

    Parameters
    ----------
    None

    Returns
    -------
    dict: dictionary
        dictionary of cmd arguments
    """
    base_args = argparse.ArgumentParser(
        prog="nfact_decomp",
        description=print(nfact_decomp_splash()),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    col = colours()
    base_arguments(base_args)
    set_up_args(base_args, col)

    decomp_input = base_args.add_argument_group(
        f"{col['plum']}Decomposition inputs{col['reset']}"
    )
    seed_roi_args(decomp_input)
    decomp_input.add_argument(
        "-m",
        "--matrix",
        dest="matrix",
        default=False,
        help="""
        Absolute path to a previously averaged group folder. NFACT will use this matrix,
        average_matrix2, coords_for_fdt_matrix2 and tract_space_coords
        and lookup_tractspace.nii.gz files in the decomposition.
        """,
    )
    decomp_input.add_argument(
        "-f",
        "--config_file",
        dest="config",
        default=False,
        help="""
        Absolute path to a configuration file.
        Congifuration file provides available hyperparameters for ICA and NMF. 
        Use nfact_config -D to create a config file.
        Please see sckit learn documentation for NMF and FASTICA for further details
        """,
    )

    decomp_args = base_args.add_argument_group(
        f"{col['pink']}Decomposition options{col['reset']}"
    )
    algo_arg(decomp_args)
    decomp_args.add_argument(
        "-d",
        "--dim",
        dest="dim",
        default=75,
        help=""" 
        Number of dimensions to retain
        after running NMF/ICA. If using NMF-sso the dimensions of the 
        final analysis won't be this. Default is 75 as this 
        provides the best coverage for whole brain seeds and doesn't overfit.
        May not work for all data
        """,
    )
    decomp_args.add_argument(
        "-i",
        "--iterations",
        dest="iterations",
        default=20,
        type=int,
        help="""
        Number of iterations of NMF for the NMF-sso.
        Default is 20
        """,
    )
    decomp_args.add_argument(
        "-n",
        "--n_cores",
        dest="n_cores",
        default=1,
        type=int,
        help="""
        To parallelize NMF-sso. Default is not to.
        """,
    )
    decomp_args.add_argument(
        "-w",
        "--wm_matrix",
        dest="wm_matrix",
        default=False,
        help="""
        Previous wm matrix to initiate NMF with. Default is 
        false (see sckit learn NMF for further details on initialisation).
        If this option is given then --gm_matrix needed.
        """,
    )
    decomp_args.add_argument(
        "-g",
        "--gm_matrix",
        dest="gm_matrix",
        default=False,
        help="""
        Previous gm matrix to initiate NMF with. Default is 
        false (see sckit learn NMF for further details on initialisation).
        If this option is given then --wm_matrix needed. 
        """,
    )
    decomp_args.add_argument(
        "-X",
        "--exclude_sso",
        dest="no_sso",
        default=False,
        action="store_true",
        help="""
        Don't do NMF-sso. 
        Just do a single NMF. Default is False
        """,
    )

    output_args = base_args.add_argument_group(
        f"{col['darker_pink']}Output options{col['reset']}"
    )
    output_args.add_argument(
        "-C",
        "--cifti",
        dest="cifti",
        action="store_true",
        default=False,
        help="""
        Option to save GM as a cifti dscalar. 
        Seeds must be left and right surfaces 
        with an optional nifti for subcortical
        structures.
        """,
    )
    output_args.add_argument(
        "-D",
        "--disk",
        dest="disk",
        action="store_true",
        default=False,
        help="""
        Save the decomposition matrices directly to disk rather than as nii/gii files      
        """,
    )
    output_args.add_argument(
        "-W",
        "--wta",
        dest="wta",
        action="store_true",
        default=False,
        help="""
        Option to create and save winner-takes-all maps.
        """,
    )
    output_args.add_argument(
        "-z",
        "--wta_zthr",
        dest="wta_zthr",
        default=0.0,
        help="Winner-takes-all threshold. Default is 0",
    )
    output_args.add_argument(
        "-N",
        "--normalise",
        dest="normalise",
        action="store_true",
        default=False,
        help="""
        Convert component values into Z scores 
        and saves map. This is useful for visualization
        """,
    )
    output_args.add_argument(
        "-t",
        "--threshold",
        dest="threshold",
        default=0,
        help="""
        Value at which to threshold Components
        at. Default is to not do thresholding.
        """,
    )
    output_args.add_argument(
        "-CS",
        "--cluster_save",
        dest="cluster_save",
        action="store_true",
        default=False,
        help="""
        When doing sso save each cluster as nifti/gifti/cifti
        as 4D files with each 4D point as a single NMF run
        """,
    )
    ica_options = base_args.add_argument_group(
        f"{col['purple']}ICA options{col['reset']}"
    )
    ica_options.add_argument(
        "-c",
        "--components",
        dest="components",
        default="1000",
        help="""
        Number of component to be 
        retained following the PCA. 
        Default is 1000
        """,
    )
    ica_options.add_argument(
        "-p",
        "--pca_type",
        dest="pca_type",
        default="pca",
        help="""
        Which type of PCA to do before ICA. 
        Options are 'pca' which is sckit learns default PCA
        or 'migp' (MELODIC's Incremental Group-PCA dimensionality).
        Default is 'pca' as for most
        cases 'migp' is slow and not needed.
        Option is case insensitive.
        """,
    )

    ica_options.add_argument(
        "-S",
        "--sign_flip",
        dest="sign_flip",
        action="store_false",
        default=True,
        help="""
        nfact_decomp by default sign flips the ICA 
        distribution to reduce the number of negative values.
        Use this option to stop the sign_flip 
        """,
    )

    no_args(base_args)
    args = base_args.parse_args()
    if args.verbose_help:
        verbose_help_message(base_args, nfact_decomp_usage())
    return vars(args)


def nfact_decomp_splash() -> str:
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
 _   _ ______   ___   _____  _____  ______  _____  _____  _____ ___  ___ _____ 
| \ | ||  ___| / _ \ /  __ \|_   _| |  _  \|  ___|/  __ \|  _  ||  \/  || ___ \\
|  \| || |_   / /_\ \| /  \/  | |   | | | || |__  | /  \/| | | || .  . || |_/ /
| . ` ||  _|  |  _  || |      | |   | | | ||  __| | |    | | | || |\/| ||  __/ 
| |\  || |    | | | || \__/\  | |   | |/ / | |___ | \__/\\\ \_/ /| |  | || |    
\_| \_/\_|    \_| |_/ \____/  \_/   |___/  \____/  \____/ \___/ \_|  |_/\_| 
{col["reset"]} 
"""


def nfact_decomp_usage():
    """
    Function to return NFACT
    decomp usage

    Parameteres
    -----------
    None

    Returns
    ------
    None
    """
    col = colours()
    return f"""
{col["darker_pink"]}Basic NMF with volume seeds usage:{col["reset"]}
    nfact_decomp --list_of_subjects /absolute path/sub_list \ 
                 --seeds /absolute path/seeds.txt \ 
    

{col["darker_pink"]}Basic NMF usage with surface seeds:{col["reset"]}
    nfact_decomp --list_of_subjects /absolute path/sub_list \ 
                 --seeds /absolute path/seeds.txt \ 
                 --roi /absolute path/rois

{col["darker_pink"]}NMF usage with surface seeds with different dims and reduced NMF-sso iterations:{col["reset"]}
    nfact_decomp --list_of_subjects /absolute path/sub_list \ 
                 --seeds /absolute path/seeds.txt \ 
                 --roi /absolute path/rois
                 --dim 50
                 --iterations 10

{col["darker_pink"]}ICA with config file usage:{col["reset"]}
    nfact_decomp --list_of_subjects /absolute path/sub_list \ 
                 --seeds /absolute path/seeds.txt \ 
                 --outdir /absolute path/study_directory \ 
                 --algo ICA \ 
                 --nfact_config /absolute path/nfact_config.decomp

{col["darker_pink"]}Advanced ICA Usage:{col["reset"]}
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
"""
