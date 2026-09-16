"""
timer_logic.py
--------------
Core state machine and high-precision timing logic for the
Abomination Grand Encounter timer.
"""

from enum import Enum
import time
from typing import Callable, Optional


class TimerState(Enum):
    STANDBY = "STANDBY"    # Waiting for Room Name: ChaseStart
    READY = "READY"        # Inside ChaseStart, armed for camera trigger
    RUNNING = "RUNNING"    # Timer actively counting
    FINISHED = "FINISHED"  # Encounter finished, final time displayed


class AbomTimer:
    """
    Abomination Grand Encounter Timer.

    Rules:
    - Chase gating: Timer functions ONLY activate after 'Room Name: ChaseStart'
      and deactivate after 'Room Name: ChaseEnd'.
    - START: Console contains 'Successfully set camera type: HeadFollow' while in chase.
    - STOP:  Console contains 'Successfully set camera type: HeadFollow' second time.
    - DEATH: Console contains 'AfterDeathModifier' -> resets timer.
    """

    CHASE_START_LINE = "Room Name: ChaseStart"
    CHASE_END_LINE = "Room Name: ChaseEnd"
    START_STOP_LINE = "Successfully set camera type: HeadFollow"
    DEATH_RESET_LINE = "AfterDeathModifier"

    def __init__(self, debounce_sec: float = 1.0):
        self.state: TimerState = TimerState.STANDBY
        self.in_chase: bool = False
        self.debounce_sec: float = debounce_sec

        # Timing tracking
        self._start_perf: Optional[float] = None
        self._end_perf: Optional[float] = None
        self._start_log_sec: Optional[float] = None
        self._end_log_sec: Optional[float] = None
        self._final_elapsed: float = 0.0

        # Callback for state changes: on_state_change(state, elapsed_sec)
        self.on_state_change: Optional[Callable[[TimerState, float], None]] = None

    def get_elapsed(self) -> float:
        """Returns the current elapsed time in seconds."""
        if self.state == TimerState.RUNNING:
            if self._start_perf is None:
                return 0.0
            return max(0.0, time.perf_counter() - self._start_perf)
        elif self.state == TimerState.FINISHED:
            return self._final_elapsed
        return 0.0

    @staticmethod
    def format_time(seconds: float) -> str:
        """
        Formats time:
        - Below 60s: SS.XXX (e.g. 0.000, 42.735)
        - 60s and above: M:SS.XXX (e.g. 1:56.686)
        """
        if seconds < 0:
            seconds = 0.0
        if seconds < 60.0:
            return f"{seconds:.3f}"
        minutes = int(seconds // 60)
        rem_seconds = seconds % 60
        return f"{minutes}:{rem_seconds:06.3f}"

    def process_console_line(
        self, time_str: str, level: str, message: str, elapsed_sec: Optional[float] = None
    ) -> None:
        """Processes a developer console message from Roblox."""

        # 1. Death detection -> reset timer
        if self.DEATH_RESET_LINE in message:
            self.reset()
            return

        # 2. Room Name: ChaseStart -> arms the timer for Abomination encounter
        if self.CHASE_START_LINE in message:
            self.in_chase = True
            if self.state != TimerState.RUNNING:
                self.state = TimerState.READY
                self._final_elapsed = 0.0
                if self.on_state_change:
                    self.on_state_change(self.state, 0.0)
            return

        # 3. Room Name: ChaseEnd -> encounter area left
        if self.CHASE_END_LINE in message:
            self.in_chase = False
            if self.state == TimerState.RUNNING:
                self._stop_timer(log_sec=elapsed_sec)
            return

        # 4. Camera Follow trigger (ONLY processed while inside chase)
        if self.START_STOP_LINE in message:
            if not self.in_chase:
                return

            if self.state == TimerState.READY:
                self._start_timer(log_sec=elapsed_sec)
            elif self.state == TimerState.RUNNING:
                # Enforce debounce to prevent duplicate log events
                if self.get_elapsed() >= self.debounce_sec:
                    self._stop_timer(log_sec=elapsed_sec)

    def _start_timer(self, log_sec: Optional[float] = None) -> None:
        self._start_perf = time.perf_counter()
        self._end_perf = None
        self._start_log_sec = log_sec
        self._end_log_sec = None
        self._final_elapsed = 0.0
        self.state = TimerState.RUNNING

        if self.on_state_change:
            self.on_state_change(self.state, 0.0)

    def _stop_timer(self, log_sec: Optional[float] = None) -> None:
        self._end_perf = time.perf_counter()
        self._end_log_sec = log_sec
        self.state = TimerState.FINISHED

        # Calculate high-precision duration using log timestamps if available
        if (
            self._start_log_sec is not None
            and self._end_log_sec is not None
            and self._end_log_sec >= self._start_log_sec
        ):
            self._final_elapsed = self._end_log_sec - self._start_log_sec
        elif self._start_perf is not None and self._end_perf is not None:
            self._final_elapsed = max(0.0, self._end_perf - self._start_perf)
        else:
            self._final_elapsed = 0.0

        if self.on_state_change:
            self.on_state_change(self.state, self._final_elapsed)

    def reset(self) -> None:
        """Manually resets the timer."""
        self.in_chase = False
        self.state = TimerState.STANDBY
        self._start_perf = None
        self._end_perf = None
        self._start_log_sec = None
        self._end_log_sec = None
        self._final_elapsed = 0.0

        if self.on_state_change:
            self.on_state_change(self.state, 0.0)
