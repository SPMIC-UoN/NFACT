"""
Unit tests for NFACT Graphical User Interface components, command builder,
and theme engine.
"""

import os
import tkinter as tk
from tkinter import ttk
from unittest.mock import MagicMock, patch
import pytest

from NFACT.gui.__main__ import (
    build_tkinter_missing_message,
    check_tkinter_availability,
    nfact_gui_main,
)
from NFACT.gui.ansi_parser import AnsiParser, configure_ansi_tags, strip_ansi
from NFACT.gui.app import NFACTGuiApp
from NFACT.gui.command_builder import (
    append_cluster_options,
    build_config_command,
    build_decomp_command,
    build_dr_command,
    build_pipeline_command,
    build_pp_command,
    build_qc_command,
    build_stats_command,
    format_command_string,
)
from NFACT.gui.gui_args import nfact_gui_splash, parse_gui_args
from NFACT.gui.tabs.config_tab import ConfigTab
from NFACT.gui.tabs.decomp_tab import DecompTab
from NFACT.gui.tabs.dr_tab import DRTab
from NFACT.gui.tabs.pipeline_tab import PipelineTab
from NFACT.gui.tabs.pp_tab import PPTab
from NFACT.gui.tabs.qc_tab import QcTab
from NFACT.gui.tabs.stats_tab import StatsTab
from NFACT.gui.theme import DARK_THEME, ThemeManager
from NFACT.gui.widgets.command_bar import CommandBar
from NFACT.gui.widgets.form_fields import (
    CollapsibleCard,
    DirectorySelectorField,
    FileSelectorField,
    MultiPathField,
)
from NFACT.gui.widgets.log_console import LogConsole


