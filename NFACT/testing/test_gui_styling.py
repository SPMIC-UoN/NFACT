"""
Unit tests for GUI design tokens, TTK styles, custom widgets, and theme switching.
"""

import tkinter as tk
from tkinter import ttk
from typing import Any
import pytest

from NFACT.gui.theme.manager import ThemeManager
from NFACT.gui.theme.palette import dark_palette, light_palette
from NFACT.gui.widgets.card import Card
from NFACT.gui.widgets.command_bar import CommandBar
from NFACT.gui.widgets.nav_sidebar import NavItem, NavSidebar
from NFACT.gui.widgets.stage_flow import StageFlowBar, StageSpec
from NFACT.gui.widgets.toggle_switch import ToggleSwitch


@pytest.fixture
def tk_root_fixture() -> Any:
    """Create and clean up a headless Tkinter root window fixture.

    Parameters
    ------------
    None

    Returns
    --------
        Any: generator yielding tk.Tk instance
            Initialized Tkinter root window fixture.
    """
    try:
        root_window = tk.Tk()
        root_window.withdraw()
    except tk.TclError:
        pytest.skip("X11 display not available for Tkinter GUI test")
    yield root_window
    try:
        root_window.destroy()
    except Exception:
        pass


def _calculate_relative_luminance(hex_colour_string: str) -> float:
    """Calculate WCAG 2.1 relative luminance for an sRGB hex colour.

    Parameters
    ------------
    hex_colour_string: str
        Colour string formatted as '#RRGGBB'.

    Returns
    --------
        float: relative luminance value
            Calculated relative luminance between 0.0 and 1.0.
    """
    cleaned_hex = hex_colour_string.lstrip("#")
    red_val = int(cleaned_hex[0:2], 16) / 255.0
    green_val = int(cleaned_hex[2:4], 16) / 255.0
    blue_val = int(cleaned_hex[4:6], 16) / 255.0

    def adjust_component(component_val: float) -> float:
        if component_val <= 0.04045:
            return component_val / 12.92
        return ((component_val + 0.055) / 1.055) ** 2.4

    adj_red = adjust_component(red_val)
    adj_green = adjust_component(green_val)
    adj_blue = adjust_component(blue_val)
    return 0.2126 * adj_red + 0.7152 * adj_green + 0.0722 * adj_blue


def _calculate_contrast_ratio(first_hex: str, second_hex: str) -> float:
    """Calculate WCAG 2.1 contrast ratio between two hex colours.

    Parameters
    ------------
    first_hex: str
        First colour formatted as '#RRGGBB'.
    second_hex: str
        Second colour formatted as '#RRGGBB'.

    Returns
    --------
        float: contrast ratio
            Calculated contrast ratio (>= 1.0).
    """
    lum_one = _calculate_relative_luminance(first_hex)
    lum_two = _calculate_relative_luminance(second_hex)
    top_lum = max(lum_one, lum_two)
    bottom_lum = min(lum_one, lum_two)
    return (top_lum + 0.05) / (bottom_lum + 0.05)


