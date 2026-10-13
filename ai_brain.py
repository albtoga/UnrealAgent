"""Claude API orqali Unreal Python skript yozdiradi."""
import os
import re
from pathlib import Path
import json
import os
import time
import urllib.request
import urllib.error

SYSTEM = """Sen Unreal Engine 5 Python (modul `unreal`) bo'yicha ekspertsan.
Vazifaga mos TO'LIQ ishlaydigan Python skript yoz. Qoidalar:
- Faqat bitta ```python kod bloki qaytar, boshqa matn yozma.
- Skript Unreal Editor ichida headless rejimda ishlaydi: input() yoki GUI ishlatma.
- Fayl yo'llarini aynan berilgan papkadan ol (absolyut yo'llar).
- Asset importda unreal.AssetImportTask va unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks() ishlat.
- Ishlar tugagach o'zgarishlarni saqla: unreal.EditorAssetLibrary.save_directory('/Game/...') va kerak bo'lsa unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True).
- Muvaffaqiyatsizlikda exception ko'tar (raise), jim o'tkazib yuborma.
- Har bosqichda unreal.log() bilan nima qilayotganingni yoz.
"""

def build_file_listing(extract_dir: Path, limit=300) -> str:
    items = []
    for p in sorted(extract_dir.rglob("*")):
        if p.is_file():
            items.append(f"{p.resolve()}  ({p.stat().st_size} bayt)")
        if len(items) >= limit:
            items.append("... (ro'yxat qisqartirildi)")
            break
    return "\n".join(items)

def extract_code(text: str) -> str:
    m = re.search(r"```(?:python)?\n(.*?)```", text, re.S)
    return (m.group(1) if m else text).strip()

def _call_gemini(cfg, user_text, previous_code, error_report):
    key = os.environ.get("GEMINI_API_KEY", "").strip().strip('"').strip("'")
    if not key:
        raise RuntimeError("GEMINI_API_KEY o'rnatilmagan (setup uchun README ga qarang).")
    contents = [{"role": "user", "parts": [{"text": user_text}]}]
    if previous_code and error_report:
        contents += [
            {"role": "model", "parts": [{"text": f"```python\n{previous_code}\n```"}]},
            {"role": "user", "parts": [{"text": "Bu skript xato berdi. Xatoni tahlil qilib TO'LIQ tuzatilgan skriptni qaytar.\n\n" + error_report[-6000:]}]},
        ]
    body = json.dumps({"systemInstruction": {"parts": [{"text": SYSTEM}]},
                       "contents": contents}).encode("utf-8")
    model = cfg.get("gemini_model", "gemini-2.5-flash")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    for wait in (0, 20, 60, 120):          # bepul tarif cheklovi (429) bo'lsa kutib qayta urinadi
        time.sleep(wait)
        req = urllib.request.Request(url, data=body, headers={
            "Content-Type": "application/json", "x-goog-api-key": key})
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                data = json.loads(r.read().decode("utf-8"))
            parts = data["candidates"][0]["content"]["parts"]
            return "".join(p.get("text", "") for p in parts)
        except urllib.error.HTTPError as e:
            if e.code in (429, 503):
                continue
            raise RuntimeError(f"Gemini xatosi {e.code}: {e.read().decode('utf-8', 'ignore')[:500]}")
    raise RuntimeError("Gemini bepul limiti tugadi, birozdan keyin qayta urinib ko'ring.")

