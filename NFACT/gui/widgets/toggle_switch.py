"""
Interactive canvas toggle switch widget bound to a BooleanVar.
"""

import tkinter as tk
from tkinter import ttk
from typing import Any, Optional

from NFACT.gui.widgets.field_label import FieldLabel
from NFACT.gui.widgets.tooltip import HoverTooltip


class ToggleSwitch(tk.Canvas):
    """Modern rounded pill toggle switch widget bound to a BooleanVar.

    Usage
    -----
    switch = ToggleSwitch(parent_frame, variable=my_bool_var)
    """

    def __init__(
        self,
        parent_container: tk.Widget,
        variable: tk.BooleanVar,
        width: int = 36,
        height: int = 20,
        theme_manager: Optional[Any] = None,
    ) -> None:
        """Initialize toggle switch canvas.

        Parameters
        ------------
        parent_container: tk.Widget
            Parent widget container.
        variable: tk.BooleanVar
            Bound boolean variable.
        width: int
            Width of toggle track in pixels. Defaults to 36.
        height: int
            Height of toggle track in pixels. Defaults to 20.
        theme_manager: Optional[Any]
            ThemeManager for color palette updates. Defaults to None.

        Returns
        --------
            None: None object
                Constructs canvas and binds events.
        """
        super().__init__(
            parent_container,
            width=width,
            height=height,
            highlightthickness=0,
            borderwidth=0,
            cursor="hand2",
            takefocus=True,
        )
        self.variable = variable
        self.track_width = width
        self.track_height = height
        self.theme_manager = theme_manager

        self.color_on = "#E91E8C"
        self.color_off = "#332C47"
        self.color_knob = "#FFFFFF"
        self.bg_parent = "#1F1B2B"

        self.bind("<Button-1>", self._on_click)
        self.bind("<space>", self._on_click)
        self.bind("<FocusIn>", self._on_focus)
        self.bind("<FocusOut>", self._on_focus)
        self.variable.trace_add("write", lambda *args: self.redraw())

        if self.theme_manager is not None:
            self.theme_manager.register_widget(self, self.apply_palette)

        self.redraw()

    def _on_click(self, event_obj: Optional[tk.Event] = None) -> None:
        """Toggle variable value on click or space keypress.

        Parameters
        ------------
        event_obj: Optional[tk.Event]
            Event object. Defaults to None.

        Returns
        --------
            None: None object
                Flips BooleanVar.
        """
        self.variable.set(not self.variable.get())

    def _on_focus(self, event_obj: tk.Event) -> None:
        """Redraw switch with focus outline when focused.

        Parameters
        ------------
        event_obj: tk.Event
            Focus event.

        Returns
        --------
            None: None object
                Redraws switch.
        """
        self.redraw()

    def apply_palette(self, palette_tokens: Any) -> None:
        """Update switch colors from palette tokens.

        Parameters
        ------------
        palette_tokens: Any
            Color palette tokens object or mapping.

        Returns
        --------
            None: None object
                Updates colors and redraws.
        """
        self.color_on = (
            palette_tokens["accent_primary"]
            if "accent_primary" in palette_tokens
            else getattr(palette_tokens, "accent_primary", "#E91E8C")
        )
        self.color_off = (
            palette_tokens["border_color"]
            if "border_color" in palette_tokens
            else getattr(palette_tokens, "border_color", "#332C47")
        )
        self.bg_parent = (
            palette_tokens["bg_surface"]
            if "bg_surface" in palette_tokens
            else getattr(palette_tokens, "bg_surface", "#1F1B2B")
        )
        self.configure(bg=self.bg_parent)
        self.redraw()

    def redraw(self) -> None:
        """Redraw track and circular knob according to boolean state.

        Parameters
        ------------
        None

        Returns
        --------
            None: None object
                Clears canvas and draws toggle state.
        """
        self.delete("all")
        is_on = bool(self.variable.get())
        radius = (self.track_height - 4) // 2
        track_color = self.color_on if is_on else self.color_off

        # Draw rounded track
        self.create_oval(
            2,
            2,
            self.track_height - 2,
            self.track_height - 2,
            fill=track_color,
            outline=track_color,
        )
        self.create_oval(
            self.track_width - self.track_height + 2,
            2,
            self.track_width - 2,
            self.track_height - 2,
            fill=track_color,
            outline=track_color,
        )
        self.create_rectangle(
            radius + 2,
            2,
            self.track_width - radius - 2,
            self.track_height - 2,
            fill=track_color,
            outline=track_color,
        )

        # Draw circular knob
        if is_on:
            knob_center_x = self.track_width - radius - 3
        else:
            knob_center_x = radius + 3

        knob_center_y = self.track_height // 2
        knob_radius = radius - 1

        self.create_oval(
            knob_center_x - knob_radius,
            knob_center_y - knob_radius,
            knob_center_x + knob_radius,
            knob_center_y + knob_radius,
            fill=self.color_knob,
            outline="",
        )


def create_toggle(
    parent_frame: tk.Widget,
    text: str,
    variable: tk.BooleanVar,
    flag: str = "",
    tooltip_text: str = "",
    theme_manager: Optional[Any] = None,
    style: str = "Surface.TFrame",
) -> ttk.Frame:
    """Create a composite row containing a ToggleSwitch and its label.

    Parameters
    ------------
    parent_frame: tk.Widget
        Parent container widget.
    text: str
        Label description for toggle.
    variable: tk.BooleanVar
        Bound boolean variable.
    flag: str
        CLI option flag badge (e.g. "-O"). Defaults to "".
    tooltip_text: str
        Optional hover tooltip text. Defaults to "".
    theme_manager: Optional[Any]
        Theme manager for dynamic theme changes. Defaults to None.
    style: str
        Style name for frame. Defaults to "Surface.TFrame".

    Returns
    --------
        ttk.Frame: row frame
            Container frame holding switch and label.
    """
    row_frame = ttk.Frame(parent_frame, style=style)

    switch_widget = ToggleSwitch(
        row_frame,
        variable=variable,
        theme_manager=theme_manager,
    )
    switch_widget.pack(side="left", padx=(0, 8))

    label_widget = FieldLabel(
        row_frame,
        text=text,
        flag=flag,
        tooltip_text=tooltip_text,
        style=style,
    )
    label_widget.pack(side="left")

    if tooltip_text:
        HoverTooltip(switch_widget, tooltip_text)

    return row_frame
