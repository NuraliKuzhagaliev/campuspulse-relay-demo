@echo off
setlocal
if /I not "%~d0"=="D:" exit /b 1
set "RELAY_LAUNCH_TEMP=D:\projects\CampusPulseRELAY\.local\tmp"
if not exist "%RELAY_LAUNCH_TEMP%" mkdir "%RELAY_LAUNCH_TEMP%"
set "TEMP=%RELAY_LAUNCH_TEMP%"
set "TMP=%RELAY_LAUNCH_TEMP%"
set "TMPDIR=%RELAY_LAUNCH_TEMP%"
start "" "%~dp0CampusPulse-RELAY-0.5.0-x64-portable.exe"
