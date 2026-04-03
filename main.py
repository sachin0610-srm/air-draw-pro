"""Main application for AirDraw Pro AI."""
from __future__ import annotations

import os
import time
from typing import Optional

import cv2
import numpy as np

from config import (
    CAMERA_INDEX,
    CANVAS_BLEND_ALPHA,
    CLEAR_COOLDOWN_FRAMES,
    DRAG_DAMPING,
    DRAW_HOLD_FRAMES,
    DRAW_ANCHOR_MODE,
    FRAME_HEIGHT,
    FRAME_WIDTH,
    HAND_LOST_GRACE_FRAMES,
    MODE_CONFIRM_FRAMES,
    MODE_TEXT_COLOR,
    MODE_TEXT_SCALE,
    MODE_TEXT_THICKNESS,
    PALETTE_COLORS,
    TIP_COLOR,
    TIP_RADIUS,
)
from drawing_utils import DrawingEngine
from gesture_utils import (
    analyze_hand,
    is_clear_mode,
    is_draw_mode,
    is_pause_mode,
)
from hand_tracker import HandTracker


def _put_mode_text(
    frame,
    mode: str,
    fps: float,
    brush: str,
    thickness: int,
    color_name: str,
    hand_stats: str,
    tool_name: str,
    assist_mode: str,
    page_text: str,
) -> None:
    h, w = frame.shape[:2]
    label = (
        f"M:{mode} | T:{tool_name.upper()} | A:{assist_mode.upper()} | "
        f"B:{brush.upper()} {thickness} | C:{color_name.upper()} | FPS:{fps:.1f}"
    )
    font = cv2.FONT_HERSHEY_SIMPLEX
    scale = MODE_TEXT_SCALE
    thickness_px = MODE_TEXT_THICKNESS
    max_width = max(40, w - 40)
    text_width = cv2.getTextSize(label, font, scale, thickness_px)[0][0]
    while text_width > max_width and len(label) > 12:
        label = label[:-2] + "…"
        text_width = cv2.getTextSize(label, font, scale, thickness_px)[0][0]

    cv2.putText(
        frame,
        label,
        (20, 40),
        font,
        scale,
        MODE_TEXT_COLOR,
        thickness_px,
        cv2.LINE_AA,
    )
    cv2.putText(
        frame,
        hand_stats,
        (20, 72),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        MODE_TEXT_COLOR,
        2,
        cv2.LINE_AA,
    )
    cv2.putText(
        frame,
        page_text,
        (20, 104),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        MODE_TEXT_COLOR,
        2,
        cv2.LINE_AA,
    )


def _draw_bottom_menu(frame) -> None:
    h, w = frame.shape[:2]
    menu_height = 96
    y0 = max(0, h - menu_height)
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, y0), (w, h), (20, 20, 20), -1)
    cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)

    line1 = "q Quit | c Clear | s Save | x Save Transparent | u Undo | r Redo | e Eraser"
    line2 = "f Free | l Line | o Circle | Space Commit Shape | n NewPg | [ PrevPg | ] NextPg | k DelPg"
    line3 = "1/2/3 Brush | 4..9 Colors | +/- Size"
    cv2.putText(frame, line1, (14, y0 + 26), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (255, 255, 255), 1, cv2.LINE_AA)
    cv2.putText(frame, line2, (14, y0 + 52), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (255, 255, 255), 1, cv2.LINE_AA)
    cv2.putText(frame, line3, (14, y0 + 78), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (255, 255, 255), 1, cv2.LINE_AA)


def _save_canvas(canvas) -> str:
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_name = f"airdraw_{timestamp}.png"
    cv2.imwrite(output_name, canvas)
    return os.path.abspath(output_name)


def _save_transparent_canvas(canvas) -> str:
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_name = f"airdraw_transparent_{timestamp}.png"
    alpha = np.any(canvas != 0, axis=2).astype(np.uint8) * 255
    rgba = np.dstack((canvas, alpha))
    cv2.imwrite(output_name, rgba)
    return os.path.abspath(output_name)


def _fit_frame_to_window(frame, window_name: str):
    """Fit frame into current window size without cropping (letterbox if needed)."""
    try:
        _, _, win_w, win_h = cv2.getWindowImageRect(window_name)
    except Exception:
        return frame

    if win_w <= 0 or win_h <= 0:
        return frame

    src_h, src_w = frame.shape[:2]
    scale = min(win_w / src_w, win_h / src_h)
    new_w = max(1, int(src_w * scale))
    new_h = max(1, int(src_h * scale))

    resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
    canvas = np.zeros((win_h, win_w, 3), dtype=np.uint8)
    x0 = (win_w - new_w) // 2
    y0 = (win_h - new_h) // 2
    canvas[y0 : y0 + new_h, x0 : x0 + new_w] = resized
    return canvas


