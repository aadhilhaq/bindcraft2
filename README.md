# BindCraft2 launcher

The desktop launcher for the HOPE Lab's [BindCraft2](https://github.com/PacesaLab/BindCraft2) page
on Grace. Run it, sign in, and the design page opens in your browser: a target, its hotspots and a
binder length go in, and the campaign is queued on a GPU node under your own account.

Nothing about BindCraft2 is installed on your computer. The launcher signs in over SSH, starts the
page on a login node, forwards a local port to it and opens a browser at the URL the page printed.
It is the HOPE-MD launcher with BindCraft2's names, so the two work the same way.

## Using it

**Windows** — download `BindCraft2-launcher-windows.zip` from the
[releases page](../../releases/latest), unzip it **whole** (the folder has to travel together) and
run `BindCraft2-launcher.exe`. It is unsigned, so the first run shows "Windows protected your PC":
More info → Run anyway.

**macOS (Apple silicon)** — download the `.zip`, unzip, then right-click the app → Open the first
time, because it is unsigned.

Then: pick **Grace (TAMU)**, type your **NetID**, press **Connect and open**. Grace asks for your
password and then a Duo approval; the launcher shows Duo's own prompt and sends back whatever you
answer. The page opens by itself.

| Box | What it is |
|---|---|
| Cluster | Grace, or another SLURM cluster with a BindCraft2 install of the same shape |
| Address | filled in by the cluster you picked |
| NetID | your own account: the page runs as you, and Slurm charges your account |
| Install directory | where BindCraft2 lives; the lab's shared install is filled in for you |
| Runs directory | leave it empty for the lab's runs folder, `/scratch/group/sflab/bindcraft_runs/<NetID>` |
| Port on the cluster | leave it on `auto`: the page takes a free port, which is what stops two people colliding |

**Disconnect** stops the page and the tunnel. A campaign already queued carries on without it —
connect again to watch it, cancel it or download the designs.

## Running it from source

```bash
pip install paramiko
python -m bindcraft_launcher
```

Python 3.10 or newer, with tkinter (it comes with python.org builds and with Homebrew's
`python-tk`). `python -m bindcraft_launcher --selftest` checks the parts that need no display, and
`--version` prints the build.

## Building the executables

A tag starting with `v` builds both, attaches them to the run in the Actions tab and makes a
release page:

```bash
git tag v0.1.0 && git push origin v0.1.0
```

PyInstaller does not cross-compile, which is why the Windows build runs on a Windows runner and the
Mac build on a Mac. The workflow also builds a console copy of each and makes it prove it starts
(`--selftest`) before the windowed build is published, since a windowed executable that fails on
the first double-click cannot say why.

## The cluster side

The page, the submit tool and the environment live with the install at
`/scratch/group/sflab/BindCraft2`; `sflab/README.md` there documents them, and
`sflab/bc2-submit` does the same job from the command line. The launcher only runs
`sflab/bc2-serve` on the login node, so a change to the page needs no new launcher.

## Credits and license

BindCraft2 is by the Pacesa lab; AlphaFold 2 (CC-BY-4.0, DeepMind) and ProteinMPNN belong to their
authors, and each campaign records the versions it used in `campaign_metadata.json`. Please cite
BindCraft2, AlphaFold 2 and ProteinMPNN, and acknowledge Texas A&M High Performance Research
Computing.

BindCraft2 may not be offered to third parties as a hosted service: the lab's install is for the
lab's own work, so please do not give people outside the group access to it or to a page that
submits to it.

Launcher by Aadhil Haq, HOPE Lab (PI Dr. Sandun Fernando), Texas A&M University.