class TestThemeAndPalettes:
    """Test suite verifying design tokens, palettes, and style configuration.

    Usage
    -----
    pytest NFACT/testing/test_gui_styling.py -k TestThemeAndPalettes
    """

    def test_palettes_have_same_tokens(self) -> None:
        """Verify dark and light palettes define identical attributes and keys.

        Parameters
        ------------
        None

        Returns
        --------
            None: None object
                Asserts field and ANSI key parity.
        """
        dark_pal = dark_palette()
        light_pal = light_palette()

        dark_keys = set(dark_pal.__dict__.keys())
        light_keys = set(light_pal.__dict__.keys())
        assert dark_keys == light_keys

        dark_ansi_keys = set(dark_pal.ansi.keys())
        light_ansi_keys = set(light_pal.ansi.keys())
        assert dark_ansi_keys == light_ansi_keys

    def test_palette_contrast(self) -> None:
        """Verify WCAG contrast ratios meet minimum accessibility thresholds.

        Parameters
        ------------
        None

        Returns
        --------
            None: None object
                Asserts contrast ratios >= 4.5 for primary and >= 3.0 for secondary.
        """
        dark_pal = dark_palette()
        light_pal = light_palette()

        # Dark theme contrast checks
        dark_primary_on_bg = _calculate_contrast_ratio(
            dark_pal.fg_primary, dark_pal.bg_primary
        )
        dark_primary_on_surface = _calculate_contrast_ratio(
            dark_pal.fg_primary, dark_pal.bg_surface
        )
        dark_secondary_on_surface = _calculate_contrast_ratio(
            dark_pal.fg_secondary, dark_pal.bg_surface
        )
        assert dark_primary_on_bg >= 4.5
        assert dark_primary_on_surface >= 4.5
        assert dark_secondary_on_surface >= 3.0

        # Light theme contrast checks
        light_primary_on_bg = _calculate_contrast_ratio(
            light_pal.fg_primary, light_pal.bg_primary
        )
        light_primary_on_surface = _calculate_contrast_ratio(
            light_pal.fg_primary, light_pal.bg_surface
        )
        light_secondary_on_surface = _calculate_contrast_ratio(
            light_pal.fg_secondary, light_pal.bg_surface
        )
        assert light_primary_on_bg >= 4.5
        assert light_primary_on_surface >= 4.5
        assert light_secondary_on_surface >= 3.0

    def test_all_used_styles_are_defined(self, tk_root_fixture: tk.Tk) -> None:
        """Verify all custom TTK styles are properly registered in ttk.Style.

        Parameters
        ------------
        tk_root_fixture: tk.Tk
            Root window fixture.

        Returns
        --------
            None: None object
                Asserts registered styles can be queried.
        """
        theme_manager = ThemeManager(initial_theme="dark")
        theme_manager.apply_theme(tk_root_fixture)

        style_engine = ttk.Style()
        expected_styles = [
            "Surface.TFrame",
            "SurfaceAlt.TFrame",
            "Card.TFrame",
            "CardHeader.TFrame",
            "Header.TFrame",
            "Sidebar.TFrame",
            "Console.TFrame",
            "StatusBar.TFrame",
            "PageTitle.TLabel",
            "PageSubtitle.TLabel",
            "CardTitle.TLabel",
            "CardChevron.TLabel",
            "FlagBadge.TLabel",
            "Required.TLabel",
            "NavItem.TLabel",
            "NavItemActive.TLabel",
            "NavSection.TLabel",
            "StatusIdle.TLabel",
            "StatusRunning.TLabel",
            "StatusSuccess.TLabel",
            "StatusError.TLabel",
            "Accent.TButton",
            "Danger.TButton",
            "Ghost.TButton",
            "Icon.TButton",
            "Header.TButton",
            "Invalid.TEntry",
            "Segment.TRadiobutton",
            "Surface.TRadiobutton",
            "Surface.TCheckbutton",
            "Hidden.TNotebook",
            "Vertical.TScrollbar",
            "Horizontal.TScrollbar",
        ]

        for style_name in expected_styles:
            cfg_dict = style_engine.configure(style_name)
            assert isinstance(cfg_dict, dict)

    def test_theme_toggle_updates_listeners(self, tk_root_fixture: tk.Tk) -> None:
        """Verify theme toggle triggers registered listener callbacks.

        Parameters
        ------------
        tk_root_fixture: tk.Tk
            Root window fixture.

        Returns
        --------
            None: None object
                Asserts listener invoked with updated Palette.
        """
        theme_manager = ThemeManager(initial_theme="dark")
        theme_manager.apply_theme(tk_root_fixture)

        received_palettes: list[Any] = []

        def on_palette_change(new_palette: Any) -> None:
            received_palettes.append(new_palette)

        theme_manager.register_listener(on_palette_change)
        assert len(received_palettes) == 1

        switched_mode = theme_manager.toggle_theme(tk_root_fixture)
        assert switched_mode == "light"
        assert len(received_palettes) == 2
        assert received_palettes[1].fg_primary == light_palette().fg_primary


