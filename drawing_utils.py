"""Drawing and drag utilities for AirDraw Pro AI."""
from __future__ import annotations

from collections import deque
from typing import Deque, Optional, Tuple

import cv2
import numpy as np

from config import (
    DRAW_COLOR,
    DRAW_THICKNESS,
    INTERPOLATION_STEP_PIXELS,
    MAX_DRAG_STEP,
    MIN_DRAW_MOVEMENT_PIXELS,
    SMOOTHING_WINDOW,
)

Point = Tuple[int, int]
BrushMode = str


class DrawingEngine:
    """Stateful drawing engine with smoothing, interpolation and drag."""

    def __init__(
        self,
        width: int,
        height: int,
        draw_color=DRAW_COLOR,
        thickness: int = DRAW_THICKNESS,
        smoothing_window: int = SMOOTHING_WINDOW,
    ) -> None:
        self.width = width
        self.height = height
        self.draw_color = draw_color
        self.thickness = thickness
        self.smoothing_window = max(2, smoothing_window)
        self.min_draw_movement = max(1, MIN_DRAW_MOVEMENT_PIXELS)
        self.brush_mode: BrushMode = "smooth"
        self.color_name = "green"
        self.block_size = max(4, self.thickness * 2)
        self.eraser_enabled = False
        self.eraser_thickness = max(8, self.thickness * 2)

        self._pages = [np.zeros((height, width, 3), dtype=np.uint8)]
        self._page_index = 0
        self._history: Deque[Point] = deque(maxlen=self.smoothing_window)
        self._prev_point: Optional[Point] = None

        self._drag_anchor: Optional[Point] = None
        self._drag_active = False
        self._undo_stacks = [deque(maxlen=40)]
        self._redo_stacks = [deque(maxlen=40)]

    @property
    def page_index(self) -> int:
        return self._page_index

    @property
    def page_count(self) -> int:
        return len(self._pages)

    @property
    def canvas(self) -> np.ndarray:
        return self._pages[self._page_index]

    @canvas.setter
    def canvas(self, value: np.ndarray) -> None:
        self._pages[self._page_index] = value

    def _undo_stack(self) -> Deque[np.ndarray]:
        return self._undo_stacks[self._page_index]

    def _redo_stack(self) -> Deque[np.ndarray]:
        return self._redo_stacks[self._page_index]

    @property
    def tool_name(self) -> str:
        return "eraser" if self.eraser_enabled else "draw"

    def _push_undo(self) -> None:
        self._undo_stack().append(self.canvas.copy())
        self._redo_stack().clear()

    def undo(self) -> bool:
        if not self._undo_stack():
            return False
        self._redo_stack().append(self.canvas.copy())
        self.canvas = self._undo_stack().pop()
        self.reset_stroke()
        self.reset_drag()
        return True

    def redo(self) -> bool:
        if not self._redo_stack():
            return False
        self._undo_stack().append(self.canvas.copy())
        self.canvas = self._redo_stack().pop()
        self.reset_stroke()
        self.reset_drag()
        return True

    def clear(self) -> None:
        if np.any(self.canvas != 0):
            self._push_undo()
        self.canvas.fill(0)
        self.reset_stroke()
        self.reset_drag()

    def new_page(self) -> int:
        self._pages.append(np.zeros((self.height, self.width, 3), dtype=np.uint8))
        self._undo_stacks.append(deque(maxlen=40))
        self._redo_stacks.append(deque(maxlen=40))
        self._page_index = len(self._pages) - 1
        self.reset_stroke()
        self.reset_drag()
        return self._page_index

    def next_page(self) -> int:
        if not self._pages:
            return 0
        self._page_index = (self._page_index + 1) % len(self._pages)
        self.reset_stroke()
        self.reset_drag()
        return self._page_index

    def prev_page(self) -> int:
        if not self._pages:
            return 0
        self._page_index = (self._page_index - 1) % len(self._pages)
        self.reset_stroke()
        self.reset_drag()
        return self._page_index

    def delete_current_page(self) -> bool:
        if len(self._pages) == 1:
            self.clear()
            return False
        self._pages.pop(self._page_index)
        self._undo_stacks.pop(self._page_index)
        self._redo_stacks.pop(self._page_index)
        if self._page_index >= len(self._pages):
            self._page_index = len(self._pages) - 1
        self.reset_stroke()
        self.reset_drag()
        return True

    def reset_stroke(self) -> None:
        self._history.clear()
        self._prev_point = None

    def reset_drag(self) -> None:
        self._drag_anchor = None
        self._drag_active = False

    def _smoothed_point(self, point: Point) -> Point:
        self._history.append(point)
        xs = [p[0] for p in self._history]
        ys = [p[1] for p in self._history]
        return int(np.mean(xs)), int(np.mean(ys))

    def _draw_interpolated_line(self, start: Point, end: Point) -> None:
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        dist = max(abs(dx), abs(dy))
        steps = max(1, dist // INTERPOLATION_STEP_PIXELS)

        for i in range(1, steps + 1):
            t0 = (i - 1) / steps
            t1 = i / steps
            x0 = int(start[0] + dx * t0)
            y0 = int(start[1] + dy * t0)
            x1 = int(start[0] + dx * t1)
            y1 = int(start[1] + dy * t1)
            cv2.line(
                self.canvas,
                (x0, y0),
                (x1, y1),
                self.draw_color,
                self.thickness,
                lineType=cv2.LINE_AA,
            )

    def _draw_eraser_line(self, start: Point, end: Point) -> None:
        cv2.line(
            self.canvas,
            start,
            end,
            (0, 0, 0),
            self.eraser_thickness,
            lineType=cv2.LINE_AA,
        )

    def _draw_marker_line(self, start: Point, end: Point) -> None:
        cv2.line(
            self.canvas,
            start,
            end,
            self.draw_color,
            max(1, self.thickness * 2),
            lineType=cv2.LINE_AA,
        )

    def _draw_block_cell(self, gx: int, gy: int) -> None:
        x0 = gx * self.block_size
        y0 = gy * self.block_size
        x1 = min(self.width - 1, x0 + self.block_size - 1)
        y1 = min(self.height - 1, y0 + self.block_size - 1)
        cv2.rectangle(self.canvas, (x0, y0), (x1, y1), self.draw_color, -1)

    def _draw_block_segment(self, start: Point, end: Point) -> None:
        gx0, gy0 = start[0] // self.block_size, start[1] // self.block_size
        gx1, gy1 = end[0] // self.block_size, end[1] // self.block_size

        dx = abs(gx1 - gx0)
        dy = abs(gy1 - gy0)
        sx = 1 if gx0 < gx1 else -1
        sy = 1 if gy0 < gy1 else -1
        err = dx - dy
        x, y = gx0, gy0

        while True:
            self._draw_block_cell(x, y)
            if x == gx1 and y == gy1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy

    def _draw_stroke_segment(self, start: Point, end: Point) -> None:
        if self.eraser_enabled:
            self._draw_eraser_line(start, end)
            return
        if self.brush_mode == "block":
            self._draw_block_segment(start, end)
        elif self.brush_mode == "marker":
            self._draw_marker_line(start, end)
        else:
            self._draw_interpolated_line(start, end)

    def draw_assisted_line(self, start: Point, end: Point) -> None:
        self._push_undo()
        color = (0, 0, 0) if self.eraser_enabled else self.draw_color
        thickness = self.eraser_thickness if self.eraser_enabled else self.thickness
        cv2.line(self.canvas, start, end, color, thickness, lineType=cv2.LINE_AA)

    def draw_assisted_circle(self, center: Point, edge: Point) -> None:
        self._push_undo()
        radius = max(1, int(np.hypot(edge[0] - center[0], edge[1] - center[1])))
        color = (0, 0, 0) if self.eraser_enabled else self.draw_color
        thickness = self.eraser_thickness if self.eraser_enabled else self.thickness
        cv2.circle(self.canvas, center, radius, color, thickness, lineType=cv2.LINE_AA)

    def draw_point(self, raw_point: Point, drawing_enabled: bool) -> Optional[Point]:
        """Draw smoothed point and return processed point."""
        if not drawing_enabled:
            self.reset_stroke()
            return None

        point = self._smoothed_point(raw_point)
        if self._prev_point is None:
            self._push_undo()
            self._prev_point = point
            return point

        movement = int(np.hypot(point[0] - self._prev_point[0], point[1] - self._prev_point[1]))
        if movement < self.min_draw_movement:
            return point

        self._draw_stroke_segment(self._prev_point, point)
        self._prev_point = point
        return point

    def set_brush_mode(self, mode: BrushMode) -> None:
        if mode in {"smooth", "marker", "block"}:
            self.brush_mode = mode
            self.reset_stroke()

    def set_color(self, name: str, bgr: Tuple[int, int, int]) -> None:
        self.color_name = name
        self.draw_color = bgr

    def set_eraser(self, enabled: bool) -> None:
        if self.eraser_enabled != enabled:
            self.eraser_enabled = enabled
            self.reset_stroke()

    def increase_thickness(self) -> None:
        self.thickness = min(24, self.thickness + 1)
        self.block_size = max(4, self.thickness * 2)
        self.eraser_thickness = max(8, self.thickness * 2)

    def decrease_thickness(self) -> None:
        self.thickness = max(1, self.thickness - 1)
        self.block_size = max(4, self.thickness * 2)
        self.eraser_thickness = max(8, self.thickness * 2)

    def start_drag(self, anchor: Point) -> None:
        if not self._drag_active:
            self._push_undo()
        self._drag_anchor = anchor
        self._drag_active = True

    def stop_drag(self) -> None:
        self.reset_drag()

    def drag_canvas(self, current: Point, damping: float) -> None:
        """Shift full canvas based on pinch movement with capped velocity."""
        if not self._drag_active or self._drag_anchor is None:
            self.start_drag(current)
            return

        raw_dx = current[0] - self._drag_anchor[0]
        raw_dy = current[1] - self._drag_anchor[1]

        dx = int(np.clip(raw_dx * damping, -MAX_DRAG_STEP, MAX_DRAG_STEP))
        dy = int(np.clip(raw_dy * damping, -MAX_DRAG_STEP, MAX_DRAG_STEP))

        if dx == 0 and dy == 0:
            self._drag_anchor = current
            return

        matrix = np.float32([[1, 0, dx], [0, 1, dy]])
        self.canvas = cv2.warpAffine(
            self.canvas,
            matrix,
            (self.width, self.height),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=(0, 0, 0),
        )

        self._drag_anchor = current

    def overlay_on(self, frame_bgr, alpha: float):
        """Overlay canvas opaquely wherever drawn pixels exist."""
        _ = alpha  # retained for call-site compatibility
        output = frame_bgr.copy()
        mask = np.any(self.canvas != 0, axis=2)
        output[mask] = self.canvas[mask]
        return output

