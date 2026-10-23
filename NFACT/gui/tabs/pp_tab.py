"""
Pre-processing tab for configuring and launching standalone nfact_pp.
"""

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


class PPTab(BaseModuleTab):
    """Tab for configuring and executing nfact_pp tractography pre-processing.

    Usage
    -----
    tab = PPTab(notebook_widget, on_change_callback=update_cmd)
    """

    def __init__(
        self,
        parent_container: tk.Widget,
        on_change_callback: Optional[Callable[[], None]] = None,
        theme_manager: Optional[Any] = None,
        style: str = "TFrame",
    ) -> None:
        """Initialize pre-processing tab.

        Parameters
        ------------
        parent_container: tk.Widget
            Parent notebook widget.
        on_change_callback: Optional[Callable[[], None]]
            Callback executed when parameter values change. Defaults to None.
        theme_manager: Optional[Any]
            ThemeManager reference for dynamic styling. Defaults to None.
        style: str
            ttk frame style name. Defaults to "TFrame".

        Returns
        --------
            None: None object
                Constructs tab layout.
        """
        super().__init__(
            parent_container,
            tab_name="Pre-processing",
            on_change_callback=on_change_callback,
            page_title="Pre-processing",
            page_description="Generate connectivity matrices with probtrackx2 tractography and downsampling.",
            cli_name="nfact_pp",
            theme_manager=theme_manager,
            style=style,
        )

        self._build_pp_ui()

    def _build_pp_ui(self) -> None:
        """Build UI components for nfact_pp.

        Parameters
        ------------
        None

        Returns
        --------
            None: None object
                Builds and places cards.
        """
        self.scrollable_frame.columnconfigure(0, weight=1)

        # 1. Preset modes banner
        self._build_preset_bar()

        # 2. Setup card
        self._build_setup_card()

        # 3. Tractography inputs card
        self._build_tractography_card()

        # 4. Advanced options card
        self._build_advanced_card()

        # 5. Downsampling card
        self._build_downsampling_card()

        # 6. Cluster submission card
        self.build_cluster_card(self.scrollable_frame).grid(
            row=5, column=0, sticky="ew", padx=12, pady=(0, 10)
        )

    def _build_preset_bar(self) -> None:
        """Build preset quick buttons for common tractography pipelines.

        Parameters
        ------------
        None

        Returns
        --------
            None: None object
                Constructs preset bar frame.
        """
        preset_frame = ttk.Frame(
            self.scrollable_frame, style="Surface.TFrame", padding=(10, 8)
        )
        preset_frame.grid(row=0, column=0, sticky="ew", padx=12, pady=(6, 8))

        preset_label = ttk.Label(
            preset_frame,
            text="Presets:",
            style="CardTitle.TLabel",
        )
        preset_label.pack(side="left", padx=(0, 10))

        hcp_btn = ttk.Button(
            preset_frame,
            text="HCP Surface Preset",
            command=self._apply_hcp_preset,
            style="TButton",
        )
        hcp_btn.pack(side="left", padx=(0, 6))

        cifti_btn = ttk.Button(
            preset_frame,
            text="HCP CIFTI Preset",
            command=self._apply_cifti_preset,
            style="TButton",
        )
        cifti_btn.pack(side="left", padx=(0, 6))

        reset_btn = ttk.Button(
            preset_frame,
            text="Clear Form",
            command=self._clear_all_fields,
            style="Ghost.TButton",
        )
        reset_btn.pack(side="right")

    def _apply_hcp_preset(self) -> None:
        """Populate fields with standard HCP surface defaults.

        Parameters
        ------------
        None

        Returns
        --------
            None: None object
                Updates variables with HCP surface preset values.
        """
        self.params["file_tree"].set("hcp")
        self.params["bpx_path"].set("T1w/Diffusion.bedpostX")
        self.params["nsamples"].set("5000")

    def _apply_cifti_preset(self) -> None:
        """Populate fields with standard HCP CIFTI defaults.

        Parameters
        ------------
        None

        Returns
        --------
            None: None object
                Updates variables with HCP CIFTI preset values.
        """
        self.params["file_tree"].set("hcp_cifti")
        self.params["bpx_path"].set("T1w/Diffusion.bedpostX")
        self.params["nsamples"].set("5000")

    def _clear_all_fields(self) -> None:
        """Reset all parameters in this tab.

        Parameters
        ------------
        None

        Returns
        --------
            None: None object
                Clears all registered variables.
        """
        for param_var in self.params.values():
            if isinstance(param_var, tk.BooleanVar):
                param_var.set(False)
            elif isinstance(param_var, tk.StringVar):
                param_var.set("")

    def _build_setup_card(self) -> None:
        """Build base inputs card (list of subjects, outdir, overwrite, gpu, cores).

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
            title="Setup & Execution Options",
            subtitle="Study paths, GPU acceleration, and CPU parallelism",
            initially_expanded=True,
            theme_manager=self.theme_manager,
        )
        card.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 10))
        card.content_frame.columnconfigure(0, weight=1)

        subjects_var = self.create_string_var("list_of_subjects", "")
        subjects_field = FileSelectorField(
            card.content_frame,
            label_text="Subjects list file",
            flag="-l",
            variable=subjects_var,
            title="Select Subjects File",
            tooltip_text="Path to text file containing subject paths.",
            required=True,
        )
        subjects_field.grid(row=0, column=0, sticky="ew", pady=(0, 6))

        outdir_var = self.create_string_var("outdir", "")
        outdir_field = DirectorySelectorField(
            card.content_frame,
            label_text="Output directory",
            flag="-o",
            variable=outdir_var,
            title="Select Output Directory",
            tooltip_text="Output directory where nfact_pp matrices will be generated.",
            required=True,
        )
        outdir_field.grid(row=1, column=0, sticky="ew", pady=(0, 6))

        options_row = ttk.Frame(card.content_frame, style="Surface.TFrame")
        options_row.grid(row=2, column=0, sticky="ew", pady=(4, 2))

        overwrite_var = self.create_bool_var("overwrite", False)
        toggle_overwrite = create_toggle(
            options_row,
            text="Overwrite outputs",
            variable=overwrite_var,
            flag="-O",
            tooltip_text="Overwrite existing result files if already present.",
            theme_manager=self.theme_manager,
        )
        toggle_overwrite.pack(side="left", padx=(0, 16))

        gpu_var = self.create_bool_var("gpu", False)
        toggle_gpu = create_toggle(
            options_row,
            text="Enable GPU probtrackx2",
            variable=gpu_var,
            flag="-G",
            tooltip_text="Run tractography via CUDA GPU probtrackx2 acceleration.",
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

    def _build_tractography_card(self) -> None:
        """Build inputs card for tractography definitions (seeds, warps, bpx, rois).

        Parameters
        ------------
        None

        Returns
        --------
            None: None object
                Constructs tractography inputs card.
        """
        card = Card(
            self.scrollable_frame,
            title="Tractography Definitions & Masks",
            subtitle="Filetree presets, seed surfaces, warp fields, and classification target",
            initially_expanded=True,
            theme_manager=self.theme_manager,
        )
        card.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 10))
        card.content_frame.columnconfigure(0, weight=1)

        tree_row = ttk.Frame(card.content_frame, style="Surface.TFrame")
        tree_row.grid(row=0, column=0, sticky="ew", pady=(0, 6))

        file_tree_var = self.create_string_var("file_tree", "")
        tree_label = FieldLabel(
            tree_row,
            text="File tree preset",
            flag="-f",
            tooltip_text="Select predefined file tree ('hcp', 'hcp_cifti') or enter custom .tree file path.",
        )
        tree_label.pack(side="left", padx=(0, 8))
        tree_combo = ttk.Combobox(
            tree_row,
            textvariable=file_tree_var,
            values=["", "hcp", "hcp_cifti"],
            width=15,
            style="TCombobox",
        )
        tree_combo.pack(side="left")

        seed_var = self.create_string_var("seed", "")
        seed_field = MultiPathField(
            card.content_frame,
            label_text="Seed masks / surfaces",
            flag="-s",
            variable=seed_var,
            title="Select Seed File(s)",
            tooltip_text="Seeds in diffusion space or relative paths in subject folder.",
        )
        seed_field.grid(row=1, column=0, sticky="ew", pady=(0, 6))

        warps_var = self.create_string_var("warps", "")
        warps_field = MultiPathField(
            card.content_frame,
            label_text="Warp transformations (Standard2diff / Diff2standard)",
            flag="-w",
            variable=warps_var,
            title="Select Warps",
            tooltip_text="Standard2diff and Diff2standard nonlinear transformations.",
        )
        warps_field.grid(row=2, column=0, sticky="ew", pady=(0, 6))

        bpx_row = ttk.Frame(card.content_frame, style="Surface.TFrame")
        bpx_row.grid(row=3, column=0, sticky="ew", pady=(0, 6))
        bpx_row.columnconfigure(1, weight=1)

        bpx_path_var = self.create_string_var("bpx_path", "")
        bpx_label = FieldLabel(
            bpx_row,
            text="BedpostX folder path",
            flag="-b",
            tooltip_text="Relative path to bedpostX folder within each subject directory.",
        )
        bpx_label.grid(row=0, column=0, sticky="w", padx=(0, 6))
        bpx_entry = ttk.Entry(bpx_row, textvariable=bpx_path_var, style="TEntry")
        bpx_entry.grid(row=0, column=1, sticky="ew")

        roi_var = self.create_string_var("roi", "")
        roi_field = MultiPathField(
            card.content_frame,
            label_text="ROI / Medial wall mask",
            flag="-r",
            variable=roi_var,
            title="Select ROI / Medial Wall Masks",
            tooltip_text="Relative paths to medial wall mask files.",
        )
        roi_field.grid(row=4, column=0, sticky="ew", pady=(0, 6))

        vol_grid = ttk.Frame(card.content_frame, style="Surface.TFrame")
        vol_grid.grid(row=5, column=0, sticky="ew", pady=(2, 0))

        seedref_container = ttk.Frame(vol_grid, style="Surface.TFrame")
        seedref_var = self.create_string_var("seedref", "")
        seedref_label = FieldLabel(
            seedref_container,
            text="Seed reference image",
            flag="-sr",
            tooltip_text="Reference volume for seed when seeds are in diffusion space.",
        )
        seedref_label.pack(fill="x", pady=(0, 2))
        seedref_entry = ttk.Entry(
            seedref_container, textvariable=seedref_var, style="TEntry"
        )
        seedref_entry.pack(fill="x")

        target_container = ttk.Frame(vol_grid, style="Surface.TFrame")
        target_var = self.create_string_var("target2", "")
        target_label = FieldLabel(
            target_container,
            text="Classification target",
            flag="-t",
            tooltip_text="Optional classification target image.",
        )
        target_label.pack(fill="x", pady=(0, 2))
        target_entry = ttk.Entry(
            target_container, textvariable=target_var, style="TEntry"
        )
        target_entry.pack(fill="x")

        place_in_form_grid(vol_grid, [seedref_container, target_container], columns=2)

    def _build_advanced_card(self) -> None:
        """Build advanced probtrackx2 parameter options.

        Parameters
        ------------
        None

        Returns
        --------
            None: None object
                Constructs advanced options card.
        """
        card = Card(
            self.scrollable_frame,
            title="Advanced Probtrackx2 Options",
            subtitle="Streamline sampling counts, custom flags, and stop/exclusion masks",
            collapsible=True,
            initially_expanded=False,
            theme_manager=self.theme_manager,
        )
        card.grid(row=3, column=0, sticky="ew", padx=12, pady=(0, 10))
        card.content_frame.columnconfigure(0, weight=1)

        row_params = ttk.Frame(card.content_frame, style="Surface.TFrame")
        row_params.grid(row=0, column=0, sticky="ew", pady=(0, 6))

        nsamples_var = self.create_string_var("nsamples", "5000")
        samples_container = ttk.Frame(row_params, style="Surface.TFrame")
        samples_container.pack(side="left", padx=(0, 24))

        nsamples_label = FieldLabel(
            samples_container,
            text="Streamline samples",
            flag="-ns",
            tooltip_text="Number of streamline samples per seed voxel (default: 5000).",
        )
        nsamples_label.pack(side="left", padx=(0, 6))
        nsamples_spin = ttk.Spinbox(
            samples_container,
            from_=100,
            to=50000,
            textvariable=nsamples_var,
            width=7,
            style="TSpinbox",
        )
        nsamples_spin.pack(side="left")

        min_mask_var = self.create_bool_var("min_mask", False)
        toggle_min_mask = create_toggle(
            row_params,
            text="Min Mask",
            variable=min_mask_var,
            flag="-mm",
            tooltip_text="Perform minimum masking across seed masks.",
            theme_manager=self.theme_manager,
        )
        toggle_min_mask.pack(side="left")

        ptx_var = self.create_string_var("ptx_options", "")
        ptx_field = FileSelectorField(
            card.content_frame,
            label_text="Custom ptx_options file",
            flag="-p",
            variable=ptx_var,
            title="Select ptx_options File",
            tooltip_text="Custom probtrackx2 command line options file.",
        )
        ptx_field.grid(row=1, column=0, sticky="ew", pady=(0, 4))

        excl_var = self.create_string_var("exclusion", "")
        excl_field = FileSelectorField(
            card.content_frame,
            label_text="Exclusion mask",
            flag="-e",
            variable=excl_var,
            title="Select Exclusion Mask",
            tooltip_text="Exclusion mask image file.",
        )
        excl_field.grid(row=2, column=0, sticky="ew", pady=(0, 4))

        stop_var = self.create_string_var("stop", "")
        stop_field = FileSelectorField(
            card.content_frame,
            label_text="Stop mask",
            flag="-S",
            variable=stop_var,
            title="Select Stop Mask",
            tooltip_text="Stop mask image file.",
        )
        stop_field.grid(row=3, column=0, sticky="ew", pady=(0, 4))

        add_row = ttk.Frame(card.content_frame, style="Surface.TFrame")
        add_row.grid(row=4, column=0, sticky="ew", pady=(0, 4))
        add_row.columnconfigure(1, weight=1)

        add_seeds_var = self.create_string_var("add_seeds", "")
        add_label = FieldLabel(
            add_row,
            text="Additional seed list",
            flag="-A",
            tooltip_text="Additional seed files to track.",
        )
        add_label.grid(row=0, column=0, sticky="w", padx=(0, 6))
        add_entry = ttk.Entry(add_row, textvariable=add_seeds_var, style="TEntry")
        add_entry.grid(row=0, column=1, sticky="ew")

        first_ref_var = self.create_string_var("first_ref", "")
        first_ref_field = FileSelectorField(
            card.content_frame,
            label_text="First subject reference image",
            flag="-F",
            variable=first_ref_var,
            title="Select First Ref Image",
            tooltip_text="Reference volume for first subject.",
        )
        first_ref_field.grid(row=5, column=0, sticky="ew", pady=(0, 4))

    def _build_downsampling_card(self) -> None:
        """Build downsampling options card.

        Parameters
        ------------
        None

        Returns
        --------
            None: None object
                Constructs downsampling card.
        """
        card = Card(
            self.scrollable_frame,
            title="Matrix Downsampling Options",
            subtitle="Resolution reduction for tractography connectivity matrices",
            collapsible=True,
            initially_expanded=False,
            theme_manager=self.theme_manager,
        )
        card.grid(row=4, column=0, sticky="ew", padx=12, pady=(0, 10))
        card.content_frame.columnconfigure(0, weight=1)

        downsample_var = self.create_bool_var("downsample", False)
        toggle_ds = create_toggle(
            card.content_frame,
            text="Downsample connectivity matrix",
            variable=downsample_var,
            flag="-D",
            tooltip_text="Downsample output matrix resolution.",
            theme_manager=self.theme_manager,
        )
        toggle_ds.grid(row=0, column=0, sticky="w", pady=(0, 6))

        downsample_row = ttk.Frame(card.content_frame, style="Surface.TFrame")
        downsample_row.grid(row=1, column=0, sticky="ew", pady=(0, 4))
        downsample_row.columnconfigure(1, weight=1)
        downsample_row.columnconfigure(3, weight=1)

        vx_var = self.create_string_var("voxel_size", "")
        vx_label = FieldLabel(
            downsample_row,
            text="Voxel / vertex size",
            flag="-vx",
            tooltip_text="Target downsampled voxel or vertex spacing.",
        )
        vx_label.grid(row=0, column=0, sticky="w", padx=(0, 4))
        vx_entry = ttk.Entry(
            downsample_row, textvariable=vx_var, width=10, style="TEntry"
        )
        vx_entry.grid(row=0, column=1, sticky="w", padx=(0, 8))

        vl_var = self.create_string_var("vol_ref", "")
        vl_label = FieldLabel(
            downsample_row,
            text="Volume reference",
            flag="-vl",
            tooltip_text="Volume reference file for downsampling.",
        )
        vl_label.grid(row=0, column=2, sticky="w", padx=(0, 4))
        vl_entry = ttk.Entry(downsample_row, textvariable=vl_var, style="TEntry")
        vl_entry.grid(row=0, column=3, sticky="ew")

    def validate(self) -> tuple[bool, list[str]]:
        """Validate nfact_pp inputs.

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
        if not subjects_path:
            error_list.append(
                "List of subjects file (-l / --list_of_subjects) is required."
            )

        outdir_path = self.params["outdir"].get().strip()  # type: ignore[union-attr]
        if not outdir_path:
            error_list.append("Output directory (-o / --outdir) is required.")

        has_seeds = bool(self.params["seed"].get().strip())  # type: ignore[union-attr]
        has_tree = bool(self.params["file_tree"].get().strip())  # type: ignore[union-attr]
        if not has_seeds and not has_tree:
            error_list.append(
                "Either Seeds (-s) or a File Tree (-f) must be specified."
            )

        return (len(error_list) == 0, error_list)
