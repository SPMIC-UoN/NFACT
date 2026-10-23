"""
Quality control tab for configuring and running standalone nfact_Qc.
"""

import os
import tkinter as tk
from tkinter import ttk
from typing import Any, Callable, Optional

from NFACT.gui.layout.grid_helpers import place_in_form_grid
from NFACT.gui.tabs.base_tab import BaseModuleTab
from NFACT.gui.widgets.card import Card
from NFACT.gui.widgets.field_label import FieldLabel
from NFACT.gui.widgets.path_fields import DirectorySelectorField
from NFACT.gui.widgets.toggle_switch import create_toggle


class QcTab(BaseModuleTab):
    """Tab for configuring and executing nfact_Qc (hitmap quality assessment).

    Usage
    -----
    tab = QcTab(notebook_widget, on_change_callback=update_cmd)
    """

    def __init__(
        self,
        parent_container: tk.Widget,
        on_change_callback: Optional[Callable[[], None]] = None,
        theme_manager: Optional[Any] = None,
        style: str = "TFrame",
    ) -> None:
        """Initialize Quality Control tab.

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
                Constructs QC tab layout.
        """
        super().__init__(
            parent_container,
            tab_name="Quality Control",
            on_change_callback=on_change_callback,
            page_title="Quality Control",
            page_description="Assess component coverage and calculate binary thresholded hitmaps.",
            cli_name="nfact_Qc",
            theme_manager=theme_manager,
            style=style,
        )

        self._build_qc_ui()

    def _build_qc_ui(self) -> None:
        """Build Quality Control tab UI elements.

        Parameters
        ------------
        None

        Returns
        --------
            None: None object
                Constructs cards for QC tab.
        """
        self.scrollable_frame.columnconfigure(0, weight=1)

        card = Card(
            self.scrollable_frame,
            title="Quality Control Parameters",
            subtitle="Decomposition results folder, algorithm, and hitmap thresholding",
            initially_expanded=True,
            theme_manager=self.theme_manager,
        )
        card.grid(row=0, column=0, sticky="ew", padx=12, pady=(6, 10))
        card.content_frame.columnconfigure(0, weight=1)

        folder_var = self.create_string_var("nfact_folder", "")
        folder_field = DirectorySelectorField(
            card.content_frame,
            label_text="NFACT decomposition results folder",
            flag="-n",
            variable=folder_var,
            title="Select nfact_decomp Folder",
            tooltip_text="Path to nfact_decomp output folder containing components.",
            required=True,
        )
        folder_field.grid(row=0, column=0, sticky="ew", pady=(0, 8))

        params_grid = ttk.Frame(card.content_frame, style="Surface.TFrame")
        params_grid.grid(row=1, column=0, sticky="ew", pady=(4, 6))

        dim_container = ttk.Frame(params_grid, style="Surface.TFrame")
        dim_var = self.create_string_var("dim", "75")
        dim_label = FieldLabel(
            dim_container,
            text="Dimensions",
            flag="-d",
            required=True,
            tooltip_text="Dimensionality of the decomposition used to create hitmaps.",
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

        algo_container = ttk.Frame(params_grid, style="Surface.TFrame")
        algo_var = self.create_string_var("algo", "NMF")
        algo_label = FieldLabel(
            algo_container,
            text="Algorithm",
            flag="-a",
            tooltip_text="Decomposition algorithm: NMF or ICA.",
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

        thresh_container = ttk.Frame(params_grid, style="Surface.TFrame")
        thresh_var = self.create_string_var("threshold", "2")
        thresh_label = FieldLabel(
            thresh_container,
            text="Z-score threshold",
            flag="-t",
            tooltip_text="Z-score threshold applied to build binary hitmaps.",
        )
        thresh_label.pack(fill="x", pady=(0, 2))
        thresh_spinbox = ttk.Spinbox(
            thresh_container,
            from_=0,
            to=20,
            textvariable=thresh_var,
            style="TSpinbox",
        )
        thresh_spinbox.pack(fill="x")

        place_in_form_grid(
            params_grid,
            [dim_container, algo_container, thresh_container],
            columns=3,
        )

        overwrite_var = self.create_bool_var("overwrite", False)
        toggle_overwrite = create_toggle(
            card.content_frame,
            text="Overwrite existing QC hitmaps",
            variable=overwrite_var,
            flag="-O",
            tooltip_text="Overwrite existing output files.",
            theme_manager=self.theme_manager,
        )
        toggle_overwrite.grid(row=2, column=0, sticky="w", pady=(4, 0))

    def validate(self) -> tuple[bool, list[str]]:
        """Validate nfact_Qc input values.

        Parameters
        ------------
        None

        Returns
        --------
            tuple[bool, list[str]]: validation result
                (is_valid, error_messages).
        """
        error_list: list[str] = []
        nfact_folder = self.params["nfact_folder"].get().strip()  # type: ignore[union-attr]
        if not nfact_folder:
            error_list.append(
                "NFACT decomposition folder (-n / --nfact_folder) is required."
            )
        elif not os.path.isdir(nfact_folder):
            error_list.append(f"Specified folder does not exist: {nfact_folder}")

        dim_str = str(self.params["dim"].get()).strip()  # type: ignore[union-attr]
        try:
            dim_val = int(dim_str)
            if dim_val <= 0:
                error_list.append("Dimensions (-d) must be greater than zero.")
        except ValueError:
            error_list.append("Dimensions (-d) must be a valid integer.")

        return (len(error_list) == 0, error_list)
