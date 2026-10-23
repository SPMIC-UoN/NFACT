"""
Main application window and orchestration controller for NFACT GUI.
"""

import os
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Optional

from NFACT.gui.command_builder import (
    build_config_command,
    build_decomp_command,
    build_dr_command,
    build_pipeline_command,
    build_pp_command,
    build_qc_command,
    build_stats_command,
    format_command_string,
)
from NFACT.gui.layout.header_bar import HeaderBar
from NFACT.gui.process_runner import ProcessRunner
from NFACT.gui.run_controller import RunController
from NFACT.gui.tabs.config_tab import ConfigTab
from NFACT.gui.tabs.decomp_tab import DecompTab
from NFACT.gui.tabs.dr_tab import DRTab
from NFACT.gui.tabs.pipeline_tab import PipelineTab
from NFACT.gui.tabs.pp_tab import PPTab
from NFACT.gui.tabs.qc_tab import QcTab
from NFACT.gui.tabs.stats_tab import StatsTab
from NFACT.gui.theme import ThemeManager
from NFACT.gui.widgets.command_bar import CommandBar
from NFACT.gui.widgets.log_console import LogConsole
from NFACT.gui.widgets.nav_sidebar import NavItem, NavSidebar
from NFACT.gui.widgets.status_bar import StatusBar


