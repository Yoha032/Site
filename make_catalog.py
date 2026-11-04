# Запуск: python make_catalog.py ПАПКА_С_ПОДКАСТАМИ
# Структура: ПАПКА/Интервью/2026-10-11 Тема.mp3 (дата в начале имени файла)
import os, re, sys, json
try:
    from mutagen.mp3 import MP3
except ImportError:
    MP3 = None
root = sys.argv[1]
folders = []
for name in sorted(os.listdir(root)):
    p = os.path.join(root, name)
    if not os.path.isdir(p):
        continue
    eps = []
    for f in sorted(os.listdir(p)):
        if not f.lower().endswith(".mp3"):
            continue
        m = re.match(r"(\d{4}-\d{2}-\d{2})[ _-]*(.*)\.mp3$", f, re.I)
        date, title = (m.group(1), m.group(2)) if m else ("", f[:-4])
        e = {"title": title or f[:-4], "file": name + "/" + f, "date": date}
        if MP3:
            e["duration"] = int(MP3(os.path.join(p, f)).info.length)
        eps.append(e)
    if eps:
        folders.append({"name": name, "episodes": eps})
json.dump({"base": "", "folders": folders}, open("catalog.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("Готово: catalog.json, папок:", len(folders))