@pytest.fixture
def tk_root_fixture():
    """
    Pytest fixture creating and cleaning up a Tkinter root window.

    Parameters
    ----------
    None

    Returns
    -------
    root_window: tk.Tk
        Initialized Tkinter root.
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


class TestCommandBuilder:
    """
    Test suite for CommandBuilder argument construction and shell formatting.

    Usage
    -----
    pytest NFACT/testing/test_gui_module.py -k TestCommandBuilder
    """

    def test_format_command_string(self) -> None:
        """
        Verify shlex-formatted command strings.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        assert format_command_string([]) == ""
        cmd_args = ["nfact", "--outdir", "/tmp/path with space/out"]
        formatted_str = format_command_string(cmd_args)
        assert "nfact" in formatted_str
        assert (
            "'/tmp/path with space/out'" in formatted_str
            or '"/tmp/path with space/out"' in formatted_str
        )

    def test_append_cluster_options(self) -> None:
        """
        Verify cluster option injection.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        command_list = ["nfact"]
        state_dict = {
            "cluster": True,
            "cluster_queue": "gpu_long",
            "cluster_ram": "120",
            "cluster_time": "12:00:00",
            "cluster_qos": "high",
            "gpu": True,
        }
        append_cluster_options(
            command_list, state_dict, cluster_flag="-C", gpu_flag="-G"
        )
        assert "-C" in command_list
        assert "-cq" in command_list
        assert "gpu_long" in command_list
        assert "-cr" in command_list
        assert "120" in command_list
        assert "-ct" in command_list
        assert "12:00:00" in command_list
        assert "-cqos" in command_list
        assert "high" in command_list
        assert "-G" in command_list

    def test_build_pipeline_command_basic(self) -> None:
        """
        Verify end-to-end pipeline command generation.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        state_dict = {
            "list_of_subjects": "/path/sub.txt",
            "outdir": "/path/out",
            "folder_name": "my_study",
            "dim": 50,
            "algo": "NMF",
            "seed": "/seed1.nii.gz /seed2.nii.gz",
            "warps": "/w1 /w2",
            "bpx_path": "diff.bedpostX",
            "roi": "/roi1.shape.gii",
            "overwrite": True,
        }
        cmd = build_pipeline_command(state_dict)
        assert cmd[0] == "nfact"
        assert "-l" in cmd and "/path/sub.txt" in cmd
        assert "-o" in cmd and "/path/out" in cmd
        assert "-n" in cmd and "my_study" in cmd
        assert "-d" in cmd and "50" in cmd
        assert "-a" in cmd and "NMF" in cmd
        assert "-s" in cmd and "/seed1.nii.gz" in cmd
        assert "-w" in cmd and "/w1" in cmd
        assert "-b" in cmd and "diff.bedpostX" in cmd
        assert "-r" in cmd and "/roi1.shape.gii" in cmd
        assert "-O" in cmd

    def test_build_pipeline_command_skips(self) -> None:
        """
        Verify stage skipping flags and rf_decomp replacement.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        state_dict = {
            "list_of_subjects": "/path/sub.txt",
            "outdir": "/path/out",
            "pp_skip": True,
            "qc_skip": True,
            "dr_skip": True,
            "rf_decomp": "/path/roi_for_decomp.txt",
            "dim": 75,
            "algo": "ICA",
        }
        cmd = build_pipeline_command(state_dict)
        assert "-P" in cmd
        assert "-Q" in cmd
        assert "-D" in cmd
        assert "-rf" in cmd
        assert "/path/roi_for_decomp.txt" in cmd

    def test_build_pipeline_command_config_mode(self) -> None:
        """
        Verify config-only pipeline command mode.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        state_dict = {
            "config": "/path/to/my_pipeline.config",
            "list_of_subjects": "/ignored",
        }
        cmd = build_pipeline_command(state_dict)
        assert cmd == ["nfact", "-c", "/path/to/my_pipeline.config"]

    def test_build_pp_command(self) -> None:
        """
        Verify nfact_pp command generation.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        state_dict = {
            "list_of_subjects": "/subs.txt",
            "outdir": "/out",
            "file_tree": "hcp",
            "bpx_path": "bedpostX",
            "nsamples": "2000",
            "min_mask": True,
            "downsample": True,
            "voxel_size": "2",
            "n_cores": "8",
        }
        cmd = build_pp_command(state_dict)
        assert cmd[0] == "nfact_pp"
        assert "-l" in cmd and "/subs.txt" in cmd
        assert "-f" in cmd and "hcp" in cmd
        assert "-ns" in cmd and "2000" in cmd
        assert "-mm" in cmd
        assert "-D" in cmd
        assert "-vx" in cmd and "2" in cmd
        assert "-n" in cmd and "8" in cmd

    def test_build_decomp_command(self) -> None:
        """
        Verify nfact_decomp command generation with NMF and ICA options.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        state_nmf = {
            "list_of_subjects": "/subs.txt",
            "outdir": "/out",
            "algo": "NMF",
            "dim": "60",
            "iterations": "30",
            "wta": True,
            "cifti": True,
            "disk_save": True,
        }
        cmd_nmf = build_decomp_command(state_nmf)
        assert cmd_nmf[0] == "nfact_decomp"
        assert "-a" in cmd_nmf and "NMF" in cmd_nmf
        assert "-d" in cmd_nmf and "60" in cmd_nmf
        assert "-i" in cmd_nmf and "30" in cmd_nmf
        assert "-w" in cmd_nmf
        assert "-C" in cmd_nmf
        assert "-D" in cmd_nmf

        state_ica = {
            "list_of_subjects": "/subs.txt",
            "outdir": "/out",
            "algo": "ICA",
            "dim": "25",
            "pca_comp": "500",
            "pca_type": "migp",
            "spatial_sign_flip": True,
        }
        cmd_ica = build_decomp_command(state_ica)
        assert "-a" in cmd_ica and "ICA" in cmd_ica
        assert "-c" in cmd_ica and "500" in cmd_ica
        assert "-p" in cmd_ica and "migp" in cmd_ica
        assert "-S" in cmd_ica

    def test_build_qc_command(self) -> None:
        """
        Verify nfact_Qc command construction.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        state_dict = {
            "nfact_folder": "/out/nfact_decomp",
            "dim": "75",
            "algo": "NMF",
            "threshold": "3",
            "overwrite": True,
        }
        cmd = build_qc_command(state_dict)
        assert cmd == [
            "nfact_Qc",
            "-n",
            "/out/nfact_decomp",
            "-d",
            "75",
            "-a",
            "NMF",
            "-t",
            "3",
            "-O",
        ]

    def test_build_dr_command(self) -> None:
        """
        Verify nfact_dr command generation.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        state_dict = {
            "list_of_subjects": "/subs.txt",
            "outdir": "/out",
            "algo": "NMF",
            "seeds": "/out/nfact_pp/seeds_for_decomp.txt",
            "roi": "/out/nfact_pp/roi_for_decomp.txt",
            "nfact_decomp_dir": "/out/nfact_decomp",
            "normalise": True,
            "dscalar": True,
            "threshold": "2",
            "n_cores": "4",
        }
        cmd = build_dr_command(state_dict)
        assert cmd[0] == "nfact_dr"
        assert "-d" in cmd and "/out/nfact_decomp" in cmd
        assert "-N" in cmd
        assert "-D" in cmd
        assert "-t" in cmd and "2" in cmd
        assert "-n" in cmd and "4" in cmd

    def test_build_stats_command(self) -> None:
        """
        Verify nfact_stats command for loadings and statsmap subcommands.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        state_loadings = {
            "subcommand": "loadings",
            "list_of_subjects": "/subs.txt",
            "outdir": "/out",
            "nfact_folder": "/out/nfact",
            "dim": "75",
            "algo": "NMF",
            "threshold": "2.5",
            "no_csv": True,
        }
        cmd_loadings = build_stats_command(state_loadings)
        assert cmd_loadings[0] == "nfact_stats"
        assert cmd_loadings[1] == "loadings"
        assert "-t" in cmd_loadings and "2.5" in cmd_loadings
        assert "-C" in cmd_loadings

        state_statsmap = {
            "subcommand": "statsmap",
            "list_of_subjects": "/subs.txt",
            "outdir": "/out",
            "nfact_folder": "/out/nfact",
            "dim": "75",
            "algo": "NMF",
            "components": "1 5 10",
            "map_name": "comp_map",
            "group_only": True,
            "skip": True,
        }
        cmd_statsmap = build_stats_command(state_statsmap)
        assert cmd_statsmap[1] == "statsmap"
        assert "-c" in cmd_statsmap and "1" in cmd_statsmap and "5" in cmd_statsmap
        assert "-m" in cmd_statsmap and "comp_map" in cmd_statsmap
        assert "-G" in cmd_statsmap
        assert "-S" in cmd_statsmap

    def test_build_config_command(self) -> None:
        """
        Verify nfact_config generator command strings.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        cmd_pipe = build_config_command({"action": "pipeline", "output_dir": "/out"})
        assert cmd_pipe == ["nfact_config", "-C", "-o", "/out"]

        cmd_decomp = build_config_command(
            {"action": "decomp", "file_name": "decomp.config"}
        )
        assert cmd_decomp == ["nfact_config", "-D", "-f", "decomp.config"]

        cmd_sub = build_config_command(
            {
                "action": "subject_list",
                "subject_dir": "/study",
                "output_dir": "/out",
            }
        )
        assert cmd_sub == ["nfact_config", "-s", "/study", "-o", "/out"]

        cmd_zip = build_config_command(
            {
                "action": "zip",
                "zip_dir": "/out/nfact_pp",
            }
        )
        assert cmd_zip == ["nfact_config", "-z", "/out/nfact_pp"]


