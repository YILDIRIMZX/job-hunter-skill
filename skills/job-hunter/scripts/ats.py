"""Check jobs against a company's OWN applicant-tracking system (public job-board endpoints).

A posting that also exists on the employer's official Greenhouse / Lever / Ashby / Workable board
is very unlikely to be fake. These endpoints are published by the ATS vendors for exactly this
use (embedding a company's open jobs), need no key, and don't require logging in anywhere.

Usage:
  python ats.py probe   "Hugging Face"                 # which ATS boards does this company have?
  python ats.py list    greenhouse airbnb [--keywords "engineer,intern"]
  python ats.py verify  "Hugging Face" "ML Engineer" [--url <posting url>]
  python ats.py detect  <posting url>                  # e.g. https://jobs.lever.co/acme/123 -> lever, acme
"""

import argparse
import difflib
import re
import sys

from common import dump, fetch_json, job, matches, strip_html, utf8_stdout

URL_PATTERNS = [
    ("greenhouse", r"(?:boards|job-boards)(?:\.eu)?\.greenhouse\.io/(?:embed/job_board\?for=)?([\w-]+)"),
    ("lever", r"jobs\.(?:eu\.)?lever\.co/([\w-]+)"),
    ("ashby", r"jobs\.ashbyhq\.com/([\w.-]+)"),
    ("workable", r"apply\.workable\.com/([\w-]+)"),
]


WORKDAY_RX = r"([\w-]+)\.(wd\d+)\.myworkdayjobs\.com/(?:[a-z]{2}-[A-Z]{2}/)?([\w-]+)"


def detect(url):
    for ats, rx in URL_PATTERNS:
        m = re.search(rx, url or "", re.I)
        if m:
            return ats, m.group(1)
    m = re.search(WORKDAY_RX, url or "")
    if m:  # slug = tenant|wdN|site, e.g. analogdevices|wd1|External
        return "workday", "|".join(m.groups())
    return None, None


def workday_search(slug, text, limit=20):
    """Workday has no 'list everything' feed; its public career-site search takes a query.
    Only usable when a posting URL tells us the tenant and site (Workday URLs can't be guessed)."""
    tenant, wd, site = slug.split("|")
    base = f"https://{tenant}.{wd}.myworkdayjobs.com"
    d = fetch_json(f"{base}/wday/cxs/{tenant}/{site}/jobs",
                   data={"appliedFacets": {}, "limit": limit, "offset": 0, "searchText": text})
    if not d or "jobPostings" not in d:
        return None
    return [job("Workday", j.get("title"), tenant, f"{base}/{site}{j.get('externalPath', '')}",
                location=j.get("locationsText", ""), posted=j.get("postedOn", ""),
                requisition=", ".join(j.get("bulletFields") or []), ats=f"workday:{tenant}/{site}")
            for j in d["jobPostings"]]


