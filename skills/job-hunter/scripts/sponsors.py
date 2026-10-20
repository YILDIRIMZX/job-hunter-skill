"""Look a company up in the UK Home Office register of licensed visa sponsors (official, daily CSV).

Usage: python sponsors.py uk "Hugging Face" ["Another Ltd" ...]

Other countries have no single downloadable list; the skill checks them on official pages instead:
- Netherlands: IND public register of recognised sponsors (ind.nl)
- Germany: no sponsor licence system; EU Blue Card / skilled-worker visa depend on the job offer (make-it-in-germany.com)
- Ireland: Critical Skills / General Employment Permit (enterprise.gov.ie)
"""

import csv
import difflib
import io
import json
import re
import sys

from common import fetch, utf8_stdout

UK_PAGE = "https://www.gov.uk/government/publications/register-of-licensed-sponsors-workers"


def uk_register():
    page = fetch(UK_PAGE, cache_hours=24)
    m = re.search(r"https://assets\.publishing\.service\.gov\.uk/[^\"]+\.csv", page or "")
    if not m:
        sys.exit("Could not find the current register CSV on gov.uk.")
    text = fetch(m.group(0), cache_hours=24, timeout=180)
    if not text:
        sys.exit("Download of the register failed.")
    return m.group(0), list(csv.DictReader(io.StringIO(text)))


def norm(s):
    s = re.sub(r"\b(ltd|limited|plc|llp|inc|uk|group|holdings?)\b\.?", "", s.lower())
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def lookup(rows, company, limit=5):
    """One entry per organisation, with all of its visa routes. Substring hits (trading names such as
    'Roofoods Ltd t/a Deliveroo') count; plain fuzzy matches need 0.88+, because lower scores matched
    unrelated firms in testing (UDELIVER vs Deliveroo scored 0.82)."""
    target = norm(company)
    orgs = {}
    for r in rows:
        name = r.get("Organisation Name", "")
        n = norm(name)
        if not n or not target:
            continue
        if n == target:
            score = 1.0
        elif re.search(rf"\b{re.escape(target)}\b", n):
            score = 0.9
        else:
            score = difflib.SequenceMatcher(None, n, target).ratio()
            if score < 0.88:
                continue
        o = orgs.setdefault(name, {"name": name, "town": r.get("Town/City"), "rating": r.get("Type & Rating"),
                                   "routes": set(), "match": round(score, 2)})
        o["routes"].add(r.get("Route"))
    out = sorted(orgs.values(), key=lambda o: -o["match"])[:limit]
    for o in out:
        o["routes"] = sorted(filter(None, o["routes"]))
        o["skilled_worker"] = "Skilled Worker" in o["routes"]
    return out


def main():
    utf8_stdout()
    if len(sys.argv) < 3 or sys.argv[1] != "uk":
        sys.exit(__doc__)
    url, rows = uk_register()
    out = {"source": url, "rows_in_register": len(rows), "results": {c: lookup(rows, c) for c in sys.argv[2:]},
           "note": "A company on the list CAN sponsor; it doesn't mean this particular job offers sponsorship. "
                   "Look for 'Skilled Worker' in the Route column and ask the employer."}
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
