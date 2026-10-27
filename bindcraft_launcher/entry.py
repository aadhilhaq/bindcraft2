"""What the launcher does when started, however it was started: `python -m bindcraft_launcher`,
the console script, or a bundled executable running a script that imports it."""
import sys


def main(argv=None):
    argv = sys.argv if argv is None else argv
    if "--version" in argv:
        from . import credit, __version__
        print("BindCraft2 launcher %s\n%s" % (__version__, credit()))
        return 0
    # --selftest is for the build: a windowed executable cannot be driven without a display,
    # but it can prove that it starts, that its imports resolve and that what it needs came
    # along in the bundle.
    if "--selftest" in argv:
        from . import session, tunnel, credit, clusters                    # noqa: F401
        line = session.command("/x/BindCraft2", runs="~/r")
        assert "bc2-serve" in line and "--host 127.0.0.1" in line, line
        assert '"$HOME"/r' in line, line
        assert tunnel.AUTH_PATIENCE >= 120, "the Duo timeout was shortened"
        assert session.URL.search("open  http://127.0.0.1:8123/?t=abcDEF_-"), "the server's URL line would not be recognized"
        assert clusters.half_typed("/scratch/user/j/bindcraft_runs", "jane.doe") and not clusters.half_typed("/scratch/user/jane.doe/bindcraft_runs", "jane.doe")
        assert clusters.SITES["Grace (TAMU)"]["install"] == "/scratch/group/sflab/BindCraft2"
        notes = []
        try:
            import paramiko
            notes.append("paramiko " + paramiko.__version__)
        except ImportError:
            notes.append("paramiko NOT INSTALLED - the launcher cannot connect until it is")
        try:
            from . import app
            assert hasattr(app, "App") and hasattr(app, "main"), "no window"
            notes.append("window ok")
        except ImportError as exc:
            notes.append("no tkinter here (%s)" % exc)
        print("%s\n  %s\nSELFTEST OK" % (credit(), "\n  ".join(notes)))
        return 0
    from .app import main as run
    run()
    return 0
