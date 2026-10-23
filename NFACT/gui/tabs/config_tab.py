"""
Config and utility tab for nfact_config generator and interactive JSON config editor.
"""

import json
import os
import tkinter as tk
from tkinter import filedialog, ttk
from typing import Any, Callable, Optional

from NFACT.gui.tabs.base_tab import BaseModuleTab
from NFACT.gui.widgets.card import Card
from NFACT.gui.widgets.field_label import FieldLabel
from NFACT.gui.widgets.path_fields import DirectorySelectorField


class ConfigTab(BaseModuleTab):
    """Tab for configuring nfact_config commands and viewing/editing JSON configs.

    Usage
    -----
    tab = ConfigTab(notebook_widget, on_change_callback=update_cmd)
    """

    def __init__(
        self,
        parent_container: tk.Widget,
        on_change_callback: Optional[Callable[[], None]] = None,
        theme_manager: Optional[Any] = None,
        style: str = "TFrame",
    ) -> None:
        """Initialize config and utility tab.

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
                Constructs config tab layout.
        """
        super().__init__(
            parent_container,
            tab_name="Config & Tools",
            on_change_callback=on_change_callback,
            page_title="Config & Utilities",
            page_description="Create configs, subject lists and compress matrices.",
            cli_name="nfact_config",
            theme_manager=theme_manager,
            style=style,
        )

        self.action_var = self.create_string_var("action", "pipeline")
        self._build_config_ui()

    def _build_config_ui(self) -> None:
        """Assemble UI components for the config and utility tab.

        Parameters
        ------------
        None

        Returns
        --------
            None: None object
                Constructs action selector and parameter cards.
        """
        self.scrollable_frame.columnconfigure(0, weight=1)

        # 1. Action selection bar
        self._build_action_card()

        # 2. Action parameters card
        self._build_action_params_card()

        # 3. Interactive JSON Config Editor
        self._build_json_editor_card()

        self._update_action_view()

    def _build_action_card(self) -> None:
        """Build utility action selector with segmented buttons.

        Parameters
        ------------
        None

        Returns
        --------
            None: None object
                Constructs action selector container.
        """
        banner_frame = ttk.Frame(
            self.scrollable_frame, style="Surface.TFrame", padding=(10, 8)
        )
        banner_frame.grid(row=0, column=0, sticky="ew", padx=12, pady=(6, 8))
        banner_frame.columnconfigure(1, weight=1)

        action_label = ttk.Label(
            banner_frame,
            text="Config Utility Action:",
            style="CardTitle.TLabel",
        )
        action_label.grid(row=0, column=0, padx=(4, 12), sticky="w")

        segments_container = ttk.Frame(banner_frame, style="Surface.TFrame")
        segments_container.grid(row=0, column=1, sticky="w")

        actions = [
            ("Pipeline Config (-C)", "pipeline"),
            ("Decomp Config (-D)", "decomp"),
            ("Subject List (-s)", "subject_list"),
            ("Compress LZ4 (-z)", "zip"),
        ]
        for label_text, action_value in actions:
            radio_btn = ttk.Radiobutton(
                segments_container,
                text=label_text,
                variable=self.action_var,
                value=action_value,
                style="Segment.TRadiobutton",
                command=self._on_action_toggled,
            )
            radio_btn.pack(side="left", padx=(0, 4))

    def _on_action_toggled(self) -> None:
        """Handle switching between utility actions.

        Parameters
        ------------
        None

        Returns
        --------
            None: None object
                Updates action view and triggers parameter change callback.
        """
        self._update_action_view()
        self._on_parameter_change()

    def _update_action_view(self) -> None:
        """Show or hide input fields relevant to the chosen action.

        Parameters
        ------------
        None

        Returns
        --------
            None: None object
                Adjusts field visibility in action params card.
        """
        selected_action = self.action_var.get()
        if selected_action == "subject_list":
            self.subject_dir_field.grid()
            self.zip_dir_field.grid_remove()
        elif selected_action == "zip":
            self.subject_dir_field.grid_remove()
            self.zip_dir_field.grid()
        else:
            self.subject_dir_field.grid_remove()
            self.zip_dir_field.grid_remove()

    def _build_action_params_card(self) -> None:
        """Build parameter card for selected nfact_config action.

        Parameters
        ------------
        None

        Returns
        --------
            None: None object
                Constructs parameters card.
        """
        card = Card(
            self.scrollable_frame,
            title="Parameters & Output Destination",
            subtitle="Action-specific directory inputs and target file names",
            initially_expanded=True,
            theme_manager=self.theme_manager,
        )
        card.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 10))
        card.content_frame.columnconfigure(0, weight=1)

        # Subject dir for -s
        subj_dir_var = self.create_string_var("subject_dir", "")
        self.subject_dir_field = DirectorySelectorField(
            card.content_frame,
            label_text="Study directory containing subjects",
            flag="-s",
            variable=subj_dir_var,
            title="Select Study Directory",
            tooltip_text="Directory containing subject sub-folders to discover.",
            required=True,
        )
        self.subject_dir_field.grid(row=0, column=0, sticky="ew", pady=(0, 6))

        # Zip dir for -z
        zip_dir_var = self.create_string_var("zip_dir", "")
        self.zip_dir_field = DirectorySelectorField(
            card.content_frame,
            label_text="Directory containing dot matrices to compress",
            flag="-z",
            variable=zip_dir_var,
            title="Select Directory to Compress",
            tooltip_text="Directory with fdt_matrix2.dot files to compress with LZ4.",
            required=True,
        )
        self.zip_dir_field.grid(row=1, column=0, sticky="ew", pady=(0, 6))

        # Output directory
        outdir_var = self.create_string_var("output_dir", "")
        self.outdir_field = DirectorySelectorField(
            card.content_frame,
            label_text="Output directory",
            flag="-o",
            variable=outdir_var,
            title="Select Output Directory",
            tooltip_text="Destination folder for generated file or configuration.",
            required=False,
        )
        self.outdir_field.grid(row=2, column=0, sticky="ew", pady=(0, 6))

        # Output file name
        fname_row = ttk.Frame(card.content_frame, style="Surface.TFrame")
        fname_row.grid(row=3, column=0, sticky="ew", pady=(2, 4))
        fname_row.columnconfigure(1, weight=1)

        fname_var = self.create_string_var("file_name", "")
        fname_label = FieldLabel(
            fname_row,
            text="Custom output file name",
            flag="-f",
            tooltip_text="Optional custom file name for the generated file.",
        )
        fname_label.grid(row=0, column=0, sticky="w", padx=(0, 8))
        fname_entry = ttk.Entry(
            fname_row,
            textvariable=fname_var,
            style="TEntry",
        )
        fname_entry.grid(row=0, column=1, sticky="ew")

    def _build_json_editor_card(self) -> None:
        """Build interactive JSON configuration editor card.

        Parameters
        ------------
        None

        Returns
        --------
            None: None object
                Constructs JSON editor card.
        """
        editor_card = Card(
            self.scrollable_frame,
            title="Interactive JSON Configuration Editor",
            subtitle="Load, edit, validate, and save pipeline or decomp configs",
            initially_expanded=True,
            theme_manager=self.theme_manager,
        )
        editor_card.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 10))
        editor_card.content_frame.columnconfigure(0, weight=1)

        toolbar = ttk.Frame(editor_card.content_frame, style="Surface.TFrame")
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 6))

        load_btn = ttk.Button(
            toolbar,
            text="Load Config...",
            command=self._load_json_file,
            style="Accent.TButton",
        )
        load_btn.pack(side="left", padx=(0, 6))

        format_btn = ttk.Button(
            toolbar,
            text="Validate & Format",
            command=self._validate_and_format_json,
            style="TButton",
        )
        format_btn.pack(side="left", padx=(0, 6))

        save_btn = ttk.Button(
            toolbar,
            text="Save Config As...",
            command=self._save_json_file,
            style="TButton",
        )
        save_btn.pack(side="left", padx=(0, 6))

        self.status_label = ttk.Label(
            toolbar,
            text="",
            style="Surface.TLabel",
        )
        self.status_label.pack(side="left", padx=(12, 0))

        text_frame = ttk.Frame(editor_card.content_frame, style="Surface.TFrame")
        text_frame.grid(row=1, column=0, sticky="nsew")
        text_frame.columnconfigure(0, weight=1)

        self.json_text = tk.Text(
            text_frame,
            height=14,
            font="NFACTMonoSmall",
            wrap="none",
            borderwidth=0,
            highlightthickness=0,
        )
        self.json_text.grid(row=0, column=0, sticky="nsew")

        json_scroll_y = ttk.Scrollbar(
            text_frame,
            orient="vertical",
            command=self.json_text.yview,
            style="Vertical.TScrollbar",
        )
        json_scroll_y.grid(row=0, column=1, sticky="ns")

        json_scroll_x = ttk.Scrollbar(
            text_frame,
            orient="horizontal",
            command=self.json_text.xview,
            style="Horizontal.TScrollbar",
        )
        json_scroll_x.grid(row=1, column=0, sticky="ew")

        self.json_text.configure(
            yscrollcommand=json_scroll_y.set,
            xscrollcommand=json_scroll_x.set,
        )

        if self.theme_manager is not None:
            self.apply_palette(self.theme_manager.get_palette())

    def apply_palette(self, palette_dict: Any) -> None:
        """Update canvas and text editor colors on theme switch.

        Parameters
        ------------
        palette_dict: Any
            Color palette tokens object or mapping.

        Returns
        --------
            None: None object
                Updates text editor widget colors.
        """
        super().apply_palette(palette_dict)
        bg_console = (
            palette_dict["bg_console"]
            if "bg_console" in palette_dict
            else getattr(palette_dict, "bg_console", "#0F0D16")
        )
        fg_primary = (
            palette_dict["fg_primary"]
            if "fg_primary" in palette_dict
            else getattr(palette_dict, "fg_primary", "#F2EFF9")
        )
        accent_secondary = (
            palette_dict["accent_secondary"]
            if "accent_secondary" in palette_dict
            else getattr(palette_dict, "accent_secondary", "#9966CC")
        )
        self.json_text.configure(
            background=bg_console,
            foreground=fg_primary,
            insertbackground=fg_primary,
            selectbackground=accent_secondary,
            selectforeground=fg_primary,
        )

    def _load_json_file(self) -> None:
        """Open file dialog to load and display a JSON configuration file.

        Parameters
        ------------
        None

        Returns
        --------
            None: None object
                Loads file contents into editor.
        """
        file_path = filedialog.askopenfilename(
            parent=self,
            title="Open Config JSON",
            filetypes=[("Config Files", "*.config *.json"), ("All Files", "*.*")],
        )
        if not file_path:
            return

        try:
            with open(file_path, "r", encoding="utf-8") as file_handle:
                parsed_content = json.load(file_handle)
            formatted_text = json.dumps(parsed_content, indent=4)
            self.json_text.delete("1.0", "end")
            self.json_text.insert("1.0", formatted_text)
            file_basename = os.path.basename(file_path)
            self.status_label.configure(text=f"Loaded: {file_basename}")
        except Exception as load_err:
            self.status_label.configure(text=f"Error loading: {load_err}")

    def _validate_and_format_json(self) -> None:
        """Parse editor contents to validate JSON syntax and re-format.

        Parameters
        ------------
        None

        Returns
        --------
            None: None object
                Validates and formats JSON in text editor.
        """
        raw_text = self.json_text.get("1.0", "end-1c").strip()
        if not raw_text:
            return

        try:
            parsed_content = json.loads(raw_text)
            formatted_text = json.dumps(parsed_content, indent=4)
            self.json_text.delete("1.0", "end")
            self.json_text.insert("1.0", formatted_text)
            self.status_label.configure(text="JSON is valid!")
        except json.JSONDecodeError as json_err:
            self.status_label.configure(text=f"Invalid JSON: {json_err.msg}")

    def _save_json_file(self) -> None:
        """Save formatted JSON editor contents to disk.

        Parameters
        ------------
        None

        Returns
        --------
            None: None object
                Writes JSON to target file.
        """
        raw_text = self.json_text.get("1.0", "end-1c").strip()
        if not raw_text:
            return

        try:
            parsed_content = json.loads(raw_text)
        except json.JSONDecodeError as json_err:
            self.status_label.configure(
                text=f"Cannot save invalid JSON: {json_err.msg}"
            )
            return

        file_path = filedialog.asksaveasfilename(
            parent=self,
            title="Save Config JSON",
            defaultextension=".config",
            filetypes=[("Config Files", "*.config *.json"), ("All Files", "*.*")],
        )
        if not file_path:
            return

        try:
            with open(file_path, "w", encoding="utf-8") as file_handle:
                json.dump(parsed_content, file_handle, indent=4)
            file_basename = os.path.basename(file_path)
            self.status_label.configure(text=f"Saved: {file_basename}")
        except OSError as save_err:
            self.status_label.configure(text=f"Save error: {save_err}")

    def validate(self) -> tuple[bool, list[str]]:
        """Validate nfact_config inputs.

        Parameters
        ------------
        None

        Returns
        --------
            tuple[bool, list[str]]: validation result
                (is_valid, error_messages).
        """
        error_list: list[str] = []
        action_name = self.action_var.get()

        self.subject_dir_field.set_invalid(False)
        self.zip_dir_field.set_invalid(False)

        if action_name == "subject_list":
            subject_dir_val = self.params["subject_dir"].get().strip()  # type: ignore[union-attr]
            if not subject_dir_val:
                error_msg = (
                    "Study directory (-s) is required for subject list generation."
                )
                error_list.append(error_msg)
                self.subject_dir_field.set_invalid(True, error_msg)
        elif action_name == "zip":
            zip_dir_val = self.params["zip_dir"].get().strip()  # type: ignore[union-attr]
            if not zip_dir_val:
                error_msg = "Directory to compress (-z) is required."
                error_list.append(error_msg)
                self.zip_dir_field.set_invalid(True, error_msg)

        is_valid = len(error_list) == 0
        return (is_valid, error_list)
