"""
test_timer.py
-------------
Automated unit tests for timer logic, chase gating, and minute formatting.
"""

import time
from timer_logic import AbomTimer, TimerState


def test_format_time():
    assert AbomTimer.format_time(0.0) == "0.000"
    assert AbomTimer.format_time(42.735) == "42.735"
    assert AbomTimer.format_time(59.999) == "59.999"
    assert AbomTimer.format_time(60.000) == "1:00.000"
    assert AbomTimer.format_time(116.686) == "1:56.686"
    assert AbomTimer.format_time(65.042) == "1:05.042"
    print("[PASS] Time formatting (seconds and M:SS.XXX) works perfectly")


def test_chase_gating():
    timer = AbomTimer(debounce_sec=0.1)
    assert timer.state == TimerState.STANDBY

    # 1. HeadFollow outside chase -> MUST BE IGNORED
    timer.process_console_line(
        "12:00:00", "WARNING", "Warning: Successfully set camera type: HeadFollow", elapsed_sec=10.0
    )
    assert timer.state == TimerState.STANDBY, "HeadFollow outside chase should be ignored!"

    # 2. Enter chase room
    timer.process_console_line("12:00:05", "INFO", "Room Name: ChaseStart", elapsed_sec=15.0)
    assert timer.state == TimerState.READY
    assert timer.in_chase is True

    # 3. HeadFollow inside chase -> START
    timer.process_console_line(
        "12:00:10", "WARNING", "Warning: Successfully set camera type: HeadFollow", elapsed_sec=20.0
    )
    assert timer.state == TimerState.RUNNING

    time.sleep(0.15)

    # 4. HeadFollow inside chase -> STOP
    timer.process_console_line(
        "12:02:06", "WARNING", "Warning: Successfully set camera type: HeadFollow", elapsed_sec=136.686
    )
    assert timer.state == TimerState.FINISHED
    # 136.686 - 20.0 = 116.686s -> 1:56.686
    assert timer.format_time(timer.get_elapsed()) == "1:56.686"

    # 5. Leave chase room
    timer.process_console_line("12:02:15", "INFO", "Room Name: ChaseEnd", elapsed_sec=145.0)
    assert timer.in_chase is False
    assert timer.state == TimerState.FINISHED  # Final time persists!
    assert timer.format_time(timer.get_elapsed()) == "1:56.686"

    # 6. Unrelated HeadFollow outside chase -> Should NOT restart or change
    timer.process_console_line(
        "12:02:30", "WARNING", "Warning: Successfully set camera type: HeadFollow", elapsed_sec=160.0
    )
    assert timer.state == TimerState.FINISHED
    assert timer.format_time(timer.get_elapsed()) == "1:56.686"

    # 7. Next encounter starts with ChaseStart -> Automatically resets & arms
    timer.process_console_line("12:05:00", "INFO", "Room Name: ChaseStart", elapsed_sec=300.0)
    assert timer.state == TimerState.READY
    assert timer.format_time(timer.get_elapsed()) == "0.000"

    print("[PASS] Chase gating (ChaseStart / ChaseEnd) works perfectly")


def test_death_reset():
    timer = AbomTimer(debounce_sec=0.1)
    timer.process_console_line("12:00:00", "INFO", "Room Name: ChaseStart", elapsed_sec=10.0)
    timer.process_console_line("12:00:05", "WARNING", "Warning: Successfully set camera type: HeadFollow", elapsed_sec=15.0)
    assert timer.state == TimerState.RUNNING

    # Player died
    timer.process_console_line("12:00:10", "INFO", "AfterDeathModifier", elapsed_sec=20.0)
    assert timer.state == TimerState.STANDBY
    assert timer.in_chase is False
    assert timer.format_time(timer.get_elapsed()) == "0.000"
    print("[PASS] AfterDeathModifier resets timer back to STANDBY")


if __name__ == "__main__":
    test_format_time()
    test_chase_gating()
    test_death_reset()
    print("\nAll timer tests passed!")