class TestAnsiParser:
    """
    Test suite for ANSI terminal sequence parsing and styled text tags.

    Usage
    -----
    pytest NFACT/testing/test_gui_module.py -k TestAnsiParser
    """

    def test_strip_ansi(self) -> None:
        """
        Verify stripping ANSI escape codes.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        raw_text = "\x1b[38;2;255;20;147mNFACT\x1b[0;0m running..."
        clean_text = strip_ansi(raw_text)
        assert clean_text == "NFACT running..."

    def test_ansi_parser_text_injection(self, tk_root_fixture: tk.Tk) -> None:
        """
        Verify ANSI sequences are converted into Tk text tags.

        Parameters
        ----------
        tk_root_fixture: tk.Tk
            Fixture providing root window.

        Returns
        -------
        None
        """
        text_widget = tk.Text(tk_root_fixture)
        configure_ansi_tags(text_widget, DARK_THEME)

        parser = AnsiParser()
        raw_line = "\x1b[1;31mError message!\x1b[0m Normal text\n"
        parser.append_text(text_widget, raw_line)

        content = text_widget.get("1.0", "end-1c")
        assert "Error message! Normal text" in content

    def test_ansi_parser_carriage_return(self, tk_root_fixture: tk.Tk) -> None:
        """
        Verify carriage return replaces the current line for progress indicators.

        Parameters
        ----------
        tk_root_fixture: tk.Tk
            Fixture providing root window.

        Returns
        -------
        None
        """
        text_widget = tk.Text(tk_root_fixture)
        parser = AnsiParser()
        parser.append_text(text_widget, "Progress: 10%")
        parser.append_text(text_widget, "\rProgress: 50%")
        content = text_widget.get("1.0", "end-1c")
        assert "50%" in content
        assert "10%" not in content


class TestThemeManager:
    """
    Test suite for theme management and runtime toggle.

    Usage
    -----
    pytest NFACT/testing/test_gui_module.py -k TestThemeManager
    """

    def test_theme_palettes(self) -> None:
        """
        Verify palette structure and NFACT brand keys.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        manager = ThemeManager(initial_theme="dark")
        dark_pal = manager.get_palette()
        assert dark_pal["bg_primary"] == "#7862A6"
        assert dark_pal["accent_primary"] == "#38186A"

        manager.set_theme("light")
        light_pal = manager.get_palette()
        assert light_pal["bg_primary"] == "#EFEBF7"
        assert light_pal["accent_primary"] == "#38186A"

    def test_theme_toggle_callback(self, tk_root_fixture: tk.Tk) -> None:
        """
        Verify theme toggle notifies registered non-ttk widgets.

        Parameters
        ----------
        tk_root_fixture: tk.Tk
            Fixture providing root window.

        Returns
        -------
        None
        """
        manager = ThemeManager(initial_theme="dark")
        mock_callback = MagicMock()
        manager.register_widget(object(), mock_callback)
        mock_callback.assert_called_once()

        manager.toggle_theme(tk_root_fixture)
        assert manager.current_theme == "light"
        assert mock_callback.call_count == 2


