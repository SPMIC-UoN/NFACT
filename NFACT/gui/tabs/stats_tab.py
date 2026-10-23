"""
Statistics tab for configuring and running nfact_stats (loadings and statsmap).
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
)
from NFACT.gui.widgets.toggle_switch import create_toggle


class StatsTab(BaseModuleTab):
    """Tab for configuring and executing nfact_stats (loadings or statistical maps).

    Usage
    -----
    tab = StatsTab(notebook_widget, on_change_callback=update_cmd)
    """

    def __init__(
        self,
        parent_container: tk.Widget,
        on_change_callback: Optional[Callable[[], None]] = None,
        theme_manager: Optional[Any] = None,
        style: str = "TFrame",
    ) -> None:
        """Initialize statistics tab.

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
                Constructs statistics tab layout.
        """
        super().__init__(
            parent_container,
            tab_name="Statistics",
            on_change_callback=on_change_callback,
            page_title="Statistics",
            page_description="Extract subject component loadings or generate component statistical maps.",
            cli_name="nfact_stats",
            theme_manager=theme_manager,
            style=style,
        )

        self.subcommand_var = self.create_string_var("subcommand", "loadings")
        self._build_stats_ui()

    def _build_stats_ui(self) -> None:
        """Build UI components for nfact_stats.

        Parameters
        ------------
        None

        Returns
        --------
            None: None object
                Builds and places cards.
        """
        self.scrollable_frame.columnconfigure(0, weight=1)

        # 1. Subcommand selector banner
        self._build_subcommand_bar()

        # 2. Shared setup card
        self._build_setup_card()

        # 3. Loadings specific card
        self._build_loadings_card()

        # 4. Statsmap specific card
        self._build_statsmap_card()

        self._update_subcommand_view()

    def _build_subcommand_bar(self) -> None:
        """Build toggle bar between loadings and statsmap subcommands.

        Parameters
        ------------
        None

        Returns
        --------
            None: None object
                Constructs segmented subcommand selection container.
        """
        banner_frame = ttk.Frame(
            self.scrollable_frame, style="Surface.TFrame", padding=(10, 8)
        )
        banner_frame.grid(row=0, column=0, sticky="ew", padx=12, pady=(6, 8))
        banner_frame.columnconfigure(1, weight=1)

        subcmd_label = ttk.Label(
            banner_frame,
            text="Subcommand Mode:",
            style="CardTitle.TLabel",
        )
        subcmd_label.grid(row=0, column=0, padx=(0, 12), sticky="w")

        segments_container = ttk.Frame(banner_frame, style="Surface.TFrame")
        segments_container.grid(row=0, column=1, sticky="w")

        radio_loadings = ttk.Radiobutton(
            segments_container,
            text="Subject Loadings (nfact_stats loadings)",
            variable=self.subcommand_var,
            value="loadings",
            style="Segment.TRadiobutton",
            command=self._on_subcommand_toggled,
        )
        radio_loadings.pack(side="left", padx=(0, 4))

        radio_statsmap = ttk.Radiobutton(
            segments_container,
            text="Statistical Maps (nfact_stats statsmap)",
            variable=self.subcommand_var,
            value="statsmap",
            style="Segment.TRadiobutton",
            command=self._on_subcommand_toggled,
        )
        radio_statsmap.pack(side="left")

    def _on_subcommand_toggled(self) -> None:
        """Respond to change of subcommand selection.

        Parameters
        ------------
        None

        Returns
        --------
            None: None object
                Updates card visibility and triggers change event.
        """
        self._update_subcommand_view()
        self._on_parameter_change()

    def _update_subcommand_view(self) -> None:
        """Show or hide loadings and statsmap cards depending on active subcommand.

        Parameters
        ------------
        None

        Returns
        --------
            None: None object
                Swaps visibility of sub-cards.
        """
        subcommand_type = self.subcommand_var.get()
        if subcommand_type == "loadings":
            self.loadings_card.grid()
            self.statsmap_card.grid_remove()
        else:
            self.loadings_card.grid_remove()
            self.statsmap_card.grid()

    def _build_setup_card(self) -> None:
        """Build common inputs card (subjects, outdir, nfact_folder, dim, algo).

        Parameters
        ------------
        None

        Returns
        --------
            None: None object
                Constructs shared setup card.
        """
        card = Card(
            self.scrollable_frame,
            title="Inputs & Setup",
            subtitle="Study paths, decomposition outputs folder, and algorithm",
            initially_expanded=True,
            theme_manager=self.theme_manager,
        )
        card.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 10))
        card.content_frame.columnconfigure(0, weight=1)

        subjects_var = self.create_string_var("list_of_subjects", "")
        self.subjects_field = FileSelectorField(
            card.content_frame,
            label_text="Subjects list file",
            flag="-l",
            variable=subjects_var,
            title="Select Subjects File",
            tooltip_text="Path to list of subjects file.",
        )
        self.subjects_field.grid(row=0, column=0, sticky="ew", pady=(0, 6))

        outdir_var = self.create_string_var("outdir", "")
        outdir_field = DirectorySelectorField(
            card.content_frame,
            label_text="Output directory",
            flag="-o",
            variable=outdir_var,
            title="Select Output Directory",
            tooltip_text="Root output directory where nfact_stats results will be saved.",
            required=True,
        )
        outdir_field.grid(row=1, column=0, sticky="ew", pady=(0, 6))

        nfact_folder_var = self.create_string_var("nfact_folder", "")
        nfact_folder_field = DirectorySelectorField(
            card.content_frame,
            label_text="NFACT output folder",
            flag="-n",
            variable=nfact_folder_var,
            title="Select NFACT Output Folder",
            tooltip_text="Directory containing nfact outputs.",
        )
        nfact_folder_field.grid(row=2, column=0, sticky="ew", pady=(0, 6))

        params_grid = ttk.Frame(card.content_frame, style="Surface.TFrame")
        params_grid.grid(row=3, column=0, sticky="ew", pady=(4, 2))

        dim_container = ttk.Frame(params_grid, style="Surface.TFrame")
        dim_var = self.create_string_var("dim", "75")
        dim_label = FieldLabel(
            dim_container,
            text="Dimensions",
            flag="-d",
            required=True,
            tooltip_text="Dimensionality of the decomposition.",
        )
        dim_label.pack(fill="x", pady=(0, 2))
        dim_spin = ttk.Spinbox(
            dim_container,
            from_=1,
            to=500,
            textvariable=dim_var,
            style="TSpinbox",
        )
        dim_spin.pack(fill="x")

        algo_container = ttk.Frame(params_grid, style="Surface.TFrame")
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

        place_in_form_grid(params_grid, [dim_container, algo_container], columns=2)

        overwrite_var = self.create_bool_var("overwrite", False)
        toggle_overwrite = create_toggle(
            card.content_frame,
            text="Overwrite outputs",
            variable=overwrite_var,
            flag="-O",
            tooltip_text="Overwrite existing files.",
            theme_manager=self.theme_manager,
        )
        toggle_overwrite.grid(row=4, column=0, sticky="w", pady=(4, 0))

    def _build_loadings_card(self) -> None:
        """Build loadings-specific card (threshold, no_csv).

        Parameters
        ------------
        None

        Returns
        --------
            None: None object
                Constructs loadings card.
        """
        self.loadings_card = Card(
            self.scrollable_frame,
            title="Loadings Options (nfact_stats loadings)",
            subtitle="Z-score threshold and format options for extracting loadings",
            initially_expanded=True,
            theme_manager=self.theme_manager,
        )
        self.loadings_card.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 10))

        row_loadings = ttk.Frame(
            self.loadings_card.content_frame, style="Surface.TFrame"
        )
        row_loadings.grid(row=0, column=0, sticky="ew", pady=4)

        thr_var = self.create_string_var("threshold", "2")
        thr_container = ttk.Frame(row_loadings, style="Surface.TFrame")
        thr_container.pack(side="left", padx=(0, 20))

        thr_label = FieldLabel(
            thr_container,
            text="Z-score threshold",
            flag="-t",
            tooltip_text="Z-score threshold for extracting subject component loadings (default: 2).",
        )
        thr_label.pack(side="left", padx=(0, 6))
        thr_spin = ttk.Spinbox(
            thr_container,
            from_=0,
            to=20,
            textvariable=thr_var,
            width=6,
            style="TSpinbox",
        )
        thr_spin.pack(side="left")

        no_csv_var = self.create_bool_var("no_csv", False)
        toggle_no_csv = create_toggle(
            row_loadings,
            text="Don't save CSV table",
            variable=no_csv_var,
            flag="-C",
            tooltip_text="Save output only as NumPy .npy array without CSV table.",
            theme_manager=self.theme_manager,
        )
        toggle_no_csv.pack(side="left")

    def _build_statsmap_card(self) -> None:
        """Build statsmap-specific card (components, map_name, threshold, group_only, skip).

        Parameters
        ------------
        None

        Returns
        --------
            None: None object
                Constructs statsmap card.
        """
        self.statsmap_card = Card(
            self.scrollable_frame,
            title="Statsmap Options (nfact_stats statsmap)",
            subtitle="Components list, statistical map name, and group-only calculation",
            initially_expanded=True,
            theme_manager=self.theme_manager,
        )
        self.statsmap_card.grid(row=3, column=0, sticky="ew", padx=12, pady=(0, 10))
        self.statsmap_card.content_frame.columnconfigure(0, weight=1)

        comps_var = self.create_string_var("components", "")
        comps_container = ttk.Frame(
            self.statsmap_card.content_frame, style="Surface.TFrame"
        )
        comps_container.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        comps_container.columnconfigure(0, weight=1)

        comps_label = FieldLabel(
            comps_container,
            text="Components list",
            flag="-c",
            tooltip_text="Space-separated integer list of components to compute statistical maps for (e.g. 1 5 12).",
        )
        comps_label.grid(row=0, column=0, sticky="ew", pady=(0, 2))
        comps_entry = ttk.Entry(comps_container, textvariable=comps_var, style="TEntry")
        comps_entry.grid(row=1, column=0, sticky="ew")

        row_params = ttk.Frame(self.statsmap_card.content_frame, style="Surface.TFrame")
        row_params.grid(row=1, column=0, sticky="ew", pady=(2, 4))

        map_name_var = self.create_string_var("map_name", "")
        map_container = ttk.Frame(row_params, style="Surface.TFrame")
        map_container.pack(side="left", padx=(0, 16))

        map_label = FieldLabel(
            map_container,
            text="Map name",
            flag="-m",
            tooltip_text="Identifier name for the output statistical map.",
        )
        map_label.pack(side="left", padx=(0, 6))
        map_entry = ttk.Entry(
            map_container, textvariable=map_name_var, width=15, style="TEntry"
        )
        map_entry.pack(side="left")

        thr_var = self.create_string_var("threshold", "2")
        thr_container = ttk.Frame(row_params, style="Surface.TFrame")
        thr_container.pack(side="left", padx=(0, 16))

        thr_label = FieldLabel(
            thr_container,
            text="Threshold",
            flag="-t",
            tooltip_text="Z-score threshold for statsmap.",
        )
        thr_label.pack(side="left", padx=(0, 6))
        thr_spin = ttk.Spinbox(
            thr_container,
            from_=0,
            to=20,
            textvariable=thr_var,
            width=6,
            style="TSpinbox",
        )
        thr_spin.pack(side="left")

        group_only_var = self.create_bool_var("group_only", False)
        toggle_group_only = create_toggle(
            row_params,
            text="Group Only",
            variable=group_only_var,
            flag="-G",
            tooltip_text="Compute group-level statistical maps only.",
            theme_manager=self.theme_manager,
        )
        toggle_group_only.pack(side="left", padx=(0, 16))

        skip_var = self.create_bool_var("skip", False)
        toggle_skip = create_toggle(
            row_params,
            text="Skip Variance Maps",
            variable=skip_var,
            flag="-S",
            tooltip_text="Skip variance map calculations.",
            theme_manager=self.theme_manager,
        )
        toggle_skip.pack(side="left")

    def validate(self) -> tuple[bool, list[str]]:
        """Validate nfact_stats input values.

        Parameters
        ------------
        None

        Returns
        --------
            tuple[bool, list[str]]: validation result
                (is_valid, error_messages).
        """
        error_list: list[str] = []
        outdir_val = self.params["outdir"].get().strip()  # type: ignore[union-attr]
        if not outdir_val:
            error_list.append("Output directory (-o / --outdir) is required.")

        subcommand_type = self.subcommand_var.get()
        is_group_only = self.params.get("group_only", tk.BooleanVar(value=False)).get()

        if subcommand_type == "loadings" or not is_group_only:
            subjects_val = self.params["list_of_subjects"].get().strip()  # type: ignore[union-attr]
            if not subjects_val:
                error_list.append(
                    "List of subjects file (-l / --list_of_subjects) is required."
                )

        dim_str = str(self.params["dim"].get()).strip()  # type: ignore[union-attr]
        try:
            dim_val = int(dim_str)
            if dim_val <= 0:
                error_list.append("Dimensions (-d) must be a positive integer.")
        except ValueError:
            error_list.append("Dimensions (-d) must be a valid integer.")

        return (len(error_list) == 0, error_list)
