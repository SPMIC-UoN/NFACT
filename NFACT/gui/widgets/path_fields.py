"""
Path selector input fields for files, directories, and multi-file collections.
"""

import os
import tkinter as tk
from tkinter import filedialog, font as tkfont, ttk
from typing import Callable, Optional, Sequence

from NFACT.gui.widgets.field_label import FieldLabel


def _detect_picker_glyphs(root_window: Optional[tk.Widget] = None) -> tuple[str, str]:
    """Detect whether unicode emoji folder and clear glyphs can render cleanly.

    Parameters
    ------------
    root_window: Optional[tk.Widget]
        Tkinter widget to check fonts with. Defaults to None.

    Returns
    --------
        tuple[str, str]: glyph pair
            (folder_glyph, clear_glyph)
    """
    if root_window is not None:
        try:
            sample_font = tkfont.nametofont("TkDefaultFont")
            if sample_font.measure("📁") > 0:
                return ("📁", "✕")
        except Exception:
            pass
    return ("...", "×")


class FileSelectorField(ttk.Frame):
    """File selector field with label, entry, browse dialog, and clear button.

    Usage
    -----
    file_field = FileSelectorField(
        parent_frame,
        label_text="Seeds file",
        flag="-s",
        title="Select seeds file",
    )
    """

    def __init__(
        self,
        parent_container: tk.Widget,
        label_text: str,
        flag: str = "",
        variable: Optional[tk.StringVar] = None,
        filetypes: Optional[Sequence[tuple[str, str]]] = None,
        title: str = "Select File",
        tooltip_text: str = "",
        required: bool = False,
        on_change_callback: Optional[Callable[[str], None]] = None,
        style: str = "Surface.TFrame",
        entry_width: int = 40,
    ) -> None:
        """Initialize file selector field.

        Parameters
        ------------
        parent_container: tk.Widget
            Parent Tkinter widget.
        label_text: str
            Label text displayed above entry.
        flag: str
            CLI option flag badge (e.g. "-l"). Defaults to "".
        variable: Optional[tk.StringVar]
            Bound variable. Defaults to None.
        filetypes: Optional[Sequence[tuple[str, str]]]
            File filters for dialog. Defaults to None.
        title: str
            Title for file dialog. Defaults to "Select File".
        tooltip_text: str
            Optional hover help text. Defaults to "".
        required: bool
            Whether field is marked required. Defaults to False.
        on_change_callback: Optional[Callable[[str], None]]
            Callback executed when path changes. Defaults to None.
        style: str
            ttk frame style name. Defaults to "Surface.TFrame".
        entry_width: int
            Width of entry widget. Defaults to 40.

        Returns
        --------
            None: None object
                Constructs file selector field layout.
        """
        super().__init__(parent_container, style=style)
        self.variable = variable if variable is not None else tk.StringVar(value="")
        self.filetypes = (
            filetypes
            if filetypes is not None
            else [("All Files", "*.*"), ("Text Files", "*.txt *.csv *.tsv")]
        )
        self.dialog_title = title
        self.on_change_callback = on_change_callback

        self.columnconfigure(0, weight=1)

        # Field Label
        self.label_widget = FieldLabel(
            self,
            text=label_text,
            flag=flag,
            required=required,
            tooltip_text=tooltip_text,
            style=style,
        )
        self.label_widget.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 3))

        # Input row
        input_row = ttk.Frame(self, style=style)
        input_row.grid(row=1, column=0, columnspan=3, sticky="ew")
        input_row.columnconfigure(0, weight=1)

        self.entry_widget = ttk.Entry(
            input_row, textvariable=self.variable, width=entry_width, style="TEntry"
        )
        self.entry_widget.grid(row=0, column=0, sticky="ew", padx=(0, 4))

        browse_glyph, clear_glyph = _detect_picker_glyphs(self)

        self.browse_button = ttk.Button(
            input_row,
            text=f" {browse_glyph} ",
            command=self._on_browse_click,
            style="TButton",
            width=4,
        )
        self.browse_button.grid(row=0, column=1, padx=(0, 2))

        self.clear_button = ttk.Button(
            input_row,
            text=f" {clear_glyph} ",
            command=self._on_clear_click,
            style="TButton",
            width=3,
        )
        self.clear_button.grid(row=0, column=2)

        # Error label container (hidden by default)
        self.error_label = ttk.Label(self, text="", style="ErrorText.Surface.TLabel")
        self.error_label.grid(row=2, column=0, columnspan=3, sticky="w", pady=(2, 0))
        self.error_label.grid_remove()

        if self.on_change_callback is not None:
            self.variable.trace_add("write", self._notify_change)

    def _notify_change(self, *unused_args: object) -> None:
        """Invoke change callback when variable changes.

        Parameters
        ------------
        unused_args: object
            Tkinter trace arguments.

        Returns
        --------
            None: None object
                Calls on_change_callback if present.
        """
        if self.on_change_callback is not None:
            self.on_change_callback(self.variable.get().strip())

    def _on_browse_click(self) -> None:
        """Open file selection dialog.

        Parameters
        ------------
        None

        Returns
        --------
            None: None object
                Sets variable if file chosen.
        """
        current_dir = os.path.dirname(self.variable.get().strip())
        initial_dir = current_dir if os.path.isdir(current_dir) else os.getcwd()
        selected_path = filedialog.askopenfilename(
            parent=self,
            title=self.dialog_title,
            initialdir=initial_dir,
            filetypes=self.filetypes,
        )
        if selected_path:
            self.variable.set(selected_path)
            self.set_invalid(False)

    def _on_clear_click(self) -> None:
        """Clear entry field value.

        Parameters
        ------------
        None

        Returns
        --------
            None: None object
                Sets empty string.
        """
        self.variable.set("")

    def get(self) -> str:
        """Retrieve current string path.

        Parameters
        ------------
        None

        Returns
        --------
            str: path value
                Path string currently held in entry.
        """
        return self.variable.get().strip()

    def set(self, path_value: str) -> None:
        """Set string path into entry.

        Parameters
        ------------
        path_value: str
            Path to set.

        Returns
        --------
            None: None object
                Updates bound variable.
        """
        self.variable.set(path_value)

    def set_invalid(self, is_invalid: bool, message: str = "") -> None:
        """Toggle invalid highlight state and error message caption.

        Parameters
        ------------
        is_invalid: bool
            Whether field is currently in an invalid state.
        message: str
            Validation failure message to display. Defaults to "".

        Returns
        --------
            None: None object
                Updates style and error text.
        """
        if is_invalid:
            self.entry_widget.configure(style="Invalid.TEntry")
            if message:
                self.error_label.configure(text=message)
                self.error_label.grid()
        else:
            self.entry_widget.configure(style="TEntry")
            self.error_label.grid_remove()


