"""
Floating tooltip popup widget on mouse hover for Tkinter widgets.
"""

import tkinter as tk
from typing import Optional


class HoverTooltip:
    """Floating tooltip popups on mouse hover for Tkinter widgets.

    Usage
    -----
    tooltip = HoverTooltip(widget_instance, "Description text for parameter")
    """

    def __init__(
        self,
        target_widget: tk.Widget,
        tooltip_text: str,
        delay_ms: int = 500,
    ) -> None:
        """Initialize hover tooltip.

        Parameters
        ------------
        target_widget: tk.Widget
            Widget to attach the hover tooltip to.
        tooltip_text: str
            Text string to display in the tooltip window.
        delay_ms: int
            Delay in milliseconds before display. Defaults to 500.

        Returns
        --------
            None: None object
                Sets up bindings on target widget.
        """
        self.target_widget = target_widget
        self.tooltip_text = tooltip_text
        self.delay_ms = delay_ms
        self.tooltip_window: Optional[tk.Toplevel] = None
        self.after_id: Optional[str] = None

        self.target_widget.bind("<Enter>", self._on_enter, add="+")
        self.target_widget.bind("<Leave>", self._on_leave, add="+")
        self.target_widget.bind("<ButtonPress>", self._on_leave, add="+")

    def _on_enter(self, event_obj: Optional[tk.Event] = None) -> None:
        """Handle mouse entering widget boundary.

        Parameters
        ------------
        event_obj: Optional[tk.Event]
            Tkinter event object. Defaults to None.

        Returns
        --------
            None: None object
                Schedules tooltip display.
        """
        self._cancel_schedule()
        self.after_id = self.target_widget.after(self.delay_ms, self._display_tooltip)

    def _on_leave(self, event_obj: Optional[tk.Event] = None) -> None:
        """Handle mouse leaving widget boundary.

        Parameters
        ------------
        event_obj: Optional[tk.Event]
            Tkinter event object. Defaults to None.

        Returns
        --------
            None: None object
                Cancels scheduled display and dismisses active tooltip.
        """
        self._cancel_schedule()
        self._dismiss_tooltip()

    def _cancel_schedule(self) -> None:
        """Cancel scheduled tooltip appearance.

        Parameters
        ------------
        None

        Returns
        --------
            None: None object
                Cancels after callback if pending.
        """
        if self.after_id is not None:
            self.target_widget.after_cancel(self.after_id)
            self.after_id = None

    def _display_tooltip(self) -> None:
        """Render and display the tooltip window next to the cursor.

        Parameters
        ------------
        None

        Returns
        --------
            None: None object
                Draws the tooltip popup window.
        """
        if not self.tooltip_text:
            return

        pos_x = self.target_widget.winfo_rootx() + 16
        pos_y = self.target_widget.winfo_rooty() + self.target_widget.winfo_height() + 4

        # Clamp inside screen dimensions
        screen_width = self.target_widget.winfo_screenwidth()
        screen_height = self.target_widget.winfo_screenheight()
        if pos_x + 380 > screen_width:
            pos_x = max(10, screen_width - 390)
        if pos_y + 80 > screen_height:
            pos_y = max(10, self.target_widget.winfo_rooty() - 50)

        self.tooltip_window = tk.Toplevel(self.target_widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{pos_x}+{pos_y}")

        container_frame = tk.Frame(
            self.tooltip_window,
            background="#272236",
            highlightbackground="#332C47",
            highlightthickness=1,
            borderwidth=0,
        )
        container_frame.pack(fill="both", expand=True)

        label_widget = tk.Label(
            container_frame,
            text=self.tooltip_text,
            justify="left",
            background="#272236",
            foreground="#EEEAF6",
            font="NFACTCaption",
            padx=8,
            pady=4,
            wraplength=360,
        )
        label_widget.pack()

    def _dismiss_tooltip(self) -> None:
        """Destroy active tooltip popup window.

        Parameters
        ------------
        None

        Returns
        --------
            None: None object
                Destroys the popup if visible.
        """
        if self.tooltip_window is not None:
            self.tooltip_window.destroy()
            self.tooltip_window = None
