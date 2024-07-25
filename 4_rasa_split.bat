@echo off

pushd %~dp0\bin\rasa
python3.9 -m rasa data split nlu

pause