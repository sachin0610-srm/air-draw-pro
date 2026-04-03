"""Configuration for AirDraw Pro AI."""

# Camera
CAMERA_INDEX = 0
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720

# Hand tracking
MAX_NUM_HANDS = 2
MIN_DETECTION_CONFIDENCE = 0.78
MIN_TRACKING_CONFIDENCE = 0.72

# Gesture thresholds
# Pixel distance between thumb tip and index tip for pinch detection
PINCH_DISTANCE_THRESHOLD = 38
PINCH_RELEASE_MULTIPLIER = 1.5
PINCH_RATIO_THRESHOLD = 0.33

# Mode stability (frame counts)
MODE_CONFIRM_FRAMES = 4
CLEAR_COOLDOWN_FRAMES = 18
HAND_LOST_GRACE_FRAMES = 4
DRAW_HOLD_FRAMES = 5

# Drawing
DRAW_COLOR = (0, 255, 0)  # BGR
DRAW_THICKNESS = 6
SMOOTHING_WINDOW = 5
INTERPOLATION_STEP_PIXELS = 2
MIN_DRAW_MOVEMENT_PIXELS = 2
DRAW_ANCHOR_MODE = "index"  # index | centroid

# Drag behavior
DRAG_DAMPING = 0.45
MAX_DRAG_STEP = 24

# UI
TIP_COLOR = (0, 0, 255)  # BGR
TIP_RADIUS = 8
MODE_TEXT_COLOR = (255, 255, 255)
MODE_TEXT_SCALE = 1.0
MODE_TEXT_THICKNESS = 2
CANVAS_BLEND_ALPHA = 0.65

# Preset colors (BGR) for hotkeys 4-9
PALETTE_COLORS = {
    "green": (0, 255, 0),
    "red": (0, 0, 255),
    "blue": (255, 0, 0),
    "yellow": (0, 255, 255),
    "magenta": (255, 0, 255),
    "white": (255, 255, 255),
}

