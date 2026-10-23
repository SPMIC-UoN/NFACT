"""
Parser translating NFACT ANSI escape codes and returns into Tk text tags.
"""

import re
import tkinter as tk
from typing import Any, Optional

ANSI_ESCAPE_REGEX = re.compile(r"(\x1b\[[0-9;?]*[a-zA-Z])")

ANSI_TAG_MAP = {
    "1;31m": "ansi_red",
    "31m": "ansi_red",
    "1;35m": "ansi_pink",
    "35m": "ansi_pink",
    "38;2;255;20;147m": "ansi_deep_pink",
    "38;5;93m": "ansi_purple",
    "38;5;129m": "ansi_darker_pink",
    "0;35m": "ansi_plum",
    "38;2;153;102;204m": "ansi_amethyst",
    "38;5;141m": "ansi_lav",
    "38;5;217m": "ansi_light_pink",
    "1;32m": "ansi_green",
    "32m": "ansi_green",
    "1;33m": "ansi_yellow",
    "33m": "ansi_yellow",
    "1;36m": "ansi_cyan",
    "36m": "ansi_cyan",
}


def strip_ansi(raw_text: str) -> str:
    """Remove all ANSI escape sequences from a text string.

    Parameters
    ------------
    raw_text: str
        Raw string containing ANSI escape sequences.

    Returns
    --------
        str: cleaned text
            Clean string with escape sequences stripped.
    """
    return ANSI_ESCAPE_REGEX.sub("", raw_text)


def configure_ansi_tags(text_widget: tk.Text, palette: Any) -> None:
    """Configure text color tags corresponding to terminal color codes.

    Parameters
    ------------
    text_widget: tk.Text
        Target text widget.
    palette: Any
        Palette object or dictionary with theme color mappings.

    Returns
    --------
        None: None object
            Configures tags in-place on the text widget.
    """
    ansi_map = (
        palette["ansi"]
        if isinstance(palette, dict) and "ansi" in palette
        else getattr(palette, "ansi", {})
    )

    status_error = (
        palette["status_error"]
        if "status_error" in palette
        else getattr(palette, "status_error", "#FF5252")
    )
    status_success = (
        palette["status_success"]
        if "status_success" in palette
        else getattr(palette, "status_success", "#2ECC71")
    )

    text_widget.tag_configure(
        "ansi_red", foreground=ansi_map.get("ansi_red", status_error)
    )
    text_widget.tag_configure(
        "ansi_pink", foreground=ansi_map.get("ansi_pink", "#E040FB")
    )
    text_widget.tag_configure(
        "ansi_deep_pink",
        foreground=ansi_map.get("ansi_deep_pink", "#FF1493"),
    )
    text_widget.tag_configure(
        "ansi_purple", foreground=ansi_map.get("ansi_purple", "#8700FF")
    )
    text_widget.tag_configure(
        "ansi_darker_pink",
        foreground=ansi_map.get("ansi_darker_pink", "#AF00FF"),
    )
    text_widget.tag_configure(
        "ansi_plum", foreground=ansi_map.get("ansi_plum", "#BA68C8")
    )
    text_widget.tag_configure(
        "ansi_amethyst", foreground=ansi_map.get("ansi_amethyst", "#9966CC")
    )
    text_widget.tag_configure(
        "ansi_lav", foreground=ansi_map.get("ansi_lav", "#AF87FF")
    )
    text_widget.tag_configure(
        "ansi_light_pink",
        foreground=ansi_map.get("ansi_light_pink", "#FFAFAF"),
    )
    text_widget.tag_configure(
        "ansi_green", foreground=ansi_map.get("ansi_green", status_success)
    )
    text_widget.tag_configure(
        "ansi_yellow", foreground=ansi_map.get("ansi_yellow", "#F1C40F")
    )
    text_widget.tag_configure(
        "ansi_cyan", foreground=ansi_map.get("ansi_cyan", "#00BCD4")
    )
    text_widget.tag_configure("ansi_bold", font="NFACTMono")


class AnsiParser:
    """Parser to convert ANSI terminal sequences to Tkinter styled text.

    Usage
    -----
    parser = AnsiParser()
    parser.append_text(text_widget, raw_terminal_line)
    """

    def __init__(self) -> None:
        """Initialize the ANSI parser state.

        Parameters
        ------------
        None

        Returns
        --------
            None: None object
                Initializes active tag tracker.
        """
        self.active_tag: Optional[str] = None

    def append_text(self, text_widget: tk.Text, raw_string: str) -> None:
        """Parse raw terminal string and insert styled segments into text widget.

        Parameters
        ------------
        text_widget: tk.Text
            Target text widget to append into.
        raw_string: str
            Raw text line containing potential ANSI codes or carriage returns.

        Returns
        --------
            None: None object
                Inserts styled text into the target widget.
        """
        text_widget.configure(state="normal")

        if "\r" in raw_string and "\n" not in raw_string:
            line_start = text_widget.index("end-1c linestart")
            line_end = text_widget.index("end-1c lineend")
            text_widget.delete(line_start, line_end)
            raw_string = raw_string.replace("\r", "")

        token_list = ANSI_ESCAPE_REGEX.split(raw_string)
        for token_item in token_list:
            if not token_item:
                continue

            if token_item.startswith("\x1b["):
                code_str = token_item[2:]
                if code_str in ["0;0m", "0m", "m"]:
                    self.active_tag = None
                else:
                    matched_tag = next(
                        (
                            tag_name
                            for ansi_key, tag_name in ANSI_TAG_MAP.items()
                            if code_str == ansi_key
                        ),
                        None,
                    )
                    if matched_tag:
                        self.active_tag = matched_tag
            else:
                if self.active_tag:
                    text_widget.insert("end", token_item, (self.active_tag,))
                else:
                    text_widget.insert("end", token_item)

        text_widget.configure(state="disabled")
