"""
Interactive multi-view Runlog console featuring live stream, command history, and log file browser.
"""

from datetime import datetime
import glob
import os
import tkinter as tk
from tkinter import filedialog, ttk
from typing import Optional

from NFACT.gui.ansi_parser import AnsiParser, configure_ansi_tags


class LogConsole(ttk.Frame):
    """
    Multi-tab console displaying real-time ANSI-rendered logs, executed command history,
    and saved log file inspector.

    Usage
    -----
    console = LogConsole(parent_container)
    console.append_stream("Process output line\\n")
    """

    def __init__(
        self,
        parent_container: tk.Widget,
        style: str = "Surface.TFrame",
    ) -> None:
        """
        Initialize the log console.

        Parameters
        ----------
        parent_container: tk.Widget
            Parent Tkinter widget.
        style: str, default="Surface.TFrame"
            ttk frame style name.

        Returns
        -------
        None
        """
        super().__init__(parent_container, style=style)

        self.ansi_parser = AnsiParser()
        self.inspector_parser = AnsiParser()
        self.auto_scroll_var = tk.BooleanVar(value=True)
        self.filter_var = tk.StringVar(value="")
        self.current_palette: dict = {}

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # Tab notebook
        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=0, column=0, sticky="nsew")

        # 1. Live stream tab
        self.stream_tab = ttk.Frame(self.notebook, style="Surface.TFrame")
        self.notebook.add(self.stream_tab, text=" Live Runlog ")
        self._build_stream_tab()

        # 2. Command history tab
        self.history_tab = ttk.Frame(self.notebook, style="Surface.TFrame")
        self.notebook.add(self.history_tab, text=" Command History ")
        self._build_history_tab()

        # 3. Log inspector tab
        self.inspector_tab = ttk.Frame(self.notebook, style="Surface.TFrame")
        self.notebook.add(self.inspector_tab, text=" Saved Log Inspector ")
        self._build_inspector_tab()

    def _build_stream_tab(self) -> None:
        """
        Construct live stream tab with toolbar, text view, and scrollbars.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        self.stream_tab.columnconfigure(0, weight=1)
        self.stream_tab.rowconfigure(1, weight=1)

        # Toolbar
        stream_toolbar = ttk.Frame(self.stream_tab, style="Surface.TFrame", padding=4)
        stream_toolbar.grid(row=0, column=0, sticky="ew")

        clear_button = ttk.Button(
            stream_toolbar,
            text="Clear",
            width=7,
            command=self.clear_stream,
            style="TButton",
        )
        clear_button.pack(side="left", padx=(0, 4))

        autoscroll_check = ttk.Checkbutton(
            stream_toolbar,
            text="Auto-scroll",
            variable=self.auto_scroll_var,
            style="TCheckbutton",
        )
        autoscroll_check.pack(side="left", padx=(0, 8))

        filter_label = ttk.Label(
            stream_toolbar,
            text="Filter:",
            style="Surface.TLabel",
        )
        filter_label.pack(side="left", padx=(0, 4))

        filter_entry = ttk.Entry(
            stream_toolbar,
            textvariable=self.filter_var,
            width=20,
        )
        filter_entry.pack(side="left", padx=(0, 4))
        self.filter_var.trace_add("write", self._on_filter_changed)

        export_button = ttk.Button(
            stream_toolbar,
            text="Export...",
            width=9,
            command=self.export_stream_log,
            style="TButton",
        )
        export_button.pack(side="right", padx=(4, 0))

        # Text area container
        text_container = ttk.Frame(self.stream_tab, style="Surface.TFrame")
        text_container.grid(row=1, column=0, sticky="nsew", padx=2, pady=2)
        text_container.columnconfigure(0, weight=1)
        text_container.rowconfigure(0, weight=1)

        self.stream_text = tk.Text(
            text_container,
            wrap="none",
            font="NFACTMono",
            state="disabled",
            borderwidth=0,
            highlightthickness=0,
            padx=8,
            pady=6,
        )
        self.stream_text.grid(row=0, column=0, sticky="nsew")

        vert_scrollbar = ttk.Scrollbar(
            text_container,
            orient="vertical",
            command=self.stream_text.yview,
            style="Vertical.TScrollbar",
        )
        vert_scrollbar.grid(row=0, column=1, sticky="ns")

        horiz_scrollbar = ttk.Scrollbar(
            text_container,
            orient="horizontal",
            command=self.stream_text.xview,
            style="Horizontal.TScrollbar",
        )
        horiz_scrollbar.grid(row=1, column=0, sticky="ew")

        self.stream_text.configure(
            xscrollcommand=horiz_scrollbar.set,
            yscrollcommand=vert_scrollbar.set,
        )

    def _build_history_tab(self) -> None:
        """
        Construct command execution history tab with Treeview.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        self.history_tab.columnconfigure(0, weight=1)
        self.history_tab.rowconfigure(1, weight=1)

        # Toolbar
        history_toolbar = ttk.Frame(self.history_tab, style="Surface.TFrame", padding=4)
        history_toolbar.grid(row=0, column=0, sticky="ew")

        copy_history_button = ttk.Button(
            history_toolbar,
            text="Copy Selected Command",
            command=self._copy_selected_history_command,
            style="TButton",
        )
        copy_history_button.pack(side="left", padx=(0, 4))

        clear_history_button = ttk.Button(
            history_toolbar,
            text="Clear History",
            command=self._clear_history,
            style="TButton",
        )
        clear_history_button.pack(side="left", padx=(0, 4))

        # Treeview table
        table_container = ttk.Frame(self.history_tab, style="Surface.TFrame")
        table_container.grid(row=1, column=0, sticky="nsew", padx=2, pady=2)
        table_container.columnconfigure(0, weight=1)
        table_container.rowconfigure(0, weight=1)

        columns_spec = ("timestamp", "status", "duration", "command", "workdir")
        self.history_tree = ttk.Treeview(
            table_container,
            columns=columns_spec,
            show="headings",
            selectmode="browse",
        )
        self.history_tree.heading("timestamp", text="Time")
        self.history_tree.heading("status", text="Status")
        self.history_tree.heading("duration", text="Duration")
        self.history_tree.heading("command", text="Command")
        self.history_tree.heading("workdir", text="Working Directory")

        self.history_tree.column("timestamp", width=90, stretch=False)
        self.history_tree.column("status", width=110, stretch=False)
        self.history_tree.column("duration", width=90, stretch=False)
        self.history_tree.column("command", width=450, stretch=True)
        self.history_tree.column("workdir", width=220, stretch=False)

        self.history_tree.grid(row=0, column=0, sticky="nsew")

        tree_vert_scroll = ttk.Scrollbar(
            table_container,
            orient="vertical",
            command=self.history_tree.yview,
            style="Vertical.TScrollbar",
        )
        tree_vert_scroll.grid(row=0, column=1, sticky="ns")

        tree_horiz_scroll = ttk.Scrollbar(
            table_container,
            orient="horizontal",
            command=self.history_tree.xview,
            style="Horizontal.TScrollbar",
        )
        tree_horiz_scroll.grid(row=1, column=0, sticky="ew")

        self.history_tree.configure(
            xscrollcommand=tree_horiz_scroll.set,
            yscrollcommand=tree_vert_scroll.set,
        )

    def _build_inspector_tab(self) -> None:
        """
        Construct saved log inspector tab with folder scanner and viewer.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        self.inspector_tab.columnconfigure(0, weight=1)
        self.inspector_tab.rowconfigure(1, weight=1)

        # Toolbar
        inspector_toolbar = ttk.Frame(
            self.inspector_tab, style="Surface.TFrame", padding=4
        )
        inspector_toolbar.grid(row=0, column=0, sticky="ew")

        inspector_label = ttk.Label(
            inspector_toolbar,
            text="Log File:",
            style="Surface.TLabel",
        )
        inspector_label.pack(side="left", padx=(0, 4))

        self.inspector_combobox = ttk.Combobox(
            inspector_toolbar,
            width=50,
            state="readonly",
        )
        self.inspector_combobox.pack(side="left", padx=(0, 4))
        self.inspector_combobox.bind("<<ComboboxSelected>>", self._on_log_file_selected)

        browse_log_button = ttk.Button(
            inspector_toolbar,
            text="Browse...",
            width=9,
            command=self._on_browse_log_file,
            style="TButton",
        )
        browse_log_button.pack(side="left", padx=(0, 4))

        refresh_log_button = ttk.Button(
            inspector_toolbar,
            text="Refresh",
            width=9,
            command=self.refresh_log_files,
            style="TButton",
        )
        refresh_log_button.pack(side="left", padx=(0, 4))

        # Text area container
        inspector_text_container = ttk.Frame(self.inspector_tab, style="Surface.TFrame")
        inspector_text_container.grid(row=1, column=0, sticky="nsew", padx=2, pady=2)
        inspector_text_container.columnconfigure(0, weight=1)
        inspector_text_container.rowconfigure(0, weight=1)

        self.inspector_text = tk.Text(
            inspector_text_container,
            wrap="none",
            font="NFACTMono",
            state="disabled",
            borderwidth=0,
            highlightthickness=0,
            padx=8,
            pady=6,
        )
        self.inspector_text.grid(row=0, column=0, sticky="nsew")

        inspector_vert_scroll = ttk.Scrollbar(
            inspector_text_container,
            orient="vertical",
            command=self.inspector_text.yview,
            style="Vertical.TScrollbar",
        )
        inspector_vert_scroll.grid(row=0, column=1, sticky="ns")

        inspector_horiz_scroll = ttk.Scrollbar(
            inspector_text_container,
            orient="horizontal",
            command=self.inspector_text.xview,
            style="Horizontal.TScrollbar",
        )
        inspector_horiz_scroll.grid(row=1, column=0, sticky="ew")

        self.inspector_text.configure(
            xscrollcommand=inspector_horiz_scroll.set,
            yscrollcommand=inspector_vert_scroll.set,
        )

        self.discovered_logs_dir: Optional[str] = None

    def apply_palette(self, palette_dict: dict) -> None:
        """
        Apply theme colors to non-ttk widgets and text tags.

        Parameters
        ----------
        palette_dict: dict
            Color palette mapping.

        Returns
        -------
        None
        """
        self.current_palette = palette_dict

        # Stream text styling
        self.stream_text.configure(
            background=palette_dict.get("bg_console", "#0F0D16"),
            foreground=palette_dict.get("fg_primary", "#F2EFF9"),
            insertbackground=palette_dict.get("fg_primary", "#F2EFF9"),
            selectbackground=palette_dict.get("accent_secondary", "#9966CC"),
            selectforeground=palette_dict.get("fg_primary", "#F2EFF9"),
        )
        configure_ansi_tags(self.stream_text, palette_dict)

        # Inspector text styling
        self.inspector_text.configure(
            background=palette_dict.get("bg_console", "#0F0D16"),
            foreground=palette_dict.get("fg_primary", "#F2EFF9"),
            insertbackground=palette_dict.get("fg_primary", "#F2EFF9"),
            selectbackground=palette_dict.get("accent_secondary", "#9966CC"),
            selectforeground=palette_dict.get("fg_primary", "#F2EFF9"),
        )
        configure_ansi_tags(self.inspector_text, palette_dict)

    def append_stream(self, text_chunk: str) -> None:
        """
        Append output text chunk to live runlog stream.

        Parameters
        ----------
        text_chunk: str
            Raw text line or chunk to insert.

        Returns
        -------
        None
        """
        filter_str = self.filter_var.get().strip().lower()
        if filter_str and filter_str not in text_chunk.lower():
            # If line doesn't match filter, still maintain internal stream or skip
            pass

        self.ansi_parser.append_text(self.stream_text, text_chunk)

        if self.auto_scroll_var.get():
            self.stream_text.see("end")

    def clear_stream(self) -> None:
        """
        Clear all text from live stream console.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        self.stream_text.configure(state="normal")
        self.stream_text.delete("1.0", "end")
        self.stream_text.configure(state="disabled")

    def _on_filter_changed(self, *unused_args: object) -> None:
        """
        Handle filter query change.

        Parameters
        ----------
        unused_args: object
            Tkinter trace args.

        Returns
        -------
        None
        """
        filter_query = self.filter_var.get().strip()
        self.stream_text.tag_remove("highlight_match", "1.0", "end")
        if not filter_query:
            return

        warning_color = (
            self.current_palette.get("status_warning", "#F1C40F")
            if hasattr(self.current_palette, "get")
            else "#F1C40F"
        )
        self.stream_text.tag_configure(
            "highlight_match",
            background=warning_color,
            foreground="#000000",
        )

        search_pos = "1.0"
        while True:
            match_index = self.stream_text.search(
                filter_query, search_pos, stopindex="end", nocase=True
            )
            if not match_index:
                break
            end_index = f"{match_index}+{len(filter_query)}c"
            self.stream_text.tag_add("highlight_match", match_index, end_index)
            search_pos = end_index

    def export_stream_log(self) -> None:
        """
        Export live stream text to a file on disk.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        file_path = filedialog.asksaveasfilename(
            parent=self,
            title="Export Runlog",
            defaultextension=".log",
            filetypes=[("Log files", "*.log"), ("Text files", "*.txt"), ("All", "*.*")],
        )
        if not file_path:
            return

        full_content = self.stream_text.get("1.0", "end-1c")
        try:
            with open(file_path, "w", encoding="utf-8") as file_handle:
                file_handle.write(full_content)
        except OSError:
            pass

    def add_command_entry(
        self,
        command_string: str,
        workdir_path: str,
        initial_status: str = "Running",
    ) -> str:
        """
        Add a newly executed command to history treeview.

        Parameters
        ----------
        command_string: str
            Full CLI command string.
        workdir_path: str
            Directory from which command was launched.
        initial_status: str, default="Running"
            Initial status string.

        Returns
        -------
        entry_id: str
            Treeview item identifier.
        """
        timestamp_str = datetime.now().strftime("%H:%M:%S")
        entry_id = self.history_tree.insert(
            "",
            0,
            values=(
                timestamp_str,
                initial_status,
                "0.0s",
                command_string,
                workdir_path,
            ),
        )
        return entry_id

    def update_command_entry(
        self,
        entry_id: str,
        status_label: str,
        duration_string: str,
    ) -> None:
        """
        Update execution status and duration of an entry in the history tree.

        Parameters
        ----------
        entry_id: str
            Treeview item id returned by add_command_entry.
        status_label: str
            Status string (e.g. 'Completed (0)', 'Failed (1)', 'Stopped').
        duration_string: str
            Elapsed duration (e.g. '12.4s').

        Returns
        -------
        None
        """
        if self.history_tree.exists(entry_id):
            current_values = list(self.history_tree.item(entry_id, "values"))
            if len(current_values) >= 3:
                current_values[1] = status_label
                current_values[2] = duration_string
                self.history_tree.item(entry_id, values=current_values)

    def _copy_selected_history_command(self) -> None:
        """
        Copy command of currently selected history item to clipboard.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        selected_items = self.history_tree.selection()
        if not selected_items:
            return
        item_values = self.history_tree.item(selected_items[0], "values")
        if len(item_values) >= 4:
            command_text = item_values[3]
            self.clipboard_clear()
            self.clipboard_append(command_text)

    def _clear_history(self) -> None:
        """
        Clear all entries from command history table.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        for item_id in self.history_tree.get_children():
            self.history_tree.delete(item_id)

    def set_logs_directory(self, logs_dir_path: str) -> None:
        """
        Set target directory for NFACT log files and update dropdown.

        Parameters
        ----------
        logs_dir_path: str
            Directory path containing NFACT .log files.

        Returns
        -------
        None
        """
        self.discovered_logs_dir = logs_dir_path
        self.refresh_log_files()

    def refresh_log_files(self) -> None:
        """
        Rescan current logs directory and populate combobox.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        if not self.discovered_logs_dir or not os.path.isdir(self.discovered_logs_dir):
            return

        pattern = os.path.join(self.discovered_logs_dir, "*.log")
        found_files = sorted(glob.glob(pattern), reverse=True)
        self.inspector_combobox["values"] = found_files
        if found_files and not self.inspector_combobox.get():
            self.inspector_combobox.set(found_files[0])
            self._load_file_into_inspector(found_files[0])

    def _on_log_file_selected(self, event_obj: Optional[tk.Event] = None) -> None:
        """
        Handle combobox selection of log file.

        Parameters
        ----------
        event_obj: Optional[tk.Event]
            Event object.

        Returns
        -------
        None
        """
        selected_file = self.inspector_combobox.get().strip()
        if selected_file and os.path.isfile(selected_file):
            self._load_file_into_inspector(selected_file)

    def _on_browse_log_file(self) -> None:
        """
        Browse for an arbitrary log file.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        selected_file = filedialog.askopenfilename(
            parent=self,
            title="Select Log File to View",
            filetypes=[("Log files", "*.log"), ("Text files", "*.txt"), ("All", "*.*")],
        )
        if selected_file:
            current_vals = list(self.inspector_combobox["values"])
            if selected_file not in current_vals:
                current_vals.insert(0, selected_file)
                self.inspector_combobox["values"] = current_vals
            self.inspector_combobox.set(selected_file)
            self._load_file_into_inspector(selected_file)

    def _load_file_into_inspector(self, file_path: str) -> None:
        """
        Read file and render styled ANSI text in inspector view.

        Parameters
        ----------
        file_path: str
            Path to log file.

        Returns
        -------
        None
        """
        self.inspector_text.configure(state="normal")
        self.inspector_text.delete("1.0", "end")
        try:
            with open(
                file_path, "r", encoding="utf-8", errors="replace"
            ) as file_handle:
                for line_content in file_handle:
                    self.inspector_parser.append_text(self.inspector_text, line_content)
        except OSError as read_error:
            self.inspector_text.insert("end", f"Error reading log file: {read_error}\n")
        self.inspector_text.configure(state="disabled")
