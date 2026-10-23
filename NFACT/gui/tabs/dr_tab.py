"""
Dual regression tab for configuring and launching standalone nfact_dr.
"""

import os
import tkinter as tk
from tkinter import ttk
from typing import Any, Callable, Optional

from NFACT.gui.tabs.base_tab import BaseModuleTab
from NFACT.gui.widgets.card import Card
from NFACT.gui.widgets.field_label import FieldLabel
from NFACT.gui.widgets.path_fields import (
    DirectorySelectorField,
    FileSelectorField,
    MultiPathField,
)
from NFACT.gui.widgets.toggle_switch import create_toggle
from NFACT.gui.widgets.tooltip import HoverTooltip


class DRTab(BaseModuleTab):
    """Tab for configuring and executing nfact_dr (dual regression).

    Usage
    -----
    tab = DRTab(notebook_widget, on_change_callback=update_cmd)
    """

    def __init__(
        self,
        parent_container: tk.Widget,
        on_change_callback: Optional[Callable[[], None]] = None,
        theme_manager: Optional[Any] = None,
        style: str = "TFrame",
    ) -> None:
        """Initialize dual regression tab.

        Parameters
        ------------
        parent_container: tk.Widget
            Parent notebook container.
        on_change_callback: Optional[Callable[[], None]]
            Callback executed when parameter values change. Defaults to None.
        theme_manager: Optional[Any]
            ThemeManager reference for dynamic styling. Defaults to None.
        style: str
            ttk frame style name. Defaults to "TFrame".

        Returns
        --------
            None: None object
                Constructs dual regression tab layout.
        """
        super().__init__(
            parent_container,
            tab_name="Dual Regression",
            on_change_callback=on_change_callback,
            page_title="Dual Regression",
            page_description="Project group decomposition maps back onto individual subject tractography.",
            cli_name="nfact_dr",
            theme_manager=theme_manager,
            style=style,
        )

        self._build_dr_ui()

    def _build_dr_ui(self) -> None:
        """Build dual regression tab UI layout.

        Parameters
        ------------
        None

        Returns
        --------
            None: None object
                Constructs cards for dual regression.
        """
        self.scrollable_frame.columnconfigure(0, weight=1)

        # 1. Setup card
        self._build_setup_card()

        # 2. Dual regression options card
        self._build_options_card()

        # 3. Cluster submission card
        cluster_card = self.build_cluster_card(self.scrollable_frame)
        cluster_card.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 10))

    def _build_setup_card(self) -> None:
        """Build paths and inputs card for dual regression.

        Parameters
        ------------
        None

        Returns
        --------
            None: None object
                Constructs inputs card.
        """
        card = Card(
            self.scrollable_frame,
            title="Dual Regression Inputs & Paths",
            subtitle="Study paths, group decomposition folder, and seed/ROI definitions",
            initially_expanded=True,
            theme_manager=self.theme_manager,
        )
        card.grid(row=0, column=0, sticky="ew", padx=12, pady=(6, 10))
        card.content_frame.columnconfigure(0, weight=1)

        action_row = ttk.Frame(card.content_frame, style="Surface.TFrame")
        action_row.grid(row=0, column=0, sticky="ew", pady=(0, 6))

        autofill_btn = ttk.Button(
            action_row,
            text="Auto-fill Paths from Output Directory",
            command=self._autofill_paths,
            style="Ghost.TButton",
        )
        autofill_btn.pack(side="left")
        HoverTooltip(
            autofill_btn,
            "Auto-detect seeds, rois, and nfact_decomp directory in output tree.",
        )

        subjects_var = self.create_string_var("list_of_subjects", "")
        subjects_field = FileSelectorField(
            card.content_frame,
            label_text="Subjects list file",
            flag="-l",
            variable=subjects_var,
            title="Select Subjects File",
            tooltip_text="Path to list of subjects file.",
            required=True,
        )
        subjects_field.grid(row=1, column=0, sticky="ew", pady=(0, 6))

        outdir_var = self.create_string_var("outdir", "")
        outdir_field = DirectorySelectorField(
            card.content_frame,
            label_text="Output directory",
            flag="-o",
            variable=outdir_var,
            title="Select Output Directory",
            tooltip_text="Root output directory where nfact_dr will create its output folder.",
            required=True,
        )
        outdir_field.grid(row=2, column=0, sticky="ew", pady=(0, 6))

        nfact_decomp_var = self.create_string_var("nfact_decomp_dir", "")
        self.nfact_decomp_field = DirectorySelectorField(
            card.content_frame,
            label_text="NFACT decomposition results directory",
            flag="-d",
            variable=nfact_decomp_var,
            title="Select nfact_decomp Folder",
            tooltip_text="Path to nfact_decomp directory containing group factorisation matrices.",
        )
        self.nfact_decomp_field.grid(row=3, column=0, sticky="ew", pady=(0, 6))

        decomp_var = self.create_string_var("decomp_dir", "")
        decomp_field = DirectorySelectorField(
            card.content_frame,
            label_text="Pre-existing decomposition directory",
            flag="-dd",
            variable=decomp_var,
            title="Select Pre-existing Decomp Directory",
            tooltip_text="Alternative directory containing decomposition results.",
        )
        decomp_field.grid(row=4, column=0, sticky="ew", pady=(0, 6))

        seeds_var = self.create_string_var("seeds", "")
        self.seeds_field = MultiPathField(
            card.content_frame,
            label_text="Seeds for dual regression",
            flag="-s",
            variable=seeds_var,
            title="Select Seeds",
            tooltip_text="Path to seeds_for_decomp.txt file.",
        )
        self.seeds_field.grid(row=5, column=0, sticky="ew", pady=(0, 6))

        roi_var = self.create_string_var("roi", "")
        self.roi_field = MultiPathField(
            card.content_frame,
            label_text="ROI / Medial wall mask",
            flag="-r",
            variable=roi_var,
            title="Select ROI / Medial Wall Masks",
            tooltip_text="Path to roi_for_decomp.txt file.",
        )
        self.roi_field.grid(row=6, column=0, sticky="ew", pady=(0, 6))

        options_row = ttk.Frame(card.content_frame, style="Surface.TFrame")
        options_row.grid(row=7, column=0, sticky="ew", pady=(4, 2))

        overwrite_var = self.create_bool_var("overwrite", False)
        toggle_overwrite = create_toggle(
            options_row,
            text="Overwrite outputs",
            variable=overwrite_var,
            flag="-O",
            tooltip_text="Overwrite existing files.",
            theme_manager=self.theme_manager,
        )
        toggle_overwrite.pack(side="left", padx=(0, 16))

        gpu_var = self.create_bool_var("gpu", False)
        toggle_gpu = create_toggle(
            options_row,
            text="Enable GPU",
            variable=gpu_var,
            flag="-G",
            tooltip_text="Run dual regression using CuPy CUDA GPU acceleration.",
            theme_manager=self.theme_manager,
        )
        toggle_gpu.pack(side="left", padx=(0, 16))

        cores_var = self.create_string_var("n_cores", "")
        cores_container = ttk.Frame(options_row, style="Surface.TFrame")
        cores_container.pack(side="left")

        cores_label = FieldLabel(
            cores_container,
            text="Parallel CPU cores",
            flag="-n",
            tooltip_text="Number of CPU cores for parallel processing.",
        )
        cores_label.pack(side="left", padx=(0, 6))
        cores_spinbox = ttk.Spinbox(
            cores_container,
            from_=1,
            to=128,
            textvariable=cores_var,
            width=5,
            style="TSpinbox",
        )
        cores_spinbox.pack(side="left")

    def _autofill_paths(self) -> None:
        """Auto-populate seeds, roi, and nfact_decomp directory from output directory.

        Parameters
        ------------
        None

        Returns
        --------
            None: None object
                Sets variable values if matching files exist.
        """
        base_outdir = self.params["outdir"].get().strip()  # type: ignore[union-attr]
        if not base_outdir:
            return

        candidate_dirs = [
            os.path.join(base_outdir, "nfact", "nfact_pp"),
            os.path.join(base_outdir, "nfact_pp"),
            base_outdir,
        ]

        for check_dir in candidate_dirs:
            candidate_seeds = os.path.join(check_dir, "seeds_for_decomp.txt")
            if os.path.isfile(candidate_seeds):
                self.params["seeds"].set(candidate_seeds)
                break

        for check_dir in candidate_dirs:
            candidate_roi = os.path.join(check_dir, "roi_for_decomp.txt")
            if os.path.isfile(candidate_roi):
                self.params["roi"].set(candidate_roi)
                break

        candidate_decomp_dirs = [
            os.path.join(base_outdir, "nfact", "nfact_decomp"),
            os.path.join(base_outdir, "nfact_decomp"),
        ]
        for check_decomp in candidate_decomp_dirs:
            if os.path.isdir(check_decomp):
                self.params["nfact_decomp_dir"].set(check_decomp)
                break

    def _build_options_card(self) -> None:
        """Build dual regression parameters card.

        Parameters
        ------------
        None

        Returns
        --------
            None: None object
                Constructs options card.
        """
        card = Card(
            self.scrollable_frame,
            title="Dual Regression Parameters",
            subtitle="Algorithm type, normalisation, CIFTI dscalar format, and threshold",
            initially_expanded=True,
            theme_manager=self.theme_manager,
        )
        card.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 10))

        row_params = ttk.Frame(card.content_frame, style="Surface.TFrame")
        row_params.grid(row=0, column=0, sticky="ew", pady=(0, 4))

        algo_var = self.create_string_var("algo", "NMF")
        algo_container = ttk.Frame(row_params, style="Surface.TFrame")
        algo_container.pack(side="left", padx=(0, 16))

        algo_label = FieldLabel(
            algo_container,
            text="Algorithm",
            flag="-a",
            tooltip_text="Factorization algorithm: NMF or ICA.",
        )
        algo_label.pack(side="left", padx=(0, 6))
        algo_combo = ttk.Combobox(
            algo_container,
            textvariable=algo_var,
            values=["NMF", "ICA"],
            state="readonly",
            width=8,
            style="TCombobox",
        )
        algo_combo.pack(side="left")

        norm_var = self.create_bool_var("normalise", False)
        toggle_norm = create_toggle(
            row_params,
            text="Normalise Spatial Maps",
            variable=norm_var,
            flag="-N",
            tooltip_text="Normalise subject spatial component maps.",
            theme_manager=self.theme_manager,
        )
        toggle_norm.pack(side="left", padx=(0, 16))

        dscalar_var = self.create_bool_var("dscalar", False)
        toggle_dscalar = create_toggle(
            row_params,
            text="CIFTI dscalar format",
            variable=dscalar_var,
            flag="-D",
            tooltip_text="Export outputs in CIFTI dscalar format.",
            theme_manager=self.theme_manager,
        )
        toggle_dscalar.pack(side="left", padx=(0, 16))

        thr_var = self.create_string_var("threshold", "0")
        thr_container = ttk.Frame(row_params, style="Surface.TFrame")
        thr_container.pack(side="left")

        thr_label = FieldLabel(
            thr_container,
            text="Threshold",
            flag="-t",
            tooltip_text="Z-score threshold value.",
        )
        thr_label.pack(side="left", padx=(0, 6))
        thr_entry = ttk.Entry(
            thr_container, textvariable=thr_var, width=6, style="TEntry"
        )
        thr_entry.pack(side="left")

    def validate(self) -> tuple[bool, list[str]]:
        """Validate nfact_dr input values.

        Parameters
        ------------
        None

        Returns
        --------
            tuple[bool, list[str]]: validation result
                (is_valid, error_messages).
        """
        error_list: list[str] = []
        subjects_path = self.params["list_of_subjects"].get().strip()  # type: ignore[union-attr]
        outdir_path = self.params["outdir"].get().strip()  # type: ignore[union-attr]

        if not subjects_path:
            error_list.append("List of subjects (-l / --list_of_subjects) is required.")
        if not outdir_path:
            error_list.append("Output directory (-o / --outdir) is required.")

        decomp_path = self.params["nfact_decomp_dir"].get().strip()  # type: ignore[union-attr]
        alt_decomp_path = self.params["decomp_dir"].get().strip()  # type: ignore[union-attr]
        if not decomp_path and not alt_decomp_path:
            error_list.append(
                "Either NFACT Decomp Directory (-d) or Pre-existing Decomp Directory (-dd) must be provided."
            )

        return (len(error_list) == 0, error_list)
