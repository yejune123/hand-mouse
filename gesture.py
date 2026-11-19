"""Thumb/index midpoint pointer and pinch click/scroll logic."""
from __future__ import annotations

from dataclasses import dataclass
from math import hypot


@dataclass
class Settings:
    camera: int = 0
    pointer_mode: str = "���������� ����"
    sensitivity: float = 1.0
    movement_mode: str = "�� �̵���"
    smoothing: float = 0.35
    pinch_ratio: float = 0.42
    scroll_threshold: float = 0.025
    scroll_sensitivity: float = 1.0
    scroll_direction: str = "�հ� ���� ����"
    stop_key: str = "F8"
    pause_on_external: bool = True


def distance(a, b):
    return hypot(a.x - b.x, a.y - b.y)


def pointer_target(x, y, previous, current, screen, settings):
    """Map a detected point to a desktop position using the chosen mode."""
    rx, ry, width, height = screen
    if settings.movement_mode == "ȭ�� ��ġ":
        sx = max(0.0, min(1.0, (x - 0.12) / 0.76))
        sy = max(0.0, min(1.0, (y - 0.12) / 0.76))
        sx = max(0.0, min(1.0, 0.5 + (sx - 0.5) * settings.sensitivity))
        sy = max(0.0, min(1.0, 0.5 + (sy - 0.5) * settings.sensitivity))
        return rx + sx * (width - 1), ry + sy * (height - 1)
    if previous is None:
        return current
    gain = settings.sensitivity / 0.76
    return (max(rx, min(rx + width - 1, current[0] + (x - previous[0]) * width * gain)),
            max(ry, min(ry + height - 1, current[1] + (y - previous[1]) * height * gain)))


class GestureEngine:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.pinching = False
        self.scroll_y = None
        self.pinch_y = None
        self.scrolled = False
        self.missing_since = None
        self.pinch_started_at = None
        self.clicked = False

    def reset(self):
        self.pinching = False
        self.scroll_y = None
        self.pinch_y = None
        self.scrolled = False
        self.missing_since = None
        self.pinch_started_at = None
        self.clicked = False
        return []

    def update(self, p, now):
        if not p:
            if not self.pinching:
                return []
            if self.missing_since is None:
                self.missing_since = now
            elif now - self.missing_since >= 0.25:
                click = not self.scrolled and not self.clicked
                self.reset()
                return [("left_click",)] if click else []
            return []
        self.missing_since = None
        s = self.settings
        thumb, index = p[4], p[8]
        mid_x = (thumb.x + index.x) / 2
        mid_y = (thumb.y + index.y) / 2
        palm = max(distance(p[0], p[9]), 0.04)
        ratio = distance(thumb, index) / palm
        # A wider release threshold prevents one noisy frame from ending a pinch.
        pinched = ratio < s.pinch_ratio * (1.35 if self.pinching else 1.0)
        if s.pointer_mode == "���� ��":
            pointer = (thumb.x, thumb.y)
        else:
            pointer = (mid_x, mid_y)
        actions = [("move", *pointer)]
        if pinched:
            if not self.pinching:
                self.pinching = True
                self.scroll_y = mid_y
                self.pinch_y = mid_y
                self.scrolled = False
                self.pinch_started_at = now
                self.clicked = False
            else:
                # Ignore normal hand jitter until there is a deliberate move.
                if not self.scrolled and abs(mid_y - self.pinch_y) >= 0.09:
                    self.scrolled = True
                    self.scroll_y = mid_y
                elif self.scrolled:
                    delta = self.scroll_y - mid_y
                    direction = -1 if s.scroll_direction == "�հ� �ݴ� ����" else 1
                    steps = int(direction * delta * s.scroll_sensitivity / s.scroll_threshold)
                    if steps:
                        actions.append(("scroll", max(-5, min(5, steps))))
                        self.scroll_y = mid_y
                if not self.scrolled and not self.clicked and now - self.pinch_started_at >= 0.20:
                    actions.append(("left_click",))
                    self.clicked = True
        elif self.pinching:
            if not self.scrolled and not self.clicked:
                # Click at the last pinched position, before the separating
                # fingers pull the pointer away from the intended target.
                actions.insert(0, ("left_click",))
            self.reset()
        return actions
