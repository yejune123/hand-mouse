"""Small Windows mouse bridge with multi-monitor coordinates."""
import ctypes
import threading
import time

user32 = ctypes.windll.user32
SM_XVIRTUALSCREEN, SM_YVIRTUALSCREEN = 76, 77
SM_CXVIRTUALSCREEN, SM_CYVIRTUALSCREEN = 78, 79
LEFTDOWN, LEFTUP, RIGHTDOWN, RIGHTUP, WHEEL = 0x0002, 0x0004, 0x0008, 0x0010, 0x0800
OWN_EVENT = 0x484D4F55
_last_move = (0, 0, 0.0)


class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


class MSLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [("pt", POINT), ("mouseData", ctypes.c_ulong),
                ("flags", ctypes.c_ulong), ("time", ctypes.c_ulong),
                ("dwExtraInfo", ctypes.c_size_t)]


class MSG(ctypes.Structure):
    _fields_ = [("hwnd", ctypes.c_void_p), ("message", ctypes.c_uint),
                ("wParam", ctypes.c_size_t), ("lParam", ctypes.c_ssize_t),
                ("time", ctypes.c_ulong), ("pt", POINT), ("lPrivate", ctypes.c_ulong)]


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long), ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong), ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong), ("dwExtraInfo", ctypes.c_size_t)]


class INPUTUNION(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT)]


class INPUT(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong), ("data", INPUTUNION)]


HOOKPROC = ctypes.WINFUNCTYPE(ctypes.c_ssize_t, ctypes.c_int, ctypes.c_size_t, ctypes.c_ssize_t)
user32.SetWindowsHookExW.argtypes = (ctypes.c_int, HOOKPROC, ctypes.c_void_p, ctypes.c_ulong)
user32.SetWindowsHookExW.restype = ctypes.c_void_p
user32.CallNextHookEx.argtypes = (ctypes.c_void_p, ctypes.c_int, ctypes.c_size_t, ctypes.c_ssize_t)
user32.CallNextHookEx.restype = ctypes.c_ssize_t
user32.UnhookWindowsHookEx.argtypes = (ctypes.c_void_p,)
user32.PeekMessageW.argtypes = (ctypes.POINTER(MSG), ctypes.c_void_p, ctypes.c_uint, ctypes.c_uint, ctypes.c_uint)
user32.PeekMessageW.restype = ctypes.c_int
user32.GetCursorPos.argtypes = (ctypes.POINTER(POINT),)
user32.SendInput.argtypes = (ctypes.c_uint, ctypes.POINTER(INPUT), ctypes.c_int)
user32.SendInput.restype = ctypes.c_uint


def cursor_position():
    p = POINT()
    if not user32.GetCursorPos(ctypes.byref(p)):
        raise OSError("Ŀ�� ��ġ�� ���� �� �����ϴ�.")
    return p.x, p.y


class PhysicalMouseWatcher:
    """Watch physical mouse/touchpad events on a thread with its own hook queue."""
    def __init__(self):
        self.seen = threading.Event()
        self._stop = threading.Event()
        self._ready = threading.Event()
        self.error = None
        self._thread = None
        self._hook = None
        self._proc = None
        self.arm_at = time.monotonic() + 0.7

    def start(self):
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        self._ready.wait(2)
        if self.error:
            raise OSError(self.error)

    def stop(self):
        self._stop.set()

    def _callback(self, code, msg, data):
        if code >= 0 and time.monotonic() >= self.arm_at:
            event = ctypes.cast(data, ctypes.POINTER(MSLLHOOKSTRUCT)).contents
            if event.dwExtraInfo != OWN_EVENT:
                own_move = (msg == 0x0200 and
                            abs(event.pt.x - _last_move[0]) <= 1 and
                            abs(event.pt.y - _last_move[1]) <= 1 and
                            time.monotonic() - _last_move[2] < 0.15)
                if not own_move and msg in (0x0200, 0x0201, 0x0202, 0x0204, 0x0205, 0x0207, 0x0208, 0x020A, 0x020E):
                    self.seen.set()
        return user32.CallNextHookEx(self._hook, code, msg, data)

    def _run(self):
        self._proc = HOOKPROC(self._callback)
        self._hook = user32.SetWindowsHookExW(14, self._proc, None, 0)
        if not self._hook:
            self.error = "�ٸ� ���콺 �Է� ���� ����� ������ �� �����ϴ�."
            self._ready.set()
            return
        self._ready.set()
        message = MSG()
        try:
            while not self._stop.is_set():
                while user32.PeekMessageW(ctypes.byref(message), None, 0, 0, 1):
                    pass
                time.sleep(0.01)
        finally:
            user32.UnhookWindowsHookEx(self._hook)


def screen_rect():
    return tuple(user32.GetSystemMetrics(n) for n in (
        SM_XVIRTUALSCREEN, SM_YVIRTUALSCREEN, SM_CXVIRTUALSCREEN, SM_CYVIRTUALSCREEN
    ))


def move(x, y):
    global _last_move
    _last_move = (int(x), int(y), time.monotonic())
    user32.SetCursorPos(int(x), int(y))


def mouse(flags, data=0):
    event = INPUT(type=0, data=INPUTUNION(mi=MOUSEINPUT(
        dx=0, dy=0, mouseData=data, dwFlags=flags, time=0, dwExtraInfo=OWN_EVENT
    )))
    if user32.SendInput(1, ctypes.byref(event), ctypes.sizeof(INPUT)) != 1:
        raise ctypes.WinError()


def click_left():
    mouse(LEFTDOWN)
    mouse(LEFTUP)


def click_right():
    mouse(RIGHTDOWN)
    mouse(RIGHTUP)


def scroll(steps):
    mouse(WHEEL, ctypes.c_ulong(steps * 120).value)
