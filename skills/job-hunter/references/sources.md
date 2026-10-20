# Sources

Rules for every source: public pages only, no logging in, no CAPTCHA bypassing, no bulk crawling.
Fetch only the pages you need (about 30 per source per run), follow each site's terms, and record
where every job was found. Job boards change; if a site blocks automated reading (e.g. HTTP 403), say so
and move on: **don't disguise the request** (fake browser User-Agent, rotating headers, proxies) to get
around the block. Use search-result snippets, the employer's own site, or ask the user to open the page.

## Türkiye

| Source | Best for | How to search |
|---|---|---|
| Kariyer.net | Largest general board | web search `site:kariyer.net/is-ilani <rol> <şehir>`; open the posting page |
| Youthall | Internships, new graduates, talent programs | `site:youthall.com <staj / yeni mezun> <alan>` |
| Toptalent.co | Students, internships | `site:toptalent.co <staj>` |
| Techcareer.net, Coderspace | Software / tech roles, bootcamp-linked hiring | `site:techcareer.net`, `site:coderspace.io` |
| Yenibiris, Secretcv, Eleman.net | General, part-time, blue collar | `site:yenibiris.com`, `site:secretcv.com`, `site:eleman.net` |
| Kariyer Kapısı (kariyerkapisi.gov.tr) | Official public-sector jobs, the National Internship Program (Ulusal Staj Programı) | official site; government programs announce dates there |
| İŞKUR (iskur.gov.tr) | Official employment agency listings, İŞKUR programs | official site / e-Şube. İŞKUR never charges job seekers |
| Company career pages | Large employers (defense, telecom, banking, e-commerce, gaming) | search `<şirket> kariyer staj` and use the company's own domain |
| University career centers | Campus-only internships | the user's university site |

Large international employers with Turkish offices often use **Workday** (`<tenant>.wdN.myworkdayjobs.com`):
when a posting links there, `ats.py verify ... --url <workday link>` searches that tenant directly.
Workday tenants can't be guessed from a company name; find the link on the company's careers page.
Other corporate systems (SuccessFactors, Phenom, Avature, Eightfold, Oracle) have no script support: open the
company's careers page and confirm the posting there by hand (in testing: DHL uses Avature, Kuehne+Nagel
SuccessFactors/Phenom, Vodafone Eightfold).

Turkish employers rarely use Greenhouse/Lever/Ashby, so "not on an ATS board" is normal here.
Verify via the company's official site, its verified LinkedIn company page and registry records instead.

## International

| Source | Best for | How |
|---|---|---|
| Company ATS boards | The strongest source: postings straight from the employer | find boards with web search (`site:boards.greenhouse.io`, `site:job-boards.greenhouse.io`, `site:jobs.lever.co`, `site:jobs.ashbyhq.com`, `site:apply.workable.com` + role + city), then `scripts/ats.py list <ats> <slug>` |
| Himalayas, Arbeitnow, Remotive | Remote jobs; Europe (Arbeitnow) | `scripts/feeds.py`. Remotive: show "Source: Remotive" and its link, max ~4 calls a day (cached) |
| EURES (eures.europa.eu) | EU public job mobility portal | web search + official page |
| Bundesagentur für Arbeit Jobbörse | Germany, official | official site |
| Erasmus+ traineeships, ErasmusIntern | EU internships for students at Erasmus universities | check the user's university Erasmus office too |
| IAESTE, AIESEC Global Talent | Paid technical internships abroad (IAESTE has a Turkey committee) | official sites; application windows are seasonal |
| Welcome to the Jungle, Wellfound | European companies, startups | public listing pages via web search |

## LinkedIn (public pages only)

LinkedIn's User Agreement (section 8.2) prohibits bots, scripts and scraping; violating it gets the
user's account restricted. So:
- Find public job pages through web search: `site:linkedin.com/jobs/view <role> <location>`.
- Read only those public pages, a handful per run. Never log in, never drive the user's logged-in
  browser, never send connection requests or messages.
- Prefer the employer's own posting: every LinkedIn job should be traced to the company's careers page
  or ATS before it can be marked "Doğrulandı".
- The user can paste LinkedIn links they found; treat them like any other lead.

## Verification sources

| Check | Türkiye | Elsewhere |
|---|---|---|
| Company exists | Ticaret Sicil Gazetesi (ticaretsicil.gov.tr), official website and domain age, verified LinkedIn company page, news | UK Companies House, OpenCorporates, Germany Handelsregister / North Data, Netherlands KVK |
| Complaints about fake postings | Şikayetvar (user claims, not verified facts), news | Glassdoor, Reddit, news; scam warnings on the company's own site |
| Salary | Kariyer.net salary pages, Youthall reports, Glassdoor, peers | Glassdoor, Levels.fyi (tech), national statistics, the posting itself (EU pay-transparency rules increasingly require ranges) |
| Visa / work permit | n/a | UK: `scripts/sponsors.py uk <company>` (official register); Netherlands: IND public register of recognised sponsors; Germany: make-it-in-germany.com (no sponsor licence; depends on the offer); Ireland: enterprise.gov.ie permits; US internships for students usually need a J-1 sponsor organisation |

**Visa reality check (do it for every job abroad).** A recognised sponsor is not enough: the offered salary
must meet the route's threshold, which changes every year, so read the current figure on the official page.
Example from testing (Netherlands, 2026): the highly-skilled-migrant route needed about €4,357 gross/month
under age 30; the reduced graduate threshold only applies to graduates of Dutch or top-200 universities.
Entry-level operations and admin roles usually pay below that, which makes the permit a hard blocker even
when the employer is a sponsor. Also check WHICH legal entity employs the role: group companies on the
register may not be the one hiring.
Germany (from testing, 2026): the EU Blue Card has a standard threshold and a lower one for shortage
occupations and for career starters whose degree is at most 3 years old; the skilled-worker route (§18b)
has no fixed salary threshold under age 45 but needs a recognised/comparable degree (anabin/ZAB) and usually
Federal Employment Agency approval. Read the current figures on an official page (e.g. service.berlin.de,
make-it-in-germany.com) at run time. In practice the bigger barrier for entry-level logistics roles in
Germany was mandatory German, not the visa.
| Company health | layoff and funding news, hiring freezes, recent reviews | layoffs trackers, funding news |
