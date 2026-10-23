"""
Parameter card construction helpers for the NFACT Full Pipeline tab.
"""

from tkinter import ttk
from typing import Any

from NFACT.gui.layout.grid_helpers import place_in_form_grid
from NFACT.gui.widgets.card import Card
from NFACT.gui.widgets.field_label import FieldLabel
from NFACT.gui.widgets.path_fields import (
    DirectorySelectorField,
    FileSelectorField,
    MultiPathField,
)
from NFACT.gui.widgets.toggle_switch import create_toggle


def build_pipeline_setup_card(tab_instance: Any) -> Card:
    """Build general pipeline setup card with study paths and folder options.

    Parameters
    ------------
    tab_instance: Any
        PipelineTab instance owning parameter variables.

    Returns
    --------
        Card: setup card
            Configured Card widget.
    """
    card = Card(
        tab_instance.scrollable_frame,
        title="Pipeline Inputs & Paths",
        subtitle="Study list of subjects and root output directory",
        initially_expanded=True,
        theme_manager=tab_instance.theme_manager,
    )
    card.content_frame.columnconfigure(0, weight=1)

    subjects_var = tab_instance.create_string_var("list_of_subjects", "")
    subjects_field = FileSelectorField(
        card.content_frame,
        label_text="Subjects list file",
        flag="-l",
        variable=subjects_var,
        title="Select Subjects File",
        tooltip_text="Path to text file containing one subject per line.",
        required=True,
    )
    subjects_field.grid(row=0, column=0, sticky="ew", pady=(0, 6))

    outdir_var = tab_instance.create_string_var("outdir", "")
    outdir_field = DirectorySelectorField(
        card.content_frame,
        label_text="Output directory",
        flag="-o",
        variable=outdir_var,
        title="Select Output Directory",
        tooltip_text="Directory where the nfact output folder will be created.",
        required=True,
    )
    outdir_field.grid(row=1, column=0, sticky="ew", pady=(0, 6))

    subfolder_row = ttk.Frame(card.content_frame, style="Surface.TFrame")
    subfolder_row.grid(row=2, column=0, sticky="ew", pady=(4, 2))

    folder_container = ttk.Frame(subfolder_row, style="Surface.TFrame")
    folder_container.pack(side="left", padx=(0, 24))

    folder_name_var = tab_instance.create_string_var("folder_name", "nfact")
    folder_label = FieldLabel(
        folder_container,
        text="Output folder name",
        flag="-n",
        tooltip_text="Name of subfolder created under outdir (default: 'nfact').",
    )
    folder_label.pack(side="left", padx=(0, 6))
    folder_entry = ttk.Entry(
        folder_container, textvariable=folder_name_var, width=14, style="TEntry"
    )
    folder_entry.pack(side="left")

    overwrite_var = tab_instance.create_bool_var("overwrite", False)
    toggle_frame = create_toggle(
        subfolder_row,
        text="Overwrite existing outputs",
        variable=overwrite_var,
        flag="-O",
        tooltip_text="Overwrite existing result files if already present.",
        theme_manager=tab_instance.theme_manager,
    )
    toggle_frame.pack(side="left")

    return card


