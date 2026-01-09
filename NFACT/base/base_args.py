from NFACT.base.utils import colours


def cluster_args(base_args: object, col: dict) -> None:
    """
    Function to add in cluster arguments to
    arguments. Adds in argument group

    Parameters
    ----------
    base_args: argparse.ArgumentParser
        ArgumentParser to add group to
    col: dict
        dictionary of colour strings

    Returns
    -------
    cluster_options: argparse.ArgumentParser
        strictly not necessary for return
        but useful for linting so
        variables aren't unassigned.
    """
    cluster_options = base_args.add_argument_group(
        f"{col['amethyst']}Cluster options{col['reset']}"
    )

    cluster_options.add_argument(
        "-C",
        "--cluster",
        dest="cluster",
        action="store_true",
        default=False,
        help="Use cluster enviornment",
    )
    cluster_options.add_argument(
        "-cq",
        "--queue",
        dest="cluster_queue",
        default=None,
        help="Cluster queue to submit to",
    )
    cluster_options.add_argument(
        "-cr",
        "--cluster_ram",
        dest="cluster_ram",
        default="60",
        help="Ram that job will take. Default is 60",
    )
    cluster_options.add_argument(
        "-ct",
        "--cluster_time",
        dest="cluster_time",
        default=False,
        help="Time that job will take. nfact will assign a time if none given",
    )
    cluster_options.add_argument(
        "-cqos",
        "--cluster_qos",
        dest="cluster_qos",
        default=False,
        help="Set the qos for the cluster",
    )
    return cluster_options


def parallel_args(base_args: object, col: dict, help_message: str) -> None:
    """
    Function to add in parallel arguments to
    arguments. Adds in argument group

    Parameters
    ----------
    base_args: argparse.ArgumentParser
        ArgumentParser to add group to
    col: dict
        dictionary of colour strings

    Returns
    -------
    None
    """
    parallel_process = base_args.add_argument_group(
        f"{col['darker_pink']}Parallel Processing option{col['reset']}"
    )
    parallel_process.add_argument(
        "-n",
        "--n_cores",
        dest="n_cores",
        help=help_message,
        default=False,
    )


def set_up_args(base_args: object, col: dict) -> None:
    """
    Function to add in set up arguments to
    arguments. Adds in argument group

    Parameters
    ----------
    base_args: argparse.ArgumentParser
        ArgumentParser to add group to
    col: dict
        dictionary of colour strings

    Returns
    -------
    None
    """
    set_up_args = base_args.add_argument_group(
        f"{col['deep_pink']}Set up options{col['reset']}"
    )
    set_up_args.add_argument(
        "-l",
        "--list_of_subjects",
        dest="list_of_subjects",
        help="Filepath to a list of subjects",
    )
    set_up_args.add_argument(
        "-o",
        "--outdir",
        dest="outdir",
        help="Path to output directory",
    )


def base_arguments(base_args: object) -> None:
    """
    Function to return base
    arguments for nfact modules.

    Parameters
    ----------
    base_args: argparse.ArgumentParser
        ArgumentParser to add group to

    Returns
    -------
    None
    """
    base_args.add_argument(
        "-hh",
        "--verbose_help",
        dest="verbose_help",
        default=False,
        action="store_true",
        help="""
        Verbose help message.
        Prints help message and example usages
      """,
    )
    base_args.add_argument(
        "-O",
        "--overwrite",
        dest="overwrite",
        action="store_true",
        default=False,
        help="Overwrites previous file structure",
    )


def seed_roi_args(args: object) -> None:
    """
    Function to return seed
    and roi arguments.

    Parameters
    ----------
    args: argparse.ArgumentParser
        ArgumentParser to add group to

    Returns
    -------
    None
    """
    args.add_argument(
        "--seeds",
        "-s",
        dest="seeds",
        help="""
        Absolute path to a text file of seed(s) 
        used in nfact_pp/probtrackx.
        If used nfact_pp this is the seeds_for_decomp.txt
        in the nfact_pp directory.
        """,
    )
    args.add_argument(
        "--roi",
        "-r",
        dest="roi",
        default=False,
        help="""
        Absolute path to a text file containing the  
        absolute path ROI(s) paths to restrict seeding to 
        (e.g. medial wall masks). This is not needed if
        seeds are not surfaces. If used nfact_pp then this
        is the roi_for_decomp.txt file in the nfact_pp
        directory.
        """,
    )


def algo_arg(arg) -> None:
    """
    Function to return
    algo argument.

    Parameters
    ----------
    args: argparse.ArgumentParser
        ArgumentParser to add group to

    Returns
    -------
    None
    """

    arg.add_argument(
        "-a",
        "--algo",
        dest="algo",
        default="NMF",
        help="""
        Which decomposition algorithm. 
        Options are: NMF (default), or ICA. This is case
        insensitive
        """,
    )


def nfact_decomp_folder(args) -> None:
    """
    Function to return nfact_decomp
    arguments

    Parameters
    ----------
    args: argparse.ArgumentParser
        ArgumentParser to add group to

    Returns
    -------
    None
    """
    col = colours()
    args.add_argument(
        "-d",
        "--dim",
        dest="dim",
        help="""
        Number of dimensions/components that 
        was used to generate nfact_decomp image
        """,
    )
    args.add_argument(
        "-n",
        "--nfact_folder",
        dest="nfact_folder",
        help=f"""{col["red"]}REQUIRED:{col["reset"]}
        Absolute path to nfact_decomp output folder.
        """,
    )
