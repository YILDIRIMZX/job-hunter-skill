"""Pull jobs from free public feeds and print normalized records as JSON.

Usage:
  python feeds.py --keywords "python,machine learning,intern" [--sources himalayas,arbeitnow,remotive]
                  [--max 60] [--location germany]

Sources and their terms (respect them):
- Himalayas  https://himalayas.app/api        remote jobs, no key, max 20 per request.
- Arbeitnow  https://www.arbeitnow.com/api    Europe (mostly Germany), no key, link back to the job.
- Remotive   https://remotive.com/api-documentation  remote jobs, 24 h delayed, at most ~4 calls a day,
             always show Remotive as the source and link to the Remotive URL. Cached for 6 h here.
"""

import argparse
import sys

from common import dump, fetch_json, job, matches, strip_html


def himalayas(pages=3):
    out = []
    for i in range(pages):
        d = fetch_json(f"https://himalayas.app/jobs/api?limit=20&offset={i * 20}")
        if not d or not d.get("jobs"):
            break
        for j in d["jobs"]:
            out.append(job("Himalayas", j.get("title"), j.get("companyName"), j.get("applicationLink") or j.get("guid"),
                           location=", ".join(j.get("locationRestrictions") or []) or "Remote", remote=True,
                           employment_type=j.get("employmentType", ""), posted=str(j.get("pubDate", "")),
                           salary_min=j.get("minSalary"), salary_max=j.get("maxSalary"), currency=j.get("currency", ""),
                           description=strip_html(j.get("description") or j.get("excerpt")),
                           tags=(j.get("categories") or []) + ([j["seniority"]] if isinstance(j.get("seniority"), str) else (j.get("seniority") or []))))
    return out


def arbeitnow(pages=3):
    out = []
    for p in range(1, pages + 1):
        d = fetch_json(f"https://www.arbeitnow.com/api/job-board-api?page={p}")
        if not d or not d.get("data"):
            break
        for j in d["data"]:
            out.append(job("Arbeitnow", j.get("title"), j.get("company_name"), j.get("url"),
                           location=j.get("location", ""), remote=bool(j.get("remote")),
                           employment_type=", ".join(j.get("job_types") or []), posted=str(j.get("created_at", "")),
                           description=strip_html(j.get("description")), tags=j.get("tags") or []))
    return out


def remotive(keywords):
    q = keywords[0] if keywords else ""
    d = fetch_json(f"https://remotive.com/api/remote-jobs?search={q}", cache_hours=6)
    out = []
    for j in (d or {}).get("jobs", []):
        out.append(job("Remotive", j.get("title"), j.get("company_name"), j.get("url"),
                       location=j.get("candidate_required_location", ""), remote=True,
                       employment_type=j.get("job_type", ""), posted=j.get("publication_date", ""),
                       description=strip_html(j.get("description")), tags=j.get("tags") or [],
                       salary_text=j.get("salary", ""), attribution="Source: Remotive (remotive.com)"))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--keywords", default="", help="comma-separated; a job matches if ANY keyword appears")
    ap.add_argument("--sources", default="himalayas,arbeitnow,remotive")
    ap.add_argument("--location", default="", help="optional substring filter on location (e.g. germany, remote)")
    ap.add_argument("--max", type=int, default=60)
    ap.add_argument("--in-description", action="store_true", help="also match keywords inside job descriptions (broader, noisier)")
    a = ap.parse_args()
    kws = [k.strip() for k in a.keywords.split(",") if k.strip()]
    srcs = {s.strip() for s in a.sources.split(",")}
    recs = []
    if "himalayas" in srcs:
        recs += himalayas()
    if "arbeitnow" in srcs:
        recs += arbeitnow()
    if "remotive" in srcs:
        recs += remotive(kws)
    recs = [r for r in recs if matches(r, kws, in_description=a.in_description)]
    if a.location:
        loc = a.location.lower()
        recs = [r for r in recs if loc in (r.get("location") or "").lower() or (loc == "remote" and r.get("remote"))]
    seen, uniq = set(), []
    for r in recs:
        if r["id"] not in seen:
            seen.add(r["id"]); uniq.append(r)
    print(f"[info] {len(uniq)} matching jobs", file=sys.stderr)
    dump(uniq[: a.max])


if __name__ == "__main__":
    main()