class NFACTGuiApp(tk.Tk):
    """Main Tkinter application window for the NFACT Graphical User Interface.

    Usage
    -----
    app = NFACTGuiApp(initial_theme="dark")
    app.mainloop()
    """

    def __init__(
        self,
        initial_theme: str = "dark",
        initial_config: Optional[str] = None,
        initial_workdir: Optional[str] = None,
    ) -> None:
        """Initialize the NFACT GUI application.

        Parameters
        ------------
        initial_theme: str
            Initial theme ('dark' or 'light'). Defaults to "dark".
        initial_config: Optional[str]
            Optional path to a pipeline config file. Defaults to None.
        initial_workdir: Optional[str]
            Initial working directory. Defaults to None.

        Returns
        --------
            None: None object
                Constructs root window and initiates layouts.
        """
        super().__init__()

        self.title("NFACT - Non-negative Matrix Factorisation of Tractography Data")
        self.geometry("1340x860")
        self.minsize(1024, 680)

        self.theme_manager = ThemeManager(initial_theme=initial_theme)
        self.runner = ProcessRunner()
        self.run_controller = RunController(self)

        self.current_workdir = (
            initial_workdir
            if initial_workdir and os.path.isdir(initial_workdir)
            else os.getcwd()
        )

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # 1. Top Header Bar
        self.header_bar = HeaderBar(
            self,
            current_workdir=self.current_workdir,
            theme_manager=self.theme_manager,
            on_change_workdir=self._on_workdir_changed,
            on_toggle_theme=self.toggle_theme,
        )
        self.header_bar.grid(row=0, column=0, sticky="ew")
        self.theme_toggle_btn = self.header_bar.theme_button

        # 2. Main Central Body (Sidebar on left, Paned workspace on right)
        self._build_main_body()

        # 3. Footer Status Bar
        self.status_bar = StatusBar(self)
        self.status_bar.grid(row=2, column=0, sticky="ew")

        # Intercept window close
        self.protocol("WM_DELETE_WINDOW", self._on_window_close)

        # Apply theme
        self.theme_manager.apply_theme(self)
        self.header_bar.update_theme_label(self.theme_manager.current_theme)

        # Bind keyboard shortcuts for page switching (Ctrl+1 .. Ctrl+7)
        for page_index in range(7):
            self.bind_all(
                f"<Control-Key-{page_index + 1}>",
                lambda evt, idx=page_index: self.sidebar.select(idx),
            )

        # Initial command preview update
        self._on_param_changed()

        # Pre-load initial config if specified
        if initial_config and os.path.isfile(initial_config):
            self.pipeline_tab.config_path_var.set(initial_config)
            self.pipeline_tab.use_config_file_var.set(True)
            self.pipeline_tab._on_mode_toggled()

    def _build_main_body(self) -> None:
        """Construct central layout containing navigation sidebar and workspace.

        Parameters
        ------------
        None

        Returns
        --------
            None: None object
                Constructs body layout.
        """
        body_frame = ttk.Frame(self, style="TFrame")
        body_frame.grid(row=1, column=0, sticky="nsew")
        body_frame.columnconfigure(1, weight=1)
        body_frame.rowconfigure(0, weight=1)

        # Sidebar navigation items
        nav_destinations = [
            NavItem("Full Pipeline", "nfact", "PIPELINE"),
            NavItem("Pre-processing", "nfact_pp", "MODULES"),
            NavItem("Decomposition", "nfact_decomp", "MODULES"),
            NavItem("Quality Control", "nfact_Qc", "MODULES"),
            NavItem("Dual Regression", "nfact_dr", "MODULES"),
            NavItem("Statistics", "nfact_stats", "MODULES"),
            NavItem("Config & Tools", "nfact_config", "TOOLS"),
        ]

        self.sidebar = NavSidebar(
            body_frame,
            items=nav_destinations,
            on_select=self._on_sidebar_select,
            theme_manager=self.theme_manager,
            width=210,
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        # Vertical separator between sidebar and main content
        sidebar_sep = ttk.Separator(body_frame, orient="vertical")
        sidebar_sep.grid(row=0, column=0, sticky="nse")

        # Right workspace: Vertical PanedWindow (Top: Pages & Command Bar, Bottom: Logs)
        self.paned_window = ttk.PanedWindow(body_frame, orient="vertical")
        self.paned_window.grid(row=0, column=1, sticky="nsew", padx=(2, 4), pady=2)

        upper_container = ttk.Frame(self.paned_window, style="TFrame")
        upper_container.columnconfigure(0, weight=1)
        upper_container.rowconfigure(0, weight=1)

        # Hidden Notebook: manages page swapping without standard top tab tabs
        self.notebook = ttk.Notebook(upper_container, style="Hidden.TNotebook")
        self.notebook.grid(row=0, column=0, sticky="nsew")
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        # Instantiate module tabs
        self.pipeline_tab = PipelineTab(
            self.notebook,
            on_change_callback=self._on_param_changed,
            theme_manager=self.theme_manager,
        )
        self.pp_tab = PPTab(
            self.notebook,
            on_change_callback=self._on_param_changed,
            theme_manager=self.theme_manager,
        )
        self.decomp_tab = DecompTab(
            self.notebook,
            on_change_callback=self._on_param_changed,
            theme_manager=self.theme_manager,
        )
        self.qc_tab = QcTab(
            self.notebook,
            on_change_callback=self._on_param_changed,
            theme_manager=self.theme_manager,
        )
        self.dr_tab = DRTab(
            self.notebook,
            on_change_callback=self._on_param_changed,
            theme_manager=self.theme_manager,
        )
        self.stats_tab = StatsTab(
            self.notebook,
            on_change_callback=self._on_param_changed,
            theme_manager=self.theme_manager,
        )
        self.config_tab = ConfigTab(
            self.notebook,
            on_change_callback=self._on_param_changed,
            theme_manager=self.theme_manager,
        )

        self.notebook.add(self.pipeline_tab, text="Full Pipeline")
        self.notebook.add(self.pp_tab, text="Pre-processing")
        self.notebook.add(self.decomp_tab, text="Decomposition")
        self.notebook.add(self.qc_tab, text="Quality Control")
        self.notebook.add(self.dr_tab, text="Dual Regression")
        self.notebook.add(self.stats_tab, text="Statistics")
        self.notebook.add(self.config_tab, text="Config & Tools")

        # Command preview and execution bar docked below pages
        self.command_bar = CommandBar(
            upper_container,
            on_run_callback=self.run_current_tab,
            on_stop_callback=self.stop_current_process,
            on_validate_callback=self.validate_active_tab,
            theme_manager=self.theme_manager,
        )
        self.command_bar.grid(row=1, column=0, sticky="ew", pady=(4, 0))

        self.paned_window.add(upper_container, weight=3)

        # Lower container: Log console drawer
        self.log_console = LogConsole(self.paned_window)
        self.paned_window.add(self.log_console, weight=2)

    def _on_sidebar_select(self, page_index: int) -> None:
        """Handle page selection from the sidebar.

        Parameters
        ------------
        page_index: int
            Selected page index.

        Returns
        --------
            None: None object
                Selects tab in hidden notebook.
        """
        self.notebook.select(page_index)

    def _on_workdir_changed(self, new_directory: str) -> None:
        """Update active working directory reference across application.

        Parameters
        ------------
        new_directory: str
            New working directory path.

        Returns
        --------
            None: None object
                Updates current_workdir.
        """
        self.current_workdir = new_directory

    def get_active_tab_instance(self) -> ttk.Frame:
        """Return the active tab frame object.

        Parameters
        ------------
        None

        Returns
        --------
            ttk.Frame: tab instance
                Currently selected tab.
        """
        current_index = self.notebook.index(self.notebook.select())
        tab_list = [
            self.pipeline_tab,
            self.pp_tab,
            self.decomp_tab,
            self.qc_tab,
            self.dr_tab,
            self.stats_tab,
            self.config_tab,
        ]
        return tab_list[current_index]

    def _get_active_tab_instance(self) -> ttk.Frame:
        """Backward compatibility helper for get_active_tab_instance.

        Parameters
        ------------
        None

        Returns
        --------
            ttk.Frame: tab instance
                Currently selected tab.
        """
        return self.get_active_tab_instance()

    def construct_active_command(self) -> tuple[list[str], str]:
        """Build CLI command list and string for the active tab.

        Parameters
        ------------
        None

        Returns
        --------
            tuple[list[str], str]: command tokens
                (command_list, formatted_command_string).
        """
        active_tab = self.get_active_tab_instance()
        state_dict = getattr(active_tab, "get_state")()

        if active_tab is self.pipeline_tab:
            cmd_list = build_pipeline_command(state_dict)
        elif active_tab is self.pp_tab:
            cmd_list = build_pp_command(state_dict)
        elif active_tab is self.decomp_tab:
            cmd_list = build_decomp_command(state_dict)
        elif active_tab is self.qc_tab:
            cmd_list = build_qc_command(state_dict)
        elif active_tab is self.dr_tab:
            cmd_list = build_dr_command(state_dict)
        elif active_tab is self.stats_tab:
            cmd_list = build_stats_command(state_dict)
        elif active_tab is self.config_tab:
            cmd_list = build_config_command(state_dict)
        else:
            cmd_list = ["nfact"]

        cmd_string = format_command_string(cmd_list)
        return (cmd_list, cmd_string)

    def _construct_active_command(self) -> tuple[list[str], str]:
        """Backward compatibility helper for construct_active_command.

        Parameters
        ------------
        None

        Returns
        --------
            tuple[list[str], str]: command tokens
                (command_list, formatted_command_string).
        """
        return self.construct_active_command()

    def _on_param_changed(self) -> None:
        """Update command preview whenever parameters change in the active tab.

        Parameters
        ------------
        None

        Returns
        --------
            None: None object
                Updates command bar preview text.
        """
        if not self.runner.is_running:
            _, cmd_str = self.construct_active_command()
            self.command_bar.set_command(cmd_str)

    def _on_tab_changed(self, event_obj: Optional[tk.Event] = None) -> None:
        """Handle notebook tab switch and update command preview.

        Parameters
        ------------
        event_obj: Optional[tk.Event]
            Tab change event. Defaults to None.

        Returns
        --------
            None: None object
                Updates command preview on tab switch.
        """
        self._on_param_changed()

    def validate_active_tab(self) -> bool:
        """Validate inputs on the currently active tab.

        Parameters
        ------------
        None

        Returns
        --------
            bool: is valid
                True if all required parameters are valid, False otherwise.
        """
        active_tab = self.get_active_tab_instance()
        is_valid, error_list = getattr(active_tab, "validate")()
        if is_valid:
            messagebox.showinfo(
                "Validation Successful",
                "All required parameters are valid and ready to run.",
                parent=self,
            )
            return True
        else:
            errors_message = "\n- " + "\n- ".join(error_list)
            messagebox.showwarning(
                "Validation Issues",
                f"Please fix the following parameter issues before running:\n{errors_message}",
                parent=self,
            )
            return False

    def run_current_tab(self) -> None:
        """Delegate command execution to the run controller.

        Parameters
        ------------
        None

        Returns
        --------
            None: None object
                Executes active tab command.
        """
        self.run_controller.run_active_tab()

    def stop_current_process(self) -> None:
        """Delegate process termination to the run controller.

        Parameters
        ------------
        None

        Returns
        --------
            None: None object
                Terminates process.
        """
        self.run_controller.stop_process()

    def toggle_theme(self) -> None:
        """Toggle between Dark and Light color themes.

        Parameters
        ------------
        None

        Returns
        --------
            None: None object
                Toggles theme in ThemeManager.
        """
        new_theme = self.theme_manager.toggle_theme(self)
        self.header_bar.update_theme_label(new_theme)

    def _on_window_close(self) -> None:
        """Handle window close event, terminating any active process safely.

        Parameters
        ------------
        None

        Returns
        --------
            None: None object
                Closes application safely.
        """
        if self.runner.is_running:
            should_close = messagebox.askyesno(
                "Process Running",
                "A process is currently running. Do you want to terminate it and exit?",
                parent=self,
            )
            if not should_close:
                return
            self.runner.terminate_process()

        self.destroy()
