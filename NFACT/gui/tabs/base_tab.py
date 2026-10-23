"""
Base module tab providing scrollable canvas layout, parameter binding, and validation.
"""

import os
import tkinter as tk
from tkinter import ttk
from typing import Any, Callable, Optional

from NFACT.gui.layout.grid_helpers import place_in_form_grid
from NFACT.gui.widgets.card import Card
from NFACT.gui.widgets.field_label import FieldLabel
from NFACT.gui.widgets.page_header import PageHeader
from NFACT.gui.widgets.path_fields import (
    DirectorySelectorField,
    FileSelectorField,
)
from NFACT.gui.widgets.toggle_switch import create_toggle


class BaseModuleTab(ttk.Frame):
    """Abstract base frame for NFACT GUI module tabs.

    Usage
    -----
    class MyTab(BaseModuleTab):
        def _build_tab_ui(self):
            # add cards into self.scrollable_frame
            pass
    """

    def __init__(
        self,
        parent_container: tk.Widget,
        tab_name: str,
        on_change_callback: Optional[Callable[[], None]] = None,
        page_title: str = "",
        page_description: str = "",
        cli_name: str = "",
        theme_manager: Optional[Any] = None,
        style: str = "TFrame",
    ) -> None:
        """Initialize base module tab.

        Parameters
        ------------
        parent_container: tk.Widget
            Parent container (typically ttk.Notebook).
        tab_name: str
            Human-readable name of module tab.
        on_change_callback: Optional[Callable[[], None]]
            Callback invoked whenever any registered parameter changes. Defaults to None.
        page_title: str
            Optional top title displayed in PageHeader. Defaults to "".
        page_description: str
            Optional subtitle description for PageHeader. Defaults to "".
        cli_name: str
            Optional CLI command badge (e.g. "nfact_pp"). Defaults to "".
        theme_manager: Optional[Any]
            ThemeManager reference for dynamic styling. Defaults to None.
        style: str
            ttk frame style name. Defaults to "TFrame".

        Returns
        --------
            None: None object
                Initializes base tab framework.
        """
        super().__init__(parent_container, style=style)
        self.tab_name = tab_name
        self.on_change_callback = on_change_callback
        self.theme_manager = theme_manager

        self.params: dict[str, tk.Variable] = {}
        self.cluster_inputs_frame: Optional[ttk.Frame] = None

        self.columnconfigure(0, weight=1)
        row_offset = 0

        # Render top page header if title provided
        if page_title:
            self.header_banner = PageHeader(
                self,
                title=page_title,
                description=page_description,
                cli_name=cli_name,
            )
            self.header_banner.grid(row=0, column=0, columnspan=2, sticky="ew")
            self.rowconfigure(0, weight=0)
            row_offset = 1

        self.rowconfigure(row_offset, weight=1)

        # Scrollable canvas architecture
        self.canvas = tk.Canvas(
            self,
            highlightthickness=0,
            borderwidth=0,
            bg="#15131D",
        )
        self.canvas.grid(row=row_offset, column=0, sticky="nsew")

        self.scrollbar = ttk.Scrollbar(
            self,
            orient="vertical",
            command=self.canvas.yview,
            style="Vertical.TScrollbar",
        )
        self.scrollbar.grid(row=row_offset, column=1, sticky="ns")

        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollable_frame = ttk.Frame(self.canvas, style="TFrame")
        self.canvas_window_id = self.canvas.create_window(
            (0, 0), window=self.scrollable_frame, anchor="nw"
        )

        self.scrollable_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        self.bind("<Enter>", self._bind_mousewheel)
        self.bind("<Leave>", self._unbind_mousewheel)

        if self.theme_manager is not None:
            self.theme_manager.register_widget(self, self.apply_palette)

    def _on_frame_configure(self, event_obj: tk.Event) -> None:
        """Update canvas scroll region to encompass full scrollable frame.

        Parameters
        ------------
        event_obj: tk.Event
            Configuration event.

        Returns
        --------
            None: None object
                Updates scrollregion bounding box.
        """
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event_obj: tk.Event) -> None:
        """Adjust scrollable frame width to match canvas viewport width.

        Parameters
        ------------
        event_obj: tk.Event
            Configuration event.

        Returns
        --------
            None: None object
                Sets canvas window width.
        """
        self.canvas.itemconfig(self.canvas_window_id, width=event_obj.width)

    def _bind_mousewheel(self, event_obj: Optional[tk.Event] = None) -> None:
        """Bind mousewheel scrolling when mouse enters tab view.

        Parameters
        ------------
        event_obj: Optional[tk.Event]
            Event. Defaults to None.

        Returns
        --------
            None: None object
                Binds mousewheel events.
        """
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel_linux)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel_linux)

    def _unbind_mousewheel(self, event_obj: Optional[tk.Event] = None) -> None:
        """Unbind mousewheel scrolling when mouse leaves tab view.

        Parameters
        ------------
        event_obj: Optional[tk.Event]
            Event. Defaults to None.

        Returns
        --------
            None: None object
                Unbinds mousewheel events.
        """
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")

    def _on_mousewheel(self, event_obj: tk.Event) -> None:
        """Handle mousewheel scroll for Windows / macOS.

        Parameters
        ------------
        event_obj: tk.Event
            Mousewheel event.

        Returns
        --------
            None: None object
                Scrolls canvas vertically.
        """
        if self.canvas.winfo_exists():
            delta_val = int(-1 * (event_obj.delta / 120))
            self.canvas.yview_scroll(delta_val, "units")

    def _on_mousewheel_linux(self, event_obj: tk.Event) -> None:
        """Handle mousewheel scroll for Linux Button-4 and Button-5.

        Parameters
        ------------
        event_obj: tk.Event
            Button event.

        Returns
        --------
            None: None object
                Scrolls canvas vertically.
        """
        if self.canvas.winfo_exists():
            if event_obj.num == 4:
                self.canvas.yview_scroll(-2, "units")
            elif event_obj.num == 5:
                self.canvas.yview_scroll(2, "units")

    def register_variable(
        self,
        var_name: str,
        var_instance: tk.Variable,
    ) -> tk.Variable:
        """Register a Tkinter variable and attach a trace listener.

        Parameters
        ------------
        var_name: str
            Key identifying the parameter.
        var_instance: tk.Variable
            StringVar, BooleanVar, or IntVar.

        Returns
        --------
            tk.Variable: registered variable
                The registered variable instance.
        """
        self.params[var_name] = var_instance
        var_instance.trace_add("write", self._on_parameter_change)
        return var_instance

    def create_string_var(
        self,
        var_name: str,
        initial_value: str = "",
    ) -> tk.StringVar:
        """Create and register a tk.StringVar.

        Parameters
        ------------
        var_name: str
            Parameter name.
        initial_value: str
            Starting value. Defaults to "".

        Returns
        --------
            tk.StringVar: created variable
                The created StringVar.
        """
        var_obj = tk.StringVar(value=initial_value)
        return self.register_variable(var_name, var_obj)  # type: ignore[return-value]

    def create_bool_var(
        self,
        var_name: str,
        initial_value: bool = False,
    ) -> tk.BooleanVar:
        """Create and register a tk.BooleanVar.

        Parameters
        ------------
        var_name: str
            Parameter name.
        initial_value: bool
            Starting value. Defaults to False.

        Returns
        --------
            tk.BooleanVar: created variable
                The created BooleanVar.
        """
        var_obj = tk.BooleanVar(value=initial_value)
        return self.register_variable(var_name, var_obj)  # type: ignore[return-value]

    def create_int_var(
        self,
        var_name: str,
        initial_value: int = 0,
    ) -> tk.IntVar:
        """Create and register a tk.IntVar.

        Parameters
        ------------
        var_name: str
            Parameter name.
        initial_value: int
            Starting value. Defaults to 0.

        Returns
        --------
            tk.IntVar: created variable
                The created IntVar.
        """
        var_obj = tk.IntVar(value=initial_value)
        return self.register_variable(var_name, var_obj)  # type: ignore[return-value]

    def _on_parameter_change(self, *unused_args: object) -> None:
        """Invoke change callback whenever any registered parameter updates.

        Parameters
        ------------
        unused_args: object
            Tkinter trace args.

        Returns
        --------
            None: None object
                Invokes change callback if present.
        """
        if self.on_change_callback is not None:
            self.on_change_callback()

    def get_state(self) -> dict[str, object]:
        """Export dictionary of all current parameter values.

        Parameters
        ------------
        None

        Returns
        --------
            dict[str, object]: state dictionary
                Map of parameter names to values.
        """
        state_dict: dict[str, object] = {}
        for param_key, var_item in self.params.items():
            state_dict[param_key] = var_item.get()
        return state_dict

    def set_state(self, state_dict: dict[str, object]) -> None:
        """Import dictionary of parameter values into tab controls.

        Parameters
        ------------
        state_dict: dict[str, object]
            Dictionary containing parameter values to populate.

        Returns
        --------
            None: None object
                Sets values into registered variables.
        """
        for param_key, param_value in state_dict.items():
            if param_key in self.params:
                target_var = self.params[param_key]
                if isinstance(target_var, tk.BooleanVar):
                    target_var.set(bool(param_value))
                elif isinstance(target_var, tk.IntVar):
                    try:
                        target_var.set(int(param_value))
                    except (ValueError, TypeError):
                        pass
                else:
                    if isinstance(param_value, list):
                        target_var.set(" ".join(str(item) for item in param_value))
                    else:
                        target_var.set(
                            str(param_value) if param_value is not None else ""
                        )

    def validate(self) -> tuple[bool, list[str]]:
        """Validate inputs in this tab. Override in subclasses.

        Parameters
        ------------
        None

        Returns
        --------
            tuple[bool, list[str]]: validation result
                (is_valid, error_messages).
        """
        return (True, [])

    def apply_palette(self, palette_dict: Any) -> None:
        """Update canvas background color when theme switches.

        Parameters
        ------------
        palette_dict: Any
            Color palette tokens object or mapping.

        Returns
        --------
            None: None object
                Updates canvas background color.
        """
        bg_primary = (
            palette_dict["bg_primary"]
            if "bg_primary" in palette_dict
            else getattr(palette_dict, "bg_primary", "#15131D")
        )
        self.canvas.configure(bg=bg_primary)

    def build_cluster_card(self, parent_frame: tk.Widget) -> Card:
        """Build reusable SGE/SLURM cluster configuration card.

        Parameters
        ------------
        parent_frame: tk.Widget
            Parent container frame.

        Returns
        --------
            Card: cluster card
                Configured collapsible card.
        """
        card = Card(
            parent_frame,
            title="Cluster / Grid Submission Options",
            subtitle="SLURM / SGE cluster queue options",
            collapsible=True,
            initially_expanded=False,
            theme_manager=self.theme_manager,
        )

        cluster_flag = self.create_bool_var("cluster", False)
        cluster_queue = self.create_string_var("cluster_queue", "")
        cluster_ram = self.create_string_var("cluster_ram", "60")
        cluster_time = self.create_string_var("cluster_time", "")
        cluster_qos = self.create_string_var("cluster_qos", "")

        toggle_frame = create_toggle(
            card.content_frame,
            text="Submit jobs to compute cluster",
            variable=cluster_flag,
            flag="-C",
            tooltip_text="Submit jobs to cluster (SGE/SLURM) via fsl_sub.",
            theme_manager=self.theme_manager,
        )
        toggle_frame.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))
        cluster_flag.trace_add(
            "write", lambda *args: self._toggle_cluster_inputs(cluster_flag.get())
        )

        self.cluster_inputs_frame = ttk.Frame(
            card.content_frame, style="Surface.TFrame"
        )
        self.cluster_inputs_frame.grid(row=1, column=0, columnspan=2, sticky="nsew")

        # Field items placed in 2-column grid
        queue_container = ttk.Frame(self.cluster_inputs_frame, style="Surface.TFrame")
        queue_label = FieldLabel(
            queue_container,
            text="Queue partition",
            flag="-cq",
            tooltip_text="Cluster queue / partition name.",
        )
        queue_label.pack(fill="x", pady=(0, 2))
        queue_entry = ttk.Entry(
            queue_container, textvariable=cluster_queue, style="TEntry"
        )
        queue_entry.pack(fill="x")

        ram_container = ttk.Frame(self.cluster_inputs_frame, style="Surface.TFrame")
        ram_label = FieldLabel(
            ram_container,
            text="Memory limit (GB)",
            flag="-cr",
            tooltip_text="RAM memory limit in GB per cluster job.",
        )
        ram_label.pack(fill="x", pady=(0, 2))
        ram_spinbox = ttk.Spinbox(
            ram_container,
            from_=1,
            to=1024,
            textvariable=cluster_ram,
            style="TSpinbox",
        )
        ram_spinbox.pack(fill="x")

        time_container = ttk.Frame(self.cluster_inputs_frame, style="Surface.TFrame")
        time_label = FieldLabel(
            time_container,
            text="Max walltime",
            flag="-ct",
            tooltip_text="Max walltime limit (e.g. 24:00:00).",
        )
        time_label.pack(fill="x", pady=(0, 2))
        time_entry = ttk.Entry(
            time_container, textvariable=cluster_time, style="TEntry"
        )
        time_entry.pack(fill="x")

        qos_container = ttk.Frame(self.cluster_inputs_frame, style="Surface.TFrame")
        qos_label = FieldLabel(
            qos_container,
            text="Quality of Service",
            flag="-cqos",
            tooltip_text="Cluster Quality of Service string.",
        )
        qos_label.pack(fill="x", pady=(0, 2))
        qos_entry = ttk.Entry(qos_container, textvariable=cluster_qos, style="TEntry")
        qos_entry.pack(fill="x")

        place_in_form_grid(
            self.cluster_inputs_frame,
            [queue_container, ram_container, time_container, qos_container],
            columns=2,
        )

        self._toggle_cluster_inputs(cluster_flag.get())
        return card

    def _toggle_cluster_inputs(self, is_enabled: bool) -> None:
        """Enable or disable cluster input controls based on cluster flag.

        Parameters
        ------------
        is_enabled: bool
            Whether cluster execution is enabled.

        Returns
        --------
            None: None object
                Updates child controls states.
        """
        if self.cluster_inputs_frame is not None:
            for child_widget in self.cluster_inputs_frame.winfo_children():
                for sub_child in child_widget.winfo_children():
                    if isinstance(sub_child, (ttk.Entry, ttk.Spinbox)):
                        sub_child.configure(
                            state="normal" if is_enabled else "disabled"
                        )

    def build_base_setup_card(
        self,
        parent_frame: tk.Widget,
        title: str = "Required Setup & Paths",
        require_subjects: bool = True,
        show_cores: bool = True,
    ) -> Card:
        """Build reusable setup card containing list_of_subjects, outdir, overwrite, n_cores.

        Parameters
        ------------
        parent_frame: tk.Widget
            Parent container.
        title: str
            Card title. Defaults to "Required Setup & Paths".
        require_subjects: bool
            Whether to include list_of_subjects field. Defaults to True.
        show_cores: bool
            Whether to include parallelization cores field. Defaults to True.

        Returns
        --------
            Card: configured card
                Configured card instance.
        """
        card = Card(
            parent_frame,
            title=title,
            subtitle="Study paths and processing execution options",
            initially_expanded=True,
            theme_manager=self.theme_manager,
        )
        card.content_frame.columnconfigure(0, weight=1)

        row_idx = 0
        if require_subjects:
            subjects_var = self.create_string_var("list_of_subjects", "")
            subjects_field = FileSelectorField(
                card.content_frame,
                label_text="List of subjects file",
                flag="-l",
                variable=subjects_var,
                title="Select List of Subjects",
                tooltip_text="Path to text file containing subject identifiers or directory paths.",
                required=True,
            )
            subjects_field.grid(row=row_idx, column=0, sticky="ew", pady=(0, 6))
            row_idx += 1

        outdir_var = self.create_string_var("outdir", "")
        outdir_field = DirectorySelectorField(
            card.content_frame,
            label_text="Output directory",
            flag="-o",
            variable=outdir_var,
            title="Select Output Directory",
            tooltip_text="Root output directory where results will be generated.",
            required=True,
        )
        outdir_field.grid(row=row_idx, column=0, sticky="ew", pady=(0, 6))
        row_idx += 1

        # Checkbox & cores row
        options_row = ttk.Frame(card.content_frame, style="Surface.TFrame")
        options_row.grid(row=row_idx, column=0, sticky="ew", pady=(4, 4))
        options_row.columnconfigure(1, weight=1)
        row_idx += 1

        overwrite_var = self.create_bool_var("overwrite", False)
        toggle_frame = create_toggle(
            options_row,
            text="Overwrite existing outputs",
            variable=overwrite_var,
            flag="-O",
            tooltip_text="Overwrite existing result files if already present.",
            theme_manager=self.theme_manager,
        )
        toggle_frame.pack(side="left", padx=(0, 24))

        if show_cores:
            cpu_count = os.cpu_count() or 4
            cores_var = self.create_string_var("n_cores", "")
            cores_container = ttk.Frame(options_row, style="Surface.TFrame")
            cores_container.pack(side="left")

            cores_label = FieldLabel(
                cores_container,
                text="Parallel CPU cores",
                flag="-n",
                tooltip_text=f"Number of CPU cores for parallel processing (1 to {cpu_count}).",
            )
            cores_label.pack(side="left", padx=(0, 6))

            cores_spinbox = ttk.Spinbox(
                cores_container,
                from_=1,
                to=cpu_count,
                textvariable=cores_var,
                width=5,
                style="TSpinbox",
            )
            cores_spinbox.pack(side="left")

        return card
