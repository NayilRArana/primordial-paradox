@echo off
rem Starts the game for a HUMAN playthrough and keeps the game's own log in build\human-run.log (manager, 2026-11-02).
rem Double click it. Close the game window when done. The log is what lets the manager see how far the route got.
cd /d "%~dp0..\output\PrimordialParadox"
if not exist "%~dp0..\build" mkdir "%~dp0..\build"
set PP_AUDIO_LOG=1
"PrimordialParadox.exe" -game "PrimordialParadox.win" > "%~dp0..\build\human-run.log" 2>&1
