#!/usr/bin/env python3
"""Пересобирает catalog.json по папке podcasts/.

Структура:  podcasts/<Папка>/<файл>.mp3
Имя файла:  "2026-10-24 Название выпуска.mp3"  (дата в начале необязательна)

Что уже есть в catalog.json (название, дата, обложка, длительность),
сохраняется: правьте вручную, скрипт не перезапишет.
"""
import json, re, subprocess, unicodedata
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CAT = ROOT / "catalog.json"
DEFAULT_FOLDERS = ["Интервью", "Подкасты", "Эфиры"]
EXTS = {".mp3", ".m4a"}


def nfc(s):
    return unicodedata.normalize("NFC", s)


def find_podcasts_dir():
    for d in ROOT.iterdir():
        if d.is_dir() and d.name.lower() == "podcasts":
            return d
    return None


def duration(path):
    try:
        from mutagen import File
        f = File(path)
        if f is not None and f.info and f.info.length:
            return round(f.info.length)
    except Exception:
        pass
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
            capture_output=True, text=True, timeout=60).stdout.strip()
        return round(float(out))
    except Exception:
        return 0


def added_date(path):
    try:
        out = subprocess.run(
            ["git", "log", "--diff-filter=A", "--format=%as", "--", str(path)],
            capture_output=True, text=True, cwd=ROOT, timeout=30).stdout.split()
        if out:
            return out[-1]
    except Exception:
        pass
    return date.today().isoformat()


def title_and_date(path):
    stem = nfc(path.stem)
    m = re.match(r"^(\d{4}-\d{2}-\d{2})[\s_\-]+(.+)$", stem)
    if m:
        return m.group(2).strip(), m.group(1)
    return stem.strip(), added_date(path)


def main():
    old, old_folder = {}, {}
    base, featured = "", None
    if CAT.exists():
        try:
            data = json.loads(CAT.read_text(encoding="utf-8"))
            base, featured = data.get("base", ""), data.get("featured")
            for f in data.get("folders", []):
                for e in f.get("episodes", []):
                    key = nfc(e.get("file", ""))
                    old[key] = e
                    old_folder[key] = nfc(f.get("name", ""))
        except Exception:
            pass

    pdir = find_podcasts_dir()
    found = {}
    if pdir:
        for sub in sorted(p for p in pdir.iterdir() if p.is_dir()):
            found[nfc(sub.name)] = sorted(p for p in sub.iterdir() if p.suffix.lower() in EXTS)
        # mp3 прямо в podcasts/, без подпапки, попадают в раздел «Подкасты»
        loose = [p for p in pdir.iterdir() if p.is_file() and p.suffix.lower() in EXTS]
        if loose:
            found["Подкасты"] = sorted(found.get("Подкасты", []) + loose)

    # Записи, чьи файлы лежат вне podcasts/ (например, джингл в корне), не теряем,
    # пока файл существует.
    extras = {}
    for key, e in old.items():
        if re.match(r"^podcasts/", key, re.I) or not key:
            continue
        if (ROOT / e["file"]).is_file():
            extras.setdefault(old_folder[key], []).append(dict(e))

    names = list(DEFAULT_FOLDERS) + sorted(n for n in set(found) | set(extras) if n not in DEFAULT_FOLDERS)
    folders = []
    for name in names:
        eps = list(extras.get(name, []))
        for p in found.get(name, []):
            rel = p.relative_to(ROOT).as_posix()
            prev = old.get(nfc(rel))
            if prev:
                ep = dict(prev)
                ep["file"] = rel
                if not ep.get("duration"):
                    d = duration(p)
                    if d:
                        ep["duration"] = d
            else:
                title, day = title_and_date(p)
                ep = {"title": title, "file": rel, "date": day}
                d = duration(p)
                if d:
                    ep["duration"] = d
            eps.append(ep)
        eps.sort(key=lambda e: (e.get("date", ""), e["title"]), reverse=True)
        folders.append({"name": name, "episodes": eps})

    out = {"base": base, "folders": folders}
    if featured:
        out["featured"] = featured
    CAT.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("Готово:", sum(len(f["episodes"]) for f in folders), "выпусков в", len(folders), "папках")


if __name__ == "__main__":
    main()
