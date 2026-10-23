"""
Argument parsing and splash screen utilities for the NFACT Graphical User Interface.
"""

import argparse
import os
from typing import Optional

from NFACT.base.utils import colours, verbose_help_message


def nfact_gui_splash() -> str:
    """Return NFACT GUI banner string in authentic colors.

    Parameters
    ------------
    None

    Returns
    --------
        str: banner text
            Formatted ASCII banner.
    """
    color_palette = colours()
    return f"""
{color_palette["deep_pink"]} _   _ ______ ___  _____ _____   _____ _   _ _____ 
{color_palette["pink"]}| \\ | ||  ___/ _ \\/  __ \\_   _| |  __ \\ | | |_   _|
{color_palette["darker_pink"]}|  \\| || |_ / /_\\ \\ /  \\/ | |   | |  \\/ | | | | |  
{color_palette["plum"]}| . ` ||  _||  _  | |     | |   | | __| | | | | |  
{color_palette["amethyst"]}| |\\  || |  | | | | \\__/\\ | |   | |_\\ \\ |_| |_| |_ 
{color_palette["purple"]}\\_| \\_/\\_|  \\_| |_/\\____/ \\_/    \\____/\\___/ \\___/ 
{color_palette["reset"]}
"""


def nfact_gui_verbose_usage() -> str:
    """Return verbose usage and examples for NFACT GUI.

    Parameters
    ------------
    None

    Returns
    --------
        str: usage text
            Formatted verbose usage string.
    """
    return """
Example Usages:
---------------
1. Launch default dark-themed GUI:
   nfact_gui

2. Launch GUI with light theme:
   nfact_gui --theme light

3. Launch GUI with a pre-loaded pipeline configuration:
   nfact_gui --config /path/to/my_pipeline.config

4. Launch GUI with a custom initial working directory:
   nfact_gui --workdir /path/to/study/

5. Launch GUI with high-DPI scaling override:
   nfact_gui --scale 1.5
"""


def parse_gui_args(
    arguments_list: Optional[list[str]] = None,
) -> dict[str, object]:
    """Define and parse command line arguments for the NFACT GUI.

    Parameters
    ------------
    arguments_list: Optional[list[str]]
        Explicit argument list for headless testing. Defaults to None.

    Returns
    --------
        dict[str, object]: parsed arguments
            Dictionary of parsed command line options.
    """
    parser = argparse.ArgumentParser(
        prog="nfact_gui",
        description=nfact_gui_splash(),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--theme",
        dest="theme",
        choices=["dark", "light"],
        default="dark",
        help="Initial graphical user interface theme (default: dark)",
    )
    parser.add_argument(
        "-c",
        "--config",
        dest="config",
        default=None,
        help="Path to an initial pipeline or decomposition configuration file",
    )
    parser.add_argument(
        "-w",
        "--workdir",
        dest="workdir",
        default=os.getcwd(),
        help="Initial working directory for file pickers (default: current directory)",
    )
    parser.add_argument(
        "--scale",
        dest="scale",
        type=float,
        default=None,
        help="Display scaling factor override (e.g. 1.5, 2.0)",
    )
    parser.add_argument(
        "-hh",
        "--verbose_help",
        dest="verbose_help",
        action="store_true",
        help="Display extended help message and exit",
    )

    parsed_arguments = parser.parse_args(arguments_list)
    if parsed_arguments.verbose_help:
        verbose_help_message(parser, nfact_gui_verbose_usage())

    return vars(parsed_arguments)
