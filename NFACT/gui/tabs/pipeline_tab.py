"""
End-to-end NFACT pipeline tab with interactive 4-stage execution toggles.
"""

import json
import os
import tkinter as tk
from tkinter import ttk
from typing import Any, Callable, Optional

from NFACT.gui.tabs.base_tab import BaseModuleTab
from NFACT.gui.tabs.pipeline_cards import (
    build_pipeline_decomp_card,
    build_pipeline_pp_card,
    build_pipeline_qc_card,
    build_pipeline_setup_card,
)
from NFACT.gui.widgets.path_fields import FileSelectorField
from NFACT.gui.widgets.stage_flow import StageFlowBar, StageSpec


class PipelineTab(BaseModuleTab):
    """Tab for configuring and executing the full end-to-end NFACT pipeline.

    Usage
    -----
    tab = PipelineTab(notebook_widget, on_change_callback=update_cmd)
    """

    def __init__(
        self,
        parent_container: tk.Widget,
        on_change_callback: Optional[Callable[[], None]] = None,
        theme_manager: Optional[Any] = None,
        style: str = "TFrame",
    ) -> None:
        """Initialize pipeline tab.

        Parameters
        ------------
        parent_container: tk.Widget
            Parent notebook container.
        on_change_callback: Optional[Callable[[], None]]
            Callback executed when any parameter changes. Defaults to None.
        theme_manager: Optional[Any]
            ThemeManager reference for dynamic styling. Defaults to None.
        style: str
            ttk frame style name. Defaults to "TFrame".

        Returns
        --------
            None: None object
                Constructs pipeline tab layout.
        """
        super().__init__(
            parent_container,
            tab_name="Full Pipeline",
            on_change_callback=on_change_callback,
            page_title="Full Pipeline",
            page_description="Execute the end-to-end NFACT tractography factorisation pipeline.",
            cli_name="nfact",
            theme_manager=theme_manager,
            style=style,
        )

        # Stage skip flags
        self.pp_skip_var = self.create_bool_var("pp_skip", False)
        self.qc_skip_var = self.create_bool_var("qc_skip", False)
        self.dr_skip_var = self.create_bool_var("dr_skip", False)

        # Config mode flag and file path
        self.use_config_file_var = self.create_bool_var("use_config_file", False)
        self.config_path_var = self.create_string_var("config", "")

        self._build_pipeline_ui()

    def _build_pipeline_ui(self) -> None:
        """Assemble the complete UI layout for the pipeline tab.

        Parameters
        ------------
        None

        Returns
        --------
            None: None object
                Builds and places cards on scrollable canvas.
        """
        self.scrollable_frame.columnconfigure(0, weight=1)

        # 1. Mode selector card (Form vs Config File)
        self._build_mode_selector_card()

        # 2. Pipeline 4-Stage Flow Control Bar
        self._build_stage_flow_bar()

        # 3. Pipeline Setup Card
        self.setup_card = build_pipeline_setup_card(self)
        self.setup_card.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 10))

        # 4. Pre-processing Inputs Card
        self.pp_card = build_pipeline_pp_card(self)
        self.pp_card.grid(row=3, column=0, sticky="ew", padx=12, pady=(0, 10))

        # 5. Decomposition & Dual Regression Card
        self.decomp_card = build_pipeline_decomp_card(self)
        self.decomp_card.grid(row=4, column=0, sticky="ew", padx=12, pady=(0, 10))

        # 6. Quality Control Card
        self.qc_card = build_pipeline_qc_card(self)
        self.qc_card.grid(row=5, column=0, sticky="ew", padx=12, pady=(0, 10))

        # 7. Cluster Card
        self.cluster_card = self.build_cluster_card(self.scrollable_frame)
        self.cluster_card.grid(row=6, column=0, sticky="ew", padx=12, pady=(0, 10))

    def _build_mode_selector_card(self) -> None:
        """Build segmented mode selector toggle between Form and Config File.

        Parameters
        ------------
        None

        Returns
        --------
            None: None object
                Constructs mode selection container.
        """
        mode_card = ttk.Frame(self.scrollable_frame, style="Surface.TFrame", padding=8)
        mode_card.grid(row=0, column=0, sticky="ew", padx=12, pady=(6, 8))
        mode_card.columnconfigure(1, weight=1)

        mode_label = ttk.Label(
            mode_card,
            text="Execution Mode:",
            style="CardTitle.TLabel",
        )
        mode_label.grid(row=0, column=0, padx=(4, 12), sticky="w")

        segments_container = ttk.Frame(mode_card, style="Surface.TFrame")
        segments_container.grid(row=0, column=1, sticky="w")

        radio_form = ttk.Radiobutton(
            segments_container,
            text="Interactive Parameter Form",
            variable=self.use_config_file_var,
            value=False,
            style="Segment.TRadiobutton",
            command=self._on_mode_toggled,
        )
        radio_form.pack(side="left", padx=(0, 4))

        radio_config = ttk.Radiobutton(
            segments_container,
            text="Pipeline Config File (-c)",
            variable=self.use_config_file_var,
            value=True,
            style="Segment.TRadiobutton",
            command=self._on_mode_toggled,
        )
        radio_config.pack(side="left")

        # Config file picker row (initially hidden)
        self.config_picker_frame = ttk.Frame(mode_card, style="Surface.TFrame")
        self.config_picker_frame.grid(
            row=1, column=0, columnspan=2, sticky="ew", pady=(8, 0)
        )
        self.config_picker_frame.columnconfigure(0, weight=1)

        self.config_field = FileSelectorField(
            self.config_picker_frame,
            label_text="Path to .pipeline.config file",
            flag="-c",
            variable=self.config_path_var,
            filetypes=[("Pipeline Config", "*.config *.json"), ("All Files", "*.*")],
            title="Select Pipeline Config File",
            tooltip_text="JSON config file created by nfact_config or edited manually.",
        )
        self.config_field.grid(row=0, column=0, sticky="ew", padx=(4, 8))

        load_btn = ttk.Button(
            self.config_picker_frame,
            text="Load Config into Form",
            command=self._load_config_into_form,
            style="TButton",
        )
        load_btn.grid(row=0, column=1, sticky="e")

        self.config_picker_frame.grid_remove()

    def _on_mode_toggled(self) -> None:
        """Handle switching between Form and Config File execution modes.

        Parameters
        ------------
        None

        Returns
        --------
            None: None object
                Toggles visibility of config picker frame.
        """
        is_config_mode = self.use_config_file_var.get()
        if is_config_mode:
            self.config_picker_frame.grid()
        else:
            self.config_picker_frame.grid_remove()
            self.config_path_var.set("")
        self._on_parameter_change()

    def _load_config_into_form(self) -> None:
        """Parse selected pipeline config file and populate form fields.

        Parameters
        ------------
        None

        Returns
        --------
            None: None object
                Reads JSON and updates form state.
        """
        config_file_path = self.config_path_var.get().strip()
        if not config_file_path or not os.path.isfile(config_file_path):
            return

        try:
            with open(config_file_path, "r", encoding="utf-8") as file_handle:
                loaded_dict = json.load(file_handle)
            self.set_state(loaded_dict)
            self.use_config_file_var.set(False)
            self._on_mode_toggled()
        except Exception:
            pass

    def _build_stage_flow_bar(self) -> None:
        """Build the interactive 4-stage pipeline execution control bar.

        Parameters
        ------------
        None

        Returns
        --------
            None: None object
                Constructs StageFlowBar canvas.
        """
        flow_container = ttk.Frame(
            self.scrollable_frame, style="Surface.TFrame", padding=(10, 8)
        )
        flow_container.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 8))
        flow_container.columnconfigure(0, weight=1)

        stage_specs = [
            StageSpec(
                key="pp",
                title="1. Pre-process",
                subtitle="nfact_pp",
                state="enabled",
            ),
            StageSpec(
                key="decomp",
                title="2. Decomp",
                subtitle="nfact_decomp (Core)",
                state="locked",
                locked=True,
            ),
            StageSpec(
                key="qc",
                title="3. Quality Control",
                subtitle="nfact_Qc",
                state="enabled",
            ),
            StageSpec(
                key="dr",
                title="4. Dual Reg",
                subtitle="nfact_dr",
                state="enabled",
            ),
        ]

        self.stage_flow_bar = StageFlowBar(
            flow_container,
            stages=stage_specs,
            on_toggle=self._on_stage_toggled,
            theme_manager=self.theme_manager,
            height=46,
        )
        self.stage_flow_bar.grid(row=0, column=0, sticky="ew")

    def _on_stage_toggled(self, stage_key: str, is_enabled: bool) -> None:
        """Handle user toggling a pipeline stage pill.

        Parameters
        ------------
        stage_key: str
            Stage identifier ('pp', 'qc', 'dr').
        is_enabled: bool
            Whether stage was switched to enabled.

        Returns
        --------
            None: None object
                Updates parameter skip flags and card expansion.
        """
        if stage_key == "pp":
            self.pp_skip_var.set(not is_enabled)
            if is_enabled:
                self.pp_card.set_enabled(True)
                self.pp_card.expand()
                self.rf_decomp_field.grid_remove()
            else:
                self.pp_card.set_enabled(False)
                self.pp_card.collapse()
                self.rf_decomp_field.grid()
        elif stage_key == "qc":
            self.qc_skip_var.set(not is_enabled)
            if is_enabled:
                self.qc_card.set_enabled(True)
                self.qc_card.expand()
            else:
                self.qc_card.set_enabled(False)
                self.qc_card.collapse()
        elif stage_key == "dr":
            self.dr_skip_var.set(not is_enabled)

        self._on_parameter_change()

    def validate(self) -> tuple[bool, list[str]]:
        """Validate required inputs on the pipeline tab.

        Parameters
        ------------
        None

        Returns
        --------
            tuple[bool, list[str]]: validation result
                (is_valid, error_messages).
        """
        error_list: list[str] = []

        if self.use_config_file_var.get():
            cfg_path = self.config_path_var.get().strip()
            if not cfg_path:
                error_list.append("Pipeline config file path must be specified.")
            elif not os.path.isfile(cfg_path):
                error_list.append(f"Specified config file does not exist: {cfg_path}")
            return (len(error_list) == 0, error_list)

        subjects_path = self.params["list_of_subjects"].get().strip()  # type: ignore[union-attr]
        if not subjects_path:
            error_list.append(
                "List of subjects file (-l / --list_of_subjects) is required."
            )

        outdir_path = self.params["outdir"].get().strip()  # type: ignore[union-attr]
        if not outdir_path:
            error_list.append("Output directory (-o / --outdir) is required.")

        dim_str = str(self.params["dim"].get()).strip()  # type: ignore[union-attr]
        try:
            dim_val = int(dim_str)
            if dim_val <= 0:
                error_list.append("Dimension (-d / --dim) must be a positive integer.")
        except ValueError:
            error_list.append("Dimension (-d / --dim) must be a valid integer.")

        if not self.pp_skip_var.get():
            has_seeds = bool(self.params["seed"].get().strip())  # type: ignore[union-attr]
            has_tree = bool(self.params["file_tree"].get().strip())  # type: ignore[union-attr]
            if not has_seeds and not has_tree:
                error_list.append(
                    "Either Seed masks (-s) or a File Tree (-f) must be specified for pre-processing."
                )

        return (len(error_list) == 0, error_list)
