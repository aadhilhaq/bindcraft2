"""The window. Tkinter, because it is in the standard library and a launcher that needs a
toolkit installed before it can ask for a password is not a launcher.

One screen: where to connect, who you are, where BindCraft2 lives and where the runs go, and a
button. Everything else is a log, because the useful thing when a connection fails is what the
far end said. This is the HOPE-MD launcher's window with BindCraft2's names, and without its
Update button: the install here is a clone of someone else's repository, and keeping it current
is the maintainer's job rather than a button in everybody's launcher.
"""
import json
import os
import queue
import threading
import webbrowser

import tkinter as tk
from tkinter import messagebox, ttk

from . import APP, TAGLINE, __version__, credit, HOW_TO_CITE, ACK, LICENCE_NOTE
from . import clusters
from . import session as sessionmod, tunnel

#: This launcher's own settings file, not shared with any sibling launcher: several may be open
#: at once, and one file between them would have each overwriting the others' cluster and account.
CONFIG = os.path.join(os.path.expanduser("~"), ".bindcraft_launcher.json")

#: The banner's palette: the page's teal, its rust, paper.
BANNER = dict(deep="#0d5c6b", deeper="#083944", teal="#5fb3c4", warm="#c2603a",
              paper="#f4f8f8", muted="#b7d6dc", faint="#8fb6bd")


def banner_layout(width, height, line_heights, line_widths, panel=80, gutter=18, gap=20,
                  line_gap=3, motif_min=140, motif_clear=44):
    """Where everything in the header banner goes, as plain arithmetic (testable without Tk):
    every text line starts at the same x; the text block is centred vertically as a block on
    the mark's centre line; the motif starts after the widest line plus a margin and is left
    out when there is no room."""
    px = gutter
    py = (height - panel) / 2.0
    tx = px + panel + gap
    block = sum(line_heights) + line_gap * (len(line_heights) - 1)
    y = (height - block) / 2.0
    ys = []
    for lh in line_heights:
        ys.append(y)
        y += lh + line_gap
    start = tx + max(line_widths or [0]) + motif_clear
    stop = width - gutter
    motif = (start, stop) if stop - start >= motif_min else None
    return {"panel": (px, py, px + panel, py + panel), "text_x": tx, "text_ys": ys, "motif": motif}


def centre_on(pw, ph, px, py, w, h, sw, sh):
    """Where a w x h dialogue goes over a pw x ph parent at (px, py): clamped onto the screen."""
    if pw > w and ph > h:
        x = px + (pw - w) // 2
        y = py + (ph - h) // 3
    else:
        x = (sw - w) // 2
        y = (sh - h) // 3
    x = max(0, min(x, max(0, sw - w)))
    y = max(0, min(y, max(0, sh - h)))
    return x, y


def place_over(win, parent, log=None):
    """Put a dialogue over the window that raised it, then show it: never mapped unplaced."""
    try:
        if parent is not None:
            parent.update_idletasks()
        win.update_idletasks()
        w = max(win.winfo_width(), win.winfo_reqwidth())
        h = max(win.winfo_height(), win.winfo_reqheight())
        pw = ph = px = py = 0
        if parent is not None and parent.winfo_viewable():
            pw, ph = parent.winfo_width(), parent.winfo_height()
            px, py = parent.winfo_rootx(), parent.winfo_rooty()
        x, y = centre_on(pw, ph, px, py, w, h, win.winfo_screenwidth(), win.winfo_screenheight())
        win.geometry("%dx%d+%d+%d" % (w, h, x, y))
        win.deiconify()
        win.lift()
    except Exception as exc:                                    # noqa: BLE001
        if log:
            log("could not place the dialogue (%s: %s); it will open wherever the window manager puts it"
                % (type(exc).__name__, exc))
        try:
            win.deiconify()
        except Exception:                                       # noqa: BLE001
            pass


#: Bumped when a default changes in a way that makes a remembered answer wrong: an older
#: settings file keeps the cluster and the account and lets the site table fill the paths again.
SCHEMA = 1


def load():
    try:
        with open(CONFIG) as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


def save(d):
    try:
        with open(CONFIG, "w") as fh:
            json.dump(dict(d, schema=SCHEMA), fh, indent=1)
    except OSError:
        pass


