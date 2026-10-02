"""The desktop launcher: open the BindCraft2 page from a laptop.

It makes an SSH connection to the cluster, starts the page's own web server on a login node,
forwards a local port to it and opens a browser. Nothing about BindCraft2 has to be installed
on the laptop except this launcher and paramiko. It is the HOPE-MD launcher (its
hopemd_launcher/) with BindCraft2's names; the lab's launchers are meant to feel identical.
"""

__version__ = "0.1.0"
APP = "BindCraft2"
TAGLINE = "design a binder, on Grace"
BLURB = "Binder design with AlphaFold 2 and ProteinMPNN: a target, its hotspots, a binder length."
LAB = "HOPE Lab"
AUTHORS = ("Aadhil Haq",)
PI = "Dr. Sandun Fernando"
POWERED_BY = "Powered by HOPE Lab"

# What this is, and whose the method is. This launcher opens the lab's BindCraft2 page; the
# method and the models belong to their authors.
ENGINE_CREDIT = ("A launcher for the lab's BindCraft2 page; BindCraft2 is by the Pacesa lab, and "
                 "AlphaFold 2 and ProteinMPNN belong to their authors. %s." % POWERED_BY)

HOW_TO_CITE = ("How to cite: BindCraft2 (github.com/PacesaLab/BindCraft2), AlphaFold 2 and "
               "ProteinMPNN. Each campaign records the versions it used in its "
               "campaign_metadata.json.")

ACK = "Please acknowledge Texas A&M High Performance Research Computing (HPRC) for the computational resources."

# BindCraft2 is source-available and free to use, with one restriction that matters here: it may
# not be offered to third parties as a hosted service. The launcher reaches the lab's own install
# with the person's own account, which is the intended use.
LICENCE_NOTE = ("The lab's install is for the lab's own work: please do not give people outside "
                "the group access to it, or to a page that submits to it.")


def credit(sep=" · "):
    """The credit line, and nothing appended to it."""
    return ENGINE_CREDIT
