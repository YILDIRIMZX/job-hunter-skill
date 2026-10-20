"""Rule-based red-flag scan of a job posting (Turkish + English).

Indicators come from published work on recruitment fraud (EMSCAD / Vidros et al. 2017; the 2026
crime-script review of employment scams) and Turkish consumer warnings (fake "training/registration
fee", WhatsApp-only contact, impersonating real companies, "İŞKUR kayıt ücreti"). The scan only
produces EVIDENCE with quotes; the verification agent makes the call together with official checks.

Usage:
  python red_flags.py posting.txt [--email hr@acme.com] [--company "Acme"] [--salary 250000 --currency TRY --period month]
  python red_flags.py -   (read the posting from stdin)
Output JSON: {"risk_points": n, "level": "low|medium|high|critical", "flags": [{id, severity, evidence}]}
"""

import argparse
import json
import re
import sys

from common import utf8_stdout

# id, severity (points), regex (Turkish + English), explanation
RULES = [
    ("fee_request", 40, r"(eğitim|kayıt|başvuru|dosya|kargo|ekipman|kit|sigorta|teminat|depozito|aidat)\s*(ücreti|bedeli|masrafı)|"
     r"ücret(i)?\s*(yatır|öde)|para\s*(yatır|gönder)|iban(?!\w)|papara|(training|registration|application|equipment|starter[- ]kit|processing)\s*fee|"
     r"pay\s*(a|the)?\s*(fee|deposit)|send\s*money|wire\s*transfer|gift\s*cards?",
     "Asks the candidate to pay. Legitimate employers never charge applicants."),
    ("crypto_or_payment_handling", 30, r"kripto|bitcoin|usdt|binance|hesabınızı\s*kullan|ödeme\s*al(ıp|arak)\s*(aktar|gönder)|"
     r"crypto|receive\s*(and|&)\s*(forward|transfer)\s*(payments|funds)|payment\s*processing\s*agent|reshipp?ing",
     "Money-mule / reshipping pattern: you would move money or goods for strangers."),
    ("chat_only_contact", 20, r"whats\s*app|telegram|signal\s*(app|üzerinden)|sadece\s*(mesaj|dm)|wa\.me/|t\.me/",
     "Contact only via messaging apps instead of a company channel."),
    ("sensitive_data_early", 30, r"t\.?c\.?\s*(kimlik)?\s*(no|numara)|kimlik\s*fotokopi|e-?devlet\s*şifre|sms\s*(kod|onay)|"
     r"kart\s*bilgi|banka\s*(hesap\s*)?bilgi|social\s*security|ssn|passport\s*(copy|scan)|bank\s*(account\s*)?details|"
     r"credit\s*card",
     "Requests identity, bank or login data before any interview or offer."),
    ("no_interview", 15, r"mülakat(sız)?\s*(yok|gerekmez)|mülakatsız|hemen\s*işe\s*başla|no\s*interview|hired\s*immediately|"
     r"start\s*(today|immediately)\s*without",
     "No interview step; one in three fake postings in a text-mining study skipped it."),
    ("too_good_to_be_true", 15, r"günde\s*\d+\s*(saat|dk).{0,40}(bin|\d{4,})\s*(tl|₺)|evden\s*(paketleme|boncuk|kalem)|"
     r"tecrübe\s*gerekmez.{0,60}yüksek\s*kazanç|kolay\s*para|sınırsız\s*kazanç|"
     r"earn\s*\$?\d{3,}\s*(per|a)\s*(day|week)|no\s*experience.{0,40}high\s*pay|work\s*from\s*home.{0,40}\$\d{3,}\s*/\s*day|"
     r"unlimited\s*earning",
     "Unrealistic pay for little effort or experience."),
    ("urgency_pressure", 10, r"son\s*\d+\s*(kişi|kontenjan)|acil(en)?\s*(eleman|alım)|bugün\s*başvur(un)?\s*yarın\s*başla|"
     r"limited\s*(spots|positions)\s*(left|available)|act\s*now|urgent(ly)?\s*hiring.{0,30}today",
     "Pressure to act before you can check."),
    ("mlm_commission_only", 15, r"network\s*marketing|ağ\s*pazarlama|sadece\s*prim|prim\s*usulü|komisyon\s*bazlı|"
     r"commission[- ]only|multi[- ]level|mlm|be\s*your\s*own\s*boss",
     "Commission-only / MLM pattern rather than a salaried job."),
    ("vague_role", 10, r"(çeşitli|basit)\s*(ofis\s*)?işler|herkes\s*yapabilir|data\s*entry\s*from\s*home|"
     r"(simple|easy)\s*(online\s*)?tasks|like\s*and\s*(review|rate)|ürün\s*(beğen|değerlendir)",
     "Task scams (\"like products / rate apps for pay\") and vague duties."),
    ("iskur_fee", 40, r"iş\s*kur.{0,40}(ücret|bedel|ödeme)|işkur\s*kayıt\s*ücreti",
     "Uses İŞKUR's name to ask for money. İŞKUR does not charge job seekers."),
]

