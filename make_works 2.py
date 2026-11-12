#!/usr/bin/env python3
"""Дополняет works.json данными со страниц видео ВК.

Для каждой записи, где `url` ведёт на ВК, берёт со страницы видео:
название, описание, длительность, дату и обложку (картинка скачивается в covers/).
Заполняются только пустые поля. Всё, что вы вписали руками, остаётся как есть.
Временные названия вида «Видео 1» считаются пустыми и заменяются настоящими.

Запускается на GitHub Actions (вкладка Actions → «Подтянуть данные о видео» → Run workflow)
или локально: python3 make_works.py
"""
import html as H
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WORKS = ROOT / "works.json"
COVERS = ROOT / "covers"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
VK = re.compile(r"vk(?:video)?\.(?:com|ru)/video(-?\d+)_(\d+)")
TEMP_TITLE = re.compile(r"^\s*Видео\s*\d*\s*$", re.I)
SITE_SUFFIX = re.compile(r"\s*[|—–-]\s*(ВКонтакте|VK Видео|VK Video|VK|ВК Видео|ВК)\s*$", re.I)


def get(url, timeout=25):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA, "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.5",
        "Accept": "text/html,application/xhtml+xml,image/avif,image/webp,*/*;q=0.8"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read(), r.headers


def decode(raw, headers):
    m = re.search(r"charset=([\w-]+)", headers.get("Content-Type", "") or "", re.I)
    for enc in ([m.group(1)] if m else []) + ["utf-8", "cp1251"]:
        try:
            return raw.decode(enc)
        except Exception:
            continue
    return raw.decode("utf-8", "replace")


def meta(page, *names):
    for n in names:
        n = re.escape(n)
        for pat in (r'<meta[^>]+(?:property|name)=["\']%s["\'][^>]*?content=["\']([^"\']*)["\']' % n,
                    r'<meta[^>]+content=["\']([^"\']*)["\'][^>]*?(?:property|name)=["\']%s["\']' % n):
            m = re.search(pat, page, re.I)
            if m and m.group(1).strip():
                return H.unescape(m.group(1)).strip()
    return ""


def iso_duration(s):
    m = re.fullmatch(r"P(?:\d+D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+(?:\.\d+)?)S)?", s or "")
    if not m or not any(m.groups()):
        return 0
    h, mi, se = (float(x or 0) for x in m.groups())
    return int(h * 3600 + mi * 60 + se)


def fmt_duration(sec):
    sec = int(sec)
    if sec <= 0:
        return ""
    h, r = divmod(sec, 3600)
    m, s = divmod(r, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def parse(page):
    """Достаёт данные из HTML страницы видео."""
    title = meta(page, "og:title", "twitter:title")
    if not title:
        m = re.search(r"<title[^>]*>(.*?)</title>", page, re.S | re.I)
        title = H.unescape(m.group(1)).strip() if m else ""
    title = SITE_SUFFIX.sub("", title).strip()
    desc = meta(page, "og:description", "description", "twitter:description")
    image = meta(page, "og:image", "twitter:image")
    dur = 0
    raw = meta(page, "og:video:duration", "video:duration")
    if raw.isdigit():
        dur = int(raw)
    if not dur:
        m = re.search(r'"duration"\s*:\s*"?(P[^"\s,}]+)', page)
        dur = iso_duration(m.group(1)) if m else 0
    if not dur:
        m = re.search(r'"duration"\s*:\s*(\d{2,6})\b', page)
        dur = int(m.group(1)) if m else 0
    date = ""
    for src in (meta(page, "video:release_date", "article:published_time", "og:video:release_date"),
                (re.search(r'"(?:uploadDate|datePublished|dateCreated)"\s*:\s*"([^"]+)"', page) or [None, ""])[1]):
        m = re.match(r"(\d{4}-\d{2}-\d{2})", src or "")
        if m:
            date = m.group(1)
            break
    return {"title": title, "desc": desc, "image": image, "duration": fmt_duration(dur), "date": date}


def fetch_info(oid, vid):
    last = None
    for host in ("vkvideo.ru", "vk.com"):
        url = f"https://{host}/video{oid}_{vid}"
        try:
            raw, headers = get(url)
            info = parse(decode(raw, headers))
            if info["title"] and not re.search(r"^(Вход|Авторизация|Доступ ограничен|Ошибка)", info["title"], re.I):
                return info
            last = "страница без названия (нужен вход или видео закрыто)"
        except Exception as e:
            last = f"{type(e).__name__}: {e}"
    raise RuntimeError(last)


def save_cover(image_url, oid, vid):
    if not image_url.startswith("http"):
        return ""
    raw, headers = get(image_url)
    ctype = (headers.get("Content-Type") or "").lower()
    if "image" not in ctype or len(raw) < 500 or len(raw) > 4_000_000:
        return ""
    ext = "png" if "png" in ctype else ("webp" if "webp" in ctype else "jpg")
    COVERS.mkdir(exist_ok=True)
    name = f"vk{oid}_{vid}.{ext}".replace("-", "m")
    (COVERS / name).write_bytes(raw)
    return f"covers/{name}"


def main():
    data = json.loads(WORKS.read_text(encoding="utf-8"))
    works = data["works"] if isinstance(data, dict) else data
    changed = ok = bad = 0
    for i, w in enumerate(works, 1):
        m = VK.search(w.get("url") or "")
        if not m:
            continue
        need_title = not w.get("title") or TEMP_TITLE.match(w["title"])
        need = [k for k in ("desc", "duration", "date", "cover") if not w.get(k)]
        if not need_title and not need:
            continue
        oid, vid = m.group(1), m.group(2)
        try:
            info = fetch_info(oid, vid)
        except Exception as e:
            bad += 1
            print(f"::warning::Запись {i} ({oid}_{vid}): не удалось получить страницу: {e}")
            continue
        before = json.dumps(w, ensure_ascii=False, sort_keys=True)
        if need_title and info["title"]:
            w["title"] = info["title"]
        for k in ("desc", "duration", "date"):
            if not w.get(k) and info[k]:
                w[k] = info[k][:600] if k == "desc" else info[k]
        if not w.get("cover") and info["image"]:
            try:
                c = save_cover(info["image"], oid, vid)
                if c:
                    w["cover"] = c
            except Exception as e:
                print(f"::warning::Запись {i}: обложка не скачалась: {e}")
        ok += 1
        if json.dumps(w, ensure_ascii=False, sort_keys=True) != before:
            changed += 1
        print(f"{i}: {w.get('title')!r}" + (f", обложка {w['cover']}" if w.get("cover") else ", без обложки"))
        time.sleep(1.0)
    WORKS.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"Готово: обновлено {changed}, получено страниц {ok}, не вышло {bad}")


if __name__ == "__main__":
    sys.exit(main())
