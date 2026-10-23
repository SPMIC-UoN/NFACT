"""
Responsive grid layout helper for grouping parameter fields.
"""

import tkinter as tk

from NFACT.gui.theme.palette import Spacing


def place_in_form_grid(
    parent_frame: tk.Widget,
    widgets: list[tk.Widget],
    columns: int = 2,
    spacing: Spacing = Spacing(),
    start_row: int = 0,
) -> int:
    """Place parameter input widgets into an N-column structured grid.

    Parameters
    ------------
    parent_frame: tk.Widget
        Card content frame receiving the field widgets.
    widgets: list[tk.Widget]
        Field widgets to lay out.
    columns: int
        Number of grid columns. Defaults to 2.
    spacing: Spacing
        Spacing token instance for gutters. Defaults to Spacing().
    start_row: int
        Starting grid row index. Defaults to 0.

    Returns
    --------
        int: next row
            First free row index after placing all widgets.
    """
    for column_index in range(columns):
        parent_frame.columnconfigure(column_index, weight=1)

    current_row = start_row
    current_col = 0

    for widget_item in widgets:
        pad_right = spacing.medium if current_col < columns - 1 else 0
        widget_item.grid(
            row=current_row,
            column=current_col,
            sticky="ew",
            padx=(0, pad_right),
            pady=(0, spacing.small),
        )
        current_col += 1
        if current_col >= columns:
            current_col = 0
            current_row += 1

    return current_row if current_col == 0 else current_row + 1
