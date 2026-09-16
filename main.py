"""
main.py
-------
Abomination Grand Encounter Timer.

Rules:
- Active ONLY between "Room Name: ChaseStart" and "Room Name: ChaseEnd".
- START: "Successfully set camera type: HeadFollow"
- STOP:  "Successfully set camera type: HeadFollow"
- RESET: "AfterDeathModifier" or Reset button
- Format: SS.XXX or M:SS.XXX (when >= 60s)
"""

import os
import tkinter as tk
from typing import Optional

from roblox_console import RobloxConsoleStreamer
from timer_logic import AbomTimer, TimerState


# --- Styling Constants ---
BG_COLOR = "#121318"
PANEL_BG = "#1b1d24"
BORDER_COLOR = "#2a2d38"
TEXT_MUTED = "#8a8f9d"
TEXT_WHITE = "#ffffff"
COLOR_STANDBY = "#64748b"    # Slate / Soft Gray
COLOR_READY = "#38bdf8"      # Sky Blue
COLOR_RUNNING = "#10b981"    # Bright Emerald Green
COLOR_FINISHED = "#06b6d4"   # Vibrant Cyan
BTN_BG = "#262933"
BTN_ACTIVE_BG = "#323745"


class AbomTimerGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Abomination Timer")
        self.root.geometry("340x220")
        self.root.minsize(300, 200)
        self.root.configure(bg=BG_COLOR)

        # Always on top
        self.always_on_top = tk.BooleanVar(value=True)
        self.root.attributes("-topmost", True)

        # Timer instance
        self.timer = AbomTimer(debounce_sec=1.0)
        self.timer.on_state_change = self._on_timer_state_change

        # Streamer
        self.streamer: Optional[RobloxConsoleStreamer] = None
        self.current_log_name = tk.StringVar(value="Searching for Roblox log...")

        # UI Variables
        self.time_display_var = tk.StringVar(value="0.000")
        self.status_text_var = tk.StringVar(value="● STANDBY (Waiting for Chase)")

        self._build_ui()
        self._start_streamer()

        # Start 60fps refresh loop
        self._update_loop()

    def _build_ui(self) -> None:
        # Top Header Bar
        top_frame = tk.Frame(self.root, bg=BG_COLOR)
        top_frame.pack(fill="x", padx=16, pady=(10, 4))

        title_label = tk.Label(
            top_frame,
            text="ABOMINATION TIMER",
            font=("Segoe UI", 10, "bold"),
            fg=TEXT_WHITE,
            bg=BG_COLOR,
        )
        title_label.pack(side="left")

        cb_top = tk.Checkbutton(
            top_frame,
            text="Always on top",
            variable=self.always_on_top,
            font=("Segoe UI", 8),
            fg=TEXT_MUTED,
            bg=BG_COLOR,
            selectcolor=PANEL_BG,
            activebackground=BG_COLOR,
            activeforeground=TEXT_WHITE,
            command=self._toggle_always_on_top,
        )
        cb_top.pack(side="right")

        # Main Timer Card
        timer_card = tk.Frame(self.root, bg=PANEL_BG, highlightthickness=1, highlightbackground=BORDER_COLOR)
        timer_card.pack(fill="x", padx=16, pady=4)

        # Status Badge
        self.status_badge = tk.Label(
            timer_card,
            textvariable=self.status_text_var,
            font=("Segoe UI", 8, "bold"),
            fg=COLOR_STANDBY,
            bg=PANEL_BG,
        )
        self.status_badge.pack(pady=(10, 0))

        # Big Time Display
        self.time_label = tk.Label(
            timer_card,
            textvariable=self.time_display_var,
            font=("Consolas", 38, "bold"),
            fg=COLOR_STANDBY,
            bg=PANEL_BG,
        )
        self.time_label.pack(pady=(2, 10))

        # Controls (Reset button only, no keybinds)
        btn_frame = tk.Frame(self.root, bg=BG_COLOR)
        btn_frame.pack(fill="x", padx=16, pady=6)

        self.btn_reset = tk.Button(
            btn_frame,
            text="Reset Timer",
            font=("Segoe UI", 9, "bold"),
            fg=TEXT_WHITE,
            bg=BTN_BG,
            activebackground=BTN_ACTIVE_BG,
            activeforeground=TEXT_WHITE,
            relief="flat",
            bd=0,
            cursor="hand2",
            pady=5,
            command=self.on_click_reset,
        )
        self.btn_reset.pack(fill="x")

        # Bottom Log Status Bar
        status_bar = tk.Frame(self.root, bg="#0d0e12")
        status_bar.pack(fill="x", side="bottom")

        self.log_status_label = tk.Label(
            status_bar,
            textvariable=self.current_log_name,
            font=("Segoe UI", 8),
            fg=TEXT_MUTED,
            bg="#0d0e12",
            padx=10,
            pady=3,
            anchor="w",
        )
        self.log_status_label.pack(side="left")

    def _toggle_always_on_top(self) -> None:
        self.root.attributes("-topmost", self.always_on_top.get())

    def _start_streamer(self) -> None:
        def on_console_line(time_str: str, level: str, message: str, elapsed_sec: Optional[float] = None):
            self.root.after(0, lambda: self.timer.process_console_line(time_str, level, message, elapsed_sec))

        def on_log_attached(path: str):
            fname = os.path.basename(path)
            self.root.after(0, lambda: self.current_log_name.set(f"Connected: {fname}"))

        self.streamer = RobloxConsoleStreamer(
            on_line=on_console_line,
            on_log_attached=on_log_attached,
            poll_interval=0.03,
        )
        self.streamer.start()

        initial_log = self.streamer.get_current_log_path()
        if initial_log:
            self.current_log_name.set(f"Connected: {os.path.basename(initial_log)}")

    def _on_timer_state_change(self, new_state: TimerState, final_val: float) -> None:
        if new_state == TimerState.STANDBY:
            self.status_text_var.set("● STANDBY (Waiting for Chase)")
            self.status_badge.configure(fg=COLOR_STANDBY)
            self.time_label.configure(fg=COLOR_STANDBY)
            self.time_display_var.set("0.000")
        elif new_state == TimerState.READY:
            self.status_text_var.set("● READY (In Chase)")
            self.status_badge.configure(fg=COLOR_READY)
            self.time_label.configure(fg=COLOR_READY)
            self.time_display_var.set("0.000")
        elif new_state == TimerState.RUNNING:
            self.status_text_var.set("● RUNNING")
            self.status_badge.configure(fg=COLOR_RUNNING)
            self.time_label.configure(fg=COLOR_RUNNING)
        elif new_state == TimerState.FINISHED:
            self.status_text_var.set("● FINISHED")
            self.status_badge.configure(fg=COLOR_FINISHED)
            self.time_label.configure(fg=COLOR_FINISHED)
            self.time_display_var.set(AbomTimer.format_time(final_val))

    def on_click_reset(self) -> None:
        self.timer.reset()

    def _update_loop(self) -> None:
        """Periodic 60 FPS update for the active timer display."""
        if self.timer.state == TimerState.RUNNING:
            self.time_display_var.set(AbomTimer.format_time(self.timer.get_elapsed()))

        self.root.after(16, self._update_loop)

    def close(self) -> None:
        if self.streamer:
            self.streamer.stop()
        self.root.destroy()


def main():
    root = tk.Tk()
    app = AbomTimerGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.close)
    root.mainloop()


if __name__ == "__main__":
    main()
