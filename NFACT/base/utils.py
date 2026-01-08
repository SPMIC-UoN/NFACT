import time
import logging
import sys
import importlib.metadata
import re


class Timer:
    """
    Wrapper around timer
    to calculate how long
    processes take to run
    """

    def __init__(self):
        self._t = None

    def tic(self):
        self._t = time.time()

    def toc(self):
        return f"{time.time() - self._t:.2f}"

    def format_time(self, seconds: float):
        seconds = int(round(seconds))
        if seconds < 60:
            return f"{seconds} seconds"
        elif seconds < 3600:
            minutes, remaining_seconds = divmod(seconds, 60)
            return f"{minutes} minutes: {remaining_seconds} seconds"
        else:
            hours, remaining_seconds = divmod(seconds, 3600)
            minutes, remaining_seconds = divmod(remaining_seconds, 60)
            return f"{hours} hours: {minutes} minutes: {remaining_seconds} seconds"

    def how_long(self):
        seconds = self.toc()
        return self.format_time(float(seconds))


def colours():
    """
    Function to print out text in colors

    Parameters
    ----------
    None

    Returns
    -------
    dict: dictionary object
        dictionary of color strings
    """
    return {
        "reset": "\033[0;0m",
        "red": "\033[1;31m",
        "pink": "\033[1;35m",
        "deep_pink": "\033[38;2;255;20;147m",
        "purple": "\033[38;5;93m",
        "darker_pink": "\033[38;5;129m",
        "plum": "\033[0;35m",
        "amethyst": "\033[38;2;153;102;204m",
        "lav": "\033[38;5;141m",
    }


def error_and_exit(
    bool_statement: bool, error_message: str = None, log_message: bool = True
) -> None:
    """
    Function to exit out of script
    with error message if bool statement
    is false.

    Parameters
    ----------
    bool_statement: bool
       statement to evaluate
    error_message: str
        error message to print
        out. Default is None
    log_message: bool
        Whether to log the message. Default is True.

    Returns
    -------
    None
    """
    if not bool_statement:
        if error_message:
            error_message = re.sub(r"\[Errno 2\]", "", error_message)
            col = colours()
            message = col["red"] + error_message + col["reset"]
            if log_message:
                nprint(message)
            else:
                print(message)
        print("Exiting...\n")
        exit(1)


def nprint(message: str, to_flush: bool = False) -> None:
    """
    Function to print to terminal
    and attempt to log to pre set up
    log file.

    Parameters
    ----------
    message: str
        string to print and log
    to_flush: bool
        to flush output
        default is false

    Returns
    -------
    None
    """
    print(message, flush=to_flush)
    try:
        logging.info(message)
    except Exception:
        return None


def no_args(args: object) -> None:
    """
    Function to print help
    message if no arguments are given.

    Parameters
    ----------
    args: argparse object
        argparse object

    Returns
    -------
    None
    """
    if len(sys.argv) == 1:
        args.print_help(sys.stderr)
        sys.exit(1)


def verbose_help_message(options: object, verbose_message_str: str) -> None:
    """
    Fnction to print out a verbose
    help message.

    Parameters
    ----------
    options: object
        argparse option not parsed
    verbose_message_str: str
        str of additional help message to print

    Returns
    -------
    None
    """
    col = colours()
    print(options.format_help())
    print(verbose_message_str)
    print(
        f"{col['plum']}NFACT version:{col['reset']} {importlib.metadata.version('NFACT')}"
    )
    exit(0)
