"""Lightweight API server optimized for Railway deployment."""
from __future__ import annotations

import base64
import os
import time
from threading import Lock
from typing import Literal, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Lazy imports to reduce cold start time
import cv2
import numpy as np

# Simple in-memory drawing engine (no MediaPipe needed for API)
class LightweightDrawingEngine:
    def __init__(self, width: int = 1280, height: int = 720):
        self.width = width
        self.height = height
        self.canvas = np.zeros((height, width, 3), dtype=np.uint8)
        self.color = (0, 255, 0)  # BGR format
        self.color_name = "green"
        self.thickness = 3
        self.brush_mode = "smooth"
        self.tool_name = "DRAW"
        self.eraser_enabled = False
        self.prev_point = None
        self.pages = [self.canvas.copy()]
        self.page_index = 0
        self.histories = [[]]
        self.redo_stacks = [[]]
    
    @property
    def canvas(self):
        return self.pages[self.page_index]
    
    @canvas.setter
    def canvas(self, value):
        self.pages[self.page_index] = value
    
    @property
    def page_count(self):
        return len(self.pages)
    
    def _save_history(self):
        hist = self.histories[self.page_index]
        hist.append(self.canvas.copy())
        if len(hist) > 40:
            hist.pop(0)
        self.redo_stacks[self.page_index].clear()
    
    def draw_point(self, point, drawing_enabled=True):
        x, y = point
        if not drawing_enabled:
            self.prev_point = None
            return point
        
        if self.prev_point:
            self._save_history()
            cv2.line(self.canvas, self.prev_point, (x, y), self.color, self.thickness)
        self.prev_point = (x, y)
        return point
    
    def clear(self):
        self._save_history()
        self.canvas.fill(0)
        self.prev_point = None
    
    def undo(self):
        hist = self.histories[self.page_index]
        redo = self.redo_stacks[self.page_index]
        if hist:
            redo.append(self.canvas.copy())
            self.pages[self.page_index] = hist.pop()
            return True
        return False
    
    def redo(self):
        redo = self.redo_stacks[self.page_index]
        hist = self.histories[self.page_index]
        if redo:
            hist.append(self.canvas.copy())
            self.pages[self.page_index] = redo.pop()
            return True
        return False
    
    def set_color(self, name: str, bgr: tuple):
        self.color = bgr
        self.color_name = name
    
    def set_brush_mode(self, mode: str):
        self.brush_mode = mode
        if mode == "smooth":
            self.thickness = 3
        elif mode == "marker":
            self.thickness = 5
        elif mode == "block":
            self.thickness = 8
    
    def new_page(self):
        new_canvas = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        self.pages.append(new_canvas)
        self.histories.append([])
        self.redo_stacks.append([])
        self.page_index = len(self.pages) - 1
    
    def next_page(self):
        if self.page_index < len(self.pages) - 1:
            self.page_index += 1
        else:
            self.new_page()
    
    def prev_page(self):
        if self.page_index > 0:
            self.page_index -= 1


# Request models
class PointRequest(BaseModel):
    x: int = Field(ge=0)
    y: int = Field(ge=0)
    drawing_enabled: bool = True


class ColorRequest(BaseModel):
    name: str
    bgr: tuple[int, int, int]


class BrushRequest(BaseModel):
    mode: Literal["smooth", "marker", "block"]


# FastAPI app
app = FastAPI(
    title="AirDraw Pro AI API",
    version="1.0.0",
    description="Lightweight API for air drawing"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
lock = Lock()
engine = LightweightDrawingEngine()


@app.get("/")
def root():
    return {
        "message": "AirDraw Pro AI API",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "airdraw-api",
        "timestamp": int(time.time()),
        "memory": "optimized"
    }


@app.get("/state")
def get_state():
    with lock:
        return {
            "tool": engine.tool_name,
            "brush_mode": engine.brush_mode,
            "color_name": engine.color_name,
            "thickness": engine.thickness,
            "eraser_enabled": engine.eraser_enabled,
            "page_index": engine.page_index,
            "page_count": engine.page_count,
            "drag_active": False,
            "size": {"width": engine.width, "height": engine.height},
        }


@app.post("/canvas/clear")
def canvas_clear():
    with lock:
        engine.clear()
    return {"ok": True}


@app.post("/canvas/undo")
def canvas_undo():
    with lock:
        return {"ok": engine.undo()}


@app.post("/canvas/redo")
def canvas_redo():
    with lock:
        return {"ok": engine.redo()}


@app.get("/canvas/image")
def canvas_image(transparent: bool = False, base64_data: bool = True):
    with lock:
        canvas = engine.canvas
        if transparent:
            alpha = (canvas.any(axis=2).astype("uint8")) * 255
            rgba = cv2.cvtColor(canvas, cv2.COLOR_BGR2BGRA)
            rgba[:, :, 3] = alpha
            ok, encoded = cv2.imencode(".png", rgba)
        else:
            ok, encoded = cv2.imencode(".png", canvas)
        
        if not ok:
            raise HTTPException(status_code=500, detail="Failed to encode image")
        
        png = encoded.tobytes()
    
    if base64_data:
        return {"ok": True, "png_base64": base64.b64encode(png).decode("ascii")}
    return {"ok": True, "png_bytes_len": len(png)}


@app.post("/draw/point")
def draw_point(payload: PointRequest):
    with lock:
        p = engine.draw_point((payload.x, payload.y), payload.drawing_enabled)
    return {"ok": True, "point": p}


@app.post("/tool/brush")
def tool_brush(payload: BrushRequest):
    with lock:
        engine.set_brush_mode(payload.mode)
    return {"ok": True}


@app.post("/tool/color")
def tool_color(payload: ColorRequest):
    b, g, r = payload.bgr
    if not all(0 <= v <= 255 for v in (b, g, r)):
        raise HTTPException(status_code=422, detail="bgr values must be 0-255")
    with lock:
        engine.set_color(payload.name, payload.bgr)
    return {"ok": True}


@app.post("/page/new")
def page_new():
    with lock:
        engine.new_page()
    return {"ok": True, "page_index": engine.page_index}


@app.post("/page/next")
def page_next():
    with lock:
        engine.next_page()
    return {"ok": True, "page_index": engine.page_index}


@app.post("/page/prev")
def page_prev():
    with lock:
        engine.prev_page()
    return {"ok": True, "page_index": engine.page_index}


# Keep-alive endpoint for monitoring
@app.get("/ping")
def ping():
    return {"pong": time.time()}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
