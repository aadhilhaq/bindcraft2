"""Starting the page on the cluster and getting a URL back.

The server prints one line holding both the port it got and the token that gates it:
    open  http://127.0.0.1:<port>/?t=<token>
That line is the whole handshake: nothing is guessed about which port was free, and a server
that failed to start says so in its own words instead of leaving the launcher waiting.
"""
import re
import shlex
import time

from . import clusters

URL = re.compile(r"http://127\.0\.0\.1:(\d+)/\?t=([A-Za-z0-9_\-]+)")

#: Printed by the remote command when the install carries no bc2-serve: a marker rather than a
#: sentence, so the launcher recognizes it without matching on wording.
NO_SERVE_MARKER = "BINDCRAFT_NO_BC2_SERVE"

#: Where the install might be, when the person has not said. Tried in order.
GUESSES = (
    "/scratch/group/sflab/BindCraft2",
    "/scratch/user/$USER/BindCraft2",
    "~/BindCraft2",
)


def command(install, runs="", port=0):
    """The line run on the far end.

    `sflab/bc2-serve` rather than a Python: that wrapper names the install's own virtual
    environment, so the launcher cannot drift away from the install's layout and no module has
    to be loaded. Grace's system python3 could not even parse the server, so naming a Python
    here would be a way to fail; the wrapper is the supported way in.

    The server runs on the login node deliberately: it serves the page, reads the run folders
    and submits jobs, and the designing itself goes to the queue on a GPU node.
    """
    where = clusters.remote_path(install)
    bits = ["--host", "127.0.0.1", "--port", str(port)]
    quoted = [shlex.quote(b) for b in bits]
    if runs:
        quoted += ["--runs", clusters.remote_path(runs)]
    return (
        'cd %(where)s || exit 1; '
        '[ -x ./sflab/bc2-serve ] || { echo "%(marker)s %(install)s"; exit 78; }; '
        'exec ./sflab/bc2-serve %(args)s'
        % {"where": where, "marker": NO_SERVE_MARKER, "install": install, "args": " ".join(quoted)})


class Session:
    """A running server on the far end, and the local port that reaches it."""

    def __init__(self, channel, forwarder, local_port, remote_port, token, host):
        self.channel = channel
        self.forwarder = forwarder
        self.local_port = local_port
        self.remote_port = remote_port
        self.token = token
        self.host = host

    @property
    def url(self):
        return "http://127.0.0.1:%d/?t=%s" % (self.local_port, self.token)

    def stop(self):
        for close in (getattr(self.channel, "close", None),
                      getattr(self.forwarder, "shutdown", None),
                      getattr(self.forwarder, "server_close", None)):
            try:
                if close:
                    close()
            except Exception:                                   # noqa: BLE001
                pass


def start(t, install, runs="", timeout=90, on_output=None, forward=None, free_port=None, port=0):
    """Run the server, read its URL, forward a local port to it."""
    say = on_output or (lambda *a: None)
    line = command(install, runs, port)
    say("$ " + line)
    ch = t.open_session()
    ch.get_pty()          # so the server dies with the connection
    ch.exec_command(line)
    ch.settimeout(1.0)
    buf, deadline = "", time.time() + timeout
    while time.time() < deadline:
        if ch.exit_status_ready() and not ch.recv_ready():
            raise RuntimeError(why(buf, install))
        try:
            chunk = ch.recv(65536).decode("utf8", "replace")
        except Exception:                                       # noqa: BLE001
            chunk = ""
        if chunk:
            buf += chunk
            for ln in chunk.splitlines():
                if ln.strip():
                    say(ln.rstrip())
        m = URL.search(buf)
        if m:
            remote_port, token = int(m.group(1)), m.group(2)
            local = (free_port or (lambda: 0))()
            srv = forward(t, local, remote_port)
            local = srv.server_address[1]
            say("forwarding 127.0.0.1:%d to the cluster's %d" % (local, remote_port))
            return Session(ch, srv, local, remote_port, token, install)
        time.sleep(0.2)
    raise RuntimeError(why(buf, install) or
                       "the page did not report a URL within %ds. What it said:\n%s" % (timeout, _tail(buf)))


def why(buf, install):
    """What went wrong, in terms that can be acted on."""
    low = buf.lower()
    if NO_SERVE_MARKER in buf:
        return ("there is no sflab/bc2-serve in %s, so this does not look like a BindCraft2 install "
                "with the lab's wrapper in it.\n\n"
                "On Grace the shared install is /scratch/group/sflab/BindCraft2. Put that in the "
                "install directory box." % install)
    if "no such file or directory" in low and ("cd " in low or "cd:" in low):     # bash says "cd: /x: No such file"
        return "there is no directory %s on the cluster" % install
    if "no run folder at" in low:
        return ("the runs directory does not exist on the cluster:\n%s\n\n"
                "Leave the box empty for the lab's runs folder, or make the folder first." % _tail(buf, 3))
    if "address already in use" in low:
        return "the port the server was asked for is taken; leave the port box on auto"
    if "modulenotfounderror" in low or "importerror" in low:
        return ("the install's environment is incomplete: the page needs the BindCraft2 virtual "
                "environment beside it.\n%s" % _tail(buf))
    if "permission denied" in low:
        return "permission denied on the far end:\n%s" % _tail(buf)
    if buf.strip():
        return "the page stopped before it printed a URL:\n%s" % _tail(buf)
    return ""


def _tail(buf, n=14):
    lines = [l for l in buf.splitlines() if l.strip()]
    return "\n".join(lines[-n:])