class DirectorySelectorField(ttk.Frame):
    """Directory selector field with label, entry, browse dialog, and clear button.

    Usage
    -----
    dir_field = DirectorySelectorField(
        parent_frame,
        label_text="Output directory",
        flag="-o",
        title="Select output folder",
    )
    """

    def __init__(
        self,
        parent_container: tk.Widget,
        label_text: str,
        flag: str = "",
        variable: Optional[tk.StringVar] = None,
        title: str = "Select Directory",
        tooltip_text: str = "",
        required: bool = False,
        on_change_callback: Optional[Callable[[str], None]] = None,
        style: str = "Surface.TFrame",
        entry_width: int = 40,
    ) -> None:
        """Initialize directory selector field.

        Parameters
        ------------
        parent_container: tk.Widget
            Parent Tkinter widget.
        label_text: str
            Label displayed above entry.
        flag: str
            CLI option flag badge (e.g. "-o"). Defaults to "".
        variable: Optional[tk.StringVar]
            Bound variable. Defaults to None.
        title: str
            Title for directory dialog. Defaults to "Select Directory".
        tooltip_text: str
            Optional hover help text. Defaults to "".
        required: bool
            Whether field is marked required. Defaults to False.
        on_change_callback: Optional[Callable[[str], None]]
            Callback executed when path changes. Defaults to None.
        style: str
            ttk frame style name. Defaults to "Surface.TFrame".
        entry_width: int
            Width of entry widget. Defaults to 40.

        Returns
        --------
            None: None object
                Constructs directory selector layout.
        """
        super().__init__(parent_container, style=style)
        self.variable = variable if variable is not None else tk.StringVar(value="")
        self.dialog_title = title
        self.on_change_callback = on_change_callback

        self.columnconfigure(0, weight=1)

        self.label_widget = FieldLabel(
            self,
            text=label_text,
            flag=flag,
            required=required,
            tooltip_text=tooltip_text,
            style=style,
        )
        self.label_widget.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 3))

        input_row = ttk.Frame(self, style=style)
        input_row.grid(row=1, column=0, columnspan=3, sticky="ew")
        input_row.columnconfigure(0, weight=1)

        self.entry_widget = ttk.Entry(
            input_row, textvariable=self.variable, width=entry_width, style="TEntry"
        )
        self.entry_widget.grid(row=0, column=0, sticky="ew", padx=(0, 4))

        browse_glyph, clear_glyph = _detect_picker_glyphs(self)

        self.browse_button = ttk.Button(
            input_row,
            text=f" {browse_glyph} ",
            command=self._on_browse_click,
            style="TButton",
            width=4,
        )
        self.browse_button.grid(row=0, column=1, padx=(0, 2))

        self.clear_button = ttk.Button(
            input_row,
            text=f" {clear_glyph} ",
            command=self._on_clear_click,
            style="TButton",
            width=3,
        )
        self.clear_button.grid(row=0, column=2)

        self.error_label = ttk.Label(self, text="", style="ErrorText.Surface.TLabel")
        self.error_label.grid(row=2, column=0, columnspan=3, sticky="w", pady=(2, 0))
        self.error_label.grid_remove()

        if self.on_change_callback is not None:
            self.variable.trace_add("write", self._notify_change)

    def _notify_change(self, *unused_args: object) -> None:
        """Invoke change callback when variable changes.

        Parameters
        ------------
        unused_args: object
            Tkinter trace arguments.

        Returns
        --------
            None: None object
                Calls on_change_callback if present.
        """
        if self.on_change_callback is not None:
            self.on_change_callback(self.variable.get().strip())

    def _on_browse_click(self) -> None:
        """Open directory selection dialog.

        Parameters
        ------------
        None

        Returns
        --------
            None: None object
                Sets variable if directory chosen.
        """
        current_val = self.variable.get().strip()
        initial_dir = current_val if os.path.isdir(current_val) else os.getcwd()
        selected_dir = filedialog.askdirectory(
            parent=self,
            title=self.dialog_title,
            initialdir=initial_dir,
        )
        if selected_dir:
            self.variable.set(selected_dir)
            self.set_invalid(False)

    def _on_clear_click(self) -> None:
        """Clear directory entry value.

        Parameters
        ------------
        None

        Returns
        --------
            None: None object
                Sets empty string.
        """
        self.variable.set("")

    def get(self) -> str:
        """Retrieve current directory path string.

        Parameters
        ------------
        None

        Returns
        --------
            str: directory path
                Path string currently in entry.
        """
        return self.variable.get().strip()

    def set(self, path_value: str) -> None:
        """Set directory path into entry.

        Parameters
        ------------
        path_value: str
            Path to set.

        Returns
        --------
            None: None object
                Updates bound variable.
        """
        self.variable.set(path_value)

    def set_invalid(self, is_invalid: bool, message: str = "") -> None:
        """Toggle invalid highlight state and error message caption.

        Parameters
        ------------
        is_invalid: bool
            Whether field is currently in an invalid state.
        message: str
            Validation failure message to display. Defaults to "".

        Returns
        --------
            None: None object
                Updates style and error text.
        """
        if is_invalid:
            self.entry_widget.configure(style="Invalid.TEntry")
            if message:
                self.error_label.configure(text=message)
                self.error_label.grid()
        else:
            self.entry_widget.configure(style="TEntry")
            self.error_label.grid_remove()


