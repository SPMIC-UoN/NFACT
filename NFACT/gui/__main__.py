"""
Command line entry point for launching the NFACT Graphical User Interface.
"""

from typing import Optional

from NFACT.gui.app import NFACTGuiApp
from NFACT.gui.gui_args import parse_gui_args


def nfact_gui_main(arguments_list: Optional[list] = None) -> None:
    """
    Launch the NFACT Graphical User Interface application.

    Parameters
    ----------
    arguments_list: Optional[list], default=None
        Command line arguments list. If None, arguments are parsed from sys.argv.

    Returns
    -------
    None
    """
    parsed_dict = parse_gui_args(arguments_list)
    application_instance = NFACTGuiApp(
        initial_theme=parsed_dict.get("theme", "dark"),
        initial_config=parsed_dict.get("config"),
        initial_workdir=parsed_dict.get("workdir"),
    )
    application_instance.mainloop()


if __name__ == "__main__":
    nfact_gui_main()
