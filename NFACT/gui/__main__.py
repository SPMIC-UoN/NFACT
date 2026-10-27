"""
Command line entry point for launching the NFACT Graphical User Interface.
"""

import sys
from typing import Optional

from NFACT.base.utils import colours


def check_tkinter_availability() -> bool:
    """Check whether tkinter is available in the current Python environment.

    Attempts to import tkinter and returns True if available, False otherwise.

    Parameters
    ------------
    None

    Returns
    --------
        bool: boolean object
            True if tkinter is importable, False otherwise.
    """
    try:
        import tkinter  # noqa: F401

        return True
    except (ImportError, ModuleNotFoundError):
        return False


def build_tkinter_missing_message(platform_name: str) -> str:
    """Construct an informative error message when tkinter is not installed.

    Provides clear platform-specific guidance for macOS, Linux, and other
    operating systems to guide users on installing Tkinter or using the CLI.

    Parameters
    ------------
    platform_name: str
        The operating system platform identifier (e.g. sys.platform).

    Returns
    --------
        str: string object
            Formatted error and remediation message.
    """
    color_map = colours()
    red_color = color_map["red"]
    reset_color = color_map["reset"]
    plum_color = color_map["plum"]
    pink_color = color_map["pink"]

    message_lines = [
        f"\n{red_color}[ERROR] Unable to launch NFACT GUI: "
        f"Python Tkinter support is missing.{reset_color}\n",
    ]
    if platform_name == "darwin":
        message_lines.append(
            f"{plum_color}To use the GUI on macOS, install Tkinter bindings "
            f"for your Python distribution:{reset_color}\n"
            "  * Homebrew:    brew install python-tk\n"
            "                 (or brew install python-tk@3.12 for Python 3.12)\n"
            "  * Conda/Mamba: conda install -c conda-forge tk\n"
            "  * Pyenv:       brew install tcl-tk && rebuild Python with tcl-tk\n"
            "  * Official:    https://www.python.org/downloads/\n"
        )
    elif platform_name.startswith("linux"):
        message_lines.append(
            f"{plum_color}To use the GUI on Linux, install system "
            f"Tkinter:{reset_color}\n"
            "  * Ubuntu/Debian: sudo apt-get install python3-tk\n"
            "  * Fedora/RHEL:   sudo dnf install python3-tkinter\n"
            "  * Conda/Mamba:   conda install -c conda-forge tk\n"
        )
    else:
        message_lines.append(
            f"{plum_color}Please install Tkinter support for your Python "
            f"distribution.{reset_color}\n"
        )

    message_lines.append(
        f"{pink_color}Note: All NFACT processing commands can be run via "
        f"CLI without Tkinter:{reset_color}\n"
        "  nfact --help\n"
        "  nfact_pp --help\n"
        "  nfact_decomp --help\n"
        "  nfact_dr --help\n"
        "  nfact_qc --help\n"
        "  nfact_stats --help\n"
        "  nfact_config --help\n"
    )
    return "\n".join(message_lines)


def nfact_gui_main(arguments_list: Optional[list] = None) -> None:
    """Launch the NFACT Graphical User Interface application.

    Validates that tkinter is installed and available before attempting to
    import and instantiate the GUI application. If tkinter is missing,
    an informative error message is printed to sys.stderr and the process exits.

    Parameters
    ------------
    arguments_list: Optional[list]
        Command line arguments list. Defaults to None (parsed from sys.argv).

    Returns
    --------
        None: NoneType object
            Returns None when the application loop finishes.
    """
    if not check_tkinter_availability():
        error_message = build_tkinter_missing_message(sys.platform)
        sys.stderr.write(error_message + "\n")
        sys.exit(1)

    from NFACT.gui.app import NFACTGuiApp
    from NFACT.gui.gui_args import parse_gui_args
    
    try:
        parsed_dict = parse_gui_args(arguments_list)
        application_instance = NFACTGuiApp(
            initial_theme=parsed_dict.get("theme", "dark"),
            initial_config=parsed_dict.get("config"),
            initial_workdir=parsed_dict.get("workdir"),
        )
        application_instance.mainloop()
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    nfact_gui_main()
