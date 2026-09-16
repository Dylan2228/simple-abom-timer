# Abomination Grand Encounter Timer

A lightweight, clean, high-precision (`X.XXX`) speedrun & encounter timer for Roblox that automatically tracks the **Abomination Grand Encounter** using the Roblox Developer Console.

## Features & Rules

- **Chase Gating (Zero False Triggers)**:
  - The timer functions **ONLY** activate when you reach `"Room Name: ChaseStart"` and deactivate after leaving `"Room Name: ChaseEnd"`.
  - Any camera changes outside the encounter room (spectator cams, lockers, etc.) are completely ignored.
- **Encounter Timing**:
  - **Start**: First `"Successfully set camera type: HeadFollow"` inside the chase starts the timer.
  - **Stop**: Second `"Successfully set camera type: HeadFollow"` finishes the encounter.
- **Automatic Minute Formatting**:
  - Displays `SS.XXX` under 60 seconds (e.g. `42.735`).
  - Automatically switches to `M:SS.XXX` when reaching 60+ seconds (e.g. `1:56.686`).
- **Reset Controls**:
  - **Auto Reset on Death**: When `"AfterDeathModifier"` appears in the console, the timer resets back to `STANDBY`.
  - **Reset Button**: Click **Reset Timer** anytime to manually clear.
  - **No Keybindings**: Keyboard keys like `R` or `Space` are completely unhooked so typing in-game or in Roblox chat won't accidentally trigger the timer.
- **Clean & Minimal HUD**:
  - Compact window (340x220).
  - Clear status badges: `STANDBY (Waiting for Chase)`, `READY (In Chase)`, `RUNNING`, `FINISHED`.
  - **Always on top** toggle to float over your Roblox window.
  - No clutter (no unnecessary labels, no audio beeps, no run history bloat).

---

## How to Run

### Option 1: Double-click `AbominationTimer.exe` (Recommended)

Just double-click **[`AbominationTimer.exe`](AbominationTimer.exe)** directly! It's a self-contained executable with no Python or console window required.

### Option 2: Double-click `run.bat`

Double-click [`run.bat`](run.bat) to launch via Python.

### Option 3: Command Line

```bash
python main.py
```
