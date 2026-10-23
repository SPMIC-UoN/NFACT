"""
Page header component displaying module title, description, and CLI tool badge.
"""

import tkinter as tk
from tkinter import ttk


class PageHeader(ttk.Frame):
    """Header banner component displayed at the top of each module page.

    Usage
    -----
    header = PageHeader(
        parent_frame,
        title="Full Pipeline",
        description="Run pre-processing, decomposition, QC and dual regression.",
        cli_name="nfact",
    )
    """

    def __init__(
        self,
        parent_container: tk.Widget,
        title: str,
        description: str,
        cli_name: str = "",
        style: str = "TFrame",
    ) -> None:
        """Initialize page header layout.

        Parameters
        ------------
        parent_container: tk.Widget
            Parent container widget.
        title: str
            Module title displayed prominently.
        description: str
            One-line explanation of module functionality.
        cli_name: str
            CLI tool command name badge (e.g. "nfact_pp"). Defaults to "".
        style: str
            ttk frame style name. Defaults to "TFrame".

        Returns
        --------
            None: None object
                Constructs page header layout.
        """
        super().__init__(parent_container, style=style, padding=(16, 12, 16, 8))

        self.columnconfigure(0, weight=1)

        title_row = ttk.Frame(self, style=style)
        title_row.grid(row=0, column=0, sticky="ew")
        title_row.columnconfigure(0, weight=1)

        title_label = ttk.Label(
            title_row,
            text=title,
            style="PageTitle.TLabel",
        )
        title_label.grid(row=0, column=0, sticky="w")

        if cli_name:
            cli_badge = ttk.Label(
                title_row,
                text=cli_name,
                style="FlagBadge.TLabel",
            )
            cli_badge.grid(row=0, column=1, sticky="e", padx=(8, 0))

        subtitle_label = ttk.Label(
            self,
            text=description,
            style="PageSubtitle.TLabel",
        )
        subtitle_label.grid(row=1, column=0, sticky="w", pady=(2, 0))
