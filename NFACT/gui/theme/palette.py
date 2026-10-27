"""
Color palette definitions, spacing tokens, and typography sizing.
"""

from dataclasses import asdict, dataclass, fields
from typing import Any, Iterator


@dataclass(frozen=True)
class Palette:
    """Color palette token set for NFACT GUI themes.

    Usage
    -----
    palette = dark_palette()
    bg_color = palette.bg_primary
    """

    bg_primary: str
    bg_surface: str
    bg_surface_alt: str
    bg_input: str
    bg_console: str
    fg_primary: str
    fg_secondary: str
    fg_disabled: str
    accent_primary: str
    accent_hover: str
    accent_secondary: str
    accent_tertiary: str
    border_color: str
    border_focus: str
    status_success: str
    status_running: str
    status_warning: str
    status_error: str
    button_bg: str
    button_fg: str
    button_hover: str
    danger_bg: str
    danger_fg: str
    danger_hover: str
    ansi: dict[str, str]

    def __getitem__(self, item_key: str) -> Any:
        """Allow dictionary-style access to palette attributes.

        Parameters
        ------------
        item_key: str
            Name of the color attribute.

        Returns
        --------
            Any: attribute value
                The color string or sub-dictionary.
        """
        if not hasattr(self, str(item_key)):
            raise KeyError(item_key)
        return getattr(self, str(item_key))

    def __contains__(self, item_key: object) -> bool:
        """Check if an attribute name exists on the palette.

        Parameters
        ------------
        item_key: object
            Name of color attribute to check.

        Returns
        --------
            bool: boolean flag
                True if attribute exists, False otherwise.
        """
        return hasattr(self, str(item_key))

    def __iter__(self) -> Iterator[str]:
        """Iterate over field names of the palette.

        Parameters
        ------------
        None

        Returns
        --------
            Iterator[str]: field name iterator
                Iterator yielding token attribute names.
        """
        for field_def in fields(self):
            yield field_def.name

    def get(self, item_key: str, default_val: Any = None) -> Any:
        """Get attribute with a fallback default.

        Parameters
        ------------
        item_key: str
            Name of the color attribute.
        default_val: Any
            Default value if key is not found. Defaults to None.

        Returns
        --------
            Any: attribute value
                The color string or default value.
        """
        return getattr(self, item_key, default_val)

    def to_dict(self) -> dict[str, Any]:
        """Convert the palette dataclass into a regular dictionary.

        Parameters
        ------------
        None

        Returns
        --------
            dict: dictionary object
                Dictionary containing all palette key-value pairs.
        """
        return asdict(self)


@dataclass(frozen=True)
class Spacing:
    """Spacing scale (pixels) used for every padx/pady in the GUI.

    Usage
    -----
    spacing = Spacing()
    frame.grid(padx=spacing.medium)
    """

    xs: int = 4
    small: int = 8
    medium: int = 12
    large: int = 16
    xlarge: int = 24


@dataclass(frozen=True)
class FontSizes:
    """Typography scale for named fonts in the NFACT GUI.

    Usage
    -----
    sizes = FontSizes()
    title_pt = sizes.title
    """

    title: int = 20
    section: int = 16
    body: int = 14
    body_bold: int = 14
    caption: int = 12
    mono: int = 13
    mono_small: int = 12


def dark_palette() -> Palette:
    """Construct the primary purple theme palette tokens.

    Uses a clean light-purple background with crisp white text and
    deep dark-purple accents.

    Parameters
    ------------
    None

    Returns
    --------
        Palette: palette object
            Configured primary theme Palette instance.
    """
    ansi_map = {
        "ansi_pink": "#D8B4FE",
        "ansi_deep_pink": "#C084FC",
        "ansi_purple": "#A855F7",
        "ansi_darker_pink": "#9333EA",
        "ansi_plum": "#E9D5FF",
        "ansi_amethyst": "#C4B5FD",
        "ansi_lav": "#DDD6FE",
        "ansi_light_pink": "#F3E8FF",
        "ansi_yellow": "#FACC15",
        "ansi_cyan": "#38BDF8",
        "ansi_red": "#FF6B6B",
        "ansi_green": "#4ADE80",
    }
    return Palette(
        bg_primary="#000000",
        bg_surface="#000000",
        bg_surface_alt="#000000",
        bg_input="#000000",
        bg_console="#2D1B4E",
        fg_primary="#FFFFFF",
        fg_secondary="#F3EEFF",
        fg_disabled="#C4B5E3",
        accent_primary="#38186A",
        accent_hover="#2A1052",
        accent_secondary="#FFFFFF",
        accent_tertiary="#EBE2FF",
        border_color="#8C77B8",
        border_focus="#38186A",
        status_success="#4ADE80",
        status_running="#E2D4FF",
        status_warning="#FACC15",
        status_error="#FF6B6B",
        button_bg="#4E387A",
        button_fg="#FFFFFF",
        button_hover="#38186A",
        danger_bg="#C62828",
        danger_fg="#FFFFFF",
        danger_hover="#A81F1F",
        ansi=ansi_map,
    )


def light_palette() -> Palette:
    """Construct the secondary pale-lavender light theme palette tokens.

    Parameters
    ------------
    None

    Returns
    --------
        Palette: palette object
            Configured light theme Palette instance.
    """
    ansi_map = {
        "ansi_pink": "#6B21A8",
        "ansi_deep_pink": "#581C87",
        "ansi_purple": "#4C1D95",
        "ansi_darker_pink": "#5B21B6",
        "ansi_plum": "#6D28D9",
        "ansi_amethyst": "#7C3AED",
        "ansi_lav": "#5B21B6",
        "ansi_light_pink": "#6B21A8",
        "ansi_yellow": "#B7860B",
        "ansi_cyan": "#00838F",
        "ansi_red": "#D32F2F",
        "ansi_green": "#1E9E57",
    }
    return Palette(
        bg_primary="#EFEBF7",
        bg_surface="#FFFFFF",
        bg_surface_alt="#E5DFF2",
        bg_input="#F8F6FC",
        bg_console="#2D1B4E",
        fg_primary="#1E1433",
        fg_secondary="#4A3B69",
        fg_disabled="#9A8EB5",
        accent_primary="#38186A",
        accent_hover="#2A1052",
        accent_secondary="#38186A",
        accent_tertiary="#4A2580",
        border_color="#D0C6E6",
        border_focus="#38186A",
        status_success="#1E9E57",
        status_running="#4A2580",
        status_warning="#B7860B",
        status_error="#D32F2F",
        button_bg="#E2DAF0",
        button_fg="#1E1433",
        button_hover="#D2C6E8",
        danger_bg="#C62828",
        danger_fg="#FFFFFF",
        danger_hover="#8E0000",
        ansi=ansi_map,
    )


DARK_THEME = dark_palette()
LIGHT_THEME = light_palette()
