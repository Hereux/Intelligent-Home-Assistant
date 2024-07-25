@echo off

set display = %1
ControlMyMonitor.exe /GetValue "\\.\DISPLAY%1\Monitor0" 10
echo %errorlevel%