class TestGuiArgs:
    """
    Test suite for GUI CLI argument parsing.

    Usage
    -----
    pytest NFACT/testing/test_gui_module.py -k TestGuiArgs
    """

    def test_parse_gui_args(self) -> None:
        """
        Verify CLI options parsing.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        parsed = parse_gui_args(
            ["--theme", "light", "-c", "/path/test.config", "-w", "/tmp"]
        )
        assert parsed["theme"] == "light"
        assert parsed["config"] == "/path/test.config"
        assert parsed["workdir"] == "/tmp"

    def test_nfact_gui_splash(self) -> None:
        """
        Verify splash screen ASCII art returns formatted text.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        splash = nfact_gui_splash()
        assert "NFACT" in splash or "___" in splash


class TestGuiWidgets:
    """
    Test suite for reusable form fields, command bar, and log console.

    Usage
    -----
    pytest NFACT/testing/test_gui_module.py -k TestGuiWidgets
    """

    def test_file_selector_field(self, tk_root_fixture: tk.Tk) -> None:
        """
        Verify FileSelectorField get, set, and clear.

        Parameters
        ----------
        tk_root_fixture: tk.Tk
            Root window fixture.

        Returns
        -------
        None
        """
        field = FileSelectorField(tk_root_fixture, label_text="Test File:")
        field.set("/path/to/sample.txt")
        assert field.get() == "/path/to/sample.txt"
        field._on_clear_click()
        assert field.get() == ""

    def test_directory_selector_field(self, tk_root_fixture: tk.Tk) -> None:
        """
        Verify DirectorySelectorField get, set, and clear.

        Parameters
        ----------
        tk_root_fixture: tk.Tk
            Root window fixture.

        Returns
        -------
        None
        """
        field = DirectorySelectorField(tk_root_fixture, label_text="Test Dir:")
        field.set("/path/to/folder")
        assert field.get() == "/path/to/folder"
        field._on_clear_click()
        assert field.get() == ""

    def test_multipath_field(self, tk_root_fixture: tk.Tk) -> None:
        """
        Verify MultiPathField string and list methods.

        Parameters
        ----------
        tk_root_fixture: tk.Tk
            Root window fixture.

        Returns
        -------
        None
        """
        field = MultiPathField(tk_root_fixture, label_text="Warps:")
        field.set(["/warp1.nii.gz", "/warp2.nii.gz"])
        assert field.get_list() == ["/warp1.nii.gz", "/warp2.nii.gz"]
        assert field.get() == "/warp1.nii.gz /warp2.nii.gz"
        field._on_clear()
        assert field.get_list() == []

    def test_collapsible_card(self, tk_root_fixture: tk.Tk) -> None:
        """
        Verify CollapsibleCard expand and collapse functionality.

        Parameters
        ----------
        tk_root_fixture: tk.Tk
            Root window fixture.

        Returns
        -------
        None
        """
        card = CollapsibleCard(
            tk_root_fixture, title="Section 1", initially_expanded=True
        )
        assert card.is_expanded() is True
        card.collapse()
        assert card.is_expanded() is False
        card.expand()
        assert card.is_expanded() is True
        card.toggle()
        assert card.is_expanded() is False

    def test_command_bar(self, tk_root_fixture: tk.Tk) -> None:
        """
        Verify CommandBar state setting and preview updating.

        Parameters
        ----------
        tk_root_fixture: tk.Tk
            Root window fixture.

        Returns
        -------
        None
        """
        run_mock = MagicMock()
        stop_mock = MagicMock()
        validate_mock = MagicMock()

        bar = CommandBar(
            tk_root_fixture,
            on_run_callback=run_mock,
            on_stop_callback=stop_mock,
            on_validate_callback=validate_mock,
        )
        bar.set_command("nfact -l subs.txt -o /out")
        assert bar.get_command() == "nfact -l subs.txt -o /out"

        bar.run_action()
        run_mock.assert_called_once()

        bar.validate_action()
        validate_mock.assert_called_once()

        bar.set_running_state(True)
        assert str(bar.run_button.cget("state")) == "disabled"
        assert str(bar.stop_button.cget("state")) == "normal"

        bar.stop_action()
        stop_mock.assert_called_once()

        bar.set_running_state(False)
        assert str(bar.run_button.cget("state")) == "normal"

    def test_log_console(self, tk_root_fixture: tk.Tk) -> None:
        """
        Verify LogConsole streaming, history table insertion, and clear.

        Parameters
        ----------
        tk_root_fixture: tk.Tk
            Root window fixture.

        Returns
        -------
        None
        """
        console = LogConsole(tk_root_fixture)
        console.apply_palette(DARK_THEME)

        console.append_stream("Test execution output line\n")
        assert "Test execution output line" in console.stream_text.get("1.0", "end")

        console.clear_stream()
        assert console.stream_text.get("1.0", "end-1c") == ""

        entry_id = console.add_command_entry(
            "nfact -l sub.txt", "/tmp", initial_status="Running"
        )
        assert entry_id != ""

        console.update_command_entry(entry_id, "Completed (0)", "3.2s")
        values = console.history_tree.item(entry_id, "values")
        assert values[1] == "Completed (0)"
        assert values[2] == "3.2s"