class Banner(tk.Canvas):
    """The header: the mark on its panel, the name, the tagline and the build. Drawn rather
    than pasted, so it stays sharp on a high-DPI screen, needs no image file in the bundle and
    is recomputed on every resize."""

    H = 108

    def __init__(self, parent, name, tagline, build):
        super().__init__(parent, height=self.H, highlightthickness=0, bd=0, bg=BANNER["deep"])
        self.lines = (name, tagline, build)
        import tkinter.font as tkfont
        fam = tkfont.nametofont("TkDefaultFont").actual()["family"]
        self.fonts = (tkfont.Font(family=fam, size=17, weight="bold"),
                      tkfont.Font(family=fam, size=10),
                      tkfont.Font(family=fam, size=9))
        self.bind("<Configure>", self._draw)

    @staticmethod
    def _mix(a, b, t):
        a = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
        b = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
        return "#%02x%02x%02x" % tuple(int(a[k] + (b[k] - a[k]) * t) for k in range(3))

    def _round(self, x1, y1, x2, y2, r, **kw):
        pts = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
               x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
        return self.create_polygon(pts, smooth=True, **kw)

    def _mark(self, x1, y1, x2, y2):
        """The page's mark: a target ring with a binder sitting on it."""
        cx, cy = (x1 + x2) / 2.0, (y1 + y2) / 2.0
        r = min(x2 - x1, y2 - y1) * 0.34
        self.create_oval(cx - r, cy - r, cx + r, cy + r, outline=BANNER["paper"], width=3)
        d = r * 0.62
        self.create_polygon(cx - d, cy, cx, cy - d, cx + d, cy, cx, cy + d,
                            fill="", outline=BANNER["warm"], width=3, joinstyle="round")

    def _draw(self, _e=None):
        self.delete("all")
        w, h = max(self.winfo_width(), 1), self.H
        for x in range(0, w, 4):
            self.create_rectangle(x, 0, x + 4, h, width=0,
                                  fill=self._mix(BANNER["deep"], BANNER["deeper"], x / float(w)))
        widths = [f.measure(t) for f, t in zip(self.fonts, self.lines)]
        heights = [f.metrics("linespace") for f in self.fonts]
        L = banner_layout(w, h, heights, widths)
        if L["motif"]:
            # a chain of residues to the right, in rust, as on the page's header
            a, b = L["motif"]
            n, mid = 9, h / 2.0
            step = (b - a) / float(n - 1)
            ys = [9, -7, 5, -1, 7, -5, 3, -2, 1]
            pts = [(a + i * step, mid + ys[i] * 1.6) for i in range(n)]
            self.create_line(*[c for p in pts for c in p], width=4, smooth=True, capstyle="round",
                             fill=self._mix(BANNER["deep"], BANNER["warm"], .75))
            for x, y in (pts[0], pts[-1]):
                self.create_oval(x - 6, y - 6, x + 6, y + 6, width=0,
                                 fill=self._mix(BANNER["deep"], BANNER["warm"], .85))
        x1, y1, x2, y2 = L["panel"]
        self._round(x1, y1, x2, y2, 18, width=0, fill=self._mix(BANNER["deep"], BANNER["teal"], .18))
        self._mark(x1, y1, x2, y2)
        colours = (BANNER["paper"], BANNER["muted"], BANNER["faint"])
        for text, font, y, col in zip(self.lines, self.fonts, L["text_ys"], colours):
            self.create_text(L["text_x"], y, text=text, font=font, fill=col, anchor="nw")


