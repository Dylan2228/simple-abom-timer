@echo off
title Abomination Encounter Timer
echo Starting Abomination Encounter Timer...
python main.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo An error occurred running the timer.
    pause
)

