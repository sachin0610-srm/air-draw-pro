# AirDraw Pro AI V2

AirDraw Pro AI is a real-time gesture-based air drawing application. In **Version 2**, it has been completely rewritten into a **100% standalone WebAssembly application** that runs entirely client-side. No Python backend required!

## Features (V2 Web App)

- **100% Client-Side**: Hand tracking runs entirely in the browser using MediaPipe Tasks Vision JS SDK.
- Real-time hand tracking (21 landmarks)
- Gesture-driven modes:
  - **DRAW**: only index finger up
  - **PAUSE**: index + middle up
  - **CLEAR**: all fingers up
- Smooth HTML5 Canvas drawing engine with history tracking
- On-screen UI overlays for mode, brush, page, and size
- Interactive toolbars and keyboard shortcuts
- Professional brush system:
  - **Smooth Brush** for clean curves
  - **Marker Brush** for thick pen-like strokes
  - **Block Brush** for connected pixel/block art drawing
- **Undo/Redo System**: Memory-managed `ImageData` stack holding 40 history levels per page.
- **Save & Export**: Download drawings natively straight to your desktop.

## Tech Stack

- **Frontend**: HTML, CSS, JavaScript (Vanilla)
- **Computer Vision**: `@mediapipe/tasks-vision` (WebAssembly)
- **Canvas Rendering**: HTML5 Canvas 2D Context

## Project Structure

```text
airdraw/
├── index.html           # V2 Web App (Core file, zero-server)
├── main.py              # V1 Legacy Desktop app (Python/OpenCV)
├── api_server.py        # V1 Legacy API server
├── ...                  # Other legacy V1 python modules
└── README.md
```

## Setup & Run (V2)

Because V2 runs completely in the browser, there is **no setup required**!

1. Simply double-click `index.html` to open it in Chrome, Edge, or Firefox.
2. OR run a local server (e.g. `npx serve` or `python -m http.server`) for optimal WebAssembly loading.
3. Click **"Start Drawing"** and allow Camera permissions.

## Controls (V2)

- `c` → Clear canvas
- `u` → Undo
- `r` → Redo
- `e` → Toggle eraser tool
- `s` → Save drawing as PNG
- `-` / `_` → Decrease brush size
- `+` / `=` → Increase brush size

*(Legacy Python shortcuts apply to `main.py` if running locally via OpenCV)*

## Usage Tips

- Use good lighting and keep your hand visible.
- Keep gestures deliberate for stable mode switching.
- Ensure no other applications are using your webcam before pressing Start Drawing.
