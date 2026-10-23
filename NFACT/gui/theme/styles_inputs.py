"""
Style configuration for inputs, choice widgets, spinboxes, and scrollbars.
"""

from tkinter import ttk

from NFACT.gui.theme.palette import Palette


def configure_input_styles(style_engine: ttk.Style, palette: Palette) -> None:
    """Configure input fields, spinboxes, selectors, and scrollbars.

    Parameters
    ------------
    style_engine: ttk.Style
        Tkinter ttk style manager.
    palette: Palette
        Current color palette tokens.

    Returns
    --------
        None: None object
            Applies styles in-place.
    """
    # Entries
    style_engine.configure(
        "TEntry",
        fieldbackground=palette.bg_input,
        foreground=palette.fg_primary,
        insertcolor=palette.fg_primary,
        bordercolor=palette.border_color,
        lightcolor=palette.border_color,
        darkcolor=palette.border_color,
        padding=5,
        font="NFACTBody",
    )
    style_engine.map(
        "TEntry",
        bordercolor=[
            ("focus", palette.border_focus),
            ("disabled", palette.border_color),
        ],
        lightcolor=[("focus", palette.border_focus)],
        darkcolor=[("focus", palette.border_focus)],
    )

    style_engine.configure(
        "Invalid.TEntry",
        fieldbackground=palette.bg_input,
        foreground=palette.fg_primary,
        insertcolor=palette.fg_primary,
        bordercolor=palette.status_error,
        lightcolor=palette.status_error,
        darkcolor=palette.status_error,
        padding=5,
        font="NFACTBody",
    )
    style_engine.map(
        "Invalid.TEntry",
        bordercolor=[("focus", palette.status_error)],
        lightcolor=[("focus", palette.status_error)],
        darkcolor=[("focus", palette.status_error)],
    )

    # Comboboxes
    style_engine.configure(
        "TCombobox",
        fieldbackground=palette.bg_input,
        background=palette.button_bg,
        foreground=palette.fg_primary,
        darkcolor=palette.border_color,
        lightcolor=palette.border_color,
        arrowcolor=palette.fg_primary,
        padding=4,
        font="NFACTBody",
    )
    style_engine.map(
        "TCombobox",
        fieldbackground=[("readonly", palette.bg_input)],
        selectbackground=[("readonly", palette.bg_input)],
        selectforeground=[("readonly", palette.fg_primary)],
        bordercolor=[("focus", palette.border_focus)],
    )

    # Spinboxes
    style_engine.configure(
        "TSpinbox",
        fieldbackground=palette.bg_input,
        background=palette.button_bg,
        foreground=palette.fg_primary,
        bordercolor=palette.border_color,
        lightcolor=palette.border_color,
        darkcolor=palette.border_color,
        arrowcolor=palette.fg_primary,
        padding=4,
        font="NFACTBody",
    )
    style_engine.map(
        "TSpinbox",
        bordercolor=[
            ("focus", palette.border_focus),
            ("disabled", palette.border_color),
        ],
        lightcolor=[("focus", palette.border_focus)],
        darkcolor=[("focus", palette.border_focus)],
    )

    style_engine.configure(
        "Invalid.TSpinbox",
        fieldbackground=palette.bg_input,
        foreground=palette.fg_primary,
        bordercolor=palette.status_error,
        lightcolor=palette.status_error,
        darkcolor=palette.status_error,
        arrowcolor=palette.fg_primary,
        padding=4,
        font="NFACTBody",
    )

    # Checkbuttons
    style_engine.configure(
        "TCheckbutton",
        background=palette.bg_primary,
        foreground=palette.fg_primary,
        font="NFACTBody",
        indicatorcolor=palette.bg_input,
        indicatorrelief="flat",
    )
    style_engine.map(
        "TCheckbutton",
        indicatorcolor=[
            ("selected", palette.accent_primary),
            ("active", palette.border_focus),
        ],
        background=[("active", palette.bg_primary)],
    )

    style_engine.configure(
        "Surface.TCheckbutton",
        background=palette.bg_surface,
        foreground=palette.fg_primary,
        font="NFACTBody",
        indicatorcolor=palette.bg_input,
        indicatorrelief="flat",
    )
    style_engine.map(
        "Surface.TCheckbutton",
        indicatorcolor=[
            ("selected", palette.accent_primary),
            ("active", palette.border_focus),
        ],
        background=[("active", palette.bg_surface)],
    )

    # Radiobuttons
    style_engine.configure(
        "TRadiobutton",
        background=palette.bg_primary,
        foreground=palette.fg_primary,
        font="NFACTBody",
        indicatorcolor=palette.bg_input,
        indicatorrelief="flat",
    )
    style_engine.map(
        "TRadiobutton",
        indicatorcolor=[
            ("selected", palette.accent_primary),
            ("active", palette.border_focus),
        ],
        background=[("active", palette.bg_primary)],
    )

    style_engine.configure(
        "Surface.TRadiobutton",
        background=palette.bg_surface,
        foreground=palette.fg_primary,
        font="NFACTBody",
        indicatorcolor=palette.bg_input,
        indicatorrelief="flat",
    )
    style_engine.map(
        "Surface.TRadiobutton",
        indicatorcolor=[
            ("selected", palette.accent_primary),
            ("active", palette.border_focus),
        ],
        background=[("active", palette.bg_surface)],
    )

    # Segmented Radiobutton
    style_engine.configure(
        "Segment.TRadiobutton",
        background=palette.button_bg,
        foreground=palette.button_fg,
        font="NFACTBodyBold",
        padding=(10, 4),
        indicatoron=0,
    )
    style_engine.map(
        "Segment.TRadiobutton",
        background=[
            ("selected", palette.accent_primary),
            ("active", palette.button_hover),
        ],
        foreground=[
            ("selected", "#FFFFFF"),
            ("active", palette.fg_primary),
        ],
    )

    # Labelframe
    style_engine.configure(
        "TLabelframe",
        background=palette.bg_surface,
        bordercolor=palette.border_color,
        darkcolor=palette.border_color,
        lightcolor=palette.border_color,
        relief="solid",
        borderwidth=1,
    )
    style_engine.configure(
        "TLabelframe.Label",
        background=palette.bg_surface,
        foreground=palette.accent_secondary,
        font="NFACTSection",
    )

    # Scrollbars (thin, modern style)
    style_engine.configure(
        "Vertical.TScrollbar",
        background=palette.button_bg,
        bordercolor=palette.bg_primary,
        arrowcolor=palette.fg_secondary,
        troughcolor=palette.bg_primary,
        relief="flat",
        arrowsize=0,
        gripcount=0,
        width=10,
    )
    style_engine.map(
        "Vertical.TScrollbar",
        background=[("active", palette.fg_secondary)],
    )

    style_engine.configure(
        "Horizontal.TScrollbar",
        background=palette.button_bg,
        bordercolor=palette.bg_primary,
        arrowcolor=palette.fg_secondary,
        troughcolor=palette.bg_primary,
        relief="flat",
        arrowsize=0,
        gripcount=0,
        width=10,
    )
    style_engine.map(
        "Horizontal.TScrollbar",
        background=[("active", palette.fg_secondary)],
    )
