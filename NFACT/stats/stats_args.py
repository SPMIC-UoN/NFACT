from NFACT.base.utils import colours
from NFACT.base.base_args import (
    algo_arg,
    nfact_decomp_folder,
    set_up_args,
)
import argparse
import sys


def valid_options() -> list:
    """
    Function to get valid options

    Parameters
    -----------
    None

    Returns
    -------
    list: list[str]
        list of valid options
    """
    return ["loadings", "statsmap"]


def invalid_options(option: str, avaiable_options: list) -> None:
    """
    Function to print and exit
    after an invalid option
    was given

    Parameters
    ----------
    option: str
        str of option given
    avaiable_options: list
        list of avaiable options

    Returns
    -------
    None
    """
    col = colours()
    print(nfact_stats_splash())
    print(f"{col['red']}{option}{col['reset']} is an invalid option")
    print("Please specify from", *avaiable_options)
    print("or run --help")
    exit(1)


def usage_message() -> None:
    """
    Function to print a basic
    usage message and exit

    Parameters
    ----------
    None

    Returns
    -------
    str: string
        string of usage message
    """
    print(f"""
    {nfact_stats_splash()}
NFACT Stats has two sub functions. 
    - loadings. Calculates How similar the dual regression is to the group level
    - statsmap. Creates from given component numbers a single map of those components

RUN: 
nfact_stats loadings --help 
\tOR:
nfact_stats statsmap --help
for further info
    """)
    exit(0)


def check_subcommand() -> None:
    """
    Function to check the subcommand
    given to nfact stats.

    Parameters
    -----------
    None

    Returns
    -------
    None
    """

    avaiable_options = valid_options()
    if len(sys.argv) <= 1 or sys.argv[1] in ["-h", "--help"]:
        usage_message()
    if sys.argv[1] not in avaiable_options:
        invalid_options(sys.argv[1], avaiable_options)


def comp_loading_args(args: object) -> None:
    """
    Component loading cmd arguments

    Parameters
    ----------
    args:  object
        Argparse object

    Returns
    -------
    None
    """
    col = colours()
    comp_args = args.add_parser("loadings", help="Calculate component loadings")
    comp_args.add_argument(
        "-O",
        "--overwrite",
        dest="overwrite",
        action="store_true",
        default=False,
        help="Overwrites previous file structure",
    )
    set_up_args(comp_args, col)
    decomp_args = comp_args.add_argument_group(
        f"{col['plum']}Decomp options{col['reset']}"
    )

    nfact_decomp_folder(decomp_args)
    algo_arg(decomp_args)
    stats_args = comp_args.add_argument_group(
        f"{col['darker_pink']}Stats options{col['reset']}"
    )
    stats_args.add_argument(
        "-t",
        "--threshold",
        dest="threshold",
        default=2,
        type=int,
        help="""
        Threshold components so that component
        loadings reflect connectivity patterns
        not noise. 
        """,
    )
    stats_args.add_argument(
        "-C",
        "--no_csv",
        dest="no_csv",
        action="store_true",
        default=False,
        help="""
        Save Component Loadings as a npy file
        rather than as a csv file
        """,
    )


def stat_map_args(args) -> dict:
    """
    Function to get arguements
    to run NFACT stat map args

    Parameters
    -----------
    None

    Returns
    -------
    dict: dictionary object
        dict of arguments
    """
    col = colours()
    stats_args = args.add_parser("statsmap", help="Create a statsmap")
    set_up_args(stats_args, col)
    stats_args.add_argument(
        "-O",
        "--overwrite",
        dest="overwrite",
        action="store_true",
        default=False,
        help="Overwrites previous file structure",
    )
    decomp_args = stats_args.add_argument_group(
        f"{col['plum']}Decomp options{col['reset']}"
    )

    nfact_decomp_folder(decomp_args)
    algo_arg(decomp_args)
    map_args = stats_args.add_argument_group(
        f"{col['pink']}Statsmap options{col['reset']}"
    )
    map_args.add_argument(
        "-c",
        "--components",
        dest="components",
        type=int,
        nargs="+",
        help="""
        Components to merge. Provide as space separated list of integers. E.g. -c 1 2 3
        """,
    )
    map_args.add_argument(
        "-m",
        "--map_name",
        dest="map_name",
        default="",
        help="""
        Name to call the maps (i.e if merging components asscoiated with a network call it networkx)
        """,
    )
    map_args.add_argument(
        "-t",
        "--threshold",
        dest="threshold",
        default=2,
        type=int,
        help="""
        Threshold components so that component
        loadings reflect connectivity patterns
        not noise.
        """,
    )
    map_args.add_argument(
        "-G",
        "--group-only",
        dest="group-only",
        action="store_true",
        help="""
        Only do group level stats map. Doesn't need a subject list
        """,
    )
    map_args.add_argument(
        "-S",
        "--skip",
        dest="skip",
        default=False,
        action="store_true",
        help="""
        Skip creating variance maps and only creates a statsmap.
        """,
    )


def nfact_stats_splash() -> str:
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
 _   _ ______   ___   _____  _____   _____  _____   ___   _____  _____ 
| \ | ||  ___| / _ \ /  __ \|_   _| /  ___||_   _| / _ \ |_   _|/  ___|
|  \| || |_   / /_\ \| /  \/  | |   \ `--.   | |  / /_\ \  | |  \ `--. 
| . ` ||  _|  |  _  || |      | |    `--. \  | |  |  _  |  | |   `--. \\
| |\  || |    | | | || \__/\  | |   /\__/ /  | |  | | | |  | |  /\__/ /
\_| \_/\_|    \_| |_/ \____/  \_/   \____/   \_/  \_| |_/  \_/  \____/ 
{col["reset"]} 
"""


def nfact_stats_modules() -> dict:
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
    args = argparse.ArgumentParser(
        prog="nfact_stats",
        description=print(nfact_stats_splash()),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = args.add_subparsers(dest="command")
    comp_loading_args(subparsers)
    stat_map_args(subparsers)
    return args


def nfact_stats_args() -> dict:
    """
    Function that is entry point into
    NFACT args.

    Parameters
    ----------
    None

    Returns
    --------
    dict: dictionary
        cmd dict of arguments
    """
    check_subcommand()
    parser = nfact_stats_modules()
    args = parser.parse_args()
    if len(sys.argv) <= 3:
        parser.parse_args([args.command, "--help"])
    return vars(args)