def list_jobs(ats, slug, quiet=False):
    """All open jobs on one board as normalized records; None if the board doesn't exist."""
    if ats == "greenhouse":
        d = fetch_json(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true", quiet=quiet)
        if not d or "jobs" not in d:
            return None
        return [job("Greenhouse", j.get("title"), j.get("company_name") or slug, j.get("absolute_url"),
                    location=(j.get("location") or {}).get("name", ""), posted=j.get("first_published") or j.get("updated_at", ""),
                    description=strip_html(j.get("content")), ats=f"greenhouse:{slug}") for j in d["jobs"]]
    if ats == "lever":
        d = fetch_json(f"https://api.lever.co/v0/postings/{slug}?mode=json", quiet=quiet)
        if not isinstance(d, list):
            return None
        return [job("Lever", j.get("text"), slug, j.get("hostedUrl"), apply_url=j.get("applyUrl"),
                    location=(j.get("categories") or {}).get("location", ""), remote=(j.get("workplaceType") == "remote") or None,
                    employment_type=(j.get("categories") or {}).get("commitment", ""), posted=str(j.get("createdAt", "")),
                    description=strip_html(j.get("descriptionPlain") or j.get("description")), ats=f"lever:{slug}") for j in d]
    if ats == "ashby":
        d = fetch_json(f"https://api.ashbyhq.com/posting-api/job-board/{slug}?includeCompensation=true", quiet=quiet)
        if not d or "jobs" not in d:
            return None
        out = []
        for j in d["jobs"]:
            comp = (j.get("compensation") or {}).get("compensationTierSummary", "")
            out.append(job("Ashby", j.get("title"), slug, j.get("jobUrl"), apply_url=j.get("applyUrl"),
                           location=j.get("location", ""), remote=j.get("isRemote"), employment_type=j.get("employmentType", ""),
                           posted=j.get("publishedAt", ""), description=strip_html(j.get("descriptionPlain") or j.get("descriptionHtml")),
                           salary_text=comp, ats=f"ashby:{slug}"))
        return out
    if ats == "workable":
        d = fetch_json(f"https://apply.workable.com/api/v3/accounts/{slug}/jobs",
                       data={"query": "", "location": [], "department": [], "worktype": [], "remote": []}, quiet=quiet)
        if not d or "results" not in d:
            return None
        return [job("Workable", j.get("title"), slug, f"https://apply.workable.com/{slug}/j/{j.get('shortcode')}/",
                    location=", ".join(filter(None, [(j.get("location") or {}).get("city"), (j.get("location") or {}).get("country")])),
                    remote=j.get("remote"), posted=j.get("published", ""), ats=f"workable:{slug}") for j in d["results"]]
    raise ValueError(ats)


def slug_guesses(company):
    base = re.sub(r"\b(inc|ltd|llc|gmbh|a\.?ş\.?|as|bv|plc|co|corp|corporation|limited|teknoloji|yazılım)\b\.?", "", company.lower())
    base = base.replace("ı", "i").replace("ş", "s").replace("ğ", "g").replace("ü", "u").replace("ö", "o").replace("ç", "c")
    words = re.findall(r"[a-z0-9]+", base)
    if not words:
        return []
    # "hugging face" -> huggingface, hugging-face. No first-word-only guess: in testing, "analog"
    # (for Analog Devices) hit an unrelated company's board, which could "verify" a wrong posting.
    return list(dict.fromkeys(["".join(words), "-".join(words)]))


def owns_board(company, jobs):
    """Does a guessed board belong to this company? Greenhouse returns the company name; for the
    others, require the name (or its compact form) in the postings' text or URLs."""
    name = company.lower()
    compact = re.sub(r"[^a-z0-9]", "", name.replace("ı", "i"))
    for j in jobs[:30]:
        text = " ".join([j.get("company", ""), j.get("description", "")[:3000], j.get("url", "")]).lower()
        if name in text or (len(compact) >= 5 and compact in re.sub(r"[^a-z0-9]", "", text)):
            return True
    return False


def probe(company):
    """Try likely board names on every ATS. Returns [{ats, slug, open_jobs, owner_confirmed}]."""
    found = []
    for slug in slug_guesses(company):
        for ats, _ in URL_PATTERNS:
            jobs = list_jobs(ats, slug, quiet=True)  # 404 is the normal answer for boards a company doesn't use
            if jobs:
                found.append({"ats": ats, "slug": slug, "open_jobs": len(jobs), "owner_confirmed": owns_board(company, jobs)})
    return found


def similarity(a, b):
    norm = lambda s: re.sub(r"[^a-z0-9ğüşıöç ]", " ", (s or "").lower())
    return round(difflib.SequenceMatcher(None, norm(a), norm(b)).ratio(), 2)


def verify(company, title, url=None):
    """Is a job with this title open on the company's own ATS board?"""
    boards = []  # (ats, slug, owner_confirmed)
    ats, slug = detect(url)
    if ats:
        boards.append((ats, slug, True))  # the posting's own URL points at this board
    boards += [(b["ats"], b["slug"], b["owner_confirmed"]) for b in probe(company)
               if (b["ats"], b["slug"]) not in [(a, s) for a, s, _ in boards]]
    if not boards:
        return {"company": company, "title": title, "status": "no_public_ats_board",
                "note": "No Greenhouse/Lever/Ashby/Workable board found. Not evidence of fraud: many companies "
                        "(most Turkish employers) use their own careers page, Workday/SuccessFactors or Kariyer.net. "
                        "Check the official site."}
    best = None
    for ats, slug, owned in boards:
        postings = workday_search(slug, title) if ats == "workday" else list_jobs(ats, slug)
        for j in postings or []:
            s = similarity(title, j["title"])
            if not best or s > best["similarity"]:
                best = {"ats": ats, "slug": slug, "board_owner_confirmed": owned, "matched_title": j["title"],
                        "url": j["url"], "location": j["location"], "posted": j["posted"], "similarity": s}
    if best and best["similarity"] >= 0.75:
        status = "found_on_official_ats" if best["board_owner_confirmed"] else "found_on_unconfirmed_board"
    else:
        # Workday search returns nothing for an unknown title even though the board has jobs
        searched = any(a == "workday" for a, _, _ in boards)
        status = "board_exists_title_not_found" if best or searched else "board_empty"
    out = {"company": company, "title": title, "status": status,
           "boards": [f"{a}:{s}" + ("" if o else " (owner NOT confirmed)") for a, s, o in boards], "best_match": best}
    if status == "found_on_unconfirmed_board" or any(not o for *_, o in boards):
        out["note"] = ("A board was found by guessing its name and its postings don't mention the company. It may "
                       "belong to a different company with a similar name: confirm via the company's official site "
                       "before treating it as the official channel.")
    return out


def main():
    utf8_stdout()
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("probe"); p.add_argument("company")
    l = sub.add_parser("list"); l.add_argument("ats"); l.add_argument("slug"); l.add_argument("--keywords", default="")
    v = sub.add_parser("verify"); v.add_argument("company"); v.add_argument("title"); v.add_argument("--url")
    d = sub.add_parser("detect"); d.add_argument("url")
    a = ap.parse_args()
    import json
    if a.cmd == "probe":
        print(json.dumps(probe(a.company), ensure_ascii=False, indent=1))
    elif a.cmd == "list":
        # Workday: slug = tenant|wdN|site (from `detect`), and --keywords is used as the search text
        jobs = workday_search(a.slug, a.keywords.replace(",", " ")) if a.ats == "workday" else list_jobs(a.ats, a.slug)
        if jobs is None:
            sys.exit(f"No {a.ats} board named '{a.slug}'.")
        kws = [k.strip() for k in a.keywords.split(",") if k.strip()]
        dump([j for j in jobs if matches(j, kws)])
    elif a.cmd == "verify":
        print(json.dumps(verify(a.company, a.title, a.url), ensure_ascii=False, indent=1))
    else:
        print(json.dumps(dict(zip(["ats", "slug"], detect(a.url))), indent=1))


if __name__ == "__main__":
    main()
