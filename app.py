"""Windows camera hand mouse."""
from __future__ import annotations

import json
import os
import queue
import sys
import threading
import time
from dataclasses import asdict
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox

APP_DIR = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "HandMouse"
APP_DIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(APP_DIR / "matplotlib"))

import cv2
import mediapipe as mp
from PIL import Image, ImageTk

from gesture import GestureEngine, Settings, pointer_target
import mouse_win


def resource(name):
    return Path(getattr(sys, "_MEIPASS", Path(__file__).parent)) / name


def load_settings():
    try:
        data = json.loads((APP_DIR / "settings.json").read_text(encoding="utf-8"))
        valid = Settings.__dataclass_fields__
        values = {k: v for k, v in data.items() if k in valid}
        if "pointer_mode" not in data:
            values.pop("pinch_ratio", None)
        s = Settings(**values)
        if s.pointer_mode not in ("���������� ����", "���� ��"):
            s.pointer_mode = "���������� ����"
        if s.movement_mode not in ("�� �̵���", "ȭ�� ��ġ"):
            s.movement_mode = "�� �̵���"
        if s.scroll_direction not in ("�հ� ���� ����", "�հ� �ݴ� ����"):
            s.scroll_direction = "�հ� ���� ����"
        if s.stop_key not in [f"F{i}" for i in range(1, 13)]:
            s.stop_key = "F8"
        return s
    except (OSError, ValueError, TypeError):
        return Settings()


def save_settings(s):
    (APP_DIR / "settings.json").write_text(
        json.dumps(asdict(s), ensure_ascii=False, indent=2), encoding="utf-8"
    )


