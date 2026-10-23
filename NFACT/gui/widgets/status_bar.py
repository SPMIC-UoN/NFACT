"""
Footer status bar displaying execution state, progress bar, timer, PID, and version.
"""

from importlib.metadata import PackageNotFoundError, version as pkg_version
import tkinter as tk
from tkinter import ttk


def _get_app_version() -> str:
    """Retrieve installed NFACT version string or provide fallback.

    Parameters
    ------------
    None

    Returns
    --------
        str: version string
            Package version string.
    """
    try:
        return f"v{pkg_version('NFACT')}"
    except PackageNotFoundError:
        return "v0.2.0"


class StatusBar(ttk.Frame):
    """Footer status bar component displaying real-time process indicators.

    Usage
    -----
    status_bar = StatusBar(root_window)
    status_bar.set_running("nfact_pp", pid=12345)
    """

    def __init__(
        self,
        parent_container: tk.Widget,
        style: str = "StatusBar.TFrame",
    ) -> None:
        """Initialize status bar.

        Parameters
        ------------
        parent_container: tk.Widget
            Parent container widget.
        style: str
            ttk frame style name. Defaults to "StatusBar.TFrame".

        Returns
        --------
            None: None object
                Constructs status bar elements.
        """
        super().__init__(parent_container, style=style, padding=(10, 4))

        self.columnconfigure(0, weight=1)

        # Left: Status indicator dot & message
        left_group = ttk.Frame(self, style=style)
        left_group.grid(row=0, column=0, sticky="w")

        self.state_label = ttk.Label(
            left_group,
            text="● Idle",
            style="StatusIdle.TLabel",
        )
        self.state_label.pack(side="left", padx=(0, 12))

        self.progress_bar = ttk.Progressbar(
            left_group,
            mode="indeterminate",
            length=110,
            style="Horizontal.TProgressbar",
        )
        self.progress_bar.pack(side="left", padx=(0, 8))
        self.progress_bar.pack_forget()

        # Right: Info metrics
        right_group = ttk.Frame(self, style=style)
        right_group.grid(row=0, column=1, sticky="e")

        self.timer_label = ttk.Label(
            right_group,
            text="Elapsed: 00:00:00",
            style="Header.TLabel",
            font="NFACTMonoSmall",
        )
        self.timer_label.pack(side="left", padx=(0, 10))

        sep_one = ttk.Separator(right_group, orient="vertical")
        sep_one.pack(side="left", fill="y", padx=(0, 10))

        self.pid_label = ttk.Label(
            right_group,
            text="PID: -",
            style="Header.TLabel",
            font="NFACTMonoSmall",
        )
        self.pid_label.pack(side="left", padx=(0, 10))

        sep_two = ttk.Separator(right_group, orient="vertical")
        sep_two.pack(side="left", fill="y", padx=(0, 10))

        self.version_label = ttk.Label(
            right_group,
            text=f"NFACT {_get_app_version()}",
            style="HeaderTitle.TLabel",
            font="NFACTCaption",
        )
        self.version_label.pack(side="left")

    def set_idle(self, detail: str = "") -> None:
        """Set status bar to idle state.

        Parameters
        ------------
        detail: str
            Optional detail appended to status text. Defaults to "".

        Returns
        --------
            None: None object
                Updates visual state to idle.
        """
        text_str = f"● Idle ({detail})" if detail else "● Idle"
        self.state_label.configure(
            text=text_str,
            style="StatusIdle.TLabel",
        )
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.pid_label.configure(text="PID: -")

    def set_running(self, command_name: str, pid: int = 0) -> None:
        """Set status bar to actively running state with indeterminate progress.

        Parameters
        ------------
        command_name: str
            Command or module currently executing.
        pid: int
            Process ID. Defaults to 0.

        Returns
        --------
            None: None object
                Updates visual state to running.
        """
        self.state_label.configure(
            text=f"◌ Running: {command_name}",
            style="StatusRunning.TLabel",
        )
        self.progress_bar.pack(side="left", padx=(0, 8))
        self.progress_bar.start(10)
        self.pid_label.configure(text=f"PID: {pid if pid > 0 else '-'}")

    def set_completed(self, exit_code: int, duration_str: str) -> None:
        """Set status bar to process completed state.

        Parameters
        ------------
        exit_code: int
            Process exit status code.
        duration_str: str
            Formatted elapsed execution duration.

        Returns
        --------
            None: None object
                Updates visual state to completed or failed.
        """
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.pid_label.configure(text="PID: -")

        if exit_code == 0:
            self.state_label.configure(
                text=f"✓ Completed in {duration_str}",
                style="StatusSuccess.TLabel",
            )
        else:
            self.state_label.configure(
                text=f"✕ Failed ({exit_code}) in {duration_str}",
                style="StatusError.TLabel",
            )

    def update_elapsed(self, elapsed_text: str) -> None:
        """Update elapsed timer display string.

        Parameters
        ------------
        elapsed_text: str
            Formatted timer string (e.g. "00:01:23").

        Returns
        --------
            None: None object
                Updates timer label text.
        """
        self.timer_label.configure(text=f"Elapsed: {elapsed_text}")
