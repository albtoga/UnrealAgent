@echo off
cd /d "%~dp0"
python notify.py success "Ish muvaffaqiyatli yakunlandi"
python notify.py fail "Ish muvaffaqiyatsiz bo'ldi"
