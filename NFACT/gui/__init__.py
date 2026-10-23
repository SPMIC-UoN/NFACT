"""
NFACT Graphical User Interface (GUI) package.
"""

from typing import Any

__all__ = ["NFACTGuiApp", "nfact_gui_main"]


def __getattr__(name: str) -> Any:
    """Lazily import GUI modules to prevent premature tkinter import failures.

    Parameters
    ------------
    name: str
        Name of attribute being accessed on the module.

    Returns
    --------
        Any: object
            The resolved module attribute.
    """
    if name == "NFACTGuiApp":
        from NFACT.gui.app import NFACTGuiApp

        return NFACTGuiApp
    if name == "nfact_gui_main":
        from NFACT.gui.__main__ import nfact_gui_main

        return nfact_gui_main
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
