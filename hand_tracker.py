"""Hand tracking module using MediaPipe."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

import cv2
import mediapipe as mp

from config import (
    MAX_NUM_HANDS,
    MIN_DETECTION_CONFIDENCE,
    MIN_TRACKING_CONFIDENCE,
)

Point = Tuple[int, int]
BBox = Tuple[int, int, int, int]


@dataclass
class HandData:
    """Structured hand result for one detected hand."""

    landmarks: List[Point]
    bbox: BBox
    handedness: str


class HandTracker:
    """MediaPipe-backed hand tracker for frame-by-frame processing."""

    def __init__(
        self,
        max_num_hands: int = MAX_NUM_HANDS,
        min_detection_confidence: float = MIN_DETECTION_CONFIDENCE,
        min_tracking_confidence: float = MIN_TRACKING_CONFIDENCE,
    ) -> None:
        self._mp_hands = mp.solutions.hands
        self._hands = self._mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=max_num_hands,
            model_complexity=1,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )
        self._drawer = mp.solutions.drawing_utils

    def close(self) -> None:
        """Release MediaPipe resources."""
        self._hands.close()

    def process(self, frame_bgr, draw_landmarks: bool = False) -> List[HandData]:
        """Process a BGR frame and return list of detected hands."""
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        results = self._hands.process(frame_rgb)

        if not results.multi_hand_landmarks:
            return []

        image_h, image_w = frame_bgr.shape[:2]
        hands_output: List[HandData] = []

        for i, hand_landmarks in enumerate(results.multi_hand_landmarks):
            points: List[Point] = []
            xs: List[int] = []
            ys: List[int] = []

            for lm in hand_landmarks.landmark:
                x = int(lm.x * image_w)
                y = int(lm.y * image_h)
                points.append((x, y))
                xs.append(x)
                ys.append(y)

            x_min = max(min(xs), 0)
            y_min = max(min(ys), 0)
            x_max = min(max(xs), image_w - 1)
            y_max = min(max(ys), image_h - 1)
            bbox: BBox = (x_min, y_min, x_max, y_max)

            handedness_label = "Unknown"
            if results.multi_handedness and i < len(results.multi_handedness):
                handedness_label = results.multi_handedness[i].classification[0].label

            hands_output.append(
                HandData(
                    landmarks=points,
                    bbox=bbox,
                    handedness=handedness_label,
                )
            )

            if draw_landmarks:
                self._drawer.draw_landmarks(
                    frame_bgr,
                    hand_landmarks,
                    self._mp_hands.HAND_CONNECTIONS,
                )

        return hands_output

