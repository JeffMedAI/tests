$DashboardPath = "C:\JeffLocal\dashboard"
$PythonVenv = "$DashboardPath\.venv\Scripts\python.exe"

$ScriptContent = @'
import sys
import os
from pathlib import Path

dashboard_root = Path("C:/JeffLocal/dashboard")
os.chdir(str(dashboard_root))
sys.path.insert(0, str(dashboard_root))

try:
    from fastapi.testclient import TestClient
    from app.main import app

    with TestClient(app) as client:
        response = client.get("/")

        # Check for toggle button
        if "sidebar-toggle" in response.text:
            print("OK: Toggle button element FOUND in rendered HTML")
        else:
            print("FAIL: Toggle button element NOT FOUND")

        # Check for sidebar
        if "analytics-sidebar" in response.text:
            print("OK: Sidebar FOUND")
        else:
            print("FAIL: Sidebar NOT FOUND")

        # Check for CSS
        if "dashboard.css" in response.text:
            print("OK: CSS reference FOUND")
        else:
            print("FAIL: CSS reference NOT FOUND")

        # Show a snippet around the toggle
        if "sidebar-toggle" in response.text:
            idx = response.text.find("sidebar-toggle")
            snippet = response.text[max(0, idx-100):min(len(response.text), idx+200)]
            print(f"\nSnippet: ...{snippet}...")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
'@

# Write the Python script to a temp file
$TempScript = "$DashboardPath\__temp_check.py"
$ScriptContent | Out-File -FilePath $TempScript -Encoding UTF8

# Run it with the venv Python
& $PythonVenv $TempScript

# Clean up
Remove-Item $TempScript -ErrorAction SilentlyContinue