def _call_nvidia(cfg, user_text, previous_code, error_report):
    key = os.environ.get("NVIDIA_API_KEY", "").strip().strip('"').strip("'")
    if not key:
        raise RuntimeError("NVIDIA_API_KEY o'rnatilmagan (setx NVIDIA_API_KEY \"nvapi-...\").")
    messages = [{"role": "system", "content": SYSTEM},
                {"role": "user", "content": user_text}]
    if previous_code and error_report:
        messages += [
            {"role": "assistant", "content": f"```python\n{previous_code}\n```"},
            {"role": "user", "content": "Bu skript xato berdi. Xatoni tahlil qilib TO'LIQ tuzatilgan skriptni qaytar.\n\n" + error_report[-6000:]},
        ]
    body = json.dumps({"model": cfg.get("nvidia_model", "meta/llama-3.3-70b-instruct"),
                       "messages": messages, "temperature": 0.2, "max_tokens": 4096,
                       "stream": False}).encode("utf-8")
    url = "https://integrate.api.nvidia.com/v1/chat/completions"
    for wait in (0, 15, 45, 90):
        time.sleep(wait)
        req = urllib.request.Request(url, data=body, headers={
            "Content-Type": "application/json", "Accept": "application/json",
            "Authorization": f"Bearer {key}", "User-Agent": "UnrealAgent/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=600) as r:
                data = json.loads(r.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            if e.code in (429, 502, 503, 504):
                continue
            raise RuntimeError(f"NVIDIA xatosi {e.code}: {e.read().decode('utf-8', 'ignore')[:500]}")
    raise RuntimeError("NVIDIA limiti yoki server band, birozdan keyin qayta urinib ko'ring.")

def _call_groq(cfg, user_text, previous_code, error_report):
    key = os.environ.get("GROQ_API_KEY", "").strip().strip('"').strip("'")
    if not key:
        raise RuntimeError("GROQ_API_KEY o'rnatilmagan (setx GROQ_API_KEY \"gsk_...\").")
    messages = [{"role": "system", "content": SYSTEM},
                {"role": "user", "content": user_text}]
    if previous_code and error_report:
        messages += [
            {"role": "assistant", "content": f"```python\n{previous_code}\n```"},
            {"role": "user", "content": "Bu skript xato berdi. Xatoni tahlil qilib TO'LIQ tuzatilgan skriptni qaytar.\n\n" + error_report[-6000:]},
        ]
    body = json.dumps({"model": cfg.get("groq_model", "llama-3.3-70b-versatile"),
                       "messages": messages, "temperature": 0.2, "max_tokens": 4096,
                       "stream": False}).encode("utf-8")
    url = "https://api.groq.com/openai/v1/chat/completions"
    for wait in (0, 15, 45, 90):
        time.sleep(wait)
        req = urllib.request.Request(url, data=body, headers={
            "Content-Type": "application/json", "Accept": "application/json",
            "Authorization": f"Bearer {key}", "User-Agent": "UnrealAgent/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=600) as r:
                data = json.loads(r.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            if e.code in (429, 502, 503, 504):
                continue
            raise RuntimeError(f"Groq xatosi {e.code}: {e.read().decode('utf-8', 'ignore')[:500]}")
    raise RuntimeError("Groq limiti yoki server band, birozdan keyin qayta urinib ko'ring.")

def _call_anthropic(cfg, user_text, previous_code, error_report):
    import anthropic
    client = anthropic.Anthropic()
    messages = [{"role": "user", "content": user_text}]
    if previous_code and error_report:
        messages += [
            {"role": "assistant", "content": f"```python\n{previous_code}\n```"},
            {"role": "user", "content": "Bu skript xato berdi. Xatoni tahlil qilib TO'LIQ tuzatilgan skriptni qaytar.\n\n" + error_report[-6000:]},
        ]
    resp = client.messages.create(model=cfg["anthropic_model"], max_tokens=8000,
                                  system=SYSTEM, messages=messages)
    return "".join(b.text for b in resp.content if b.type == "text")

def generate_script(cfg, task, extract_dir, previous_code=None, error_report=None) -> str:
    user_text = f"VAZIFA:\n{task}\n\nZIP dan chiqarilgan fayllar:\n{build_file_listing(extract_dir)}\n"
    provider = cfg.get("provider", "gemini")
    if provider == "gemini":
        text = _call_gemini(cfg, user_text, previous_code, error_report)
    elif provider == "groq":
        text = _call_groq(cfg, user_text, previous_code, error_report)
    elif provider == "nvidia":
        text = _call_nvidia(cfg, user_text, previous_code, error_report)
    else:
        text = _call_anthropic(cfg, user_text, previous_code, error_report)
    return extract_code(text)