def main() -> None:
    window_name = "AirDraw Pro AI"
    cap = cv2.VideoCapture(CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

    if not cap.isOpened():
        raise RuntimeError("Unable to open webcam. Check camera permissions and camera usage.")

    tracker = HandTracker()
    drawer: Optional[DrawingEngine] = None
    fullscreen = False

    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, FRAME_WIDTH, FRAME_HEIGHT)

    mode = "PAUSE"
    candidate_mode = mode
    candidate_count = 0
    clear_cooldown = 0
    prev_time = time.time()
    drag_active = False
    dominant_handedness: Optional[str] = None
    no_hand_streak = 0
    drag_point = None
    hand_stats = "Hand: none"
    draw_hold_count = 0
    last_draw_point = None
    assist_mode = "free"
    assist_anchor = None

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                continue

            frame = cv2.flip(frame, 1)
            height, width = frame.shape[:2]

            if drawer is None:
                drawer = DrawingEngine(width=width, height=height)

            hands = tracker.process(frame, draw_landmarks=False)

            if not hands:
                no_hand_streak += 1
                raw_mode = "PAUSE"
                hand_stats = "Hand: none"
                if mode == "DRAW" and draw_hold_count < DRAW_HOLD_FRAMES:
                    draw_hold_count += 1
                    raw_mode = "DRAW"
                else:
                    drawer.reset_stroke()
                if drag_active and no_hand_streak >= HAND_LOST_GRACE_FRAMES:
                    drawer.stop_drag()
                    drag_active = False
            else:
                no_hand_streak = 0
                drag_point = None
                if dominant_handedness is None:
                    dominant_handedness = hands[0].handedness

                preferred = None
                for h in hands:
                    if h.handedness == dominant_handedness:
                        preferred = h
                        break
                if preferred is None:
                    preferred = max(
                        hands,
                        key=lambda h: (h.bbox[2] - h.bbox[0]) * (h.bbox[3] - h.bbox[1]),
                    )
                    dominant_handedness = preferred.handedness

                primary_hand = preferred
                landmarks = primary_hand.landmarks
                hand_info = analyze_hand(landmarks, primary_hand.handedness)
                finger_state = hand_info.fingers

                hand_stats = (
                    f"Fingers: {hand_info.finger_count} | "
                    f"PinchRatio: {hand_info.pinch_ratio:.2f} | "
                    f"Span: {int(hand_info.hand_span)}"
                )

                left_hand = next((h for h in hands if h.handedness == "Left"), None)
                left_drag_active = False
                if left_hand is not None:
                    left_info = analyze_hand(left_hand.landmarks, left_hand.handedness)
                    left_drag_active = left_info.finger_count >= 4
                    if left_drag_active:
                        # Use left palm center as stable anchor for select-all drag.
                        drag_point = left_info.palm_center

                # Priority: CLEAR > DRAG > DRAW > PAUSE
                clear_active = is_clear_mode(finger_state)

                draw_active = is_draw_mode(finger_state)
                pause_active = is_pause_mode(finger_state)

                if clear_cooldown > 0:
                    clear_cooldown -= 1

                if clear_active and clear_cooldown == 0:
                    raw_mode = "CLEAR"
                elif left_drag_active:
                    raw_mode = "DRAG"
                elif draw_active:
                    raw_mode = "DRAW"
                elif pause_active:
                    raw_mode = "PAUSE"
                else:
                    if mode == "DRAW" and draw_hold_count < DRAW_HOLD_FRAMES:
                        draw_hold_count += 1
                        raw_mode = "DRAW"
                    else:
                        raw_mode = "PAUSE"
                        draw_hold_count = 0

                if raw_mode == "DRAG" and drag_point is not None:
                    cv2.circle(frame, drag_point, TIP_RADIUS, TIP_COLOR, -1)

            if raw_mode == candidate_mode:
                candidate_count += 1
            else:
                candidate_mode = raw_mode
                candidate_count = 1

            if candidate_count >= MODE_CONFIRM_FRAMES:
                mode = candidate_mode

            if mode == "CLEAR":
                drawer.clear()
                drag_active = False
                clear_cooldown = CLEAR_COOLDOWN_FRAMES
                mode = "PAUSE"
            elif mode == "DRAG" and hands and drag_point is not None:
                if not drag_active:
                    drawer.start_drag(drag_point)
                    drag_active = True
                else:
                    drawer.drag_canvas(drag_point, damping=DRAG_DAMPING)
                drawer.reset_stroke()
            elif mode == "DRAW" and hands:
                draw_hold_count = 0
                if drag_active:
                    drawer.stop_drag()
                    drag_active = False
                if dominant_handedness is not None:
                    active_hand = next(
                        (h for h in hands if h.handedness == dominant_handedness),
                        hands[0],
                    )
                else:
                    active_hand = hands[0]
                active_info = analyze_hand(active_hand.landmarks, active_hand.handedness)
                draw_point = (
                    active_hand.landmarks[8]
                    if DRAW_ANCHOR_MODE == "index"
                    else active_info.centroid
                )
                last_draw_point = draw_point
                if assist_mode == "line":
                    if assist_anchor is None:
                        assist_anchor = draw_point
                    cv2.line(
                        frame,
                        assist_anchor,
                        draw_point,
                        TIP_COLOR,
                        max(1, drawer.thickness),
                        lineType=cv2.LINE_AA,
                    )
                    cv2.circle(frame, draw_point, TIP_RADIUS, TIP_COLOR, -1)
                elif assist_mode == "circle":
                    if assist_anchor is None:
                        assist_anchor = draw_point
                    radius = max(1, int(((draw_point[0] - assist_anchor[0]) ** 2 + (draw_point[1] - assist_anchor[1]) ** 2) ** 0.5))
                    cv2.circle(frame, assist_anchor, radius, TIP_COLOR, max(1, drawer.thickness), lineType=cv2.LINE_AA)
                    cv2.circle(frame, draw_point, TIP_RADIUS, TIP_COLOR, -1)
                else:
                    processed_point = drawer.draw_point(draw_point, drawing_enabled=True)
                    if processed_point is not None:
                        cv2.circle(frame, processed_point, TIP_RADIUS, TIP_COLOR, -1)
                    else:
                        cv2.circle(frame, draw_point, TIP_RADIUS, TIP_COLOR, -1)
            elif mode == "DRAW" and not hands and last_draw_point is not None:
                cv2.circle(frame, last_draw_point, TIP_RADIUS, TIP_COLOR, -1)
            else:
                if drag_active:
                    drawer.stop_drag()
                    drag_active = False
                draw_hold_count = 0
                last_draw_point = None
                assist_anchor = None
                drawer.reset_stroke()

            blended = drawer.overlay_on(frame, alpha=CANVAS_BLEND_ALPHA)

            now = time.time()
            fps = 1.0 / max(now - prev_time, 1e-6)
            prev_time = now
            _put_mode_text(
                blended,
                mode,
                fps,
                drawer.brush_mode,
                drawer.thickness,
                drawer.color_name,
                hand_stats,
                drawer.tool_name,
                assist_mode,
                f"Page: {drawer.page_index + 1}/{drawer.page_count}",
            )
            _draw_bottom_menu(blended)

            display = _fit_frame_to_window(blended, window_name)
            cv2.imshow(window_name, display)
            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                break
            if key == ord("m"):
                fullscreen = not fullscreen
                cv2.setWindowProperty(
                    window_name,
                    cv2.WND_PROP_FULLSCREEN,
                    cv2.WINDOW_FULLSCREEN if fullscreen else cv2.WINDOW_NORMAL,
                )
            if key == ord("c") and drawer is not None:
                drawer.clear()
            if key == ord("s") and drawer is not None:
                saved_path = _save_canvas(drawer.canvas)
                print(f"Saved drawing: {saved_path}")
            if key == ord("x") and drawer is not None:
                transparent_path = _save_transparent_canvas(drawer.canvas)
                print(f"Saved transparent drawing: {transparent_path}")
            if key == ord("u") and drawer is not None:
                drawer.undo()
            if key == ord("r") and drawer is not None:
                drawer.redo()
            if key == ord("e") and drawer is not None:
                drawer.set_eraser(not drawer.eraser_enabled)
            if key == ord("l"):
                assist_mode = "line"
                assist_anchor = None
            if key == ord("o"):
                assist_mode = "circle"
                assist_anchor = None
            if key == ord("f"):
                assist_mode = "free"
                assist_anchor = None
            if key == ord("n") and drawer is not None:
                drawer.new_page()
            if key == ord("]") and drawer is not None:
                drawer.next_page()
            if key == ord("[") and drawer is not None:
                drawer.prev_page()
            if key == ord("k") and drawer is not None:
                drawer.delete_current_page()
            if key == ord("1") and drawer is not None:
                drawer.set_brush_mode("smooth")
            if key == ord("2") and drawer is not None:
                drawer.set_brush_mode("marker")
            if key == ord("3") and drawer is not None:
                drawer.set_brush_mode("block")
            if key in (ord("+"), ord("=")) and drawer is not None:
                drawer.increase_thickness()
            if key in (ord("-"), ord("_")) and drawer is not None:
                drawer.decrease_thickness()
            if key == ord("4") and drawer is not None:
                drawer.set_color("green", PALETTE_COLORS["green"])
            if key == ord("5") and drawer is not None:
                drawer.set_color("red", PALETTE_COLORS["red"])
            if key == ord("6") and drawer is not None:
                drawer.set_color("blue", PALETTE_COLORS["blue"])
            if key == ord("7") and drawer is not None:
                drawer.set_color("yellow", PALETTE_COLORS["yellow"])
            if key == ord("8") and drawer is not None:
                drawer.set_color("magenta", PALETTE_COLORS["magenta"])
            if key == ord("9") and drawer is not None:
                drawer.set_color("white", PALETTE_COLORS["white"])
            if mode == "DRAW" and assist_mode in {"line", "circle"} and key == 32 and drawer is not None:
                if assist_anchor is not None and last_draw_point is not None:
                    if assist_mode == "line":
                        drawer.draw_assisted_line(assist_anchor, last_draw_point)
                    else:
                        drawer.draw_assisted_circle(assist_anchor, last_draw_point)
                    assist_anchor = None
    finally:
        cap.release()
        tracker.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()

