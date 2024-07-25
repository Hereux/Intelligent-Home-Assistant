@echo off
pushd %~dp0\bin\rasa
python3.9 -m rasa shell --debug --enable-api --endpoints endpoints.yml
pause