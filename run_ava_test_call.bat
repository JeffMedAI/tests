@echo off
cd /d C:\JeffLocal
set PATH=C:\JeffLocal\dashboard\.venv\Scripts;%PATH%
echo PRE-FLIGHT CHECK > C:\JeffLocal\docs\reports\ava_test_run_output.txt
echo ---n8n :5678--- >> C:\JeffLocal\docs\reports\ava_test_run_output.txt
powershell -NoProfile -Command "try { (Invoke-WebRequest -Uri http://localhost:5678 -UseBasicParsing -TimeoutSec 5).StatusCode } catch { $_.Exception.Message }" >> C:\JeffLocal\docs\reports\ava_test_run_output.txt 2>&1
echo ---Ollama :11434--- >> C:\JeffLocal\docs\reports\ava_test_run_output.txt
powershell -NoProfile -Command "try { (Invoke-WebRequest -Uri http://localhost:11434 -UseBasicParsing -TimeoutSec 5).StatusCode } catch { $_.Exception.Message }" >> C:\JeffLocal\docs\reports\ava_test_run_output.txt 2>&1
echo ---Dashboard :8765--- >> C:\JeffLocal\docs\reports\ava_test_run_output.txt
powershell -NoProfile -Command "try { (Invoke-WebRequest -Uri http://localhost:8765 -UseBasicParsing -TimeoutSec 5).StatusCode } catch { $_.Exception.Message }" >> C:\JeffLocal\docs\reports\ava_test_run_output.txt 2>&1
echo ============================== >> C:\JeffLocal\docs\reports\ava_test_run_output.txt
echo RUNNING TEST CALL >> C:\JeffLocal\docs\reports\ava_test_run_output.txt
C:\JeffLocal\dashboard\.venv\Scripts\python.exe tests\send_gp_demo_n8n_webhook_calls.py --confirm-send --prefix AVA-TEST-20260617-222343 --url http://localhost:5678/webhook/ava-live-intake >> C:\JeffLocal\docs\reports\ava_test_run_output.txt 2>&1
echo ============================== >> C:\JeffLocal\docs\reports\ava_test_run_output.txt
echo SCRIPT_COMPLETE >> C:\JeffLocal\docs\reports\ava_test_run_output.txt
