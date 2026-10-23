"""
Navigation sidebar providing module selection and section groupings.
"""

from dataclasses import dataclass
import tkinter as tk
from tkinter import ttk
from typing import Any, Callable, Optional


@dataclass(frozen=True)
class NavItem:
    """Navigation destination descriptor.

    Usage
    -----
    item = NavItem(title="Pre-processing", cli_name="nfact_pp", section="MODULES")
    """

    title: str
    cli_name: str
    section: str


class NavSidebar(ttk.Frame):
    """Left navigation sidebar component with section groupings and active indicator.

    Usage
    -----
    sidebar = NavSidebar(parent_frame, items=item_list, on_select=switch_page)
    """

    def __init__(
        self,
        parent_container: tk.Widget,
        items: list[NavItem],
        on_select: Callable[[int], None],
        theme_manager: Optional[Any] = None,
        style: str = "Sidebar.TFrame",
        width: int = 210,
    ) -> None:
        """Initialize navigation sidebar.

        Parameters
        ------------
        parent_container: tk.Widget
            Parent container widget.
        items: list[NavItem]
            List of navigation destinations.
        on_select: Callable[[int], None]
            Callback invoked with selected page index.
        theme_manager: Optional[Any]
            ThemeManager reference for dynamic updates. Defaults to None.
        style: str
            ttk frame style name. Defaults to "Sidebar.TFrame".
        width: int
            Fixed pixel width of sidebar. Defaults to 210.

        Returns
        --------
            None: None object
                Constructs sidebar navigation layout.
        """
        super().__init__(parent_container, style=style, width=width)
        self.items = items
        self.on_select = on_select
        self.theme_manager = theme_manager
        self.selected_index = 0

        self.item_frames: list[tk.Frame] = []
        self.accent_bars: list[tk.Frame] = []
        self.title_labels: list[ttk.Label] = []
        self.cli_labels: list[ttk.Label] = []

        self.columnconfigure(0, weight=1)
        self.rowconfigure(999, weight=1)

        self._build_nav_items()

        if self.theme_manager is not None:
            self.theme_manager.register_widget(self, self.apply_palette)

    def _build_nav_items(self) -> None:
        """Construct sidebar section headers and navigation rows.

        Parameters
        ------------
        None

        Returns
        --------
            None: None object
                Builds items into sidebar.
        """
        current_section = ""
        grid_row = 0

        for item_index, item in enumerate(self.items):
            if item.section != current_section:
                current_section = item.section
                section_label = ttk.Label(
                    self,
                    text=current_section,
                    style="NavSection.TLabel",
                )
                section_label.grid(
                    row=grid_row,
                    column=0,
                    sticky="w",
                    padx=(14, 8),
                    pady=(12 if grid_row > 0 else 8, 4),
                )
                grid_row += 1

            row_container = tk.Frame(
                self,
                background="#15131D",
                cursor="hand2",
            )
            row_container.grid(
                row=grid_row, column=0, sticky="ew", padx=(4, 4), pady=(1, 1)
            )
            row_container.columnconfigure(1, weight=1)

            accent_bar = tk.Frame(
                row_container,
                width=3,
                background="#E91E8C" if item_index == 0 else "#15131D",
            )
            accent_bar.grid(row=0, column=0, rowspan=2, sticky="ns", padx=(0, 8))

            title_style = (
                "NavItemActive.TLabel" if item_index == 0 else "NavItem.TLabel"
            )
            title_lbl = ttk.Label(
                row_container,
                text=item.title,
                style=title_style,
                cursor="hand2",
            )
            title_lbl.grid(row=0, column=1, sticky="w", pady=(3, 0))

            cli_lbl = ttk.Label(
                row_container,
                text=item.cli_name,
                style="Muted.TLabel",
                cursor="hand2",
            )
            cli_lbl.grid(row=1, column=1, sticky="w", pady=(0, 3))

            self.item_frames.append(row_container)
            self.accent_bars.append(accent_bar)
            self.title_labels.append(title_lbl)
            self.cli_labels.append(cli_lbl)

            # Bind clicks
            self._bind_row_events(row_container, item_index)
            self._bind_row_events(title_lbl, item_index)
            self._bind_row_events(cli_lbl, item_index)

            grid_row += 1

    def _bind_row_events(self, widget_target: tk.Widget, target_index: int) -> None:
        """Bind click and hover interactions to a navigation widget.

        Parameters
        ------------
        widget_target: tk.Widget
            Target widget element.
        target_index: int
            Index of navigation item.

        Returns
        --------
            None: None object
                Attaches event bindings.
        """
        widget_target.bind("<Button-1>", lambda event_obj: self.select(target_index))

    def select(self, target_index: int) -> None:
        """Select a navigation item and invoke selection callback.

        Parameters
        ------------
        target_index: int
            Index of page to activate.

        Returns
        --------
            None: None object
                Updates visual state and triggers on_select.
        """
        if target_index < 0 or target_index >= len(self.items):
            return

        self.selected_index = target_index

        palette = (
            self.theme_manager.get_palette() if self.theme_manager is not None else None
        )
        accent_color = palette.accent_primary if palette is not None else "#E91E8C"
        bg_primary = palette.bg_primary if palette is not None else "#15131D"

        for idx, (accent_frame, title_label) in enumerate(
            zip(self.accent_bars, self.title_labels)
        ):
            if idx == target_index:
                accent_frame.configure(background=accent_color)
                title_label.configure(style="NavItemActive.TLabel")
            else:
                accent_frame.configure(background=bg_primary)
                title_label.configure(style="NavItem.TLabel")

        self.on_select(target_index)

    def apply_palette(self, palette_tokens: Any) -> None:
        """Update navigation row backgrounds and accent bar colors.

        Parameters
        ------------
        palette_tokens: Any
            Color palette tokens object or mapping.

        Returns
        --------
            None: None object
                Updates sidebar colors in-place.
        """
        bg_primary = (
            palette_tokens["bg_primary"]
            if "bg_primary" in palette_tokens
            else getattr(palette_tokens, "bg_primary", "#15131D")
        )
        accent_primary = (
            palette_tokens["accent_primary"]
            if "accent_primary" in palette_tokens
            else getattr(palette_tokens, "accent_primary", "#E91E8C")
        )

        for idx, (row_frame, accent_frame) in enumerate(
            zip(self.item_frames, self.accent_bars)
        ):
            row_frame.configure(background=bg_primary)
            if idx == self.selected_index:
                accent_frame.configure(background=accent_primary)
            else:
                accent_frame.configure(background=bg_primary)
