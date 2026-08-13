"""
PyInstaller build packaging script.
Bundles Claude Usage Monitor into a standalone executable.
"""
import os
import sys
import subprocess
from pathlib import Path
from PIL import Image

# Import dynamic icon creator
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ui.icons import create_tray_icon
from models.usage import StatusLevel

def generate_exe_icon(icon_path: Path):
    """Generates a high-res .ico file for the Windows executable icon."""
    img = create_tray_icon(StatusLevel.SAFE, size=256)
    img.save(icon_path, format="ICO", sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])
    print(f"Generated executable icon at {icon_path}")

def build_executable():
    root_dir = Path(__file__).parent.resolve()
    assets_dir = root_dir / "ui" / "assets"
    icon_path = root_dir / "app_icon.ico"

    print("=== Building Claude Usage Monitor Executable ===")
    generate_exe_icon(icon_path)

    # PyInstaller arguments
    # Note: add-data format on Windows is 'source;destination'
    add_data_arg = f"{assets_dir};ui/assets"

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--name=Claude Usage Monitor",
        "--noconsole",
        "--onefile",
        f"--icon={icon_path}",
        f"--add-data={add_data_arg}",
        "--clean",
        str(root_dir / "app.py")
    ]

    print(f"Running PyInstaller command: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(root_dir))

    if result.returncode == 0:
        dist_exe = root_dir / "dist" / "Claude Usage Monitor.exe"
        print(f"\nBUILD SUCCESSFUL! Standalone binary created at:\n{dist_exe}")
    else:
        print(f"\nBUILD FAILED with exit code {result.returncode}", file=sys.stderr)
        sys.exit(result.returncode)

if __name__ == "__main__":
    build_executable()