class App:
    def __init__(self, root):
        self.root = root
        self.q = queue.Queue()
        self.lines = []          # every line, plain and technical alike, kept for a failure
        self.t = None
        self.session = None
        cfg = load()

        root.title("%s launcher" % APP)
        root.minsize(700, 580)
        pad = dict(padx=10, pady=5)

        build = os.environ.get("BINDCRAFT_BUILD") or __version__
        self.banner = Banner(root, APP, TAGLINE, "launcher build %s" % build)
        self.banner.pack(fill="x", pady=(0, 6))

        form = ttk.LabelFrame(root, text="Connection")
        form.pack(fill="x", **pad)

        self.site = tk.StringVar(value=cfg.get("site", clusters.sites()[0]))
        ttk.Label(form, text="Cluster").grid(row=0, column=0, sticky="e", padx=6, pady=4)
        self.site_box = ttk.Combobox(form, textvariable=self.site, values=clusters.sites(), state="readonly")
        self.site_box.grid(row=0, column=1, sticky="ew", padx=6, pady=4)
        self.site_box.bind("<<ComboboxSelected>>", self._on_site)

        self.host = self._row(form, 1, "Address", cfg.get("host", ""))
        self.user_label = ttk.Label(form, text="NetID")
        self.user_label.grid(row=2, column=0, sticky="e", padx=6, pady=4)
        self.user = tk.StringVar(value=cfg.get("user", ""))
        e = ttk.Entry(form, textvariable=self.user)
        e.grid(row=2, column=1, sticky="ew", padx=6, pady=4)
        self.user.trace_add("write", lambda *a: self._on_user())

        self.install = self._row(form, 3, "Install directory", cfg.get("install", ""))
        self.runs = self._row(form, 4, "Runs directory", cfg.get("runs", ""))
        # never filled in for the person and not required: empty means the server's own default
        self.runs_note = ttk.Label(form, text="", foreground="#5f7070", wraplength=580, justify="left")
        self.runs_note.grid(row=5, column=1, sticky="w", padx=6, pady=(0, 4))
        self.port = self._row(form, 6, "Port on the cluster", cfg.get("port", "auto"))
        ttk.Label(form, text="auto lets the server pick one that is free, which is what stops two people colliding",
                  foreground="#5f7070").grid(row=7, column=1, sticky="w", padx=6, pady=(0, 4))
        self.note = ttk.Label(form, text="", foreground="#5f7070", wraplength=580, justify="left")
        self.note.grid(row=8, column=1, sticky="w", padx=6, pady=(0, 6))
        # Which fields the person has taken over: a typed box is never rewritten by a site change.
        self._touched = set()
        self.jump = tk.StringVar(value=cfg.get("jump", ""))      # for a site reached through a gateway
        self.key = tk.StringVar(value=cfg.get("key", ""))
        for name in ("host", "install", "runs", "jump", "key"):
            var = getattr(self, name)
            var.trace_add("write", self._mark(name, var))
        self._apply_site(first=True, cfg=cfg)
        form.columnconfigure(1, weight=1)

        bar = ttk.Frame(root)
        bar.pack(fill="x", **pad)
        self.go = ttk.Button(bar, text="Connect and open", command=self.start)
        self.go.pack(side="left")
        self.open_btn = ttk.Button(bar, text="Open in browser", command=self.open_browser, state="disabled")
        self.open_btn.pack(side="left", padx=6)
        self.stop_btn = ttk.Button(bar, text="Disconnect", command=self.close, state="disabled")
        self.stop_btn.pack(side="left")
        self.status = ttk.Label(bar, text="not connected", foreground="#5f7070")
        self.status.pack(side="right")

        box = ttk.LabelFrame(root, text="What is happening")
        box.pack(fill="both", expand=True, **pad)
        self.log = tk.Text(box, height=15, wrap="word", font=("TkFixedFont", 10))
        self.log.pack(fill="both", expand=True, side="left")
        sb = ttk.Scrollbar(box, command=self.log.yview)
        sb.pack(fill="y", side="right")
        self.log.configure(yscrollcommand=sb.set, state="disabled")

        self.verbose = tk.BooleanVar(value=False)
        ttk.Checkbutton(root, text="Show technical details", variable=self.verbose,
                        command=self._replay).pack(anchor="w", padx=12)
        ttk.Label(root, text=credit(), foreground="#5f7070", wraplength=690,
                  justify="left").pack(anchor="w", padx=10, pady=(4, 8))

        root.protocol("WM_DELETE_WINDOW", self.quit)
        self.pump()

    # ---- the site table drives the form ---------------------------------
    def _mark(self, name, var):
        def cb(*_a):
            if getattr(self, "_filling", False):
                return
            self._touched.add(name)
        return cb

    def _set(self, name, value):
        if name in self._touched:
            return
        self._filling = True
        try:
            getattr(self, name).set(value)
        finally:
            self._filling = False

    def _apply_site(self, first=False, cfg=None):
        user = self.user.get().strip()
        d = clusters.defaults_for(self.site.get(), user)
        cfg = cfg or {}
        if first and cfg.get("schema") == SCHEMA:
            # a saved answer counts as the person's own, unless it is a half-typed account path
            for name in ("host", "install", "runs", "jump", "key"):
                if cfg.get(name) and not clusters.half_typed(cfg.get(name), user):
                    self._touched.add(name)
        # a remembered path saved mid-keystroke is dropped, never frozen
        for name in ("install", "runs"):
            if name in self._touched and clusters.half_typed(getattr(self, name).get(), user):
                self._touched.discard(name)
        self._set("host", d["host"])
        self._set("install", d["install"])
        self._set("runs", d["runs"])
        self._set("jump", d["jump"])
        self._set("key", d["key"])
        self.user_label.configure(text=d["label"])
        self.runs_note.configure(text=d.get("runs_hint", ""))
        note = d["note"]
        if d["hint"]:
            note = "%s  %s" % (note, d["hint"])
        self.note.configure(text=note.strip())

    def _on_site(self, _event=None):
        self._apply_site()

    def _on_user(self):
        self._apply_site()

    def suggested_port(self):
        return clusters.suggested_port(self.user.get().strip())

    def _row(self, parent, r, label, value):
        ttk.Label(parent, text=label).grid(row=r, column=0, sticky="e", padx=6, pady=4)
        var = tk.StringVar(value=value)
        w = ttk.Entry(parent, textvariable=var)
        w.grid(row=r, column=1, sticky="ew", padx=6, pady=4)
        return var

    # ---- the log and the queue ------------------------------------------
    def say(self, text):
        self.q.put(("log", str(text)))

    def detail(self, text):
        for ln in str(text).splitlines():
            if ln.strip():
                self.q.put(("detail", ln.rstrip()))

    def from_cluster(self, text):
        """The server's own output: the line naming the runs folder is worth reading."""
        for ln in str(text).splitlines():
            if not ln.strip():
                continue
            if ln.startswith("bindcraft2: runs in"):
                self.say("  " + ln.split("bindcraft2: ", 1)[1].strip())
            else:
                self.detail(ln)

    def _replay(self):
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        for kind, line in self.lines:
            if kind == "detail" and not self.verbose.get():
                continue
            self.log.insert("end", ("    " + line if kind == "detail" else line) + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def show_details(self):
        self.verbose.set(True)
        self._replay()

    def pump(self):
        try:
            while True:
                kind, payload = self.q.get_nowait()
                if kind in ("log", "detail"):
                    self.lines.append((kind, payload.rstrip()))
                    if kind == "detail" and not self.verbose.get():
                        continue
                    self.log.configure(state="normal")
                    self.log.insert("end", ("    " if kind == "detail" else "") + payload.rstrip() + "\n")
                    self.log.see("end")
                    self.log.configure(state="disabled")
                elif kind == "status":
                    self.status.configure(text=payload)
                elif kind == "ready":
                    self.open_btn.configure(state="normal")
                    self.stop_btn.configure(state="normal")
                    self.go.configure(state="normal")
                    self.open_browser()
                elif kind == "details":
                    self.show_details()
                elif kind == "failed":
                    self.go.configure(state="normal")
                    messagebox.showerror(APP, payload)
        except queue.Empty:
            pass
        self.root.after(120, self.pump)

    # ---- the Duo dialogue, on the main thread ---------------------------
    def ask(self, title, instructions, prompts):
        """One dialogue per challenge, however many fields it carries; built on the main thread,
        the worker waits on an event."""
        done = threading.Event()
        answers = []

        def build():
            win = tk.Toplevel(self.root)
            win.withdraw()                      # hidden until it has a position
            win.title(title or "%s - sign in" % APP)
            win.transient(self.root)
            if instructions and instructions.strip():
                ttk.Label(win, text=instructions.strip(), wraplength=460,
                          justify="left").pack(anchor="w", padx=12, pady=(12, 4))
            entries = []
            for text, echo in prompts:
                ttk.Label(win, text=text.strip() or "Response", wraplength=460,
                          justify="left").pack(anchor="w", padx=12, pady=(8, 2))
                e = ttk.Entry(win, width=44, show="" if echo else "•")
                e.pack(fill="x", padx=12)
                entries.append(e)
            if entries:
                entries[0].focus_set()
            row = ttk.Frame(win)
            row.pack(fill="x", padx=12, pady=12)

            def ok(*_):
                answers.extend(e.get() for e in entries)
                win.destroy()
                done.set()

            def cancel():
                win.destroy()
                done.set()

            ttk.Button(row, text="Continue", command=ok).pack(side="right")
            ttk.Button(row, text="Cancel", command=cancel).pack(side="right", padx=6)
            win.bind("<Return>", ok)
            win.bind("<Escape>", lambda *_a: cancel())
            win.protocol("WM_DELETE_WINDOW", cancel)
            win.resizable(False, False)
            place_over(win, self.root, log=self.say)
            win.grab_set()
            win.attributes("-topmost", True)
            win.after(300, lambda: win.attributes("-topmost", False))
            if entries:
                entries[0].focus_force()

        self.root.after(0, build)
        done.wait()
        return answers or [""] * len(prompts)

    # ---- the work -------------------------------------------------------
    def start(self):
        host, user = self.host.get().strip(), self.user.get().strip()
        if not host or not user:
            messagebox.showwarning(APP, "The cluster and your account are both needed.")
            return
        save({"site": self.site.get(), "port": self.port.get(), "host": host, "user": user,
              "install": self.install.get(), "runs": self.runs.get(),
              "jump": self.jump.get(), "key": self.key.get()})
        self.go.configure(state="disabled")
        self.q.put(("status", "connecting"))
        threading.Thread(target=self.work, args=(host, user), daemon=True).start()

    def work(self, host, user):
        try:
            jump = clusters.parse_jump(self.jump.get())
            key = self.key.get().strip() or None
            if jump:
                self.say("Connecting to %s as %s through the gateway %s:%d..." % (host, user, jump[0], jump[1]))
            else:
                self.say("Connecting to %s as %s..." % (host, user))
                self.say("Approve the Duo prompt when it reaches your phone.")
            self.t = tunnel.connect(host, user, self.ask, jump=jump, key=key, log=self.detail)
            self.say("Signed in.")
            self.q.put(("status", "starting the page"))
            self.say("Starting the BindCraft2 page on the login node...")
            port = clusters.parse_port(self.port.get())
            if port:
                self.detail("asking the cluster for port %d" % port)
            self.session = sessionmod.start(
                self.t, self.install.get().strip(), self.runs.get().strip(), port=port,
                on_output=self.from_cluster, forward=tunnel.forward, free_port=tunnel.free_port)
            self.say("Ready. Opening it in your browser.")
            self.say("  If it does not open, paste this in: %s" % self.session.url)
            self.say("")
            self.say(HOW_TO_CITE)
            self.say(ACK)
            self.q.put(("status", "connected"))
            self.q.put(("ready", ""))
        except Exception as exc:                                # noqa: BLE001
            self.say("")
            self.say("Could not connect: %s" % exc)
            self.say("The technical detail is below - send it with a report.")
            self.q.put(("details", ""))
            self.q.put(("status", "not connected"))
            self.q.put(("failed", str(exc)))

    def open_browser(self):
        if self.session:
            webbrowser.open(self.session.url)

    def close(self):
        if self.session:
            self.session.stop()
            self.session = None
        if self.t:
            try:
                self.t.close()
            except Exception:                                   # noqa: BLE001
                pass
            self.t = None
        self.open_btn.configure(state="disabled")
        self.stop_btn.configure(state="disabled")
        self.q.put(("status", "not connected"))
        self.say("Disconnected. A campaign already queued carries on without the launcher; "
                 "connect again to watch it.")

    def quit(self):
        self.close()
        self.root.destroy()


def main():
    root = tk.Tk()
    try:
        ttk.Style().theme_use("clam")
    except Exception:                                           # noqa: BLE001
        pass
    app = App(root)
    app.say(LICENCE_NOTE)
    root.mainloop()