class MultiPathField(ttk.Frame):
    """Input field allowing multiple paths with file and directory pickers.

    Usage
    -----
    multi_field = MultiPathField(
        parent_frame,
        label_text="Warp images",
        flag="--warps",
        tooltip_text="Space-separated list of warp paths",
    )
    """

    def __init__(
        self,
        parent_container: tk.Widget,
        label_text: str,
        flag: str = "",
        variable: Optional[tk.StringVar] = None,
        title: str = "Select Files",
        tooltip_text: str = "",
        required: bool = False,
        on_change_callback: Optional[Callable[[str], None]] = None,
        style: str = "Surface.TFrame",
    ) -> None:
        """Initialize multi-path field.

        Parameters
        ------------
        parent_container: tk.Widget
            Parent Tkinter widget.
        label_text: str
            Label displayed above entry.
        flag: str
            CLI option flag badge (e.g. "--warps"). Defaults to "".
        variable: Optional[tk.StringVar]
            Bound variable. Defaults to None.
        title: str
            Dialog title. Defaults to "Select Files".
        tooltip_text: str
            Optional hover help text. Defaults to "".
        required: bool
            Whether field is marked required. Defaults to False.
        on_change_callback: Optional[Callable[[str], None]]
            Callback executed on change. Defaults to None.
        style: str
            ttk frame style name. Defaults to "Surface.TFrame".

        Returns
        --------
            None: None object
                Constructs multi-path layout.
        """
        super().__init__(parent_container, style=style)
        self.variable = variable if variable is not None else tk.StringVar(value="")
        self.dialog_title = title
        self.on_change_callback = on_change_callback

        self.columnconfigure(0, weight=1)

        self.label_widget = FieldLabel(
            self,
            text=label_text,
            flag=flag,
            required=required,
            tooltip_text=tooltip_text,
            style=style,
        )
        self.label_widget.grid(row=0, column=0, columnspan=4, sticky="ew", pady=(0, 3))

        input_row = ttk.Frame(self, style=style)
        input_row.grid(row=1, column=0, columnspan=4, sticky="ew")
        input_row.columnconfigure(0, weight=1)

        self.entry_widget = ttk.Entry(
            input_row, textvariable=self.variable, style="TEntry"
        )
        self.entry_widget.grid(row=0, column=0, sticky="ew", padx=(0, 4))

        self.add_files_btn = ttk.Button(
            input_row,
            text="+ File",
            width=6,
            command=self._on_add_files,
            style="TButton",
        )
        self.add_files_btn.grid(row=0, column=1, padx=(0, 2))

        self.add_dir_btn = ttk.Button(
            input_row,
            text="+ Dir",
            width=5,
            command=self._on_add_dir,
            style="TButton",
        )
        self.add_dir_btn.grid(row=0, column=2, padx=(0, 2))

        _, clear_glyph = _detect_picker_glyphs(self)

        self.clear_btn = ttk.Button(
            input_row,
            text=f" {clear_glyph} ",
            width=3,
            command=self._on_clear,
            style="TButton",
        )
        self.clear_btn.grid(row=0, column=3)

        self.error_label = ttk.Label(self, text="", style="ErrorText.Surface.TLabel")
        self.error_label.grid(row=2, column=0, columnspan=4, sticky="w", pady=(2, 0))
        self.error_label.grid_remove()

        if self.on_change_callback is not None:
            self.variable.trace_add("write", self._notify_change)

    def _notify_change(self, *unused_args: object) -> None:
        """Invoke change callback when variable changes.

        Parameters
        ------------
        unused_args: object
            Tkinter trace arguments.

        Returns
        --------
            None: None object
                Calls on_change_callback if present.
        """
        if self.on_change_callback is not None:
            self.on_change_callback(self.variable.get().strip())

    def _on_add_files(self) -> None:
        """Append multiple selected files to entry string.

        Parameters
        ------------
        None

        Returns
        --------
            None: None object
                Appends selected paths.
        """
        selected_paths = filedialog.askopenfilenames(
            parent=self,
            title=self.dialog_title,
        )
        if selected_paths:
            current_paths = self.get_list()
            for path_item in selected_paths:
                if path_item not in current_paths:
                    current_paths.append(path_item)
            self.variable.set(" ".join(current_paths))
            self.set_invalid(False)

    def _on_add_dir(self) -> None:
        """Append selected directory to entry string.

        Parameters
        ------------
        None

        Returns
        --------
            None: None object
                Appends selected directory.
        """
        selected_dir = filedialog.askdirectory(
            parent=self,
            title=self.dialog_title,
        )
        if selected_dir:
            current_paths = self.get_list()
            if selected_dir not in current_paths:
                current_paths.append(selected_dir)
            self.variable.set(" ".join(current_paths))
            self.set_invalid(False)

    def _on_clear(self) -> None:
        """Clear entry contents.

        Parameters
        ------------
        None

        Returns
        --------
            None: None object
                Sets empty string.
        """
        self.variable.set("")

    def get(self) -> str:
        """Get space-separated string of paths.

        Parameters
        ------------
        None

        Returns
        --------
            str: paths string
                Raw space-separated paths string.
        """
        return self.variable.get().strip()

    def get_list(self) -> list[str]:
        """Get list of individual paths split by whitespace.

        Parameters
        ------------
        None

        Returns
        --------
            list[str]: list of paths
                List of distinct non-empty path strings.
        """
        raw_text = self.variable.get().strip()
        if not raw_text:
            return []
        return [path_item for path_item in raw_text.split() if path_item]

    def set(self, paths_value: str | list[str]) -> None:
        """Set paths value.

        Parameters
        ------------
        paths_value: str | list[str]
            Path string or list of path strings.

        Returns
        --------
            None: None object
                Updates bound variable.
        """
        if isinstance(paths_value, list):
            self.variable.set(" ".join(paths_value))
        else:
            self.variable.set(paths_value)

    def set_invalid(self, is_invalid: bool, message: str = "") -> None:
        """Toggle invalid highlight state and error message caption.

        Parameters
        ------------
        is_invalid: bool
            Whether field is currently in an invalid state.
        message: str
            Validation failure message to display. Defaults to "".

        Returns
        --------
            None: None object
                Updates style and error text.
        """
        if is_invalid:
            self.entry_widget.configure(style="Invalid.TEntry")
            if message:
                self.error_label.configure(text=message)
                self.error_label.grid()
        else:
            self.entry_widget.configure(style="TEntry")
            self.error_label.grid_remove()
