"""Gesture detection utilities for AirDraw Pro AI."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence, Tuple

import numpy as np

Point = Tuple[int, int]

TIP_IDS = [4, 8, 12, 16, 20]
PIP_IDS = [2, 6, 10, 14, 18]


def _euclidean(a: Point, b: Point) -> float:
    return float(np.hypot(a[0] - b[0], a[1] - b[1]))


@dataclass
class HandAnalysis:
    """Full-hand analysis output used by control logic."""

    fingers: List[bool]
    finger_count: int
    palm_center: Point
    centroid: Point
    hand_span: float
    pinch_distance: float
    pinch_ratio: float


def fingers_up(landmarks: Sequence[Point], handedness: str = "Right") -> List[bool]:
    """Return finger state as [thumb, index, middle, ring, pinky]."""
    if len(landmarks) < 21:
        return [False, False, False, False, False]

    fingers = [False, False, False, False, False]

    # Thumb depends on hand side (x-axis comparison in mirrored camera view)
    thumb_tip_x = landmarks[TIP_IDS[0]][0]
    thumb_ip_x = landmarks[3][0]
    if handedness.lower() == "right":
        fingers[0] = thumb_tip_x > thumb_ip_x
    elif handedness.lower() == "left":
        fingers[0] = thumb_tip_x < thumb_ip_x
    else:
        fingers[0] = abs(thumb_tip_x - thumb_ip_x) > 18

    # Other fingers: tip is above pip in image coordinates
    for idx in range(1, 5):
        tip_y = landmarks[TIP_IDS[idx]][1]
        pip_y = landmarks[PIP_IDS[idx]][1]
        fingers[idx] = tip_y < pip_y

    return fingers


def is_draw_mode(fingers: Sequence[bool]) -> bool:
    """Draw mode: index up, middle/ring/pinky down (thumb ignored for robustness)."""
    return (
        len(fingers) == 5
        and fingers[1]
        and not fingers[2]
        and not fingers[3]
        and not fingers[4]
    )


def is_pause_mode(fingers: Sequence[bool]) -> bool:
    """Pause mode: index + middle up, ring + pinky down (thumb ignored)."""
    return (
        len(fingers) == 5
        and fingers[1]
        and fingers[2]
        and not fingers[3]
        and not fingers[4]
    )


def is_clear_mode(fingers: Sequence[bool]) -> bool:
    """Clear mode: all fingers up."""
    return len(fingers) == 5 and all(fingers)


def is_pinch(landmarks: Sequence[Point], pinch_distance_threshold: float) -> bool:
    """Pinch mode: thumb tip close to index tip."""
    if len(landmarks) < 21:
        return False

    thumb_tip = landmarks[4]
    index_tip = landmarks[8]
    distance = _euclidean(thumb_tip, index_tip)
    return distance <= pinch_distance_threshold


def analyze_hand(landmarks: Sequence[Point], handedness: str = "Right") -> HandAnalysis:
    """Compute full-hand geometric and finger-state features."""
    if len(landmarks) < 21:
        empty = [False, False, False, False, False]
        return HandAnalysis(
            fingers=empty,
            finger_count=0,
            palm_center=(0, 0),
            centroid=(0, 0),
            hand_span=1.0,
            pinch_distance=9999.0,
            pinch_ratio=9999.0,
        )

    finger_state = fingers_up(landmarks, handedness)
    finger_count = int(sum(finger_state))

    palm_ids = [0, 1, 2, 5, 9, 13, 17]
    palm_x = [landmarks[i][0] for i in palm_ids]
    palm_y = [landmarks[i][1] for i in palm_ids]
    palm_center = (int(np.mean(palm_x)), int(np.mean(palm_y)))

    all_x = [p[0] for p in landmarks]
    all_y = [p[1] for p in landmarks]
    centroid = (int(np.mean(all_x)), int(np.mean(all_y)))

    xs = np.array(all_x, dtype=np.float32)
    ys = np.array(all_y, dtype=np.float32)
    hand_span = float(max(xs.max() - xs.min(), ys.max() - ys.min(), 1.0))

    pinch_distance = _euclidean(landmarks[4], landmarks[8])
    pinch_ratio = float(pinch_distance / hand_span)

    return HandAnalysis(
        fingers=finger_state,
        finger_count=finger_count,
        palm_center=palm_center,
        centroid=centroid,
        hand_span=hand_span,
        pinch_distance=pinch_distance,
        pinch_ratio=pinch_ratio,
    )

