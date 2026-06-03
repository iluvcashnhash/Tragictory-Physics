"""
Build script for Tragictory Physics.

Packages the application into a standalone distributable using PyInstaller.

Usage
-----
Activate the project virtual environment first, then run:

    python build.py

The finished bundle will be placed in the ``dist/TragictoryPhysics/``
directory.  On macOS you will also find a ``TragictoryPhysics.app``
inside that folder.

Notes
-----
- ``--onedir`` is intentionally chosen over ``--onefile`` because
  QtWebEngine ships several large helper binaries that must live next to
  the main executable; onefile mode unpacks them to a temp directory on
  every launch which is noticeably slower and can trigger OS security
  warnings.
- Re-run this script after any change to assets or source files to
  regenerate the bundle.
"""

import os
import PyInstaller.__main__


def build() -> None:
    """Run PyInstaller with the project-specific configuration."""
    sep = os.pathsep  # ':' on macOS/Linux, ';' on Windows

    args = [
        "main.py",
        "--name=TragictoryPhysics",
        "--windowed",
        f"--add-data=assets{sep}assets",
        f"--add-data=data{sep}data",
        "--onedir",
        "--noconfirm",
    ]

    PyInstaller.__main__.run(args)


if __name__ == "__main__":
    build()
