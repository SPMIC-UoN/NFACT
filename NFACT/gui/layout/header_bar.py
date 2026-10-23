"""
Top header bar featuring branding, working directory chip, and theme toggle.
"""

import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Any, Callable

from NFACT.gui.widgets.tooltip import HoverTooltip


def _truncate_path_middle(full_path: str, max_chars: int = 36) -> str:
    """Shorten long path with middle ellipsis for compact chip display.

    Parameters
    ------------
    full_path: str
        Original full directory path.
    max_chars: int
        Maximum length allowed. Defaults to 36.

    Returns
    --------
        str: truncated path
            Abbreviated directory string.
    """
    if len(full_path) <= max_chars:
        return full_path
    half_budget = (max_chars - 3) // 2
    return f"{full_path[:half_budget]}...{full_path[-half_budget:]}"


class HeaderBar(ttk.Frame):
    """Top application header bar with branding, working directory, and controls.

    Usage
    -----
    header = HeaderBar(root_window, theme_manager, on_change_dir, on_toggle_theme)
    """

    def __init__(
        self,
        parent_container: tk.Widget,
        current_workdir: str,
        theme_manager: Any,
        on_change_workdir: Callable[[str], None],
        on_toggle_theme: Callable[[], None],
        style: str = "Header.TFrame",
    ) -> None:
        """Initialize header bar.

        Parameters
        ------------
        parent_container: tk.Widget
            Parent window.
        current_workdir: str
            Initial working directory path.
        theme_manager: Any
            ThemeManager reference.
        on_change_workdir: Callable[[str], None]
            Callback invoked when user changes the working directory.
        on_toggle_theme: Callable[[], None]
            Callback invoked when user clicks theme toggle.
        style: str
            ttk frame style name. Defaults to "Header.TFrame".

        Returns
        --------
            None: None object
                Constructs header elements.
        """
        super().__init__(parent_container, style=style, padding=(12, 6, 12, 6))
        self.current_workdir = current_workdir
        self.theme_manager = theme_manager
        self.on_change_workdir = on_change_workdir
        self.on_toggle_theme = on_toggle_theme

        self.columnconfigure(1, weight=1)

        # 1. Branding: Logo Diamond + NFACT + Subtitle
        brand_group = ttk.Frame(self, style=style)
        brand_group.grid(row=0, column=0, sticky="w")

        self.logo_canvas = tk.Canvas(
            brand_group,
            width=18,
            height=18,
            highlightthickness=0,
            borderwidth=0,
            bg="#1F1B2B",
        )
        self.logo_canvas.pack(side="left", padx=(0, 6))
        self._draw_diamond_logo()

        self.brand_title = ttk.Label(
            brand_group,
            text="NFACT",
            style="HeaderTitle.TLabel",
        )
        self.brand_title.pack(side="left", padx=(0, 6))

        self.brand_subtitle = ttk.Label(
            brand_group,
            text="Tractography Factorisation",
            style="HeaderSubtitle.TLabel",
        )
        self.brand_subtitle.pack(side="left", padx=(0, 16))

        # 2. Centre: Working Directory Chip
        workdir_group = ttk.Frame(self, style=style)
        workdir_group.grid(row=0, column=1, sticky="w", padx=8)

        truncated_text = _truncate_path_middle(self.current_workdir)
        self.workdir_button = ttk.Button(
            workdir_group,
            text=f" 📂 {truncated_text} ",
            command=self._select_working_directory,
            style="Ghost.TButton",
        )
        self.workdir_button.pack(side="left")
        self.workdir_tooltip = HoverTooltip(
            self.workdir_button,
            f"Working Directory: {self.current_workdir}\nClick to change.",
        )

        # 3. Right: Theme Toggle & About Buttons
        controls_group = ttk.Frame(self, style=style)
        controls_group.grid(row=0, column=2, sticky="e")

        theme_icon = (
            "☀ Light Mode"
            if self.theme_manager.current_theme == "dark"
            else "☾ Dark Mode"
        )
        self.theme_button = ttk.Button(
            controls_group,
            text=theme_icon,
            command=self.on_toggle_theme,
            style="Header.TButton",
            width=12,
        )
        self.theme_button.pack(side="left", padx=(0, 6))
        HoverTooltip(self.theme_button, "Toggle between Dark and Light color modes.")

        self.about_button = ttk.Button(
            controls_group,
            text="ⓘ About",
            command=self._show_about_dialog,
            style="Header.TButton",
            width=8,
        )
        self.about_button.pack(side="left")

        # Bottom 1-px separator
        bottom_sep = ttk.Separator(self, orient="horizontal")
        bottom_sep.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(6, 0))

        if self.theme_manager is not None:
            self.theme_manager.register_widget(self, self.apply_palette)

    def _draw_diamond_logo(self) -> None:
        """Draw small diamond brand icon in canvas.

        Parameters
        ------------
        None

        Returns
        --------
            None: None object
                Draws diamond polygon.
        """
        self.logo_canvas.delete("all")
        palette = (
            self.theme_manager.get_palette() if self.theme_manager is not None else None
        )
        accent_color = palette.accent_primary if palette is not None else "#E91E8C"
        bg_surface = palette.bg_surface if palette is not None else "#1F1B2B"
        self.logo_canvas.configure(bg=bg_surface)
        self.logo_canvas.create_polygon(
            9,
            1,
            17,
            9,
            9,
            17,
            1,
            9,
            fill=accent_color,
            outline="",
        )

    def _select_working_directory(self) -> None:
        """Open directory chooser to update application working directory.

        Parameters
        ------------
        None

        Returns
        --------
            None: None object
                Updates current directory and triggers callback.
        """
        new_dir = filedialog.askdirectory(
            parent=self,
            title="Select Working Directory",
            initialdir=self.current_workdir,
        )
        if new_dir:
            self.current_workdir = new_dir
            truncated_name = _truncate_path_middle(new_dir)
            self.workdir_button.configure(text=f" 📂 {truncated_name} ")
            self.workdir_tooltip.tooltip_text = (
                f"Working Directory: {new_dir}\nClick to change."
            )
            try:
                os.chdir(new_dir)
            except OSError:
                pass
            self.on_change_workdir(new_dir)

    def update_theme_label(self, current_theme_name: str) -> None:
        """Update toggle button label to match current theme.

        Parameters
        ------------
        current_theme_name: str
            Active theme name ('dark' or 'light').

        Returns
        --------
            None: None object
                Updates theme button text.
        """
        button_text = "☀ Light Mode" if current_theme_name == "dark" else "☾ Dark Mode"
        self.theme_button.configure(text=button_text)

    def _show_about_dialog(self) -> None:
        """Show informative About dialog for NFACT.

        Parameters
        ------------
        None

        Returns
        --------
            None: None object
                Displays modal about message.
        """
        about_text = (
            "NFACT - Non-negative Matrix Factorisation of Tractography Data\n\n"
            "An integrated software suite for whole-brain and targeted tractography\n"
            "decomposition, dual regression, and statistical analysis.\n\n"
            "Built with standard library Tkinter.\n"
            "Repository: https://github.com/dhaimand/NFACT"
        )
        messagebox.showinfo("About NFACT GUI", about_text, parent=self)

    def apply_palette(self, palette_tokens: Any) -> None:
        """Update header canvas icon and colors on theme switch.

        Parameters
        ------------
        palette_tokens: Any
            Color palette tokens object or mapping.

        Returns
        --------
            None: None object
                Redraws logo diamond with new accent.
        """
        self._draw_diamond_logo()
