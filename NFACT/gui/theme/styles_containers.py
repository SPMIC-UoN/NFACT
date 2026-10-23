"""
Style configuration for containers, notebooks, treeviews, and progress bars.
"""

from tkinter import ttk

from NFACT.gui.theme.palette import Palette


def configure_container_styles(style_engine: ttk.Style, palette: Palette) -> None:
    """Configure notebook, treeview, paned window, and progress bar styles.

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
    # PanedWindow & Sash
    style_engine.configure(
        "TPanedwindow",
        background=palette.bg_primary,
    )
    style_engine.configure(
        "Sash",
        background=palette.border_color,
        sashthickness=6,
    )

    # Standard Notebook (used for log console drawer)
    style_engine.configure(
        "TNotebook",
        background=palette.bg_surface,
        bordercolor=palette.border_color,
        tabmargins=[2, 4, 2, 0],
    )
    style_engine.configure(
        "TNotebook.Tab",
        background=palette.button_bg,
        foreground=palette.fg_secondary,
        bordercolor=palette.border_color,
        padding=[14, 6],
        font="NFACTBodyBold",
    )
    style_engine.map(
        "TNotebook.Tab",
        background=[
            ("selected", palette.accent_primary),
            ("active", palette.button_hover),
        ],
        foreground=[
            ("selected", "#FFFFFF"),
            ("active", palette.fg_primary),
        ],
        bordercolor=[("selected", palette.accent_primary)],
    )

    # Hidden Notebook (for sidebar page switching without visible tabs)
    style_engine.configure(
        "Hidden.TNotebook",
        background=palette.bg_primary,
        borderwidth=0,
        highlightthickness=0,
    )
    try:
        style_engine.layout("Hidden.TNotebook.Tab", [])
    except Exception:
        pass

    # Treeview
    style_engine.configure(
        "Treeview",
        background=palette.bg_input,
        foreground=palette.fg_primary,
        fieldbackground=palette.bg_input,
        bordercolor=palette.border_color,
        rowheight=28,
        font="NFACTMonoSmall",
    )
    style_engine.map(
        "Treeview",
        background=[("selected", palette.accent_primary)],
        foreground=[("selected", "#FFFFFF")],
    )
    style_engine.configure(
        "Treeview.Heading",
        background=palette.bg_surface_alt,
        foreground=palette.fg_primary,
        relief="flat",
        font="NFACTBodyBold",
        padding=(6, 4),
    )

    # Progressbar
    style_engine.configure(
        "Horizontal.TProgressbar",
        background=palette.accent_primary,
        troughcolor=palette.bg_surface_alt,
        bordercolor=palette.border_color,
        lightcolor=palette.accent_primary,
        darkcolor=palette.accent_primary,
    )
