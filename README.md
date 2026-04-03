# AirDraw Pro AI

AirDraw Pro AI is a real-time gesture-based air drawing application powered by webcam hand tracking.

## Features

- Real-time hand tracking with MediaPipe (21 landmarks)
- Gesture-driven modes:
  - **DRAW**: only index finger up
  - **PAUSE**: index + middle up
  - **DRAG**: thumb-index pinch to move the full canvas
  - **CLEAR**: all fingers up
- Smooth line rendering using moving-average smoothing + interpolation
- Stable drag behavior with damped and capped movement to avoid sudden jumps
- On-screen UI overlays for mode, FPS, and fingertip indicator
- Bottom in-app command menu showing all keyboard shortcuts
- Keyboard controls for quit, clear, and save
- Professional brush system:
  - **Smooth Brush** for clean curves
  - **Marker Brush** for thick pen-like strokes
  - **Block Brush** for connected pixel/block art drawing
- Full-hand analysis pipeline:
  - Finger count, palm center, hand centroid, and hand span
  - Scale-aware pinch detection using distance + normalized ratio
  - Stable palm-based drag anchor for better select/drag behavior

## Tech Stack

- OpenCV
- MediaPipe
- NumPy

## Project Structure

```text
airdraw/
├── main.py              # Desktop app with webcam
├── api_server.py        # REST API server
├── index.html           # Web frontend
├── hand_tracker.py      # MediaPipe hand tracking
├── gesture_utils.py     # Gesture detection logic
├── drawing_utils.py     # Drawing engine
├── config.py            # Configuration
├── requirements.txt     # Dependencies
└── README.md
```

## Setup

1. Open a terminal in the `airdraw` directory.
2. (Recommended) Create and activate a virtual environment.
3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Run

### Option 1: Desktop Application (Standalone)

```bash
python main.py
```

This runs the full desktop app with webcam, hand tracking, and real-time drawing.

### Option 2: REST API + Web Frontend

**Step 1: Start the API Server**

```bash
uvicorn api_server:app --host 0.0.0.0 --port 8000
```

**Step 2: Open the Web Frontend**

Open `index.html` in your browser:
- Double-click the file, or
- Use VS Code Live Server, or
- Navigate to `file:///C:/Users/sachi/OneDrive/Desktop/Air Visual/airdraw/index.html`

**Step 3: Click "Start Drawing"**

The frontend will connect to the API and display real-time canvas updates.

Then use `http://localhost:8000/docs` for interactive API documentation.

### Core API endpoints

- `GET /health`
- `GET /state`
- `POST /canvas/clear`, `/canvas/undo`, `/canvas/redo`
- `GET /canvas/image?transparent=true&base64_data=true`
- `POST /draw/point`, `/draw/line`, `/draw/circle`
- `POST /drag/start`, `/drag/move`, `/drag/stop`
- `POST /tool/brush`, `/tool/color`, `/tool/eraser`, `/tool/size`
- `POST /page/new`, `/page/next`, `/page/prev`, `/page/delete`

## Controls

- `q` → Quit
- `m` → Toggle fullscreen window
- `c` → Clear canvas
- `s` → Save drawing as PNG in current directory
- `x` → Save transparent PNG (background removed)
- `u` → Undo
- `r` → Redo
- `e` → Toggle eraser tool
- `f` → Free draw assist mode
- `l` → Straight line assist mode
- `o` → Circle assist mode
- `Space` → Commit assisted shape (line/circle)
- `n` → New page
- `[` → Previous page
- `]` → Next page
- `k` → Delete current page
- `1` → Smooth brush
- `2` → Marker brush
- `3` → Block brush (connected blocks)
- `4` → Green color
- `5` → Red color
- `6` → Blue color
- `7` → Yellow color
- `8` → Magenta color
- `9` → White color
- `+` / `=` → Increase brush size
- `-` / `_` → Decrease brush size

### Pro Drag Behavior

- Drag is **left-hand only** to avoid accidental disturbance while writing.
- Raise/open your **left hand** (4-5 fingers up) to trigger stable select-all canvas drag.
- While left hand is open, move it to reposition the full drawing.

### Multi-page + Shapes

- Pages are independent canvases with their own undo/redo histories.
- Line/circle assist shows a live preview while drawing.
- Press `Space` to commit the shape to the current page.

## Usage Tips

- Use good lighting and keep your hand visible.
- Keep gestures deliberate for stable mode switching.
- If the camera does not open, check device permissions and close other camera apps.
- Set `DRAW_ANCHOR_MODE` in `config.py`:
  - `"index"` for fingertip writing
  - `"centroid"` for full-hand writing anchor

