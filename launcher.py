import os, sys, time, subprocess, urllib.request, webbrowser

ROOT = os.path.dirname(os.path.abspath(__file__))
APP = os.path.join(ROOT, "webapp.py")
URL = "http://127.0.0.1:8765/"

def app_running():
    try:
        with urllib.request.urlopen(URL + "status", timeout=2) as r:
            return r.status == 200
    except Exception:
        return False

def main():
    if not app_running():
        exe = sys.executable
        pyw = exe[:-10] + "pythonw.exe" if exe.lower().endswith("python.exe") else exe
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        subprocess.Popen([pyw, APP], cwd=ROOT, creationflags=flags)
        for _ in range(30):
            if app_running():
                break
            time.sleep(1)
    webbrowser.open(URL)

if __name__ == "__main__":
    main()
