UNREAL AGENT - ishlatish
========================
1) Python 3.10+ o'rnating (python.org, "Add to PATH" belgilang).
2) setup.bat ni ishga tushiring.
3) TEKIN kalit: aistudio.google.com/apikey -> Create API key -> nusxala.
   cmd da bir marta:  setx GEMINI_API_KEY "AIza..."
   (Pullik Claude uchun config.json da "provider": "anthropic" va setx ANTHROPIC_API_KEY)
4) config.json:
     unreal_editor_exe -> UnrealEditor-Cmd.exe yo'li (versiyangizga moslang)
     project_path      -> .uproject fayl yo'li
   Unreal'da: Edit > Plugins > "Python Editor Script Plugin" yoqilgan bo'lsin.
5) test_notify.bat - yashil/qizil xabar ishlashini tekshiradi.
6) start_agent.bat - agentni ishga tushiring, oynani yopmang (minimize qiling).

ISHLATISH
---------
inbox/ papkasiga zip tashlang. Vazifani ikki usuldan biri bilan bering:
  a) zip bilan bir xil nomli matn fayl:  model.zip + model.txt
  b) zip ichiga task.txt qo'ying
Masalan task.txt: "Barcha .fbx modellarni /Game/Imported ga import qil va
MainLevel'ga 100 birlik oraliq bilan qatorga joylashtir."

Tugagach ekranda 3 soniya yashil "Ish muvaffaqiyatli yakunlandi" yoki
qizil "Ish muvaffaqiyatsiz bo'ldi" chiqadi. Zip done/ yoki failed/ ga o'tadi.
Batafsil loglar: work/<ish>/agent.log va unreal_*.log

RUN MODE
--------
"commandlet" - oynasiz, tez, avtomatik yopiladi (tavsiya).
"editor"     - UnrealEditor.exe (Cmd emas) yo'lini bering, to'liq editor ochiladi
               va ish tugagach o'zi yopiladi (ba'zi editor funksiyalari uchun kerak).
