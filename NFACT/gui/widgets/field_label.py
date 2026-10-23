"""
Composite label with required marker, hover tooltip, and CLI flag badge.
"""

import tkinter as tk
from tkinter import ttk

from NFACT.gui.widgets.tooltip import HoverTooltip


class FieldLabel(ttk.Frame):
    """Field label displaying parameter name, required indicator, and flag badge.

    Usage
    -----
    label = FieldLabel(
        parent_frame,
        text="Subjects list",
        flag="-l",
        required=True,
        tooltip_text="Path to subject list file",
    )
    """

    def __init__(
        self,
        parent_container: tk.Widget,
        text: str,
        flag: str = "",
        required: bool = False,
        tooltip_text: str = "",
        style: str = "Surface.TFrame",
    ) -> None:
        """Initialize composite field label.

        Parameters
        ------------
        parent_container: tk.Widget
            Parent Tkinter widget.
        text: str
            Human-readable field name.
        flag: str
            CLI option flag (e.g. "-l" or "--outdir"). Defaults to "".
        required: bool
            Whether field is strictly required. Defaults to False.
        tooltip_text: str
            Optional explanatory text shown on hover. Defaults to "".
        style: str
            Frame style name. Defaults to "Surface.TFrame".

        Returns
        --------
            None: None object
                Constructs label hierarchy.
        """
        super().__init__(parent_container, style=style)

        self.columnconfigure(0, weight=1)

        left_container = ttk.Frame(self, style=style)
        left_container.pack(side="left", fill="x", expand=True)

        self.main_label = ttk.Label(
            left_container,
            text=text,
            style="Surface.TLabel",
        )
        self.main_label.pack(side="left")

        if required:
            self.required_label = ttk.Label(
                left_container,
                text=" *",
                style="Required.TLabel",
            )
            self.required_label.pack(side="left")

        if flag:
            self.flag_label = ttk.Label(
                self,
                text=flag,
                style="FlagBadge.TLabel",
            )
            self.flag_label.pack(side="right", padx=(4, 0))

        full_tooltip = tooltip_text
        if flag and not full_tooltip.startswith(flag):
            full_tooltip = f"{flag}: {tooltip_text}" if tooltip_text else flag

        if full_tooltip:
            HoverTooltip(self.main_label, full_tooltip)
