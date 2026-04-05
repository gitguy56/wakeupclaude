"""
setup_autostart.py — Run this ONCE to make Wake Claude start automatically
with Windows and run silently in the background forever.

Usage:
    py setup_autostart.py          -- installs autostart
    py setup_autostart.py remove   -- removes autostart
"""

import os
import sys

# The name that appears in the Windows Startup folder.
SHORTCUT_NAME = "WakeClaude"

def get_startup_folder():
    """
    Returns the path to the current user's Windows Startup folder.
    Anything placed here runs automatically when you log in.
    """
    return os.path.join(
        os.environ["APPDATA"],
        r"Microsoft\Windows\Start Menu\Programs\Startup"
    )

def get_script_dir():
    """Returns the folder this script lives in (same folder as wake_claude.py)."""
    return os.path.dirname(os.path.abspath(__file__))

def get_pythonw_path():
    """
    Find pythonw.exe — the silent version of Python that runs without
    opening a black Command Prompt window.
    It lives right next to the python.exe you're currently running.
    """
    python_exe = sys.executable                      # e.g. C:\Python312\python.exe
    pythonw = python_exe.replace("python.exe", "pythonw.exe")

    if os.path.isfile(pythonw):
        return pythonw

    # Some installations name it differently — fall back to python.exe.
    # This will show a console window, but it will still work.
    print("  Note: pythonw.exe not found, using python.exe (a console window will appear).")
    return python_exe

def vbs_path():
    """Path where the .vbs launcher file will be saved (in the Startup folder)."""
    return os.path.join(get_startup_folder(), f"{SHORTCUT_NAME}.vbs")

def install():
    """
    Create a tiny VBScript file in the Windows Startup folder.
    VBScript is used because it can launch a program completely silently
    (no console window) using the 'WScript.Shell' object.

    The script runs:  pythonw.exe  wake_claude.py
    ...using the full absolute paths so it works no matter where you are.
    """
    script_dir = get_script_dir()
    wake_claude = os.path.join(script_dir, "wake_claude.py")
    pythonw = get_pythonw_path()

    # Check that wake_claude.py actually exists before installing.
    if not os.path.isfile(wake_claude):
        print(f"ERROR: Could not find wake_claude.py at: {wake_claude}")
        print("Make sure setup_autostart.py is in the same folder as wake_claude.py.")
        sys.exit(1)

    # Build the VBScript content.
    # CreateObject("WScript.Shell").Run(..., 0, False) launches the process
    # with window style 0 = hidden, and False = don't wait for it to finish.
    vbs_content = f"""' WakeClaude autostart launcher — created by setup_autostart.py
' This file runs silently at Windows login with no visible window.
Set shell = CreateObject("WScript.Shell")
shell.Run Chr(34) & "{pythonw}" & Chr(34) & " " & Chr(34) & "{wake_claude}" & Chr(34), 0, False
"""

    # Write the .vbs file into the Startup folder.
    vbs_file = vbs_path()
    with open(vbs_file, "w") as f:
        f.write(vbs_content)

    print()
    print("=" * 60)
    print("  Wake Claude autostart INSTALLED successfully!")
    print("=" * 60)
    print()
    print(f"  Launcher saved to:")
    print(f"  {vbs_file}")
    print()
    print("  Wake Claude will now start silently every time you log in.")
    print("  It runs in the background — no window will appear.")
    print()
    print("  To check it's running: open Task Manager > Details tab")
    print("  and look for 'pythonw.exe'.")
    print()
    print("  To remove autostart, run:  py setup_autostart.py remove")
    print()

    # Ask user if they want to start it right now without rebooting.
    try:
        answer = input("  Start Wake Claude right now? (y/n): ").strip().lower()
    except EOFError:
        answer = "n"

    if answer == "y":
        import subprocess
        subprocess.Popen([pythonw, wake_claude])
        print("  Wake Claude is now running in the background.")
    print()

def remove():
    """Remove the autostart entry by deleting the .vbs file from the Startup folder."""
    vbs_file = vbs_path()

    if os.path.isfile(vbs_file):
        os.remove(vbs_file)
        print()
        print("=" * 60)
        print("  Wake Claude autostart REMOVED.")
        print("=" * 60)
        print()
        print("  Wake Claude will no longer start at login.")
        print("  The wake_claude.py script itself was not deleted.")
        print()
    else:
        print()
        print("  No autostart entry found — nothing to remove.")
        print(f"  (Looked for: {vbs_file})")
        print()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1].lower() == "remove":
        remove()
    else:
        install()
