# Запуск из корня репозитория: python make_catalog.py
# Папки: podcasts/НАЗВАНИЕ_ПАПКИ/2026-10-11 Тема.mp3 (регистр папки podcasts не важен)
import os, re, json
try:
    from mutagen.mp3 import MP3
except ImportError:
    MP3 = None


def dur(path):
    if MP3 and os.path.exists(path):
        try:
            return int(MP3(path).info.length)
        except Exception:
            return None


folders = {}
for root in sorted(d for d in os.listdir(".") if d.lower() == "podcasts" and os.path.isdir(d)):
    for name in sorted(os.listdir(root)):
        p = os.path.join(root, name)
        if not os.path.isdir(p):
            continue
        eps = folders.setdefault(name, [])
        for f in sorted(os.listdir(p)):
            if not f.lower().endswith(".mp3"):
                continue
            m = re.match(r"(\d{4}-\d{2}-\d{2})[ _-]*(.*)\.mp3$", f, re.I)
            date, title = (m.group(1), m.group(2)) if m else ("", f[:-4])
            e = {"title": title or f[:-4], "file": root + "/" + name + "/" + f, "date": date}
            d = dur(os.path.join(p, f))
            if d:
                e["duration"] = d
            eps.append(e)
cat = {"base": "", "folders": [{"name": n, "episodes": e} for n, e in folders.items()]}
if os.path.exists("featured.json"):
    ft = json.load(open("featured.json", encoding="utf-8"))
    if "duration" not in ft and dur(ft["file"]):
        ft["duration"] = dur(ft["file"])
    cat["featured"] = ft
json.dump(cat, open("catalog.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("Готово: папок", len(folders))
