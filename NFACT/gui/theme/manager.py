"""
ThemeManager coordinating Tkinter named fonts, ttk.Style, and widget callbacks.
"""

import sys
import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

from NFACT.gui.theme.fonts import create_named_fonts, get_system_scalable_fonts
from NFACT.gui.theme.palette import Palette, dark_palette, light_palette
from NFACT.gui.theme.styles_base import configure_base_styles
from NFACT.gui.theme.styles_containers import configure_container_styles
from NFACT.gui.theme.styles_inputs import configure_input_styles


class ThemeManager:
    """Manager coordinating ttk.Style, fonts, and custom Tkinter theme updates.

    Usage
    -----
    theme_manager = ThemeManager(initial_theme="dark")
    theme_manager.apply_theme(root_window)
    theme_manager.toggle_theme(root_window)
    """

    def __init__(self, initial_theme: str = "dark") -> None:
        """Initialize the theme manager with an active theme mode.

        Parameters
        ------------
        initial_theme: str
            Starting theme mode ('dark' or 'light'). Defaults to "dark".

        Returns
        --------
            None: None object
                Initializes manager state.
        """
        self.current_theme = (
            initial_theme if initial_theme in ["dark", "light"] else "dark"
        )
        self.change_listeners: list[Callable[[Palette], None]] = []
        self.registered_widgets: list[tuple[object, Callable]] = []
        self.font_sans = "Liberation Sans"
        self.font_mono = "Liberation Mono"

    def apply_display_scaling(self, root_window: tk.Tk) -> float:
        """Set Tk scaling factor from true display DPI for crisp rendering.

        Parameters
        ------------
        root_window: tk.Tk
            Application root window.

        Returns
        --------
            float: scaling factor
                The calculated scaling factor applied.
        """
        try:
            if sys.platform == "darwin":
                return 1.0
            dpi_pixels = float(root_window.winfo_fpixels("1i"))
            scaling_factor = round(max(1.0, dpi_pixels / 72.0), 2)
            root_window.tk.call("tk", "scaling", scaling_factor)
            return scaling_factor
        except Exception:
            return 1.0

    def get_palette(self) -> Palette:
        """Return the active Palette tokens instance.

        Parameters
        ------------
        None

        Returns
        --------
            Palette: palette object
                Current active theme Palette object.
        """
        return dark_palette() if self.current_theme == "dark" else light_palette()

    def current_palette(self) -> Palette:
        """Convenience method returning the active Palette.

        Parameters
        ------------
        None

        Returns
        --------
            Palette: palette object
                Current active theme Palette object.
        """
        return self.get_palette()

    def register_listener(self, listener_callback: Callable[[Palette], None]) -> None:
        """Register a callback notified whenever the theme changes.

        Parameters
        ------------
        listener_callback: Callable[[Palette], None]
            Function accepting the new Palette instance.

        Returns
        --------
            None: None object
                Appends listener and immediately triggers it.
        """
        self.change_listeners.append(listener_callback)
        try:
            listener_callback(self.get_palette())
        except Exception as error_obj:
            sys.stderr.write(
                f"[NFACT GUI] Theme listener notification error: {error_obj}\n"
            )

    def register_widget(
        self, widget_instance: object, update_callback: Callable
    ) -> None:
        """Register a non-ttk widget or custom component for theme updates.

        Parameters
        ------------
        widget_instance: object
            Widget or component reference.
        update_callback: Callable
            Function called with palette when theme updates.

        Returns
        --------
            None: None object
                Registers widget and calls update_callback immediately.
        """
        self.registered_widgets.append((widget_instance, update_callback))
        try:
            update_callback(self.get_palette())
        except Exception as error_obj:
            sys.stderr.write(f"[NFACT GUI] Widget update callback error: {error_obj}\n")

    def apply_theme(
        self, root_window: tk.Tk, target_theme: Optional[str] = None
    ) -> None:
        """Apply active theme styles and fonts to the root window.

        Parameters
        ------------
        root_window: tk.Tk
            Main Tkinter root window or toplevel container.
        target_theme: Optional[str]
            Optional target theme name ('dark' or 'light'). Defaults to None.

        Returns
        --------
            None: None object
                Applies theme styles across the application.
        """
        if target_theme in ["dark", "light"]:
            self.current_theme = target_theme

        palette = self.get_palette()
        style_engine = ttk.Style(root_window)

        # Detect scalable fonts and setup named fonts
        self.apply_display_scaling(root_window)
        sans_name, mono_name = get_system_scalable_fonts(root_window)
        self.font_sans = sans_name
        self.font_mono = mono_name
        create_named_fonts(root_window)

        # Base ttk theme
        available_themes = style_engine.theme_names()
        if "clam" in available_themes:
            style_engine.theme_use("clam")

        # Configure root background
        root_window.configure(bg=palette.bg_primary)

        # Configure Option Database for popups / combobox listboxes
        root_window.option_add("*TCombobox*Listbox.background", palette.bg_input)
        root_window.option_add("*TCombobox*Listbox.foreground", palette.fg_primary)
        root_window.option_add(
            "*TCombobox*Listbox.selectBackground", palette.accent_primary
        )
        root_window.option_add("*TCombobox*Listbox.selectForeground", "#FFFFFF")
        root_window.option_add("*TCombobox*Listbox.font", "NFACTBody")

        # Configure all style categories
        configure_base_styles(style_engine, palette)
        configure_input_styles(style_engine, palette)
        configure_container_styles(style_engine, palette)

        # Notify registered widgets
        for _, update_callback in self.registered_widgets:
            try:
                update_callback(palette)
            except Exception as error_obj:
                sys.stderr.write(
                    f"[NFACT GUI] Registered widget update error: {error_obj}\n"
                )

        # Notify general change listeners
        for listener in self.change_listeners:
            try:
                listener(palette)
            except Exception as error_obj:
                sys.stderr.write(f"[NFACT GUI] Change listener error: {error_obj}\n")

    def toggle_theme(self, root_window: tk.Tk) -> str:
        """Toggle between 'dark' and 'light' modes and re-apply styles.

        Parameters
        ------------
        root_window: tk.Tk
            Main Tkinter root window.

        Returns
        --------
            str: new theme
                The newly activated theme name ('dark' or 'light').
        """
        new_theme = "light" if self.current_theme == "dark" else "dark"
        self.apply_theme(root_window, new_theme)
        return new_theme

    def set_theme(self, theme_name: str, root_window: Optional[tk.Tk] = None) -> None:
        """Set active theme to 'dark' or 'light'.

        Parameters
        ------------
        theme_name: str
            Theme name ('dark' or 'light').
        root_window: Optional[tk.Tk]
            Root Tkinter window. Defaults to None.

        Returns
        --------
            None: None object
                Sets theme and optionally applies it.
        """
        if theme_name in ["dark", "light"]:
            self.current_theme = theme_name
            if root_window is not None:
                self.apply_theme(root_window, theme_name)
