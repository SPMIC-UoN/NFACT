import argparse
from NFACT.base.utils import colours, no_args, verbose_help_message
from NFACT.base.base_args import (
    parallel_args,
    set_up_args,
    base_arguments,
    seed_roi_args,
    algo_arg,
    cluster_args,
)


def nfactdr_args() -> dict:
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
        prog="nfact_dr",
        description=print(nfact_dr_splash()),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    col = colours()
    base_arguments(base_args)
    set_up_args(base_args, col)
    dr_args = base_args.add_argument_group(
        f"{col['pink']}Dual Regression options{col['reset']}"
    )
    algo_arg(dr_args)
    seed_roi_args(dr_args)
    dr_args.add_argument(
        "-d",
        "--nfact_decomp_dir",
        dest="nfact_decomp_dir",
        help="Filepath to the NFACT_decomp directory. Use this if you have ran NFACT decomp",
    )
    dr_args.add_argument(
        "-dd",
        "--decomp_dir",
        dest="decomp_dir",
        help="""Filepath to decomposition components. 
        WARNING NFACT decomp expects components to be named in a set way. See documentation for further info.""",
    )
    dr_args.add_argument(
        "-N",
        "--normalise",
        dest="normalise",
        action="store_true",
        default=False,
        help="normalise components by scaling",
    )
    dr_args.add_argument(
        "-D",
        "--dscalar",
        dest="cifti",
        action="store_true",
        default=False,
        help="""
        Save GM as cifti dscalar. 
        Seeds must be left and right surfaces with an optional nifti for subcortical structures""",
    )
    dr_args.add_argument(
        "-t",
        "--threshold",
        dest="threshold",
        default=3,
        help="""
        Value at which to threshold Components
        at. Set to 0 to do no thresholding.
        """,
    )

    parallel_args(base_args, col, "To parallelize dual regression")
    cluster_args(base_args, col)
    no_args(base_args)
    options = base_args.parse_args()
    if options.verbose_help:
        verbose_help_message(base_args, nfact_dr_usage())
    return vars(options)


def nfact_dr_splash() -> str:
    """
    Function to return NFACT DR splash

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
 _   _ ______   ___   _____  _____  ______ ______ 
| \ | ||  ___| / _ \ /  __ \|_   _| |  _  \| ___ \\
|  \| || |_   / /_\ \| /  \/  | |   | | | || |_/ /
| . ` ||  _|  |  _  || |      | |   | | | ||    / 
| |\  || |    | | | || \__/\  | |   | |/ / | |\ \ 
\_| \_/\_|    \_| |_/ \____/  \_/   |___/  \_| \_|
{col["reset"]}                                                                              
"""


def nfact_dr_usage() -> str:
    """
    Function to print examples on how to use
    nfact_dr.

    Parameteres
    -----------
    None

    Returns
    -------
    str: str
        string of help message
    """
    col = colours()
    return f"""
{col["darker_pink"]}Dual regression usage:{col["reset"]}
    nfact_dr --list_of_subjects /path/to/nfact_config_sublist \\
        --seeds /path/to/seeds.txt \\
        --nfact_decomp_dir /path/to/nfact_decomp \\
        --outdir /path/to/output_directory \\
        --algo NMF 

{col["darker_pink"]}ICA Dual regression usage:{col["reset"]}
    nfact_dr --list_of_subjects /path/to/nfact_config_sublist \\
        --seeds /path/to//seeds.txt \\
        --nfact_decomp_dir /path/to/nfact_decomp \\
        --outdir /path/to/output_directory \\
        --algo ICA 

{col["darker_pink"]}Dual regression with roi seeds usage:{col["reset"]}
    nfact_dr --list_of_subjects /path/to/nfact_config_sublist \\
        --seeds /path/to/seeds.txt \\
        --nfact_decomp_dir /path/to/nfact_decomp \\
        --outdir /path/to/output_directory \\
        --roi /path/to/roi.txt \\
        --algo NMF 
"""
