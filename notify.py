"""Ekranda yashil/qizil xabar chiqaradi va N soniyadan keyin yo'qoladi.
Ishlatish: python notify.py success|fail "matn" [soniya]"""
import sys
import tkinter as tk

def show(kind: str, text: str, seconds: float = 3.0):
    root = tk.Tk()
    root.overrideredirect(True)
    root.attributes("-topmost", True)
    color = "#16a34a" if kind == "success" else "#dc2626"
    root.configure(bg=color)
    w, h = 640, 130
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    root.geometry(f"{w}x{h}+{(sw - w) // 2}+{int(sh * 0.08)}")
    tk.Label(root, text=text, fg="white", bg=color,
             font=("Segoe UI", 22, "bold"), wraplength=w - 40).pack(expand=True, fill="both")
    root.after(int(seconds * 1000), root.destroy)
    root.mainloop()

if __name__ == "__main__":
    kind = sys.argv[1] if len(sys.argv) > 1 else "success"
    text = sys.argv[2] if len(sys.argv) > 2 else "Test"
    secs = float(sys.argv[3]) if len(sys.argv) > 3 else 3.0
    show(kind, text, secs)
