"""What differs between one cluster and the next, as a table rather than in code.

Selecting a site fills in the rest: a person should need to know their account and password,
not where the lab keeps its install. "Other (SLURM)" covers any other cluster with a BindCraft2
install of the same shape.
"""
from __future__ import annotations

import os
import re
import shlex

FEEDBACK_TO = os.environ.get("BINDCRAFT_FEEDBACK_TO") or "aadhil.haq@tamu.edu"

OTHER = "Other (SLURM)"

SITES = {
    # The lab's shared install: the BindCraft2 checkout, which carries its own environment and
    # the AlphaFold weights, so there is nothing for a user to install or load.
    "Grace (TAMU)": {
        "host": "grace.hprc.tamu.edu",
        "auth": "password",
        "install": "/scratch/group/sflab/BindCraft2",
        # The runs directory is never filled in for the person and is not required: empty means
        # the server's default, the lab's runs folder with a folder per person inside it.
        "runs": "",
        "runs_hint": "optional: empty means the lab's runs folder, /scratch/group/sflab/bindcraft_runs/<NetID>; "
                     "name another folder to write runs there instead, or to read runs somebody opened to you",
        "hint": "Your NetID.",
        "label": "NetID",
        "note": "Password and a Duo approval on every login.",
    },
    OTHER: {
        "host": "",
        "auth": "password",
        "install": "~/BindCraft2",
        "runs": "",
        "runs_hint": "optional: empty means $SCRATCH/bindcraft_runs or ~/bindcraft_runs on that cluster",
        "hint": "Whatever you log in with.",
        "label": "Username",
        "note": "Any cluster with SLURM, GPUs and a BindCraft2 install carrying sflab/bc2-serve.",
    },
}


def sites():
    """The names, with the real clusters first and Other last."""
    return [n for n in SITES if n != OTHER] + [OTHER]


def _fill(template, user):
    """A path template, only once there is something to fill it with: "/scratch/user//bindcraft_runs"
    looks like an answer and is worse than an empty box."""
    if not template:
        return ""
    if "$USER" in template and not user:
        return ""
    return template.replace("$USER", user or "")


def defaults_for(site_name, user=""):
    """Every field the form can fill in by itself, for this site and account."""
    site = SITES.get(site_name) or {}
    return {
        "host": site.get("host", ""),
        "jump": site.get("jump", ""),
        "key": site.get("key", ""),
        "note": site.get("note", ""),
        "hint": site.get("hint", ""),
        "label": site.get("label", "Username"),
        "auth": site.get("auth", "password"),
        "feedback": FEEDBACK_TO,
        "install": _fill(site.get("install", ""), user),
        "runs": _fill(site.get("runs", ""), user),
        "runs_hint": site.get("runs_hint", "one folder per run goes here"),
    }


ACCOUNT_IN_PATH = re.compile(r"^/scratch/user/([^/]+)(/|$)")


def half_typed(path, user):
    """A saved path whose account segment is a strict prefix of the account now in the box
    ("/scratch/user/j/bindcraft_runs" while the box says "jane.doe") was saved mid-keystroke,
    and is dropped rather than kept."""
    m = ACCOUNT_IN_PATH.match((path or "").strip())
    if not m or not user:
        return False
    seg = m.group(1)
    return seg != user and user.startswith(seg)


# PORTS. The remote port defaults to 0: the server picks a free one and prints it, the only
# choice that cannot collide on a shared login node. The local port is derived from the account
# so it is stable for one person and unlikely to collide between people or between this launcher
# and its siblings (aptamer: 8000-8999, docking: 9100-9899, HOPE-MD: 10100-10899).
AUTO = 0
PORT_BASE = 11000
PORT_SPAN = 800          # 11000-11799


def suggested_port(user):
    seed = (user or "bindcraft") + "|bindcraft2"
    return PORT_BASE + (sum(ord(c) * (i + 1) for i, c in enumerate(seed)) % PORT_SPAN)


def parse_port(text):
    """What the port box means. Blank or 'auto' -> let the server choose."""
    text = (text or "").strip().lower()
    if not text or text in ("auto", "0", "any"):
        return AUTO
    if text.isdigit() and 1024 <= int(text) <= 65535:
        return int(text)
    return AUTO


def parse_jump(text):
    """'host:port' -> (host, port); blank -> None."""
    text = (text or "").strip()
    if not text:
        return None
    host, _, port = text.partition(":")
    return (host, int(port) if port.strip().isdigit() else 22)


def remote_path(path):
    """A path for the far end's shell, with ~ still able to expand: shlex.quote('~/BindCraft2')
    is '~/BindCraft2' in single quotes, which is exactly what stops the remote shell expanding
    the tilde."""
    path = (path or "").strip()
    if path == "~":
        return '"$HOME"'
    if path.startswith("~/"):
        return '"$HOME"/' + shlex.quote(path[2:])
    return shlex.quote(path)
