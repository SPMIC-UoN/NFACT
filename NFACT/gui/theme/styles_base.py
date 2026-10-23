"""
Base ttk style configuration for frames, labels, buttons, and separators.
"""

from tkinter import ttk

from NFACT.gui.theme.palette import Palette


def configure_base_styles(style_engine: ttk.Style, palette: Palette) -> None:
    """Configure foundational frame, label, button, and separator styles.

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
    # Frames
    style_engine.configure("TFrame", background=palette.bg_primary)
    style_engine.configure("Surface.TFrame", background=palette.bg_surface)
    style_engine.configure("SurfaceAlt.TFrame", background=palette.bg_surface_alt)
    style_engine.configure("Card.TFrame", background=palette.bg_surface)
    style_engine.configure("CardHeader.TFrame", background=palette.bg_surface_alt)
    style_engine.configure("Header.TFrame", background=palette.bg_surface)
    style_engine.configure("Sidebar.TFrame", background=palette.bg_primary)
    style_engine.configure("Console.TFrame", background=palette.bg_console)
    style_engine.configure("StatusBar.TFrame", background=palette.bg_surface)

    # Separators
    style_engine.configure(
        "TSeparator",
        background=palette.border_color,
    )

    # General Labels
    style_engine.configure(
        "TLabel",
        background=palette.bg_primary,
        foreground=palette.fg_primary,
        font="NFACTBody",
    )
    style_engine.configure(
        "Surface.TLabel",
        background=palette.bg_surface,
        foreground=palette.fg_primary,
        font="NFACTBody",
    )
    style_engine.configure(
        "SurfaceAlt.TLabel",
        background=palette.bg_surface_alt,
        foreground=palette.fg_primary,
        font="NFACTBody",
    )
    style_engine.configure(
        "Muted.TLabel",
        background=palette.bg_primary,
        foreground=palette.fg_secondary,
        font="NFACTCaption",
    )
    style_engine.configure(
        "Muted.Surface.TLabel",
        background=palette.bg_surface,
        foreground=palette.fg_secondary,
        font="NFACTCaption",
    )

    # Header and Navigation Labels
    style_engine.configure(
        "Header.TLabel",
        background=palette.bg_surface,
        foreground=palette.fg_primary,
        font="NFACTBody",
    )
    style_engine.configure(
        "HeaderTitle.TLabel",
        background=palette.bg_surface,
        foreground=palette.accent_primary,
        font="NFACTTitle",
    )
    style_engine.configure(
        "HeaderSubtitle.TLabel",
        background=palette.bg_surface,
        foreground=palette.fg_secondary,
        font="NFACTCaption",
    )
    style_engine.configure(
        "PageTitle.TLabel",
        background=palette.bg_primary,
        foreground=palette.fg_primary,
        font="NFACTTitle",
    )
    style_engine.configure(
        "PageSubtitle.TLabel",
        background=palette.bg_primary,
        foreground=palette.fg_secondary,
        font="NFACTCaption",
    )
    style_engine.configure(
        "CardTitle.TLabel",
        background=palette.bg_surface_alt,
        foreground=palette.accent_secondary,
        font="NFACTSection",
    )
    style_engine.configure(
        "CardChevron.TLabel",
        background=palette.bg_surface_alt,
        foreground=palette.fg_secondary,
        font="NFACTBodyBold",
    )
    style_engine.configure(
        "FlagBadge.TLabel",
        background=palette.bg_surface,
        foreground=palette.accent_tertiary,
        font="NFACTMonoSmall",
    )
    style_engine.configure(
        "Required.TLabel",
        background=palette.bg_surface,
        foreground=palette.accent_primary,
        font="NFACTBodyBold",
    )
    style_engine.configure(
        "NavItem.TLabel",
        background=palette.bg_primary,
        foreground=palette.fg_secondary,
        font="NFACTBody",
    )
    style_engine.configure(
        "NavItemActive.TLabel",
        background=palette.bg_primary,
        foreground=palette.accent_primary,
        font="NFACTBodyBold",
    )
    style_engine.configure(
        "NavSection.TLabel",
        background=palette.bg_primary,
        foreground=palette.fg_disabled,
        font="NFACTCaption",
    )

    # Status Labels
    style_engine.configure(
        "StatusIdle.TLabel",
        background=palette.bg_surface,
        foreground=palette.status_success,
        font="NFACTBody",
    )
    style_engine.configure(
        "StatusRunning.TLabel",
        background=palette.bg_surface,
        foreground=palette.status_running,
        font="NFACTBodyBold",
    )
    style_engine.configure(
        "StatusSuccess.TLabel",
        background=palette.bg_surface,
        foreground=palette.status_success,
        font="NFACTBody",
    )
    style_engine.configure(
        "StatusError.TLabel",
        background=palette.bg_surface,
        foreground=palette.status_error,
        font="NFACTBodyBold",
    )
    style_engine.configure(
        "ErrorText.Surface.TLabel",
        background=palette.bg_surface,
        foreground=palette.status_error,
        font="NFACTCaption",
    )

    # Buttons
    style_engine.configure(
        "TButton",
        background=palette.button_bg,
        foreground=palette.button_fg,
        bordercolor=palette.border_color,
        darkcolor=palette.button_bg,
        lightcolor=palette.button_bg,
        relief="flat",
        padding=(8, 4),
        font="NFACTBodyBold",
    )
    style_engine.map(
        "TButton",
        background=[
            ("active", palette.button_hover),
            ("pressed", palette.border_color),
            ("disabled", palette.border_color),
        ],
        foreground=[("disabled", palette.fg_disabled)],
    )

    style_engine.configure(
        "Accent.TButton",
        background=palette.accent_primary,
        foreground="#FFFFFF",
        bordercolor=palette.accent_primary,
        darkcolor=palette.accent_primary,
        lightcolor=palette.accent_primary,
        relief="flat",
        padding=(12, 6),
        font="NFACTBodyBold",
    )
    style_engine.map(
        "Accent.TButton",
        background=[
            ("active", palette.accent_hover),
            ("pressed", palette.accent_secondary),
            ("disabled", palette.border_color),
        ],
        foreground=[("disabled", palette.fg_disabled)],
    )

    style_engine.configure(
        "Danger.TButton",
        background=palette.danger_bg,
        foreground=palette.danger_fg,
        bordercolor=palette.danger_bg,
        darkcolor=palette.danger_bg,
        lightcolor=palette.danger_bg,
        relief="flat",
        padding=(12, 6),
        font="NFACTBodyBold",
    )
    style_engine.map(
        "Danger.TButton",
        background=[
            ("active", palette.danger_hover),
            ("pressed", palette.border_color),
            ("disabled", palette.border_color),
        ],
        foreground=[("disabled", palette.fg_disabled)],
    )

    style_engine.configure(
        "Ghost.TButton",
        background=palette.bg_surface,
        foreground=palette.fg_secondary,
        bordercolor=palette.bg_surface,
        darkcolor=palette.bg_surface,
        lightcolor=palette.bg_surface,
        relief="flat",
        padding=(6, 4),
        font="NFACTBody",
    )
    style_engine.map(
        "Ghost.TButton",
        background=[
            ("active", palette.bg_surface_alt),
            ("pressed", palette.border_color),
        ],
        foreground=[("active", palette.fg_primary)],
    )

    style_engine.configure(
        "Icon.TButton",
        background=palette.button_bg,
        foreground=palette.button_fg,
        bordercolor=palette.border_color,
        relief="flat",
        padding=(4, 2),
        font="NFACTBodyBold",
    )
    style_engine.map(
        "Icon.TButton",
        background=[
            ("active", palette.button_hover),
            ("pressed", palette.border_color),
        ],
    )

    style_engine.configure(
        "Header.TButton",
        background=palette.button_bg,
        foreground=palette.button_fg,
        bordercolor=palette.border_color,
        relief="flat",
        padding=(6, 4),
        font="NFACTBody",
    )
    style_engine.map(
        "Header.TButton",
        background=[
            ("active", palette.button_hover),
            ("pressed", palette.border_color),
        ],
    )
