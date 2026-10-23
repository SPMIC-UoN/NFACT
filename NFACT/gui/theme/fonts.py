"""
Scalable system font detection and Tkinter named font configuration.
"""

import tkinter as tk
from tkinter import font as tkfont
from typing import Optional

from NFACT.gui.theme.palette import FontSizes


def get_system_scalable_fonts(
    root_window: Optional[tk.Tk] = None,
) -> tuple[str, str]:
    """Detect the highest-quality scalable TrueType font families.

    Parameters
    ------------
    root_window: Optional[tk.Tk]
        Root Tkinter window. Defaults to None.

    Returns
    --------
        tuple[str, str]: font families
            Pair of (sans_serif_family, monospace_family).
    """
    if root_window is not None:
        try:
            available_families = {
                str(font_name).lower(): str(font_name)
                for font_name in tkfont.families(root_window)
            }
        except Exception:
            available_families = {}
    else:
        available_families = {}

    sans_priority = [
        "inter",
        "noto sans",
        "cantarell",
        "liberation sans",
        "dejavu sans",
        "ubuntu",
        "segoe ui",
        "sf pro display",
        "helvetica neue",
        "arial",
    ]
    mono_priority = [
        "jetbrains mono",
        "noto sans mono",
        "liberation mono",
        "dejavu sans mono",
        "ubuntu mono",
        "consolas",
        "menlo",
        "courier new",
    ]

    detected_sans = next(
        (available_families[key] for key in sans_priority if key in available_families),
        "Liberation Sans",
    )
    detected_mono = next(
        (available_families[key] for key in mono_priority if key in available_families),
        "Liberation Mono",
    )

    return (detected_sans, detected_mono)


def create_named_fonts(
    root_window: tk.Tk,
    sizes: Optional[FontSizes] = None,
) -> dict[str, tkfont.Font]:
    """Register application-wide named fonts with Tkinter.

    Parameters
    ------------
    root_window: tk.Tk
        Root Tkinter window.
    sizes: Optional[FontSizes]
        Font sizes scale. Defaults to None.

    Returns
    --------
        dict[str, tkfont.Font]: font mapping
            Dictionary mapping font identifier names to tkfont.Font objects.
    """
    scale_sizes = sizes if sizes is not None else FontSizes()
    sans_family, mono_family = get_system_scalable_fonts(root_window)

    font_specs = {
        "NFACTTitle": (sans_family, scale_sizes.title, "bold"),
        "NFACTSection": (sans_family, scale_sizes.section, "bold"),
        "NFACTBody": (sans_family, scale_sizes.body, "normal"),
        "NFACTBodyBold": (sans_family, scale_sizes.body_bold, "bold"),
        "NFACTCaption": (sans_family, scale_sizes.caption, "normal"),
        "NFACTMono": (mono_family, scale_sizes.mono, "normal"),
        "NFACTMonoSmall": (mono_family, scale_sizes.mono_small, "normal"),
    }

    created_fonts: dict[str, tkfont.Font] = {}
    for font_name, (family, size, weight) in font_specs.items():
        try:
            named_instance = tkfont.nametofont(font_name)
            named_instance.configure(family=family, size=size, weight=weight)
            created_fonts[font_name] = named_instance
        except tk.TclError:
            created_fonts[font_name] = tkfont.Font(
                root_window,
                name=font_name,
                family=family,
                size=size,
                weight=weight,
            )

    standard_mappings = [
        ("TkDefaultFont", sans_family, scale_sizes.body, "normal"),
        ("TkTextFont", sans_family, scale_sizes.body, "normal"),
        ("TkHeadingFont", sans_family, scale_sizes.section, "bold"),
        ("TkCaptionFont", sans_family, scale_sizes.caption, "normal"),
        ("TkSmallCaptionFont", sans_family, scale_sizes.caption, "normal"),
        ("TkMenuFont", sans_family, scale_sizes.body, "normal"),
        ("TkFixedFont", mono_family, scale_sizes.mono, "normal"),
    ]
    for tk_name, family, size, weight in standard_mappings:
        try:
            tkfont.nametofont(tk_name).configure(
                family=family, size=size, weight=weight
            )
        except Exception:
            pass

    return created_fonts
