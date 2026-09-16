"""
roblox_console.py
-----------------
Roblox live console streamer.

Tails the latest Roblox Player log and emits Developer Console
(F9 / print/warn/error) lines in real time via a callback.
"""

import glob
import inspect
import os
import re
import threading
import time
from typing import Callable, Optional

# Log-line header parser
# Group 1: YYYY-MM-DDTHH:MM:SS
# Group 2: Milliseconds (.xxx)
# Group 3: Process elapsed seconds (float with microsecond precision)
# Group 4: Optional severity word (e.g. Warning, Error, Info)
# Group 5: Tag (e.g. FLog::CreatorWarning)
# Group 6: Message text
_HEADER = re.compile(
    r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})\.(\d{3})Z"
    r",([0-9.]+),[a-f0-9]+,\d+"
    r"(?:,([A-Za-z]+))?"
    r"\s+\[([^\]]+)\]\s*(.*)$"
)

# Tags whose output counts as Developer Console (F9)
_CONSOLE_TAGS = {"creatoroutput", "creatorwarning", "creatorerror", "script", "gamejoinutil"}


def _is_console_tag(tag: str) -> bool:
    t = tag.lower()
    return any(ct in t for ct in _CONSOLE_TAGS)


def _parse_level(tag: str, severity: Optional[str]) -> str:
    tl = tag.lower()
    sl = (severity or "").lower()
    if "error" in tl or sl == "error":
        return "ERROR"
    if "warn" in tl or sl == "warning":
        return "WARNING"
    return "INFO"


def _latest_log(log_dir: Optional[str] = None) -> Optional[str]:
    if not log_dir:
        log_dir = os.path.expandvars(r"%LOCALAPPDATA%\Roblox\logs")
    if not os.path.isdir(log_dir):
        return None
    files = glob.glob(os.path.join(log_dir, "*Player*.log"))
    if not files:
        return None
    files.sort(key=os.path.getmtime, reverse=True)
    return files[0]


class RobloxConsoleStreamer:
    """
    Streams Roblox Developer Console lines to on_line in real time.

    Parameters
    ----------
    on_line : callable
        Called for every new console line.
        Supports signatures:
            on_line(time_str, level, message, elapsed_sec=None)
            or on_line(time_str, level, message)
    on_log_attached : callable(file_path), optional
        Called when a new Roblox log file is opened.
    poll_interval : float
        Seconds between file reads (default 0.05 = 50ms for low latency).
    log_dir : str, optional
        Custom directory to look for Roblox logs (defaults to %LOCALAPPDATA%\\Roblox\\logs).
    """

    def __init__(
        self,
        on_line: Callable[..., None],
        on_log_attached: Optional[Callable[[str], None]] = None,
        poll_interval: float = 0.05,
        log_dir: Optional[str] = None,
    ):
        self._on_line = on_line
        self._on_log_attached = on_log_attached
        self._poll_interval = poll_interval
        self._log_dir = log_dir
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._file_path: Optional[str] = None
        self._fh = None

        # Detect how many parameters on_line accepts
        try:
            sig = inspect.signature(on_line)
            self._pass_elapsed = len(sig.parameters) >= 4
        except Exception:
            self._pass_elapsed = False

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._loop, daemon=True, name="RobloxConsoleStreamer"
        )
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._fh:
            try:
                self._fh.close()
            except Exception:
                pass
            self._fh = None

    def get_current_log_path(self) -> Optional[str]:
        return self._file_path

    def _loop(self) -> None:
        while self._running:
            try:
                latest = _latest_log(self._log_dir)
                if latest and latest != self._file_path:
                    self._open(latest)
                if self._fh:
                    chunk = self._fh.read()
                    if chunk:
                        self._process(chunk)
            except Exception:
                pass
            time.sleep(self._poll_interval)

    def _open(self, path: str) -> None:
        if self._fh:
            try:
                self._fh.close()
            except Exception:
                pass
        self._file_path = path
        self._fh = open(path, "r", encoding="utf-8", errors="ignore")

        # Seek to the end of the file to ignore historical logs
        self._fh.seek(0, 2)

        if self._on_log_attached:
            try:
                self._on_log_attached(path)
            except Exception:
                pass

    def _process(self, text: str) -> None:
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                continue

            m = _HEADER.match(line)
            if not m:
                continue

            ts_date_time = m.group(1)
            elapsed_sec_str = m.group(3)
            severity = m.group(4)
            tag = m.group(5)
            message = m.group(6)

            if not _is_console_tag(tag):
                continue

            time_str = ts_date_time.split("T")[1] if "T" in ts_date_time else ts_date_time
            level = _parse_level(tag, severity)

            try:
                elapsed_sec = float(elapsed_sec_str)
            except Exception:
                elapsed_sec = None

            if self._pass_elapsed:
                self._on_line(time_str, level, message, elapsed_sec)
            else:
                self._on_line(time_str, level, message)
