import unreal, traceback, json
_status = {"ok": False, "error": ""}
try:
    _src = "C:\\Users\\asus\\Desktop\\UnrealAgent\\work\\ak45_task_20261010_173111\\ai_script_1.py"
    exec(compile(open(_src, encoding="utf-8").read(), _src, "exec"), {"__name__": "__main__", "unreal": unreal})
    _status["ok"] = True
except BaseException:
    _status["error"] = traceback.format_exc()
with open("C:\\Users\\asus\\Desktop\\UnrealAgent\\work\\ak45_task_20261010_173111\\result_1.json", "w", encoding="utf-8") as _f:
    json.dump(_status, _f)