class TestGuiTabs:
    """
    Test suite for module tabs state management and validation.

    Usage
    -----
    pytest NFACT/testing/test_gui_module.py -k TestGuiTabs
    """

    def test_pipeline_tab(self, tk_root_fixture: tk.Tk) -> None:
        """
        Verify PipelineTab state setting and validation rules.

        Parameters
        ----------
        tk_root_fixture: tk.Tk
            Root window fixture.

        Returns
        -------
        None
        """
        notebook = ttk.Notebook(tk_root_fixture)
        tab = PipelineTab(notebook)

        # Initially invalid (no subjects, outdir)
        is_valid, error_list = tab.validate()
        assert is_valid is False
        assert len(error_list) > 0

        # Fill valid form
        tab.set_state(
            {
                "list_of_subjects": "/subs.txt",
                "outdir": "/out",
                "dim": 75,
                "seed": "/seed1",
            }
        )
        is_valid, error_list = tab.validate()
        assert is_valid is True

    def test_pp_tab(self, tk_root_fixture: tk.Tk) -> None:
        """
        Verify PPTab validation and preset application.

        Parameters
        ----------
        tk_root_fixture: tk.Tk
            Root window fixture.

        Returns
        -------
        None
        """
        notebook = ttk.Notebook(tk_root_fixture)
        tab = PPTab(notebook)

        is_valid, _ = tab.validate()
        assert is_valid is False

        tab._apply_hcp_preset()
        assert tab.params["file_tree"].get() == "hcp"
        assert tab.params["bpx_path"].get() == "T1w/Diffusion.bedpostX"

        tab.set_state({"list_of_subjects": "/subs.txt", "outdir": "/out"})
        is_valid, _ = tab.validate()
        assert is_valid is True

    def test_decomp_tab(self, tk_root_fixture: tk.Tk) -> None:
        """
        Verify DecompTab validation and algorithm change.

        Parameters
        ----------
        tk_root_fixture: tk.Tk
            Root window fixture.

        Returns
        -------
        None
        """
        notebook = ttk.Notebook(tk_root_fixture)
        tab = DecompTab(notebook)

        tab.set_state({"list_of_subjects": "/subs.txt", "outdir": "/out", "dim": 50})
        is_valid, _ = tab.validate()
        assert is_valid is True

        tab.params["algo"].set("ICA")
        assert tab.ica_card.is_expanded() is True

    def test_qc_tab(self, tk_root_fixture: tk.Tk, tmp_path) -> None:
        """
        Verify QcTab validation.

        Parameters
        ----------
        tk_root_fixture: tk.Tk
            Root window fixture.
        tmp_path: pathlib.Path
            Temporary path fixture.

        Returns
        -------
        None
        """
        notebook = ttk.Notebook(tk_root_fixture)
        tab = QcTab(notebook)

        is_valid, _ = tab.validate()
        assert is_valid is False

        tab.set_state({"nfact_folder": str(tmp_path), "dim": 75})
        is_valid, _ = tab.validate()
        assert is_valid is True

    def test_dr_tab(self, tk_root_fixture: tk.Tk) -> None:
        """
        Verify DRTab validation.

        Parameters
        ----------
        tk_root_fixture: tk.Tk
            Root window fixture.

        Returns
        -------
        None
        """
        notebook = ttk.Notebook(tk_root_fixture)
        tab = DRTab(notebook)

        is_valid, _ = tab.validate()
        assert is_valid is False

        tab.set_state(
            {
                "list_of_subjects": "/subs.txt",
                "outdir": "/out",
                "nfact_decomp_dir": "/out/nfact_decomp",
            }
        )
        is_valid, _ = tab.validate()
        assert is_valid is True

    def test_stats_tab(self, tk_root_fixture: tk.Tk) -> None:
        """
        Verify StatsTab loadings vs statsmap mode validation.

        Parameters
        ----------
        tk_root_fixture: tk.Tk
            Root window fixture.

        Returns
        -------
        None
        """
        notebook = ttk.Notebook(tk_root_fixture)
        tab = StatsTab(notebook)

        tab.set_state(
            {
                "list_of_subjects": "/subs.txt",
                "outdir": "/out",
                "dim": 75,
            }
        )
        is_valid, _ = tab.validate()
        assert is_valid is True

        # Switch to group-only statsmap
        tab.subcommand_var.set("statsmap")
        tab._on_subcommand_toggled()
        tab.params["group_only"].set(True)
        tab.params["list_of_subjects"].set("")
        is_valid, _ = tab.validate()
        assert is_valid is True

    def test_config_tab(self, tk_root_fixture: tk.Tk) -> None:
        """
        Verify ConfigTab utility action validation and JSON editor.

        Parameters
        ----------
        tk_root_fixture: tk.Tk
            Root window fixture.

        Returns
        -------
        None
        """
        notebook = ttk.Notebook(tk_root_fixture)
        tab = ConfigTab(notebook)

        tab.action_var.set("pipeline")
        is_valid, _ = tab.validate()
        assert is_valid is True

        tab.action_var.set("subject_list")
        is_valid, _ = tab.validate()
        assert is_valid is False

        tab.params["subject_dir"].set("/study")
        is_valid, _ = tab.validate()
        assert is_valid is True

        # JSON validator
        tab.json_text.insert("1.0", '{"test_key": 123}')
        tab._validate_and_format_json()
        assert "JSON is valid!" in tab.status_label.cget("text")


