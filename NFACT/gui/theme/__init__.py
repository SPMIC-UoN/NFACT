"""
Theme package for NFACT Graphical User Interface.
"""

from NFACT.gui.theme.fonts import (
    create_named_fonts,
    get_system_scalable_fonts,
)
from NFACT.gui.theme.manager import ThemeManager
from NFACT.gui.theme.palette import (
    DARK_THEME,
    LIGHT_THEME,
    FontSizes,
    Palette,
    Spacing,
    dark_palette,
    light_palette,
)

__all__ = [
    "ThemeManager",
    "Palette",
    "DARK_THEME",
    "LIGHT_THEME",
    "Spacing",
    "FontSizes",
    "dark_palette",
    "light_palette",
    "create_named_fonts",
    "get_system_scalable_fonts",
]
