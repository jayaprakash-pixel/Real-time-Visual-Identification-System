@echo off
rem phasedoc plan CLI for this arc (shared script, arc chosen by PHASEDOC_DIR)
set PHASEDOC_DIR=%~dp0
python "C:\whitenoise\phasedoc\plan.py" %*