class TestNFACTGuiApp:
    """
    Test suite for main NFACTGuiApp lifecycle and integration.

    Usage
    -----
    pytest NFACT/testing/test_gui_module.py -k TestNFACTGuiApp
    """

    def test_app_instantiation_and_toggle(self) -> None:
        """
        Verify NFACTGuiApp window creation, active tab, and theme switching.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        try:
            app = NFACTGuiApp(initial_theme="dark")
            app.withdraw()
        except tk.TclError:
            pytest.skip("X11 display not available")

        try:
            # Active tab should initially be PipelineTab
            active_tab = app._get_active_tab_instance()
            assert isinstance(active_tab, PipelineTab)

            # Command string preview should be non-empty
            cmd_preview = app.command_bar.get_command()
            assert cmd_preview.startswith("nfact")

            # Toggle theme to light
            app.toggle_theme()
            assert app.theme_manager.current_theme == "light"
            assert "Dark Mode" in app.theme_toggle_btn.cget("text")

            # Toggle theme back to dark
            app.toggle_theme()
            assert app.theme_manager.current_theme == "dark"
            assert "Light Mode" in app.theme_toggle_btn.cget("text")

            # Update working directory
            initial_dir = app.current_workdir
            assert os.path.exists(initial_dir)
        finally:
            app.destroy()


class TestNfactGuiMain:
    """Test suite for nfact_gui command-line entry point and Tkinter checks."""

    def test_check_tkinter_availability(self) -> None:
        """Test check_tkinter_availability returns boolean status.

        Parameters
        ------------
        None

        Returns
        --------
            None: NoneType object
                Returns None.
        """
        status_flag = check_tkinter_availability()
        assert isinstance(status_flag, bool)

    def test_build_tkinter_missing_message(self) -> None:
        """Test build_tkinter_missing_message includes platform instructions.

        Parameters
        ------------
        None

        Returns
        --------
            None: NoneType object
                Returns None.
        """
        darwin_message = build_tkinter_missing_message("darwin")
        assert "brew install python-tk" in darwin_message
        assert "nfact --help" in darwin_message

        linux_message = build_tkinter_missing_message("linux")
        assert "sudo apt-get install python3-tk" in linux_message

        other_message = build_tkinter_missing_message("win32")
        assert "install Tkinter support" in other_message

    def test_nfact_gui_main_missing_tkinter(self) -> None:
        """Test nfact_gui_main exits with code 1 when tkinter is missing.

        Parameters
        ------------
        None

        Returns
        --------
            None: NoneType object
                Returns None.
        """
        with patch("NFACT.gui.__main__.check_tkinter_availability", return_value=False):
            with pytest.raises(SystemExit) as exit_info:
                nfact_gui_main(["--theme", "dark"])
            assert exit_info.value.code == 1

    def test_nfact_gui_main_success(self) -> None:
        """Test nfact_gui_main launches app when tkinter is available.

        Parameters
        ------------
        None

        Returns
        --------
            None: NoneType object
                Returns None.
        """
        mock_instance = MagicMock()
        with patch("NFACT.gui.__main__.check_tkinter_availability", return_value=True):
            with patch("NFACT.gui.app.NFACTGuiApp", return_value=mock_instance):
                nfact_gui_main(["--theme", "dark"])
                mock_instance.mainloop.assert_called_once()