FREE_MAIL = r"@(gmail|hotmail|outlook|yahoo|yandex|icloud|proton(mail)?|mail)\.(com|com\.tr|me)$"

# Rough monthly gross ceilings for entry level / internships. Beyond these the claim needs evidence.
ENTRY_CEILING = {"TRY": 150000, "EUR": 6000, "USD": 7000, "GBP": 5500}


def scan(text, email=None, company=None, salary=None, currency=None, period="month"):
    low = (text or "").replace("I", "ı").replace("İ", "i").lower()
    flags = []
    for rid, pts, rx, why in RULES:
        m = re.search(rx, low, re.I)
        if m:
            s = max(0, m.start() - 50)
            flags.append({"id": rid, "severity": pts, "why": why, "evidence": text[s:m.end() + 50].replace("\n", " ").strip()})
    if email:
        if re.search(FREE_MAIL, email.lower()):
            flags.append({"id": "free_email_domain", "severity": 15, "why": "Recruiter uses a free mailbox, not the company domain.", "evidence": email})
        elif company:
            core = re.sub(r"[^a-z0-9]", "", company.lower().replace("ı", "i"))[:6]
            dom = email.split("@")[-1].lower()
            if core and core not in re.sub(r"[^a-z0-9]", "", dom):
                flags.append({"id": "domain_mismatch", "severity": 10,
                              "why": "Email domain doesn't resemble the company name; check it against the official site.", "evidence": email})
    if salary and currency in ENTRY_CEILING:
        monthly = salary / 12 if period == "year" else salary * 160 if period == "hour" else salary
        if monthly > 2 * ENTRY_CEILING[currency]:
            flags.append({"id": "salary_outlier", "severity": 10,
                          "why": f"Pay is far above typical entry-level/intern level ({currency}).", "evidence": f"{salary} {currency}/{period}"})
    if len((text or "").split()) < 60:
        flags.append({"id": "thin_posting", "severity": 10, "why": "Very short posting: little verifiable information.",
                      "evidence": f"{len((text or '').split())} words"})
    pts = sum(f["severity"] for f in flags)
    level = "critical" if any(f["severity"] >= 40 for f in flags) or pts >= 60 else "high" if pts >= 35 else "medium" if pts >= 15 else "low"
    return {"risk_points": pts, "level": level, "flags": flags}


def main():
    utf8_stdout()
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--email"); ap.add_argument("--company")
    ap.add_argument("--salary", type=float); ap.add_argument("--currency"); ap.add_argument("--period", default="month")
    a = ap.parse_args()
    text = sys.stdin.read() if a.path == "-" else open(a.path, encoding="utf-8").read()
    print(json.dumps(scan(text, a.email, a.company, a.salary, (a.currency or "").upper() or None, a.period), ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
