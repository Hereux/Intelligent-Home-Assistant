@echo off
pushd %~dp0\bin\rasa
python3.9 -m rasa run --enable-api --endpoints endpoints.yml
pause