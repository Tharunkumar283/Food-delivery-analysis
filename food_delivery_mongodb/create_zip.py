"""
create_zip.py
Creates a ZIP archive of the project for submission.
Run from the food_delivery_mongodb directory:
    python create_zip.py
"""
import zipfile
import os
from pathlib import Path

PROJECT_DIR = Path(__file__).parent
OUTPUT_ZIP = PROJECT_DIR.parent / "food_delivery_mongodb_project.zip"

EXCLUDE = {
    ".venv", "__pycache__", ".pytest_cache", ".git",
    "*.pyc", "node_modules",
}


def should_include(path: Path) -> bool:
    for exc in EXCLUDE:
        if exc.startswith("*"):
            if path.name.endswith(exc[1:]):
                return False
        elif exc in path.parts:
            return False
    return True


with zipfile.ZipFile(OUTPUT_ZIP, "w", zipfile.ZIP_DEFLATED) as zf:
    for file in PROJECT_DIR.rglob("*"):
        if file.is_file() and should_include(file):
            arcname = file.relative_to(PROJECT_DIR.parent)
            zf.write(file, arcname)
            print(f"  Added: {arcname}")

print(f"\n[OK] ZIP created: {OUTPUT_ZIP}")
print(f"     Size: {OUTPUT_ZIP.stat().st_size / 1024:.1f} KB")
