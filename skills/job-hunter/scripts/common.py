"""Shared helpers: polite HTTP with caching, HTML stripping and the normalized job record.

Every source is mapped to the same record so the tracker, red-flag scanner and ranking
steps don't care where a job came from.
"""

import hashlib
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

USER_AGENT = "job-hunter-skill/0.1 (personal job search; respects robots and rate limits)"
CACHE_DIR = Path(os.environ.get("JOBHUNTER_CACHE", Path.home() / ".cache" / "job-hunter"))


def utf8_stdout():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass


def fetch(url, data=None, headers=None, cache_hours=6.0, timeout=60, quiet=False):
    """GET (or POST when data is given) with a file cache, so repeated runs stay polite.
    Returns text, or None on any network/HTTP error (the caller reports it)."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha256((url + (json.dumps(data, sort_keys=True) if data else "")).encode()).hexdigest()[:24]
    cached = CACHE_DIR / f"{key}.txt"
    if cache_hours and cached.exists() and time.time() - cached.stat().st_mtime < cache_hours * 3600:
        return cached.read_text(encoding="utf-8")
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, headers={
        "User-Agent": USER_AGENT, "Accept": "application/json, text/html;q=0.9",
        **({"Content-Type": "application/json"} if body else {}), **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            text = r.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        if not quiet:
            print(f"[warn] {url}: {e}", file=sys.stderr)
        return None
    cached.write_text(text, encoding="utf-8")
    return text


def fetch_json(url, **kw):
    text = fetch(url, **kw)
    if text is None:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        print(f"[warn] {url}: not JSON", file=sys.stderr)
        return None


def strip_html(s, limit=4000):
    if not s:
        return ""
    s = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", s, flags=re.S | re.I)
    s = re.sub(r"<br\s*/?>|</p>|</li>|</h\d>", "\n", s, flags=re.I)
    s = html.unescape(re.sub(r"<[^>]+>", " ", s))
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n\s*\n+", "\n", s).strip()
    return s[:limit]


def job(source, title, company, url, **extra):
    """Normalized job record. `id` is stable across runs (company + title + url host/path)."""
    norm = lambda x: re.sub(r"\s+", " ", (x or "").strip().lower())
    ident = hashlib.sha1(f"{norm(company)}|{norm(title)}|{norm(url).split('?')[0]}".encode()).hexdigest()[:12]
    rec = {"id": ident, "source": source, "title": (title or "").strip(), "company": (company or "").strip(),
           "url": url, "apply_url": extra.pop("apply_url", url), "location": "", "remote": None,
           "employment_type": "", "posted": "", "salary_min": None, "salary_max": None,
           "currency": "", "description": "", "tags": []}
    rec.update({k: v for k, v in extra.items() if v not in (None, "")})
    return rec


def matches(rec, keywords, mode="any", in_description=False):
    """Keyword filter over title + tags (and the description when asked). Case/Turkish-insensitive.
    Title + tags is the default: matching descriptions pulled in unrelated jobs that merely mention a word."""
    if not keywords:
        return True
    parts = [rec.get("title", ""), " ".join(str(t) for t in rec.get("tags", []))]
    if in_description:
        parts.append(rec.get("description", "")[:1500])
    # Fold dotted/dotless i on BOTH sides: Turkish-only casing would turn the English "AI" into "aı".
    fold = lambda s: s.lower().replace("i̇", "i").replace("ı", "i")
    hay = fold(" ".join(parts))
    hits = [fold(k) in hay for k in keywords]
    return all(hits) if mode == "all" else any(hits)


def dump(records):
    utf8_stdout()
    print(json.dumps(records, ensure_ascii=False, indent=1))
