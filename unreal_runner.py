"""Unreal Engine'ni ishga tushiradi, Python skriptni bajartiradi, natijani qaytaradi."""
import json
import os
import subprocess
import time
from pathlib import Path

WRAPPER = '''import unreal, traceback, json
_status = {{"ok": False, "error": ""}}
try:
    _src = {script}
    exec(compile(open(_src, encoding="utf-8").read(), _src, "exec"), {{"__name__": "__main__", "unreal": unreal}})
    _status["ok"] = True
except BaseException:
    _status["error"] = traceback.format_exc()
with open({result}, "w", encoding="utf-8") as _f:
    json.dump(_status, _f)
{quit_code}
'''

def tail(path: Path, n: int = 80) -> str:
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        return "\n".join(lines[-n:])
    except Exception:
        return ""

def run_unreal(cfg: dict, script_code: str, job_dir: Path, attempt: int):
    """Return (ok: bool, report: str)."""
    user_script = (job_dir / f"ai_script_{attempt}.py").resolve()
    wrapper = (job_dir / f"wrapper_{attempt}.py").resolve()
    result = (job_dir / f"result_{attempt}.json").resolve()
    log = (job_dir / f"unreal_{attempt}.log").resolve()
    user_script.write_text(script_code, encoding="utf-8")
    editor_mode = cfg.get("run_mode", "commandlet") == "editor"
    quit_code = 'unreal.SystemLibrary.execute_console_command(None, "QUIT_EDITOR")' if editor_mode else ""
    wrapper.write_text(WRAPPER.format(
        script=json.dumps(str(user_script)), result=json.dumps(str(result)), quit_code=quit_code),
        encoding="utf-8")
    if result.exists():
        result.unlink()

    exe, proj = cfg["unreal_editor_exe"], cfg["project_path"]
    if editor_mode:
        cmd = (f'"{exe}" "{proj}" -ExecutePythonScript="{wrapper}" '
               f'-unattended -nopause -nosplash -abslog="{log}"')
    else:
        cmd = (f'"{exe}" "{proj}" -run=pythonscript -script="{wrapper}" '
               f'-unattended -nopause -nosplash -stdout -abslog="{log}"')

    start = time.time()
    proc = subprocess.Popen(cmd, shell=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    timeout = cfg.get("unreal_timeout_seconds", 3600)
    while proc.poll() is None:
        if time.time() - start > timeout:
            proc.kill()
            return False, f"Unreal {timeout} soniyada tugamadi (timeout).\n" + tail(log)
        time.sleep(2)

    if result.exists():
        status = json.loads(result.read_text(encoding="utf-8"))
        if status["ok"]:
            return True, "OK"
        return False, "Skript xatosi:\n" + status["error"] + "\n--- Unreal log (oxiri) ---\n" + tail(log, 40)
    return False, (f"Unreal exit code {proc.returncode}, natija fayli yaratilmadi "
                   f"(skript umuman ishlamagan bo'lishi mumkin).\n" + tail(log))