class TestCustomWidgets:
    """Test suite verifying behaviour of custom graphical widgets.

    Usage
    -----
    pytest NFACT/testing/test_gui_styling.py -k TestCustomWidgets
    """

    def test_toggle_switch_binds_boolean_var(self, tk_root_fixture: tk.Tk) -> None:
        """Verify ToggleSwitch flips bound BooleanVar on user interaction.

        Parameters
        ------------
        tk_root_fixture: tk.Tk
            Root window fixture.

        Returns
        --------
            None: None object
                Asserts boolean variable inversion.
        """
        bool_variable = tk.BooleanVar(value=False)
        toggle_widget = ToggleSwitch(tk_root_fixture, variable=bool_variable)

        assert bool_variable.get() is False
        toggle_widget._on_click(None)
        assert bool_variable.get() is True
        toggle_widget._on_click(None)
        assert bool_variable.get() is False

    def test_card_collapse_expand(self, tk_root_fixture: tk.Tk) -> None:
        """Verify Card component toggles visibility of its content frame.

        Parameters
        ------------
        tk_root_fixture: tk.Tk
            Root window fixture.

        Returns
        --------
            None: None object
                Asserts expanded boolean state toggling.
        """
        card_widget = Card(
            tk_root_fixture,
            title="Sample Card",
            subtitle="Sample Subtitle",
            initially_expanded=True,
        )
        assert card_widget.is_expanded() is True

        card_widget.toggle()
        assert card_widget.is_expanded() is False

        card_widget.toggle()
        assert card_widget.is_expanded() is True

    def test_stage_flow_bar(self, tk_root_fixture: tk.Tk) -> None:
        """Verify StageFlowBar updates stage states and triggers callbacks.

        Parameters
        ------------
        tk_root_fixture: tk.Tk
            Root window fixture.

        Returns
        --------
            None: None object
                Asserts stage state transitions.
        """
        toggled_events: list[tuple[str, bool]] = []

        def on_stage_toggle(stage_key: str, is_active: bool) -> None:
            toggled_events.append((stage_key, is_active))

        stages = [
            StageSpec(key="pp", title="1. Pre-process", subtitle="nfact_pp"),
            StageSpec(key="decomp", title="2. Decompose", subtitle="nfact_decomp"),
        ]
        flow_bar = StageFlowBar(
            tk_root_fixture,
            stages=stages,
            on_toggle=on_stage_toggle,
        )

        assert flow_bar.get_state("pp") == "enabled"
        flow_bar.set_state("pp", "skipped")
        assert flow_bar.get_state("pp") == "skipped"

    def test_nav_sidebar_selection(self, tk_root_fixture: tk.Tk) -> None:
        """Verify NavSidebar triggers callback when page is selected.

        Parameters
        ------------
        tk_root_fixture: tk.Tk
            Root window fixture.

        Returns
        --------
            None: None object
                Asserts selection callback with correct index.
        """
        selected_indices: list[int] = []

        def on_nav_select(page_idx: int) -> None:
            selected_indices.append(page_idx)

        items = [
            NavItem(title="Full Pipeline", cli_name="nfact", section="PIPELINE"),
            NavItem(title="Pre-processing", cli_name="nfact_pp", section="MODULES"),
            NavItem(title="Decomposition", cli_name="nfact_decomp", section="MODULES"),
        ]
        sidebar_widget = NavSidebar(
            tk_root_fixture,
            items=items,
            on_select=on_nav_select,
        )

        sidebar_widget.select(2)
        assert sidebar_widget.selected_index == 2
        assert selected_indices == [2]

    def test_command_bar_highlighting(self, tk_root_fixture: tk.Tk) -> None:
        """Verify CommandBar applies syntax tags to flags and arguments.

        Parameters
        ------------
        tk_root_fixture: tk.Tk
            Root window fixture.

        Returns
        --------
            None: None object
                Asserts cmd_flag tag ranges are populated.
        """
        cmd_bar = CommandBar(tk_root_fixture)
        sample_command = "nfact_pp -l /data/subjects.txt -o /data/results -O"
        cmd_bar.set_command(sample_command)

        flag_ranges = cmd_bar.command_text.tag_ranges("cmd_flag")
        assert len(flag_ranges) > 0

        prog_ranges = cmd_bar.command_text.tag_ranges("cmd_prog")
        assert len(prog_ranges) > 0
