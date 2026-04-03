"""REST API server for AirDraw Pro AI frontend integration."""
from __future__ import annotations

import base64
import time
from threading import Lock
from typing import Literal, Optional

import cv2
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from config import FRAME_HEIGHT, FRAME_WIDTH
from drawing_utils import DrawingEngine


class PointRequest(BaseModel):
    x: int = Field(ge=0)
    y: int = Field(ge=0)
    drawing_enabled: bool = True


class DragRequest(BaseModel):
    x: int
    y: int
    damping: float = 0.45


class BrushRequest(BaseModel):
    mode: Literal["smooth", "marker", "block"]


class ColorRequest(BaseModel):
    name: str
    bgr: tuple[int, int, int]


class EraserRequest(BaseModel):
    enabled: bool


class ShapeLineRequest(BaseModel):
    x1: int
    y1: int
    x2: int
    y2: int


class ShapeCircleRequest(BaseModel):
    cx: int
    cy: int
    ex: int
    ey: int


class AirDrawState:
    def __init__(self) -> None:
        self.lock = Lock()
        self.engine = DrawingEngine(width=FRAME_WIDTH, height=FRAME_HEIGHT)
        self.drag_active = False

    def png_bytes(self, transparent: bool = False) -> bytes:
        canvas = self.engine.canvas
        if transparent:
            alpha = (canvas.any(axis=2).astype("uint8")) * 255
            rgba = cv2.cvtColor(canvas, cv2.COLOR_BGR2BGRA)
            rgba[:, :, 3] = alpha
            ok, encoded = cv2.imencode(".png", rgba)
        else:
            ok, encoded = cv2.imencode(".png", canvas)
        if not ok:
            raise RuntimeError("Failed to encode canvas as PNG")
        return encoded.tobytes()


app = FastAPI(title="AirDraw Pro AI API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
state = AirDrawState()


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "airdraw-api", "timestamp": int(time.time())}


@app.get("/state")
def get_state() -> dict:
    with state.lock:
        e = state.engine
        return {
            "tool": e.tool_name,
            "brush_mode": e.brush_mode,
            "color_name": e.color_name,
            "thickness": e.thickness,
            "eraser_enabled": e.eraser_enabled,
            "page_index": e.page_index,
            "page_count": e.page_count,
            "drag_active": state.drag_active,
            "size": {"width": e.width, "height": e.height},
        }


@app.post("/canvas/clear")
def canvas_clear() -> dict:
    with state.lock:
        state.engine.clear()
    return {"ok": True}


@app.post("/canvas/undo")
def canvas_undo() -> dict:
    with state.lock:
        return {"ok": state.engine.undo()}


@app.post("/canvas/redo")
def canvas_redo() -> dict:
    with state.lock:
        return {"ok": state.engine.redo()}


@app.get("/canvas/image")
def canvas_image(transparent: bool = False, base64_data: bool = True):
    with state.lock:
        png = state.png_bytes(transparent=transparent)
    if base64_data:
        return {"ok": True, "png_base64": base64.b64encode(png).decode("ascii")}
    return {"ok": True, "png_bytes_len": len(png)}


@app.post("/draw/point")
def draw_point(payload: PointRequest) -> dict:
    with state.lock:
        p = state.engine.draw_point((payload.x, payload.y), drawing_enabled=payload.drawing_enabled)
    return {"ok": True, "point": p}


@app.post("/draw/line")
def draw_line(payload: ShapeLineRequest) -> dict:
    with state.lock:
        state.engine.draw_assisted_line((payload.x1, payload.y1), (payload.x2, payload.y2))
    return {"ok": True}


@app.post("/draw/circle")
def draw_circle(payload: ShapeCircleRequest) -> dict:
    with state.lock:
        state.engine.draw_assisted_circle((payload.cx, payload.cy), (payload.ex, payload.ey))
    return {"ok": True}


@app.post("/drag/start")
def drag_start(payload: DragRequest) -> dict:
    with state.lock:
        state.engine.start_drag((payload.x, payload.y))
        state.drag_active = True
    return {"ok": True}


@app.post("/drag/move")
def drag_move(payload: DragRequest) -> dict:
    with state.lock:
        if not state.drag_active:
            raise HTTPException(status_code=400, detail="Drag is not active")
        state.engine.drag_canvas((payload.x, payload.y), damping=payload.damping)
    return {"ok": True}


@app.post("/drag/stop")
def drag_stop() -> dict:
    with state.lock:
        state.engine.stop_drag()
        state.drag_active = False
    return {"ok": True}


@app.post("/tool/brush")
def tool_brush(payload: BrushRequest) -> dict:
    with state.lock:
        state.engine.set_brush_mode(payload.mode)
    return {"ok": True}


@app.post("/tool/color")
def tool_color(payload: ColorRequest) -> dict:
    b, g, r = payload.bgr
    if not all(0 <= v <= 255 for v in (b, g, r)):
        raise HTTPException(status_code=422, detail="bgr values must be between 0 and 255")
    with state.lock:
        state.engine.set_color(payload.name, payload.bgr)
    return {"ok": True}


@app.post("/tool/eraser")
def tool_eraser(payload: EraserRequest) -> dict:
    with state.lock:
        state.engine.set_eraser(payload.enabled)
    return {"ok": True}


@app.post("/tool/size")
def tool_size(direction: Literal["up", "down"]) -> dict:
    with state.lock:
        if direction == "up":
            state.engine.increase_thickness()
        else:
            state.engine.decrease_thickness()
    return {"ok": True}


@app.post("/page/new")
def page_new() -> dict:
    with state.lock:
        idx = state.engine.new_page()
    return {"ok": True, "page_index": idx, "page_count": state.engine.page_count}


@app.post("/page/next")
def page_next() -> dict:
    with state.lock:
        idx = state.engine.next_page()
    return {"ok": True, "page_index": idx, "page_count": state.engine.page_count}


@app.post("/page/prev")
def page_prev() -> dict:
    with state.lock:
        idx = state.engine.prev_page()
    return {"ok": True, "page_index": idx, "page_count": state.engine.page_count}


@app.post("/page/delete")
def page_delete() -> dict:
    with state.lock:
        deleted = state.engine.delete_current_page()
    return {"ok": True, "deleted": deleted, "page_index": state.engine.page_index, "page_count": state.engine.page_count}

