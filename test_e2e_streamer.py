"""
test_e2e_streamer.py
--------------------
End-to-end test simulating Roblox log file updates and validating streamer + timer.
"""

import os
import shutil
import tempfile
import time
from roblox_console import RobloxConsoleStreamer
from timer_logic import AbomTimer, TimerState


def run_e2e_test():
    temp_dir = tempfile.mkdtemp(prefix="roblox_test_logs_")
    log_path = os.path.join(temp_dir, "0.0.0_20260916T000000Z_Player_ABC12_last.log")

    with open(log_path, "w", encoding="utf-8") as f:
        f.write("")

    try:
        timer = AbomTimer(debounce_sec=0.1)

        def on_line(time_str, level, message, elapsed_sec=None):
            timer.process_console_line(time_str, level, message, elapsed_sec)

        streamer = RobloxConsoleStreamer(on_line=on_line, poll_interval=0.02, log_dir=temp_dir)
        streamer.start()
        time.sleep(0.1)

        # 1. Outside chase: HeadFollow should be ignored!
        with open(log_path, "a", encoding="utf-8") as f:
            f.write("2026-09-16T12:00:00.000Z,100.000,1234,6,Warning [FLog::CreatorWarning] Warning: Successfully set camera type: HeadFollow\n")
            f.flush()

        time.sleep(0.1)
        assert timer.state == TimerState.STANDBY, "Must stay in STANDBY outside chase"

        # 2. Enter chase room
        with open(log_path, "a", encoding="utf-8") as f:
            f.write("2026-09-16T12:00:10.000Z,110.000000,1234,6,Info [FLog::CreatorOutput] Room Name: ChaseStart\n")
            f.flush()

        time.sleep(0.1)
        assert timer.state == TimerState.READY
        print("[E2E PASS] ChaseStart detected, timer is READY")

        # 3. HeadFollow inside chase -> START
        with open(log_path, "a", encoding="utf-8") as f:
            f.write("2026-09-16T12:00:20.123Z,120.123456,1234,6,Warning [FLog::CreatorWarning] Warning: Successfully set camera type: HeadFollow\n")
            f.flush()

        time.sleep(0.1)
        assert timer.state == TimerState.RUNNING
        print("[E2E PASS] HeadFollow inside chase started the timer")

        time.sleep(0.15)

        # 4. HeadFollow second time -> STOP (116.686 seconds later)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write("2026-09-16T12:02:16.809Z,236.809456,1234,6,Warning [FLog::CreatorWarning] Warning: Successfully set camera type: HeadFollow\n")
            f.flush()

        time.sleep(0.1)
        assert timer.state == TimerState.FINISHED
        # 236.809456 - 120.123456 = 116.686s -> 1:56.686
        assert timer.format_time(timer.get_elapsed()) == "1:56.686"
        print(f"[E2E PASS] Encounter finished! Formatted time: {timer.format_time(timer.get_elapsed())}")

        # 5. Room Name: ChaseEnd
        with open(log_path, "a", encoding="utf-8") as f:
            f.write("2026-09-16T12:02:30.000Z,250.000,1234,6,Info [FLog::CreatorOutput] Room Name: ChaseEnd\n")
            f.flush()

        time.sleep(0.1)
        assert timer.state == TimerState.FINISHED
        assert timer.in_chase is False

        # 6. Death reset
        with open(log_path, "a", encoding="utf-8") as f:
            f.write("2026-09-16T12:03:00.000Z,280.000,1234,6,Info [FLog::CreatorOutput] AfterDeathModifier\n")
            f.flush()

        time.sleep(0.1)
        assert timer.state == TimerState.STANDBY
        print("[E2E PASS] AfterDeathModifier reset timer back to STANDBY")

        streamer.stop()
        print("\nAll End-to-End Streamer tests PASSED successfully!")

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    run_e2e_test()
