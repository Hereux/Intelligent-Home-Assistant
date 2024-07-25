@echo off

cd bin\rasa
python3.9 -m rasa run actions --debug --port 5055

pause