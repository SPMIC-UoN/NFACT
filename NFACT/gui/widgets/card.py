"""
Card container frame with disclosure header, subtitle, and surface styling.
"""

import tkinter as tk
from tkinter import ttk
from typing import Any, Optional


class Card(tk.Frame):
    """Card container frame with disclosure header button, borders, and subtitle.

    Usage
    -----
    card = Card(parent_container, title="Cluster / SGE Options")
    inner_frame = card.content_frame
    """

    def __init__(
        self,
        parent_container: tk.Widget,
        title: str,
        subtitle: str = "",
        collapsible: bool = True,
        initially_expanded: bool = True,
        theme_manager: Optional[Any] = None,
    ) -> None:
        """Initialize card container.

        Parameters
        ------------
        parent_container: tk.Widget
            Parent widget container.
        title: str
            Card section header title.
        subtitle: str
            Optional subtitle description. Defaults to "".
        collapsible: bool
            Whether card can be collapsed or expanded. Defaults to True.
        initially_expanded: bool
            Whether card starts in expanded state. Defaults to True.
        theme_manager: Optional[Any]
            ThemeManager reference for dynamic palette registration. Defaults to None.

        Returns
        --------
            None: None object
                Constructs card frame and disclosure header.
        """
        super().__init__(
            parent_container,
            background="#6B5598",
            highlightbackground="#8C77B8",
            highlightthickness=1,
            borderwidth=0,
        )

        self.card_title = title
        self.card_subtitle = subtitle
        self.collapsible = collapsible
        self.expanded = initially_expanded if collapsible else True

        self.columnconfigure(0, weight=1)

        # Header strip
        self.header_frame = ttk.Frame(self, style="CardHeader.TFrame", padding=(12, 8))
        self.header_frame.grid(row=0, column=0, sticky="ew")
        self.header_frame.columnconfigure(1, weight=1)

        # Chevron indicator
        if self.collapsible:
            chevron_symbol = "▾" if self.expanded else "▸"
            self.chevron_label = ttk.Label(
                self.header_frame,
                text=chevron_symbol,
                style="CardChevron.TLabel",
            )
            self.chevron_label.grid(row=0, column=0, padx=(0, 6), sticky="w")
        else:
            self.chevron_label = None

        # Title
        self.title_label = ttk.Label(
            self.header_frame,
            text=self.card_title,
            style="CardTitle.TLabel",
        )
        self.title_label.grid(row=0, column=1, sticky="w")

        # Subtitle
        if self.card_subtitle:
            self.subtitle_label = ttk.Label(
                self.header_frame,
                text=self.card_subtitle,
                style="CardSubtitle.TLabel",
            )
            self.subtitle_label.grid(row=0, column=2, padx=(8, 0), sticky="w")

        # Content container
        self.content_frame = ttk.Frame(self, style="Surface.TFrame", padding=(12, 10))
        if self.expanded:
            self.content_frame.grid(row=1, column=0, sticky="nsew")

        if self.collapsible:
            self._bind_click_event(self.header_frame)
            self._bind_click_event(self.title_label)
            if self.chevron_label is not None:
                self._bind_click_event(self.chevron_label)

        if theme_manager is not None:
            theme_manager.register_widget(self, self.apply_palette)

    def _bind_click_event(self, widget_target: tk.Widget) -> None:
        """Bind mouse click to toggle expansion on header elements.

        Parameters
        ------------
        widget_target: tk.Widget
            Header widget to bind click on.

        Returns
        --------
            None: None object
                Binds Button-1 event.
        """
        widget_target.bind("<Button-1>", lambda event_obj: self.toggle())

    def toggle(self) -> None:
        """Toggle between expanded and collapsed states.

        Parameters
        ------------
        None

        Returns
        --------
            None: None object
                Flips expansion state.
        """
        if not self.collapsible:
            return

        if self.expanded:
            self.collapse()
        else:
            self.expand()

    def expand(self) -> None:
        """Expand the card content frame.

        Parameters
        ------------
        None

        Returns
        --------
            None: None object
                Displays content frame.
        """
        self.expanded = True
        if self.chevron_label is not None:
            self.chevron_label.configure(text="▾")
        self.content_frame.grid(row=1, column=0, sticky="nsew")

    def collapse(self) -> None:
        """Collapse the card content frame.

        Parameters
        ------------
        None

        Returns
        --------
            None: None object
                Hides content frame.
        """
        if not self.collapsible:
            return
        self.expanded = False
        if self.chevron_label is not None:
            self.chevron_label.configure(text="▸")
        self.content_frame.grid_forget()

    def is_expanded(self) -> bool:
        """Check whether the card is currently expanded.

        Parameters
        ------------
        None

        Returns
        --------
            bool: boolean flag
                True if expanded, False otherwise.
        """
        return self.expanded

    def set_enabled(self, is_enabled: bool) -> None:
        """Enable or grey out the card and its child inputs.

        Parameters
        ------------
        is_enabled: bool
            Whether card should be enabled or disabled.

        Returns
        --------
            None: None object
                Updates visual state and descendants.
        """
        target_state = "normal" if is_enabled else "disabled"
        for child_widget in self.content_frame.winfo_children():
            try:
                child_widget.configure(state=target_state)
            except Exception:
                pass

    def apply_palette(self, palette_tokens: Any) -> None:
        """Update container background and border colors on theme switch.

        Parameters
        ------------
        palette_tokens: Any
            Color palette tokens object or mapping.

        Returns
        --------
            None: None object
                Updates frame colors in-place.
        """
        bg_surface = (
            palette_tokens["bg_surface"]
            if "bg_surface" in palette_tokens
            else getattr(palette_tokens, "bg_surface", "#6B5598")
        )
        border_color = (
            palette_tokens["border_color"]
            if "border_color" in palette_tokens
            else getattr(palette_tokens, "border_color", "#8C77B8")
        )
        self.configure(
            background=bg_surface,
            highlightbackground=border_color,
        )


CollapsibleCard = Card
