import os
import platform
import re
import subprocess


# // config

# where the server is : uses your ~/.ssh/config alias, so "weep" is enough
SSH_HOST = os.getenv("WEEP_SSH_HOST", "weep")   # alias from ~/.ssh/config
SSH_USER = os.getenv("WEEP_SSH_USER", "secagent") # the scoped user, never root
MODE = os.getenv("WEEP_TOOL_MODE", "auto")      # auto | local | ssh

ALLOWED_UNITS = {"weep-manager", "weep-site", "nginx", "fail2ban", "ssh", "kage-web"}

UNIT_RE = re.compile(r"^[a-zA-Z0-9_.@-]{1,64}$")


# defining the command builder

def build_command(unit, lines):
    """Returns the argv to run. Local on the server, over ssh from anywhere else."""

    base = ["journalctl", "-u", unit, "-n", str(lines), "--no-pager"]

    use_local = MODE == "local" or (MODE == "auto" and platform.system() == "Linux")

    if use_local:
        return ["sudo", "-n"] + base, "local"

    # remote : same command, run as the scoped user over ssh
    remote = "sudo -n " + " ".join(base)

    return [
        "ssh",
        "-o", "BatchMode=yes",     # never hang on a password prompt
        "-o", "ConnectTimeout=10", # fail fast when the box is unreachable
        SSH_USER + "@" + SSH_HOST,
        remote,
    ], "ssh:" + SSH_USER + "@" + SSH_HOST


# defining the tool

def get_logs(unit, lines=50):
    """Read the most recent log lines for an allowed service. Read only."""

    unit = str(unit).strip().lower()

    # never build a shell string : fixed command + checked arguments
    if not UNIT_RE.match(unit):
        return {"ok": False, "error": "invalid unit name"}

    if unit not in ALLOWED_UNITS:
        return {"ok": False, "error": "unit not allowed: " + unit}

    try:
        lines = max(1, min(int(lines), 200))

    except (TypeError, ValueError):
        lines = 50

    argv, where = build_command(unit, lines)

    try:
        r = subprocess.run(argv, capture_output=True, text=True, timeout=40)

    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "timed out reading logs", "where": where}

    except FileNotFoundError:
        missing = argv[0]
        return {"ok": False, "error": missing + " not found on this machine", "where": where}

    return {
        "ok": r.returncode == 0,
        "unit": unit,
        "lines": lines,
        "where": where,
        "stdout": r.stdout[-8000:], # keep big logs out of the model context
        "stderr": r.stderr[-2000:],
        "rc": r.returncode,
    }
