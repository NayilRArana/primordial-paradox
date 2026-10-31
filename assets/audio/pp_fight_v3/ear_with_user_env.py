"""ear_with_user_env.py: run tools/ear_critic.py with GEMINI_API_KEY taken from the Windows user
environment store, without ever printing the value.

Why this exists: the dispatched worker's shell does not inherit the user level environment, so
os.environ is empty for GEMINI_API_KEY and ear_critic refuses to run. This wrapper reads the same
store Windows uses to populate os.environ (HKCU\\Environment, then the machine environment), puts
the value into this process's os.environ only, and hands straight over to ear_critic. Nothing is
written to disk and the value is never printed: the only output is ear_critic's own.

Usage (same arguments as ear_critic.py):
    python ear_with_user_env.py --dry-run pp_fight_v3_calm.mp3
    python ear_with_user_env.py pp_fight_v3_calm.mp3
"""

import os
import runpy
import sys

NAMES = ("GEMINI_API_KEY",)
HIVES = (
    (r"Environment", "HKCU"),
    (r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment", "HKLM"),
)


def load(winreg):
    found = []
    for subkey, hive_name in HIVES:
        hive = winreg.HKEY_CURRENT_USER if hive_name == "HKCU" else winreg.HKEY_LOCAL_MACHINE
        try:
            with winreg.OpenKey(hive, subkey) as key:
                for name in NAMES:
                    if os.environ.get(name, "").strip():
                        continue
                    try:
                        value, _ = winreg.QueryValueEx(key, name)
                    except OSError:
                        continue
                    if isinstance(value, str) and value.strip():
                        os.environ[name] = value.strip()
                        found.append("%s from %s" % (name, hive_name))
        except OSError:
            continue
    return found


def main():
    try:
        import winreg
    except ImportError:
        winreg = None
    if winreg is not None:
        for line in load(winreg):
            print("env: %s" % line)
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(os.path.dirname(os.path.dirname(here)))
    script = os.path.join(root, "tools", "ear_critic.py")
    sys.argv = [script] + sys.argv[1:]
    runpy.run_path(script, run_name="__main__")


if __name__ == "__main__":
    main()
