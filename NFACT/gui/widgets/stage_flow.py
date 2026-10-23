"""
Pipeline stage execution flow bar with modern pill toggles and chevron connectors.
"""

from dataclasses import dataclass
import tkinter as tk
from typing import Any, Callable, Optional


@dataclass
class StageSpec:
    """Specification for an execution stage pill.

    Usage
    -----
    spec = StageSpec(key="pp", title="1. Pre-process", subtitle="nfact_pp", state="enabled")
    """

    key: str
    title: str
    subtitle: str
    state: str = "enabled"
    locked: bool = False


class StageFlowBar(tk.Canvas):
    """Canvas component rendering four pipeline execution stages as interactive pills.

    Usage
    -----
    flow_bar = StageFlowBar(parent_frame, stages=specs, on_toggle=handle_stage_toggle)
    """

    def __init__(
        self,
        parent_container: tk.Widget,
        stages: list[StageSpec],
        on_toggle: Callable[[str, bool], None],
        theme_manager: Optional[Any] = None,
        height: int = 46,
    ) -> None:
        """Initialize pipeline stage flow bar.

        Parameters
        ------------
        parent_container: tk.Widget
            Parent Tkinter container.
        stages: list[StageSpec]
            List of stage pill specifications.
        on_toggle: Callable[[str, bool], None]
            Callback invoked when a stage is toggled with (stage_key, is_enabled).
        theme_manager: Optional[Any]
            ThemeManager for color synchronization. Defaults to None.
        height: int
            Canvas height in pixels. Defaults to 46.

        Returns
        --------
            None: None object
                Initializes canvas and binds redraw on resize.
        """
        super().__init__(
            parent_container,
            height=height,
            highlightthickness=0,
            borderwidth=0,
            bg="#1F1B2B",
        )
        self.stages = stages
        self.on_toggle = on_toggle
        self.theme_manager = theme_manager
        self.pill_regions: list[tuple[float, float, float, float, StageSpec]] = []

        self.bind("<Configure>", lambda event_obj: self.redraw())
        self.bind("<Button-1>", self._on_canvas_click)

        if self.theme_manager is not None:
            self.theme_manager.register_widget(self, self.apply_palette)

        self.redraw()

    def set_state(self, stage_key: str, state_value: str) -> None:
        """Update the visual state of a specific stage pill.

        Parameters
        ------------
        stage_key: str
            Stage identifier key (e.g. "pp", "decomp", "qc", "dr").
        state_value: str
            New state name ('enabled', 'skipped', 'locked', 'running', 'done').

        Returns
        --------
            None: None object
                Updates stage spec and redraws.
        """
        for stage_spec in self.stages:
            if stage_spec.key == stage_key:
                stage_spec.state = state_value
                break
        self.redraw()

    def get_state(self, stage_key: str) -> str:
        """Get the current state string of a stage pill.

        Parameters
        ------------
        stage_key: str
            Stage identifier key.

        Returns
        --------
            str: stage state
                Current state name string.
        """
        for stage_spec in self.stages:
            if stage_spec.key == stage_key:
                return stage_spec.state
        return "enabled"

    def _on_canvas_click(self, event_obj: tk.Event) -> None:
        """Handle mouse click to toggle enabled / skipped states.

        Parameters
        ------------
        event_obj: tk.Event
            Tkinter click event.

        Returns
        --------
            None: None object
                Toggles non-locked stages and invokes callback.
        """
        click_x = float(event_obj.x)
        click_y = float(event_obj.y)

        for left_x, top_y, right_x, bottom_y, spec in self.pill_regions:
            if left_x <= click_x <= right_x and top_y <= click_y <= bottom_y:
                if spec.locked:
                    return

                new_enabled = spec.state != "enabled"
                spec.state = "enabled" if new_enabled else "skipped"
                self.redraw()
                self.on_toggle(spec.key, new_enabled)
                return

    def apply_palette(self, palette_tokens: Any) -> None:
        """Update background color and trigger redraw on theme switch.

        Parameters
        ------------
        palette_tokens: Any
            Color palette tokens object or mapping.

        Returns
        --------
            None: None object
                Updates canvas background and redraws.
        """
        bg_surface = (
            palette_tokens["bg_surface"]
            if "bg_surface" in palette_tokens
            else getattr(palette_tokens, "bg_surface", "#1F1B2B")
        )
        self.configure(bg=bg_surface)
        self.redraw()

    def redraw(self) -> None:
        """Redraw all stage pills and connecting chevrons based on canvas width.

        Parameters
        ------------
        None

        Returns
        --------
            None: None object
                Clears and renders stage pills.
        """
        self.delete("all")
        self.pill_regions.clear()

        palette = (
            self.theme_manager.get_palette() if self.theme_manager is not None else None
        )
        accent_color = palette.accent_primary if palette is not None else "#E91E8C"
        border_color = palette.border_color if palette is not None else "#332C47"
        bg_surface_alt = palette.bg_surface_alt if palette is not None else "#272236"
        fg_primary = palette.fg_primary if palette is not None else "#EEEAF6"
        fg_disabled = palette.fg_disabled if palette is not None else "#5C5470"
        status_running = palette.status_running if palette is not None else "#AF87FF"
        status_success = palette.status_success if palette is not None else "#2ECC71"

        total_width = float(self.winfo_width())
        total_height = float(self.winfo_height())
        if total_width < 100:
            total_width = 700.0
        if total_height < 20:
            total_height = 46.0

        stage_count = len(self.stages)
        if stage_count == 0:
            return

        arrow_space = 20.0
        margin_x = 8.0
        usable_width = (
            total_width - (2.0 * margin_x) - ((stage_count - 1) * arrow_space)
        )
        pill_width = max(80.0, usable_width / stage_count)
        pill_height = total_height - 10.0
        start_y = 5.0

        for idx, stage in enumerate(self.stages):
            start_x = margin_x + idx * (pill_width + arrow_space)
            end_x = start_x + pill_width
            end_y = start_y + pill_height

            self.pill_regions.append((start_x, start_y, end_x, end_y, stage))

            # Determine colors based on state
            if stage.state == "enabled":
                fill_color = accent_color
                outline_color = accent_color
                text_color = "#FFFFFF"
                status_icon = "●"
            elif stage.state == "skipped":
                fill_color = ""
                outline_color = border_color
                text_color = fg_disabled
                status_icon = "○"
            elif stage.state == "locked":
                fill_color = bg_surface_alt
                outline_color = border_color
                text_color = fg_primary
                status_icon = "🔒"
            elif stage.state == "running":
                fill_color = status_running
                outline_color = status_running
                text_color = "#FFFFFF"
                status_icon = "◌"
            else:  # done
                fill_color = status_success
                outline_color = status_success
                text_color = "#FFFFFF"
                status_icon = "✓"

            # Draw pill with rounded corners (two ovals and a rectangle)
            corner_radius = 6.0
            self.create_rectangle(
                start_x + corner_radius,
                start_y,
                end_x - corner_radius,
                end_y,
                fill=fill_color,
                outline=outline_color,
            )
            self.create_oval(
                start_x,
                start_y,
                start_x + 2 * corner_radius,
                end_y,
                fill=fill_color,
                outline=outline_color,
            )
            self.create_oval(
                end_x - 2 * corner_radius,
                start_y,
                end_x,
                end_y,
                fill=fill_color,
                outline=outline_color,
            )

            # Draw text
            center_x = (start_x + end_x) / 2.0
            center_y = (start_y + end_y) / 2.0

            title_text = f"{status_icon} {stage.title}"
            self.create_text(
                center_x,
                center_y - 7,
                text=title_text,
                fill=text_color,
                font="NFACTBodyBold",
            )
            self.create_text(
                center_x,
                center_y + 9,
                text=stage.subtitle,
                fill=text_color,
                font="NFACTCaption",
            )

            # Draw chevron connector
            if idx < stage_count - 1:
                chevron_x = end_x + (arrow_space / 2.0)
                self.create_text(
                    chevron_x,
                    center_y,
                    text="›",
                    fill=fg_disabled,
                    font="NFACTSection",
                )
