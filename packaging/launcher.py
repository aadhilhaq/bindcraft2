"""The script PyInstaller bundles.

A bundled executable runs its entry script as a top-level script with no package around it, so
this imports absolutely and does nothing else. Pointing PyInstaller at
bindcraft_launcher/__main__.py produces a build that fails on the first double-click with
"attempted relative import with no known parent package", which a windowed executable cannot
report.
"""
import os
import sys


def _stamp():
    """Publish the commit this bundle was built from: the workflow writes BUILD_VERSION into the
    bundle and this puts it where the window looks (BINDCRAFT_BUILD)."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    for candidate in (os.path.join(base, "BUILD_VERSION"), os.path.join(os.path.dirname(base), "BUILD_VERSION"),
                      os.path.join(os.path.dirname(os.path.dirname(base)), "BUILD_VERSION")):
        try:
            with open(candidate) as fh:
                text = fh.read().strip()
            if text:
                os.environ.setdefault("BINDCRAFT_BUILD", text)
                return
        except OSError:
            continue


_stamp()

from bindcraft_launcher.entry import main                       # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
