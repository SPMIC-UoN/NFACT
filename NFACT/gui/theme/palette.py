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

    title: int = 16
    section: int = 11
    body: int = 10
    body_bold: int = 10
    caption: int = 9
    mono: int = 10
    mono_small: int = 9


def dark_palette() -> Palette:
    """Construct the dark theme palette tokens.

    Parameters
    ------------
    None

    Returns
    --------
        Palette: palette object
            Configured dark theme Palette instance.
    """
    ansi_map = {
        "ansi_pink": "#E040FB",
        "ansi_deep_pink": "#FF1493",
        "ansi_purple": "#8700FF",
        "ansi_darker_pink": "#AF00FF",
        "ansi_plum": "#BA68C8",
        "ansi_amethyst": "#9966CC",
        "ansi_lav": "#AF87FF",
        "ansi_light_pink": "#FFAFAF",
        "ansi_yellow": "#F1C40F",
        "ansi_cyan": "#00BCD4",
        "ansi_red": "#FF5252",
        "ansi_green": "#2ECC71",
    }
    return Palette(
        bg_primary="#15131D",
        bg_surface="#1F1B2B",
        bg_surface_alt="#272236",
        bg_input="#120F19",
        bg_console="#0E0C14",
        fg_primary="#EEEAF6",
        fg_secondary="#9C93B3",
        fg_disabled="#5C5470",
        accent_primary="#E91E8C",
        accent_hover="#F0479F",
        accent_secondary="#9966CC",
        accent_tertiary="#AF87FF",
        border_color="#332C47",
        border_focus="#E91E8C",
        status_success="#2ECC71",
        status_running="#AF87FF",
        status_warning="#F1C40F",
        status_error="#FF5252",
        button_bg="#2A2539",
        button_fg="#EEEAF6",
        button_hover="#363049",
        danger_bg="#D32F2F",
        danger_fg="#FFFFFF",
        danger_hover="#B71C1C",
        ansi=ansi_map,
    )


def light_palette() -> Palette:
    """Construct the light theme palette tokens.

    Parameters
    ------------
    None

    Returns
    --------
        Palette: palette object
            Configured light theme Palette instance.
    """
    ansi_map = {
        "ansi_pink": "#C2185B",
        "ansi_deep_pink": "#C21868",
        "ansi_purple": "#5E35B1",
        "ansi_darker_pink": "#7B1FA2",
        "ansi_plum": "#7B1FA2",
        "ansi_amethyst": "#7B42BC",
        "ansi_lav": "#5E35B1",
        "ansi_light_pink": "#8E24AA",
        "ansi_yellow": "#B7860B",
        "ansi_cyan": "#00838F",
        "ansi_red": "#D32F2F",
        "ansi_green": "#1E9E57",
    }
    return Palette(
        bg_primary="#F6F4FA",
        bg_surface="#FFFFFF",
        bg_surface_alt="#F1EEF7",
        bg_input="#FBFAFD",
        bg_console="#1B1824",
        fg_primary="#1D1828",
        fg_secondary="#5F5674",
        fg_disabled="#A79FB8",
        accent_primary="#C21868",
        accent_hover="#A51458",
        accent_secondary="#7B42BC",
        accent_tertiary="#5E35B1",
        border_color="#DDD7E9",
        border_focus="#C21868",
        status_success="#1E9E57",
        status_running="#6A1B9A",
        status_warning="#B7860B",
        status_error="#D32F2F",
        button_bg="#EEEAF5",
        button_fg="#1D1828",
        button_hover="#E2DCEE",
        danger_bg="#C62828",
        danger_fg="#FFFFFF",
        danger_hover="#8E0000",
        ansi=ansi_map,
    )


DARK_THEME = dark_palette()
LIGHT_THEME = light_palette()
