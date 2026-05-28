#!/usr/bin/env python3
import sys
import os
from pathlib import Path

# Use the dashboard venv Python
dashboard_root = Path("C:/JeffLocal/dashboard")
dashboard_venv_python = dashboard_root / ".venv" / "Scripts" / "python.exe"

os.chdir(str(dashboard_root))
sys.path.insert(0, str(dashboard_root))

try:
    from fastapi.testclient import TestClient
    from app.main import app

    with TestClient(app) as client:
        response = client.get("/")
        if "sidebar-toggle" in response.text:
            print("✓ Toggle button element FOUND in rendered HTML")
            # Find the context
            idx = response.text.find("sidebar-toggle")
            start = max(0, idx - 200)
            end = min(len(response.text), idx + 200)
            print("\nContext:")
            print(response.text[start:end])
            print("\n✓ SUCCESS: Button is in the template output!")
        else:
            print("✗ Toggle button element NOT FOUND in rendered HTML")
            # Check if sidebar is at least there
            if "analytics-sidebar" in response.text:
                print("✓ Sidebar FOUND")
            else:
                print("✗ Sidebar NOT FOUND")
            if "dashboard.css" in response.text:
                print("✓ CSS reference FOUND")
            else:
                print("✗ CSS reference NOT FOUND")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
