"""
Command bar widget featuring live CLI command preview, copy, and execution controls.
"""

import shlex
import tkinter as tk
from tkinter import ttk
from typing import Any, Callable, Optional

from NFACT.gui.widgets.tooltip import HoverTooltip


class CommandBar(ttk.Frame):
    """Bottom-docked command preview and execution bar.

    Usage
    -----
    bar = CommandBar(
        parent_frame,
        on_run_callback=handle_run,
        on_stop_callback=handle_stop,
        on_validate_callback=handle_validate,
    )
    bar.set_command("nfact -l sub_list.txt -o /path/out -d 75")
    """

    def __init__(
        self,
        parent_container: tk.Widget,
        on_run_callback: Optional[Callable[[], None]] = None,
        on_stop_callback: Optional[Callable[[], None]] = None,
        on_validate_callback: Optional[Callable[[], None]] = None,
        theme_manager: Optional[Any] = None,
        style: str = "Surface.TFrame",
    ) -> None:
        """Initialize command bar widget.

        Parameters
        ------------
        parent_container: tk.Widget
            Parent Tkinter widget.
        on_run_callback: Optional[Callable[[], None]]
            Callback executed when Run button is clicked. Defaults to None.
        on_stop_callback: Optional[Callable[[], None]]
            Callback executed when Stop button is clicked. Defaults to None.
        on_validate_callback: Optional[Callable[[], None]]
            Callback executed when Validate button is clicked. Defaults to None.
        theme_manager: Optional[Any]
            ThemeManager reference for dynamic styling. Defaults to None.
        style: str
            ttk frame style name. Defaults to "Surface.TFrame".

        Returns
        --------
            None: None object
                Constructs command bar widgets and layout.
        """
        super().__init__(parent_container, style=style, padding=(10, 6))
        self.on_run_callback = on_run_callback
        self.on_stop_callback = on_stop_callback
        self.on_validate_callback = on_validate_callback
        self.theme_manager = theme_manager

        self.command_variable = tk.StringVar(value="")
        self.is_running = False

        self.columnconfigure(0, weight=1)

        # Container for text preview and buttons
        main_row = ttk.Frame(self, style=style)
        main_row.grid(row=0, column=0, sticky="ew")
        main_row.columnconfigure(0, weight=1)

        # Multi-line syntax-highlighted command preview text
        self.command_text = tk.Text(
            main_row,
            height=2,
            wrap="word",
            background="#2D1B4E",
            foreground="#FFFFFF",
            insertbackground="#FFFFFF",
            highlightthickness=1,
            highlightbackground="#8C77B8",
            borderwidth=0,
            padx=10,
            pady=6,
            font="NFACTMono",
        )
        self.command_text.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.command_text.configure(state="disabled")

        # Backward compatibility alias
        self.command_entry = self.command_text

        # Setup tags
        self._configure_syntax_tags()

        # Action Buttons on right
        button_group = ttk.Frame(main_row, style=style)
        button_group.grid(row=0, column=1, sticky="e")

        self.copy_button = ttk.Button(
            button_group,
            text="Copy",
            width=7,
            command=self.copy_command,
            style="Ghost.TButton",
        )
        self.copy_button.pack(side="left", padx=(0, 6))
        HoverTooltip(self.copy_button, "Copy command string to clipboard.")

        self.validate_button = ttk.Button(
            button_group,
            text="Validate",
            width=9,
            command=self.validate_action,
            style="TButton",
        )
        self.validate_button.pack(side="left", padx=(0, 6))
        HoverTooltip(self.validate_button, "Check all parameters for required values.")

        self.run_button = ttk.Button(
            button_group,
            text="▶ Run",
            width=9,
            command=self.run_action,
            style="Accent.TButton",
        )
        self.run_button.pack(side="left", padx=(0, 6))

        self.stop_button = ttk.Button(
            button_group,
            text="■ Stop",
            width=9,
            command=self.stop_action,
            style="Danger.TButton",
            state="disabled",
        )
        self.stop_button.pack(side="left")

        if self.theme_manager is not None:
            self.theme_manager.register_widget(self, self.apply_palette)

    def _configure_syntax_tags(self) -> None:
        """Configure syntax color tags for command preview text.

        Parameters
        ------------
        None

        Returns
        --------
            None: None object
                Configures text tags in-place.
        """
        self.command_text.tag_configure(
            "cmd_prompt", foreground="#C4B5FD", font="NFACTMono"
        )
        self.command_text.tag_configure(
            "cmd_prog", foreground="#FFFFFF", font="NFACTMono"
        )
        self.command_text.tag_configure(
            "cmd_flag", foreground="#EBE2FF", font="NFACTMono"
        )
        self.command_text.tag_configure(
            "cmd_val", foreground="#FFFFFF", font="NFACTMono"
        )
        self.command_text.tag_configure(
            "cmd_path", foreground="#E9D5FF", font="NFACTMono"
        )

    def set_command(self, command_text: str) -> None:
        """Update the command string displayed in the preview.

        Parameters
        ------------
        command_text: str
            New command string to display.

        Returns
        --------
            None: None object
                Renders highlighted tokens in preview text.
        """
        self.command_variable.set(command_text)

        self.command_text.configure(state="normal")
        self.command_text.delete("1.0", "end")

        if not command_text.strip():
            self.command_text.configure(state="disabled")
            return

        self.command_text.insert("end", "$ ", "cmd_prompt")

        try:
            tokens = shlex.split(command_text)
        except ValueError:
            tokens = command_text.split()

        for idx, token in enumerate(tokens):
            if idx == 0:
                self.command_text.insert("end", token, "cmd_prog")
            elif token.startswith("-"):
                self.command_text.insert("end", token, "cmd_flag")
            elif "/" in token or "\\" in token:
                self.command_text.insert("end", token, "cmd_path")
            else:
                self.command_text.insert("end", token, "cmd_val")

            if idx < len(tokens) - 1:
                self.command_text.insert("end", " ")

        self.command_text.configure(state="disabled")

    def get_command(self) -> str:
        """Get the current command string from the entry.

        Parameters
        ------------
        None

        Returns
        --------
            str: command string
                Current command text.
        """
        return self.command_variable.get().strip()

    def set_running_state(self, running_status: bool) -> None:
        """Update button states according to running status.

        Parameters
        ------------
        running_status: bool
            True if process is actively executing, False otherwise.

        Returns
        --------
            None: None object
                Enables or disables action buttons.
        """
        self.is_running = running_status
        if running_status:
            self.run_button.configure(state="disabled")
            self.validate_button.configure(state="disabled")
            self.stop_button.configure(state="normal")
        else:
            self.run_button.configure(state="normal")
            self.validate_button.configure(state="normal")
            self.stop_button.configure(state="disabled")

    def copy_command(self) -> None:
        """Copy current command to system clipboard and provide visual feedback.

        Parameters
        ------------
        None

        Returns
        --------
            None: None object
                Copies text and schedules button label restoration.
        """
        command_string = self.command_variable.get().strip()
        if not command_string:
            return

        self.clipboard_clear()
        self.clipboard_append(command_string)
        self.copy_button.configure(text="Copied ✓")
        self.after(1500, self._restore_copy_label)

    def _restore_copy_label(self) -> None:
        """Restore copy button label text.

        Parameters
        ------------
        None

        Returns
        --------
            None: None object
                Restores label to "Copy".
        """
        self.copy_button.configure(text="Copy")

    def run_action(self) -> None:
        """Trigger on_run callback if registered.

        Parameters
        ------------
        None

        Returns
        --------
            None: None object
                Calls on_run_callback.
        """
        if self.on_run_callback is not None:
            self.on_run_callback()

    def stop_action(self) -> None:
        """Trigger on_stop callback if registered.

        Parameters
        ------------
        None

        Returns
        --------
            None: None object
                Calls on_stop_callback.
        """
        if self.on_stop_callback is not None:
            self.on_stop_callback()

    def validate_action(self) -> None:
        """Trigger on_validate callback if registered.

        Parameters
        ------------
        None

        Returns
        --------
            None: None object
                Calls on_validate_callback.
        """
        if self.on_validate_callback is not None:
            self.on_validate_callback()

    def apply_palette(self, palette_tokens: Any) -> None:
        """Update colors of command preview text on theme switch.

        Parameters
        ------------
        palette_tokens: Any
            Color palette tokens object or mapping.

        Returns
        --------
            None: None object
                Updates text background and highlight colors.
        """
        bg_console = (
            palette_tokens["bg_console"]
            if "bg_console" in palette_tokens
            else getattr(palette_tokens, "bg_console", "#2D1B4E")
        )
        border_color = (
            palette_tokens["border_color"]
            if "border_color" in palette_tokens
            else getattr(palette_tokens, "border_color", "#8C77B8")
        )
        self.command_text.configure(
            background=bg_console,
            foreground="#FFFFFF",
            insertbackground="#FFFFFF",
            highlightbackground=border_color,
        )
        self._configure_syntax_tags()
        self.set_command(self.command_variable.get())