class App:
    def __init__(self):
        self.settings = load_settings()
        self.root = tk.Tk()
        self.root.title("�� �ν� ���콺")
        self.root.geometry("800x780")
        self.root.minsize(720, 700)
        self.root.configure(bg="#f4f6f9")
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.running = threading.Event()
        self.events = queue.Queue(maxsize=2)
        self.worker = None
        self.preview_image = None
        self.stop_key_was_down = False
        self.watcher = None
        self.active_settings = self.settings
        self.last_click_at = 0.0
        self.stop_reason = None
        self._build_ui()
        self.root.after(35, self.poll)

    def _build_ui(self):
        outer = ttk.Frame(self.root, padding=18)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text="�� �ν� ���콺", font=("Malgun Gothic", 19, "bold")).pack(anchor="w")
        ttk.Label(outer, text="Ŀ�� ��ġ ���� �� ������ ������ ���̸� Ŭ�� �� ���� ä ����� ���Ʒ��� �����̸� ��ũ��", wraplength=700).pack(anchor="w", pady=(5, 12))
        self.status = tk.StringVar(value="ī�޶� ������ �ּ���. ������ ���� ����Ű�� ������ ���� �� �ֽ��ϴ�.")
        ttk.Label(outer, textvariable=self.status, foreground="#194c90", wraplength=700).pack(anchor="w", pady=(0, 9))
        self.preview = tk.Label(outer, bg="#17202b", fg="white", text="ī�޶� �̸�����", width=85, height=18)
        self.preview.pack(fill="both", expand=True)

        bar = ttk.Frame(outer)
        bar.pack(fill="x", pady=(12, 8))
        self.start_button = ttk.Button(bar, text="ī�޶� ����", command=self.start)
        self.start_button.pack(side="left")
        self.stop_button = ttk.Button(bar, text="����", command=self.stop, state="disabled")
        self.stop_button.pack(side="left", padx=8)
        self.hotkey_hint = tk.StringVar(value=f"��� ����: {self.settings.stop_key}")
        ttk.Label(bar, textvariable=self.hotkey_hint).pack(side="right")

        panel = ttk.LabelFrame(outer, text="����", padding=12)
        panel.pack(fill="x")
        self.camera = tk.StringVar(value=str(self.settings.camera))
        self.pointer_mode = tk.StringVar(value=self.settings.pointer_mode)
        self.movement_mode = tk.StringVar(value=self.settings.movement_mode)
        self.sensitivity = tk.DoubleVar(value=self.settings.sensitivity)
        self.smoothing = tk.DoubleVar(value=self.settings.smoothing)
        self.pinch_ratio = tk.DoubleVar(value=self.settings.pinch_ratio)
        self.scroll_sensitivity = tk.DoubleVar(value=self.settings.scroll_sensitivity)
        self.scroll_direction = tk.StringVar(value=self.settings.scroll_direction)
        self.stop_key = tk.StringVar(value=self.settings.stop_key)
        self.pause_on_external = tk.BooleanVar(value=self.settings.pause_on_external)
        ttk.Label(panel, text="ī�޶� ��ȣ").grid(row=0, column=0, sticky="w", pady=5)
        ttk.Combobox(panel, textvariable=self.camera, values=["0", "1", "2", "3"], width=7, state="readonly").grid(row=0, column=1, sticky="w")
        ttk.Label(panel, text="�հ��� ���� ����").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Scale(panel, from_=0.25, to=0.75, variable=self.pinch_ratio, orient="horizontal", length=170).grid(row=1, column=1, sticky="w")
        ttk.Label(panel, text="Ŀ�� ��ġ").grid(row=2, column=0, sticky="w", pady=5)
        ttk.Combobox(panel, textvariable=self.pointer_mode, values=["���������� ����", "���� ��"], width=16, state="readonly").grid(row=2, column=1, sticky="w")
        ttk.Label(panel, text="Ŀ�� �̵� ���").grid(row=5, column=0, sticky="w", pady=5)
        ttk.Combobox(panel, textvariable=self.movement_mode, values=["�� �̵���", "ȭ�� ��ġ"], width=16, state="readonly").grid(row=5, column=1, sticky="w")
        ttk.Label(panel, text="�̵� �ӵ� (�� �̵��� ����)").grid(row=0, column=2, sticky="w", padx=(24, 0))
        ttk.Scale(panel, from_=0.2, to=3.0, variable=self.sensitivity, orient="horizontal", length=170).grid(row=0, column=3)
        self.speed_value = ttk.Label(panel, width=5)
        self.speed_value.grid(row=0, column=4)
        self.sensitivity.trace_add("write", lambda *_: self.speed_value.configure(text=f"{self.sensitivity.get():.1f}��"))
        self.speed_value.configure(text=f"{self.sensitivity.get():.1f}��")
        ttk.Label(panel, text="�ε巴��").grid(row=1, column=2, sticky="w", padx=(24, 0))
        ttk.Scale(panel, from_=0.1, to=0.8, variable=self.smoothing, orient="horizontal", length=170).grid(row=1, column=3)
        ttk.Button(panel, text="���� ����", command=self.save).grid(row=2, column=3, sticky="e")
        ttk.Label(panel, text="��ũ�� ����").grid(row=3, column=0, sticky="w", pady=5)
        ttk.Combobox(panel, textvariable=self.scroll_direction, values=["�հ� ���� ����", "�հ� �ݴ� ����"], width=16, state="readonly").grid(row=3, column=1, sticky="w")
        ttk.Label(panel, text="��ũ�� ����").grid(row=3, column=2, sticky="w", padx=(24, 0))
        ttk.Scale(panel, from_=0.2, to=3.0, variable=self.scroll_sensitivity, orient="horizontal", length=170).grid(row=3, column=3)
        self.scroll_value = ttk.Label(panel, width=5)
        self.scroll_value.grid(row=3, column=4)
        self.scroll_sensitivity.trace_add("write", lambda *_: self.scroll_value.configure(text=f"{self.scroll_sensitivity.get():.1f}��"))
        self.scroll_value.configure(text=f"{self.scroll_sensitivity.get():.1f}��")
        ttk.Label(panel, text="���� ����Ű").grid(row=4, column=0, sticky="w", pady=5)
        ttk.Combobox(panel, textvariable=self.stop_key, values=[f"F{i}" for i in range(1, 13)], width=7, state="readonly").grid(row=4, column=1, sticky="w")
        ttk.Checkbutton(panel, text="���콺����ġ�е� �Է� �� ��� ����", variable=self.pause_on_external).grid(row=4, column=2, columnspan=3, sticky="w", padx=(24, 0))
        ttk.Label(outer, text="ī�޶� ������ PC �ȿ����� ó���Ǹ� �����ϰų� �������� �ʽ��ϴ�. �ֺ��� ��� ���� ȭ�� �ȿ� ���̵��� �� �ּ���.", wraplength=700).pack(anchor="w", pady=(10, 0))

    def save(self):
        self.settings.camera = int(self.camera.get())
        self.settings.pointer_mode = self.pointer_mode.get()
        self.settings.movement_mode = self.movement_mode.get()
        self.settings.sensitivity = float(self.sensitivity.get())
        self.settings.smoothing = float(self.smoothing.get())
        self.settings.pinch_ratio = float(self.pinch_ratio.get())
        self.settings.scroll_direction = self.scroll_direction.get()
        self.settings.scroll_sensitivity = float(self.scroll_sensitivity.get())
        self.settings.stop_key = self.stop_key.get()
        self.settings.pause_on_external = bool(self.pause_on_external.get())
        save_settings(self.settings)
        self.hotkey_hint.set(f"��� ����: {self.settings.stop_key}")
        self.status.set("������ �����߽��ϴ�. ���� ���̾��ٸ� �ٽ� �����ϸ� ����˴ϴ�.")
        return True

    def start(self):
        if self.worker is not None and self.worker.is_alive():
            self.status.set("���� ī�޶� ����Ǵ� ���Դϴ�. ��� �� �ٽ� ������ �ּ���.")
            return
        if not self.save():
            return
        if self.running.is_set():
            return
        self.running.set()
        self.stop_reason = None
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.status.set("ī�޶� ���� ��...")
        settings = Settings(**asdict(self.settings))
        self.active_settings = settings
        self.stop_key_was_down = False
        if settings.pause_on_external:
            self.watcher = mouse_win.PhysicalMouseWatcher()
            try:
                self.watcher.start()
            except OSError as exc:
                self.watcher = None
                self.status.set(str(exc))
        self.worker = threading.Thread(target=self.camera_loop, args=(settings,), daemon=True)
        self.worker.start()

    def stop(self, reason=None):
        self.running.clear()
        self.stop_reason = reason
        if self.watcher:
            self.watcher.stop()
            self.watcher = None
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="disabled")
        self.status.set(reason or "ī�޶� �����ϴ� ���Դϴ�...")

    def put_event(self, item):
        try:
            if self.events.full():
                self.events.get_nowait()
            self.events.put_nowait(item)
        except queue.Empty:
            pass

    def camera_loop(self, settings):
        cap = None
        engine = GestureEngine(settings)
        smooth = None
        pointer_last = None
        target = None
        try:
            for backend in (cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY):
                cap = cv2.VideoCapture(settings.camera, backend)
                if cap.isOpened():
                    break
                cap.release()
            if not cap.isOpened():
                raise RuntimeError("ī�޶� �� �� �����ϴ�. Windows ī�޶� ���Ѱ� ī�޶� ��ȣ�� Ȯ���� �ּ���.")
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            model = resource("assets/hand_landmarker.task").read_bytes()
            options = mp.tasks.vision.HandLandmarkerOptions(
                base_options=mp.tasks.BaseOptions(model_asset_buffer=model),
                running_mode=mp.tasks.vision.RunningMode.VIDEO,
                num_hands=1,
            )
            with mp.tasks.vision.HandLandmarker.create_from_options(options) as landmarker:
                started = time.monotonic()
                last_ms = -1
                while self.running.is_set():
                    ok, frame = cap.read()
                    if not ok:
                        raise RuntimeError("ī�޶� ������ ������ϴ�. ���� ���¸� Ȯ���� �ּ���.")
                    frame = cv2.flip(frame, 1)
                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    ms = max(last_ms + 1, int((time.monotonic() - started) * 1000))
                    last_ms = ms
                    result = landmarker.detect_for_video(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb), ms)
                    points = result.hand_landmarks[0] if result.hand_landmarks else None
                    if points is None:
                        pointer_last = None
                        target = None
                        smooth = None
                    actions = engine.update(points, time.monotonic())
                    for action in actions:
                        kind = action[0]
                        if kind == "move":
                            x, y = action[1:]
                            if pointer_last is None and settings.movement_mode == "�� �̵���":
                                target = mouse_win.cursor_position()
                                smooth = target
                                pointer_last = (x, y)
                                continue
                            target = pointer_target(x, y, pointer_last, target,
                                                    mouse_win.screen_rect(), settings)
                            pointer_last = (x, y)
                            smooth = target if smooth is None else tuple(
                                a + settings.smoothing * (b - a) for a, b in zip(smooth, target)
                            )
                            mouse_win.move(*smooth)
                        elif kind == "left_click":
                            mouse_win.click_left()
                            self.last_click_at = time.monotonic()
                        elif kind == "scroll":
                            mouse_win.scroll(action[1])
                    if points:
                        h, w = frame.shape[:2]
                        for i in (4, 8):
                            cv2.circle(frame, (int(points[i].x*w), int(points[i].y*h)), 7, (40, 220, 100), -1)
                        a = (int(points[4].x*w), int(points[4].y*h))
                        b = (int(points[8].x*w), int(points[8].y*h))
                        cv2.line(frame, a, b, (30, 220, 255), 2)
                        marker = a if settings.pointer_mode == "���� ��" else ((a[0]+b[0])//2, (a[1]+b[1])//2)
                        cv2.circle(frame, marker, 6, (0, 100, 255), -1)
                    self.put_event(("frame", cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), bool(points), engine.pinching, engine.scrolled))
        except Exception as exc:
            self.put_event(("error", str(exc)))
        finally:
            engine.reset()
            if cap is not None:
                cap.release()
            self.running.clear()
            self.put_event(("done",))

    def poll(self):
        # Function keys work even when another window has focus.
        vk = 0x70 + int(self.active_settings.stop_key[1:]) - 1
        down = bool(mouse_win.user32.GetAsyncKeyState(vk) & 0x8000)
        if down and not self.stop_key_was_down and self.running.is_set():
            self.stop("����Ű�� ���� �����߽��ϴ�.")
        self.stop_key_was_down = down
        if self.watcher and self.watcher.seen.is_set() and self.running.is_set():
            self.stop("���콺 �Ǵ� ��ġ�е� �Է��� ������ �����߽��ϴ�.")
        try:
            while True:
                item = self.events.get_nowait()
                if item[0] == "frame":
                    if not self.running.is_set():
                        continue
                    image = Image.fromarray(item[1])
                    image.thumbnail((700, 390))
                    self.preview_image = ImageTk.PhotoImage(image)
                    self.preview.configure(image=self.preview_image, text="")
                    if time.monotonic() - self.last_click_at < 0.7:
                        self.status.set("Ŭ���߽��ϴ�.")
                    elif item[4]:
                        self.status.set("��ũ�� ���Դϴ�.")
                    elif item[3]:
                        self.status.set("���������� ���� �ν�: Ŭ�� �Ǵ� ���Ʒ��� ������ ��ũ��")
                    else:
                        self.status.set("���� �ν��߽��ϴ�." if item[2] else "���� ī�޶� ���� �ּ���.")
                elif item[0] == "error":
                    self.status.set(item[1])
                    messagebox.showerror("ī�޶� ����", item[1])
                elif item[0] == "done":
                    if self.watcher:
                        self.watcher.stop()
                        self.watcher = None
                    self.start_button.configure(state="normal")
                    self.stop_button.configure(state="disabled")
                    if self.stop_reason is None and self.status.get() == "ī�޶� �����ϴ� ���Դϴ�...":
                        self.status.set("�����߽��ϴ�. �ٽ� �����Ϸ��� ī�޶� ������ ��������.")
        except queue.Empty:
            pass
        self.root.after(35, self.poll)

    def close(self):
        self.running.clear()
        if self.watcher:
            self.watcher.stop()
        self.root.destroy()


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        result_path = Path(sys.argv[sys.argv.index("--self-test") + 1])
        try:
            options = mp.tasks.vision.HandLandmarkerOptions(
                base_options=mp.tasks.BaseOptions(model_asset_buffer=resource("assets/hand_landmarker.task").read_bytes())
            )
            with mp.tasks.vision.HandLandmarker.create_from_options(options):
                pass
            result_path.write_text("OK", encoding="utf-8")
        except Exception as exc:
            result_path.write_text(repr(exc), encoding="utf-8")
        sys.exit(0)
    ctypes = __import__("ctypes")
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except (AttributeError, OSError):
        pass
    App().root.mainloop()
