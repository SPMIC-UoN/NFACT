"""
Decomposition tab for configuring and launching standalone nfact_decomp.
"""

import os
import tkinter as tk
from tkinter import ttk
from typing import Any, Callable, Optional

from NFACT.gui.layout.grid_helpers import place_in_form_grid
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


class DecompTab(BaseModuleTab):
    """Tab for configuring and executing nfact_decomp (NMF / ICA decomposition).

    Usage
    -----
    tab = DecompTab(notebook_widget, on_change_callback=update_cmd)
    """

    def __init__(
        self,
        parent_container: tk.Widget,
        on_change_callback: Optional[Callable[[], None]] = None,
        theme_manager: Optional[Any] = None,
        style: str = "TFrame",
    ) -> None:
        """Initialize decomposition tab.

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
                Constructs decomposition tab layout.
        """
        super().__init__(
            parent_container,
            tab_name="Decomposition",
            on_change_callback=on_change_callback,
            page_title="Decomposition",
            page_description="Factorise group tractography connectivity matrices into spatial components (NMF / ICA).",
            cli_name="nfact_decomp",
            theme_manager=theme_manager,
            style=style,
        )

        self._build_decomp_ui()

    def _build_decomp_ui(self) -> None:
        """Build decomposition UI elements.

        Parameters
        ------------
        None

        Returns
        --------
            None: None object
                Constructs cards for decomposition.
        """
        self.scrollable_frame.columnconfigure(0, weight=1)

        # 1. Setup card
        self._build_setup_card()

        # 2. Decomposition core parameters
        self._build_core_params_card()

        # 3. ICA options card (conditionally shown when algo == ICA)
        self._build_ica_card()

        # 4. Output options card
        self._build_output_card()

        # 5. Cluster options card
        cluster_card = self.build_cluster_card(self.scrollable_frame)
        cluster_card.grid(row=4, column=0, sticky="ew", padx=12, pady=(0, 10))

    def _build_setup_card(self) -> None:
        """Build inputs and paths card.

        Parameters
        ------------
        None

        Returns
        --------
            None: None object
                Constructs setup card.
        """
        card = Card(
            self.scrollable_frame,
            title="Inputs & Setup",
            subtitle="Study paths, pre-computed matrices, and seed/ROI definitions",
            initially_expanded=True,
            theme_manager=self.theme_manager,
        )
        card.grid(row=0, column=0, sticky="ew", padx=12, pady=(6, 10))
        card.content_frame.columnconfigure(0, weight=1)

        # Quick action row: Auto-fill from outdir
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
            "Auto-detect seeds_for_decomp.txt and roi_for_decomp.txt in <outdir>/nfact/nfact_pp/.",
        )

        subjects_var = self.create_string_var("list_of_subjects", "")
        subjects_field = FileSelectorField(
            card.content_frame,
            label_text="Subjects list file",
            flag="-l",
            variable=subjects_var,
            title="Select Subjects File",
            tooltip_text="Path to subjects list text file.",
        )
        subjects_field.grid(row=1, column=0, sticky="ew", pady=(0, 6))

        outdir_var = self.create_string_var("outdir", "")
        outdir_field = DirectorySelectorField(
            card.content_frame,
            label_text="Output directory",
            flag="-o",
            variable=outdir_var,
            title="Select Output Directory",
            tooltip_text="Root output directory where nfact_decomp results will be saved.",
            required=True,
        )
        outdir_field.grid(row=2, column=0, sticky="ew", pady=(0, 6))

        seeds_var = self.create_string_var("seeds", "")
        self.seeds_field = MultiPathField(
            card.content_frame,
            label_text="Seeds for decomposition",
            flag="-s",
            variable=seeds_var,
            title="Select seeds_for_decomp.txt or Seed Files",
            tooltip_text="Path to seeds_for_decomp.txt file generated by nfact_pp.",
        )
        self.seeds_field.grid(row=3, column=0, sticky="ew", pady=(0, 6))

        roi_var = self.create_string_var("roi", "")
        self.roi_field = MultiPathField(
            card.content_frame,
            label_text="ROI for decomposition",
            flag="-r",
            variable=roi_var,
            title="Select roi_for_decomp.txt or ROI Files",
            tooltip_text="Path to roi_for_decomp.txt file generated by nfact_pp.",
        )
        self.roi_field.grid(row=4, column=0, sticky="ew", pady=(0, 6))

        matrix_var = self.create_string_var("matrix", "")
        matrix_field = DirectorySelectorField(
            card.content_frame,
            label_text="Pre-computed matrix folder",
            flag="-m",
            variable=matrix_var,
            title="Select Matrix Directory",
            tooltip_text="Optional folder containing pre-averaged dot matrix.",
        )
        matrix_field.grid(row=5, column=0, sticky="ew", pady=(0, 6))

        config_file_var = self.create_string_var("config_file", "")
        config_field = FileSelectorField(
            card.content_frame,
            label_text="Decomposition hyperparameter config file",
            flag="-f",
            variable=config_file_var,
            filetypes=[("Decomp Config", "*.config *.json"), ("All Files", "*.*")],
            title="Select Decomp Config File",
            tooltip_text="JSON hyperparameter configuration file for sklearn NMF / FastICA.",
        )
        config_field.grid(row=6, column=0, sticky="ew", pady=(0, 6))

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
            tooltip_text="Run decomposition using CuPy CUDA GPU acceleration.",
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
        """Auto-populate seeds and roi text files from output directory.

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

    def _build_core_params_card(self) -> None:
        """Build decomposition parameters card (algo, dim, iterations, etc.).

        Parameters
        ------------
        None

        Returns
        --------
            None: None object
                Constructs core parameters card.
        """
        card = Card(
            self.scrollable_frame,
            title="Factorisation Parameters",
            subtitle="Algorithm selection, dimensions, iterations, and winner-takes-all",
            initially_expanded=True,
            theme_manager=self.theme_manager,
        )
        card.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 10))
        card.content_frame.columnconfigure(0, weight=1)

        row_params = ttk.Frame(card.content_frame, style="Surface.TFrame")
        row_params.grid(row=0, column=0, sticky="ew", pady=(0, 6))

        dim_container = ttk.Frame(row_params, style="Surface.TFrame")
        dim_var = self.create_string_var("dim", "75")
        dim_label = FieldLabel(
            dim_container,
            text="Number of dimensions",
            flag="-d",
            required=True,
            tooltip_text="Number of components for factorization.",
        )
        dim_label.pack(fill="x", pady=(0, 2))
        dim_spinbox = ttk.Spinbox(
            dim_container,
            from_=1,
            to=500,
            textvariable=dim_var,
            style="TSpinbox",
        )
        dim_spinbox.pack(fill="x")

        algo_container = ttk.Frame(row_params, style="Surface.TFrame")
        algo_var = self.create_string_var("algo", "NMF")
        algo_label = FieldLabel(
            algo_container,
            text="Algorithm",
            flag="-a",
            tooltip_text="Factorization algorithm: NMF or ICA.",
        )
        algo_label.pack(fill="x", pady=(0, 2))
        algo_combo = ttk.Combobox(
            algo_container,
            textvariable=algo_var,
            values=["NMF", "ICA"],
            state="readonly",
            style="TCombobox",
        )
        algo_combo.pack(fill="x")
        algo_var.trace_add("write", self._on_algo_changed)

        iter_container = ttk.Frame(row_params, style="Surface.TFrame")
        iter_var = self.create_string_var("iterations", "20")
        iter_label = FieldLabel(
            iter_container,
            text="Max iterations",
            flag="-i",
            tooltip_text="Max iterations for matrix factorization solver.",
        )
        iter_label.pack(fill="x", pady=(0, 2))
        iter_spinbox = ttk.Spinbox(
            iter_container,
            from_=1,
            to=500,
            textvariable=iter_var,
            style="TSpinbox",
        )
        iter_spinbox.pack(fill="x")

        place_in_form_grid(
            row_params,
            [dim_container, algo_container, iter_container],
            columns=3,
        )

        row_toggles = ttk.Frame(card.content_frame, style="Surface.TFrame")
        row_toggles.grid(row=1, column=0, sticky="ew", pady=(4, 2))

        wta_var = self.create_bool_var("wta", False)
        toggle_wta = create_toggle(
            row_toggles,
            text="Winner Takes All",
            variable=wta_var,
            flag="-w",
            tooltip_text="Perform winner-takes-all hard classification.",
            theme_manager=self.theme_manager,
        )
        toggle_wta.pack(side="left", padx=(0, 16))

        wta_zhr_var = self.create_string_var("wta_zhr", "")
        wta_container = ttk.Frame(row_toggles, style="Surface.TFrame")
        wta_container.pack(side="left", padx=(0, 16))

        wta_zhr_label = FieldLabel(
            wta_container,
            text="WTA Z-threshold",
            flag="-g",
            tooltip_text="Z-score threshold for winner-takes-all.",
        )
        wta_zhr_label.pack(side="left", padx=(0, 6))
        wta_zhr_entry = ttk.Entry(
            wta_container, textvariable=wta_zhr_var, width=6, style="TEntry"
        )
        wta_zhr_entry.pack(side="left")

        no_decomp_var = self.create_bool_var("no_decomp", False)
        toggle_no_decomp = create_toggle(
            row_toggles,
            text="Skip Decomp Computation",
            variable=no_decomp_var,
            flag="-X",
            tooltip_text="Skip computation and run outputs only.",
            theme_manager=self.theme_manager,
        )
        toggle_no_decomp.pack(side="left")

    def _build_ica_card(self) -> None:
        """Build ICA-specific options card (PCA components, PCA type, sign flip).

        Parameters
        ------------
        None

        Returns
        --------
            None: None object
                Constructs ICA card.
        """
        self.ica_card = Card(
            self.scrollable_frame,
            title="Independent Component Analysis (ICA) Options",
            subtitle="PCA dimension reduction, solver type, and spatial sign flip",
            collapsible=True,
            initially_expanded=False,
            theme_manager=self.theme_manager,
        )
        self.ica_card.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 10))

        row_ica = ttk.Frame(self.ica_card.content_frame, style="Surface.TFrame")
        row_ica.grid(row=0, column=0, sticky="ew", pady=4)

        pca_container = ttk.Frame(row_ica, style="Surface.TFrame")
        pca_comp_var = self.create_string_var("pca_comp", "1000")
        pca_comp_label = FieldLabel(
            pca_container,
            text="PCA components",
            flag="-c",
            tooltip_text="Number of PCA components to reduce data to before FastICA.",
        )
        pca_comp_label.pack(fill="x", pady=(0, 2))
        pca_comp_entry = ttk.Entry(
            pca_container, textvariable=pca_comp_var, style="TEntry"
        )
        pca_comp_entry.pack(fill="x")

        type_container = ttk.Frame(row_ica, style="Surface.TFrame")
        pca_type_var = self.create_string_var("pca_type", "pca")
        pca_type_label = FieldLabel(
            type_container,
            text="PCA type",
            flag="-p",
            tooltip_text="PCA algorithm: 'pca' (standard) or 'migp' (MIGP memory-efficient).",
        )
        pca_type_label.pack(fill="x", pady=(0, 2))
        pca_type_combo = ttk.Combobox(
            type_container,
            textvariable=pca_type_var,
            values=["pca", "migp"],
            state="readonly",
            style="TCombobox",
        )
        pca_type_combo.pack(fill="x")

        place_in_form_grid(row_ica, [pca_container, type_container], columns=2)

        sign_flip_var = self.create_bool_var("spatial_sign_flip", False)
        toggle_flip = create_toggle(
            self.ica_card.content_frame,
            text="Disable Spatial Sign Flip",
            variable=sign_flip_var,
            flag="-S",
            tooltip_text="Disable spatial skewness-based sign flipping.",
            theme_manager=self.theme_manager,
        )
        toggle_flip.grid(row=1, column=0, sticky="w", pady=(4, 0))

        self._update_ica_visibility()

    def _on_algo_changed(self, *unused_args: object) -> None:
        """Respond to algorithm combo change.

        Parameters
        ------------
        unused_args: object
            Tkinter trace args.

        Returns
        --------
            None: None object
                Updates ICA card expansion state.
        """
        self._update_ica_visibility()

    def _update_ica_visibility(self) -> None:
        """Expand or collapse ICA options card based on selected algorithm.

        Parameters
        ------------
        None

        Returns
        --------
            None: None object
                Expands or collapses ICA card.
        """
        algo_name = str(self.params["algo"].get()).strip().upper()  # type: ignore[union-attr]
        if algo_name == "ICA":
            self.ica_card.expand()
        else:
            self.ica_card.collapse()

    def _build_output_card(self) -> None:
        """Build outputs and saving options card.

        Parameters
        ------------
        None

        Returns
        --------
            None: None object
                Constructs output options card.
        """
        card = Card(
            self.scrollable_frame,
            title="Outputs & Post-Processing Options",
            subtitle="File formats, normalisation, disk caching, and WTA maps",
            collapsible=True,
            initially_expanded=True,
            theme_manager=self.theme_manager,
        )
        card.grid(row=3, column=0, sticky="ew", padx=12, pady=(0, 10))

        row_outputs = ttk.Frame(card.content_frame, style="Surface.TFrame")
        row_outputs.grid(row=0, column=0, sticky="ew", pady=(0, 4))

        cifti_var = self.create_bool_var("cifti", False)
        toggle_cifti = create_toggle(
            row_outputs,
            text="CIFTI format",
            variable=cifti_var,
            flag="-C",
            tooltip_text="Save outputs in CIFTI format.",
            theme_manager=self.theme_manager,
        )
        toggle_cifti.pack(side="left", padx=(0, 14))

        disk_var = self.create_bool_var("disk_save", False)
        toggle_disk = create_toggle(
            row_outputs,
            text="Save to disk",
            variable=disk_var,
            flag="-D",
            tooltip_text="Save individual subject components directly to disk.",
            theme_manager=self.theme_manager,
        )
        toggle_disk.pack(side="left", padx=(0, 14))

        normalise_var = self.create_bool_var("normalise", False)
        toggle_norm = create_toggle(
            row_outputs,
            text="Normalise",
            variable=normalise_var,
            flag="-N",
            tooltip_text="Normalise spatial components.",
            theme_manager=self.theme_manager,
        )
        toggle_norm.pack(side="left", padx=(0, 14))

        cluster_save_var = self.create_bool_var("cluster_save", False)
        toggle_cs = create_toggle(
            row_outputs,
            text="Cluster save",
            variable=cluster_save_var,
            flag="-CS",
            tooltip_text="Save on cluster filesystem.",
            theme_manager=self.theme_manager,
        )
        toggle_cs.pack(side="left")

        row_thr = ttk.Frame(card.content_frame, style="Surface.TFrame")
        row_thr.grid(row=1, column=0, sticky="ew", pady=(4, 2))

        thr_var = self.create_string_var("threshold", "")
        thr_container = ttk.Frame(row_thr, style="Surface.TFrame")
        thr_container.pack(side="left", padx=(0, 20))

        thr_label = FieldLabel(
            thr_container,
            text="Threshold",
            flag="-t",
            tooltip_text="Z-score threshold for component thresholding.",
        )
        thr_label.pack(side="left", padx=(0, 6))
        thr_entry = ttk.Entry(
            thr_container, textvariable=thr_var, width=6, style="TEntry"
        )
        thr_entry.pack(side="left")

        wta_save_var = self.create_bool_var("wta_save", False)
        toggle_wta_save = create_toggle(
            row_thr,
            text="Save WTA map",
            variable=wta_save_var,
            flag="-W",
            tooltip_text="Save winner-takes-all classification map.",
            theme_manager=self.theme_manager,
        )
        toggle_wta_save.pack(side="left", padx=(0, 20))

        wta_thr_var = self.create_string_var("wta_thr", "")
        wta_thr_container = ttk.Frame(row_thr, style="Surface.TFrame")
        wta_thr_container.pack(side="left")

        wta_thr_label = FieldLabel(
            wta_thr_container,
            text="WTA threshold",
            flag="-z",
            tooltip_text="WTA component thresholding value.",
        )
        wta_thr_label.pack(side="left", padx=(0, 6))
        wta_thr_entry = ttk.Entry(
            wta_thr_container, textvariable=wta_thr_var, width=6, style="TEntry"
        )
        wta_thr_entry.pack(side="left")

    def validate(self) -> tuple[bool, list[str]]:
        """Validate nfact_decomp inputs.

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

        if not subjects_path and not self.params["matrix"].get().strip():  # type: ignore[union-attr]
            error_list.append(
                "Either List of Subjects (-l) or Pre-computed Matrix folder (-m) must be specified."
            )

        if not outdir_path:
            error_list.append("Output directory (-o / --outdir) is required.")

        dim_str = str(self.params["dim"].get()).strip()  # type: ignore[union-attr]
        try:
            dim_val = int(dim_str)
            if dim_val <= 0:
                error_list.append("Dimensions (-d) must be greater than zero.")
        except ValueError:
            error_list.append("Dimensions (-d) must be a valid integer.")

        return (len(error_list) == 0, error_list)
