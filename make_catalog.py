# Запуск из корня репозитория: python make_catalog.py
# Папки: podcasts/НАЗВАНИЕ_ПАПКИ/2026-10-11 Тема.mp3
# Дата может быть в начале имени файла ИЛИ в конце названия («… 24 октября»).
# Папка = раздел на сайте. Регистр папки podcasts не важен.
import os
import re
import json

try:
    from mutagen.mp3 import MP3
except ImportError:
    MP3 = None

DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")
MONTHS = {
    "января": "01", "февраля": "02", "марта": "03", "апреля": "04",
    "мая": "05", "июня": "06", "июля": "07", "августа": "08",
    "сентября": "09", "октября": "10", "ноября": "11", "декабря": "12",
}


def dur(path):
    if MP3 and os.path.exists(path):
        try:
            return int(MP3(path).info.length)
        except Exception:
            return None
    return None


def extract_date_and_title(filename):
    """Из имени файла достаём ISO-дату и чистое название."""
    name = filename[:-4] if filename.lower().endswith(".mp3") else filename

    # 1) Явная ISO-дата в начале: 2026-10-24 Тема
    m = re.match(r"^(\d{4}-\d{2}-\d{2})[ _\-–—]*(.*)$", name)
    if m:
        return m.group(1), (m.group(2) or name).strip(" _-–—") or name

    # 2) ISO-дата где угодно в имени
    m = DATE_RE.search(name)
    if m:
        date = m.group(1)
        title = (name[: m.start()] + name[m.end() :]).strip(" _-–—")
        return date, title or name

    # 3) «24 октября» или «24 октября 2026»
    m = re.search(
        r"(\d{1,2})\s+(января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)(?:\s+(\d{4}))?",
        name,
        re.I,
    )
    if m:
        day = int(m.group(1))
        mon = MONTHS[m.group(2).lower()]
        year = m.group(3) or "2026"
        date = f"{year}-{mon}-{day:02d}"
        title = (name[: m.start()] + name[m.end() :]).strip(" _-–—")
        return date, title or name

    return "", name.strip()


def main():
    folders = {}
    for root in sorted(
        d for d in os.listdir(".") if d.lower() == "podcasts" and os.path.isdir(d)
    ):
        for name in sorted(os.listdir(root)):
            p = os.path.join(root, name)
            if not os.path.isdir(p):
                continue
            eps = folders.setdefault(name, [])
            for f in sorted(os.listdir(p)):
                if not f.lower().endswith(".mp3"):
                    continue
                date, title = extract_date_and_title(f)
                rel = f"{root}/{name}/{f}"
                e = {"title": title or f[:-4], "file": rel, "date": date}
                d = dur(os.path.join(p, f))
                if d:
                    e["duration"] = d
                eps.append(e)

    # Стабильный порядок разделов
    preferred = ["Интервью", "Подкасты", "Эфиры"]
    ordered = []
    seen = set()
    for n in preferred:
        if n in folders:
            ordered.append({"name": n, "episodes": folders[n]})
            seen.add(n)
    for n, eps in folders.items():
        if n not in seen:
            ordered.append({"name": n, "episodes": eps})

    cat = {"base": "", "folders": ordered}

    if os.path.exists("featured.json"):
        with open("featured.json", encoding="utf-8") as fh:
            ft = json.load(fh)
        if "duration" not in ft and ft.get("file"):
            d = dur(ft["file"])
            if d:
                ft["duration"] = d
        cat["featured"] = ft

    with open("catalog.json", "w", encoding="utf-8") as fh:
        json.dump(cat, fh, ensure_ascii=False, indent=1)

    total = sum(len(f["episodes"]) for f in ordered)
    print(f"Готово: папок {len(ordered)}, выпусков {total}")


if __name__ == "__main__":
    main()