def build_pipeline_pp_card(tab_instance: Any) -> Card:
    """Build pre-processing inputs card for Stage 1 (nfact_pp).

    Parameters
    ------------
    tab_instance: Any
        PipelineTab instance owning parameter variables.

    Returns
    --------
        Card: pp card
            Configured Card widget.
    """
    card = Card(
        tab_instance.scrollable_frame,
        title="Stage 1: Pre-processing Inputs",
        subtitle="Tractography matrix generation with probtrackx2",
        initially_expanded=True,
        theme_manager=tab_instance.theme_manager,
    )
    card.content_frame.columnconfigure(0, weight=1)

    # File tree preset
    tree_row = ttk.Frame(card.content_frame, style="Surface.TFrame")
    tree_row.grid(row=0, column=0, sticky="ew", pady=(0, 6))

    file_tree_var = tab_instance.create_string_var("file_tree", "")
    tree_label = FieldLabel(
        tree_row,
        text="File tree preset",
        flag="-f",
        tooltip_text="File tree preset ('hcp', 'hcp_cifti') or custom path.",
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

    # Seeds
    seed_var = tab_instance.create_string_var("seed", "")
    seed_field = MultiPathField(
        card.content_frame,
        label_text="Seed masks / surfaces",
        flag="-s",
        variable=seed_var,
        title="Select Seed File(s)",
        tooltip_text="Relative paths to seed files inside subject directories.",
    )
    seed_field.grid(row=1, column=0, sticky="ew", pady=(0, 6))

    # Warps
    warps_var = tab_instance.create_string_var("warps", "")
    warps_field = MultiPathField(
        card.content_frame,
        label_text="Warp fields (standard2diff & diff2standard)",
        flag="-w",
        variable=warps_var,
        title="Select Warp Images",
        tooltip_text="Relative paths to Standard2diff and Diff2standard warp fields.",
    )
    warps_field.grid(row=2, column=0, sticky="ew", pady=(0, 6))

    # BPX path
    bpx_row = ttk.Frame(card.content_frame, style="Surface.TFrame")
    bpx_row.grid(row=3, column=0, sticky="ew", pady=(0, 6))
    bpx_row.columnconfigure(1, weight=1)

    bpx_path_var = tab_instance.create_string_var("bpx_path", "")
    bpx_label = FieldLabel(
        bpx_row,
        text="BedpostX folder path",
        flag="-b",
        tooltip_text="Relative path to bedpostX folder within subject directories.",
    )
    bpx_label.grid(row=0, column=0, sticky="w", padx=(0, 6))
    bpx_entry = ttk.Entry(bpx_row, textvariable=bpx_path_var, style="TEntry")
    bpx_entry.grid(row=0, column=1, sticky="ew")

    # Medial wall / ROI
    roi_var = tab_instance.create_string_var("roi", "")
    roi_field = MultiPathField(
        card.content_frame,
        label_text="ROI / Medial wall mask",
        flag="-r",
        variable=roi_var,
        title="Select ROI / Medial Wall Masks",
        tooltip_text="Surface medial wall masks to exclude non-cortex vertices.",
    )
    roi_field.grid(row=4, column=0, sticky="ew", pady=(0, 6))

    # Optional volume reference & target in 2-column grid
    vol_grid = ttk.Frame(card.content_frame, style="Surface.TFrame")
    vol_grid.grid(row=5, column=0, sticky="ew", pady=(2, 0))

    seedref_container = ttk.Frame(vol_grid, style="Surface.TFrame")
    seedref_var = tab_instance.create_string_var("seedref", "")
    seedref_label = FieldLabel(
        seedref_container,
        text="Seed reference image",
        flag="-sr",
        tooltip_text="Optional reference image for seed when seeds are in diffusion space.",
    )
    seedref_label.pack(fill="x", pady=(0, 2))
    seedref_entry = ttk.Entry(
        seedref_container, textvariable=seedref_var, style="TEntry"
    )
    seedref_entry.pack(fill="x")

    target_container = ttk.Frame(vol_grid, style="Surface.TFrame")
    target_var = tab_instance.create_string_var("target2", "")
    target_label = FieldLabel(
        target_container,
        text="Classification target",
        flag="-t",
        tooltip_text="Optional classification target image.",
    )
    target_label.pack(fill="x", pady=(0, 2))
    target_entry = ttk.Entry(target_container, textvariable=target_var, style="TEntry")
    target_entry.pack(fill="x")

    place_in_form_grid(vol_grid, [seedref_container, target_container], columns=2)

    return card


def build_pipeline_decomp_card(tab_instance: Any) -> Card:
    """Build decomposition & dual regression settings card for Stage 2 & 4.

    Parameters
    ------------
    tab_instance: Any
        PipelineTab instance owning parameter variables.

    Returns
    --------
        Card: decomp card
            Configured Card widget.
    """
    card = Card(
        tab_instance.scrollable_frame,
        title="Stage 2 & 4: Decomposition & Dual Regression",
        subtitle="Matrix factorization components and individual subject projection",
        initially_expanded=True,
        theme_manager=tab_instance.theme_manager,
    )
    card.content_frame.columnconfigure(0, weight=1)

    options_grid = ttk.Frame(card.content_frame, style="Surface.TFrame")
    options_grid.grid(row=0, column=0, sticky="ew", pady=(0, 6))

    dim_container = ttk.Frame(options_grid, style="Surface.TFrame")
    dim_var = tab_instance.create_string_var("dim", "75")
    dim_label = FieldLabel(
        dim_container,
        text="Number of dimensions",
        flag="-d",
        required=True,
        tooltip_text="Number of components/dimensions for factorization (default: 75).",
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

    algo_container = ttk.Frame(options_grid, style="Surface.TFrame")
    algo_var = tab_instance.create_string_var("algo", "NMF")
    algo_label = FieldLabel(
        algo_container,
        text="Factorization algorithm",
        flag="-a",
        tooltip_text="Matrix factorization algorithm: NMF or ICA.",
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

    place_in_form_grid(options_grid, [dim_container, algo_container], columns=2)

    # GPU toggle switch
    gpu_var = tab_instance.create_bool_var("gpu", False)
    gpu_toggle = create_toggle(
        card.content_frame,
        text="Enable CUDA GPU acceleration",
        variable=gpu_var,
        flag="-G",
        tooltip_text="Run decomposition and DR with CuPy CUDA GPU acceleration.",
        theme_manager=tab_instance.theme_manager,
    )
    gpu_toggle.grid(row=1, column=0, sticky="w", pady=(2, 6))

    # rf_decomp (shown when Stage 1 is skipped)
    rf_decomp_var = tab_instance.create_string_var("rf_decomp", "")
    tab_instance.rf_decomp_field = FileSelectorField(
        card.content_frame,
        label_text="ROI for decomp file",
        flag="-rf",
        variable=rf_decomp_var,
        title="Select ROI for Decomp Text File",
        tooltip_text="Path to roi_for_decomp.txt file (required when pre-processing is skipped).",
    )
    tab_instance.rf_decomp_field.grid(row=2, column=0, sticky="ew", pady=(2, 0))
    tab_instance.rf_decomp_field.grid_remove()

    return card


def build_pipeline_qc_card(tab_instance: Any) -> Card:
    """Build quality control threshold card for Stage 3 (nfact_Qc).

    Parameters
    ------------
    tab_instance: Any
        PipelineTab instance owning parameter variables.

    Returns
    --------
        Card: qc card
            Configured Card widget.
    """
    card = Card(
        tab_instance.scrollable_frame,
        title="Stage 3: Quality Control Hitmaps",
        subtitle="Component coverage and binary thresholding",
        initially_expanded=True,
        theme_manager=tab_instance.theme_manager,
    )
    card.content_frame.columnconfigure(0, weight=1)

    thresh_row = ttk.Frame(card.content_frame, style="Surface.TFrame")
    thresh_row.grid(row=0, column=0, sticky="w", pady=2)

    thresh_var = tab_instance.create_string_var("threshold", "2")
    thresh_label = FieldLabel(
        thresh_row,
        text="Z-score threshold",
        flag="--threshold",
        tooltip_text="Z-score threshold value applied when calculating binary hitmaps (default: 2).",
    )
    thresh_label.pack(side="left", padx=(0, 8))
    thresh_spin = ttk.Spinbox(
        thresh_row,
        from_=0,
        to=20,
        textvariable=thresh_var,
        width=8,
        style="TSpinbox",
    )
    thresh_spin.pack(side="left")

    return card
