"""Asosiy dastur: inbox papkasini kuzatadi, zip kelsa ishni bajaradi."""
import json
import shutil
import subprocess
import sys
import time
import traceback
import zipfile
from datetime import datetime
from pathlib import Path

import ai_brain
import unreal_runner

BASE = Path(__file__).parent.resolve()
CFG = json.loads((BASE / "config.json").read_text(encoding="utf-8"))
INBOX = BASE / CFG["inbox_dir"]
WORK = BASE / CFG["work_dir"]
DONE, FAILED = INBOX / "done", INBOX / "failed"
for d in (INBOX, WORK, DONE, FAILED):
    d.mkdir(parents=True, exist_ok=True)

# Yordam sahifasi havolasi. config.json ga "help_url": "https://..." deb yozsangiz shu ishlatiladi.
HELP_URL = CFG.get("help_url", "https://github.com/SENING_ISMING/REPO_NOMI#vazifani-qanday-yozaman")


class TaskError(Exception):
    """Vazifa noto'g'ri yoki yo'q bo'lganda."""


def notify(kind, text):
    subprocess.Popen([sys.executable, str(BASE / "notify.py"), kind, text,
                      str(CFG.get("notification_seconds", 3))],
                     creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))


def read_task(zip_path: Path, extract_dir: Path) -> str:
    side = zip_path.with_suffix(".txt")           # 1) zip yonidagi matn fayl
    if side.exists():
        return side.read_text(encoding="utf-8", errors="ignore").strip()
    for name in ("task.txt", "vazifa.txt", "prompt.txt"):   # 2) zip ichidagi matn
        for p in extract_dir.rglob(name):
            return p.read_text(encoding="utf-8", errors="ignore").strip()
    raise TaskError("Vazifa topilmadi: zip bilan bir xil nomli .txt yoki zip ichida task.txt kerak.")


def process(zip_path: Path):
    job = WORK / f"{zip_path.stem}_{datetime.now():%Y%m%d_%H%M%S}"
    extract_dir = job / "extracted"
    extract_dir.mkdir(parents=True)
    log = job / "agent.log"

    def say(msg):
        line = f"[{datetime.now():%H:%M:%S}] {msg}"
        print(line)
        with log.open("a", encoding="utf-8") as f:
            f.write(line + "\n")

    try:
        say(f"Ish boshlandi: {zip_path.name}")
        with zipfile.ZipFile(zip_path) as z:
            z.extractall(extract_dir)
        task = read_task(zip_path, extract_dir)
        if len(task) < 15:
            raise TaskError("Vazifa juda qisqa. Nima qilish kerakligini aniqroq yozing.")
        say(f"Vazifa: {task[:200]}")
        code, report = None, None
        for attempt in range(1, CFG["max_attempts"] + 1):
            say(f"Urinish {attempt}: AI skript yozmoqda...")
            code = ai_brain.generate_script(CFG, task, extract_dir, code, report)
            say("Unreal ishga tushmoqda...")
            ok, report = unreal_runner.run_unreal(CFG, code, job, attempt)
            if ok:
                say("MUVAFFAQIYATLI")
                notify("success", "Ish muvaffaqiyatli yakunlandi")
                shutil.move(str(zip_path), DONE / zip_path.name)
                return
            say(f"Xato:\n{report[:1500]}")
        raise RuntimeError(f"Barcha urinishlar muvaffaqiyatsiz. Vazifa aniq yozilganmi? Yordam: {HELP_URL}")
    except TaskError as e:
        say(f"VAZIFA XATOSI: {e}\nYordam sahifasi: {HELP_URL}")
        notify("fail", "Vazifa noto'g'ri yozilgan. Yordam sahifasiga qarang")
        if zip_path.exists():
            shutil.move(str(zip_path), FAILED / zip_path.name)
    except Exception as e:
        say(f"MUVAFFAQIYATSIZ: {e}\n{traceback.format_exc()}")
        notify("fail", "Ish muvaffaqiyatsiz bo'ldi")
        if zip_path.exists():
            shutil.move(str(zip_path), FAILED / zip_path.name)


def is_stable(p: Path) -> bool:
    try:
        s1 = p.stat().st_size
        time.sleep(1.5)
        return s1 == p.stat().st_size and s1 > 0
    except OSError:
        return False


def main():
    print(f"Kuzatilmoqda: {INBOX}\nZip fayl tashlang (Ctrl+C - to'xtatish).")
    while True:
        for z in sorted(INBOX.glob("*.zip")):
            if is_stable(z):
                process(z)
        time.sleep(2)


if __name__ == "__main__":
    main()