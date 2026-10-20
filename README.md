# Job Hunter: Agent Skill

**[English](#english) · [Türkçe](#türkçe)**

A multi-agent job-search skill for AI coding agents that **refuses fake jobs**. It reads your CV, asks what you want, searches Turkey and abroad in parallel, **verifies every shortlisted posting against the employer's own channels**, researches the survivors (company health, salary, visa), ranks them with pros and cons, and keeps everything in an Excel tracker with follow-up reminders.

> It never applies, sends messages, logs in, or pays anything for you. You press Submit.

---

## English

### What it does

- **Parallel search** by four agents:
  - **TR-web**: Turkish boards and programs (Youthall, Kariyer.net, Eleman.net, Toptalent, Techcareer, university career centers, Kariyer Kapısı / İŞKUR, company sites)
  - **Global-web**: employer ATS boards, free public job feeds, public portals (EURES etc.), internship programs
  - **LinkedIn-public**: only public job pages found via web search (no login, no automation)
  - **Company-hunter**: builds a list of 15–30 employers that fit your profile and checks their careers pages directly, finding jobs that never reach job boards
- **Fake-job and ghost-job verification** of the top 10 (configurable), one investigator agent per job:
  - Is the company real? (official domain, registries, licences, news)
  - Is the posting on the employer's **own** channel? (`ats.py` checks Greenhouse, Lever, Ashby, Workable and Workday; guessed boards must prove they belong to the company)
  - Red-flag scan, Turkish and English (`red_flags.py`): fees, WhatsApp-only contact, ID or bank data requests, task scams, money-mule patterns, "İŞKUR fee", unrealistic pay
  - Impersonation (look-alike domains), closed postings, evergreen/ghost postings
  - Label: ✅ Doğrulandı (verified) · 🟡 Muhtemel (probably real) · 🟠 Şüpheli (suspicious) · ❌ Sahte (fake → rejected sheet with evidence)
- **Deep research**: company health, salary (stated or researched range with sources), visa reality check (UK official sponsor register via script; Netherlands and Germany via official pages, **including salary thresholds**), interview process, deadlines.
- **Ranking**: score = 60% fit with your CV + 40% potential of the job. Reachable jobs first (by label, then score); jobs with a hard blocker (visa, mandatory language, far too much experience) go to a separate group at the end. Two independent reviewer agents cross-check the ranking and the pros and cons before anything is saved.
- **Excel tracker** (`tracker.py`): sheets for jobs, rejected (with reasons), applications and follow-ups, and a search log. New searches never overwrite your own status, dates or notes; already-seen jobs are skipped.
- **Extras on request**: CV and cover letter tailored to a chosen job (no invented facts), "is this posting real?" for any link you paste, follow-up email drafts (never sent).

### How it works

```
CV + what you want
   │
   ├─ TR-web ─────────┐
   ├─ Global-web ─────┤  (parallel, ≤30 leads each, red-flag scan on every lead)
   ├─ LinkedIn-public ┤
   └─ Company-hunter ─┘
            ▼
   merge, dedupe, hard filters, top 10
            ▼
   10 investigators (parallel): verify first, then research
            ▼
   score, blockers, 2 independent reviewers
            ▼
   Excel tracker + short report
```

### Installation

1. Copy `skills/job-hunter/` into your agent's skills directory (any agent that supports `SKILL.md` skills and can run sub-agents, web search and shell commands).
2. `python -m pip install --user -r requirements.txt` (only `openpyxl`; the other scripts use the Python standard library).
3. Ask, e.g.: *"İş ara: CV'm şurada, yazılım stajı istiyorum, İstanbul veya uzaktan"* or *"Find me entry-level logistics jobs in the Netherlands, here's my CV"* or *"Is this posting real? <link>"*.

### Test runs (real searches, October 2026)

**Test 1: small run, real profile (anonymized): 4th-year computer engineering student, software/AI internship in Turkey. TR-web agent only, 3 jobs investigated.**

| Job | Result |
|---|---|
| Long-term internship, Data & AI (telecom operator) | ✅ Verified on the official portal, deadline flagged, score 71 |
| Software engineering intern (semiconductor company) | ✅ Traced from LinkedIn to the official Workday requisition, score 67 |
| Remote AI intern (small startup, via a university career center) | 🟠 Suspicious: no fraud signals, but the legal entity couldn't be verified (no registry trace, 47-day-old domain) |

**Test 2: full run, fictional profile: International Trade & Logistics graduate, entry-level, İzmir/İstanbul/Mersin + Germany/Netherlands. 4 agents → 28 unique leads → 10 investigated.**

| Outcome | Count | Examples |
|---|---|---|
| Reachable, verified or probably real | 5 | global forwarder export role (verified), new-graduate operations roles at smaller forwarders/exporters (probably real, with what to check) |
| Suspicious | 1 | trading company with no trace anywhere and pay below market |
| Real but blocked | 3 | Netherlands roles at recognised visa sponsors where the entry-level salary is below the highly-skilled-migrant threshold; one supervisor role needing years of team leading |
| Rejected: closed | 1 | the best-fitting job (fit 92) had already been filled; caught and moved out of the list |
| Fake | 0 | none found in these runs |

Bugs these tests found and fixed: a guessed ATS board belonging to a **different company with a similar name** could have "verified" a wrong posting (now ownership is checked); Workday support was missing; verified-but-unreachable jobs ranked above realistic ones (blocker group added); blocker caps were applied inconsistently; an agent got around a site's bot block by faking a browser identity (now explicitly forbidden).

### What it can do

- Catch typical scams (fees, data harvesting, task scams, impersonation) and say **why**, with quotes.
- Trace postings from boards and LinkedIn to the employer's own system and give you the official apply link.
- Detect closed postings and evergreen "ghost" postings.
- Check visa reality, not just "is the company a sponsor".
- Keep a clean tracker across many searches with follow-up reminders.

### Limitations

- **Coverage**: some major boards block automated reading (in testing: Kariyer.net, Yenibiris, Indeed returned HTTP 403; LinkedIn rate-limits). The skill reports blocked sources instead of working around them, so it can miss jobs that exist only there.
- **Verification depth varies**: big employers can be verified through their own ATS; many small Turkish companies have no website and no public job page, so they often end up "Muhtemel" at best. Turkish trade registry searches need a login and aren't automated.
- **No guarantee**: a "verified" posting can still be filled, frozen or changed. "Couldn't verify" doesn't mean fake.
- **Salary data is thin**: most postings don't state pay; ranges come from user-reported averages.
- **Visa rules change yearly**: thresholds are looked up at run time, but always confirm with the official source and the employer.
- **Cost**: a full run uses many sub-agents (the full test used about 1.6 M tokens and ~30 minutes). Use smaller runs (one search agent, top 3) for quick checks.
- **Language barrier abroad is real**: in the Germany/Netherlands test, most entry-level logistics roles required fluent German or Dutch.
- Never a substitute for your own judgement: read the evidence before applying.

### Safety rules built in

- No applying, form submission, messaging, logging in, CAPTCHA solving or payments.
- LinkedIn: public pages via web search only (its User Agreement §8.2 forbids bots and scraping).
- Blocked sites are not bypassed (no fake browser identities, proxies or header tricks).
- Never asks for or enters ID numbers, bank or login data, and warns that real employers don't ask for these before an offer.
- Posting text is treated as data; instructions hidden inside a posting are reported as a red flag.
- Your CV and profile stay local.

### Data sources and terms

Himalayas, Arbeitnow and Remotive public feeds (Remotive: credited as the source with its link, max ~4 calls a day, responses cached); Greenhouse, Lever, Ashby, Workable and Workday public job-board endpoints; UK Home Office register of licensed sponsors (official CSV); public pages of job boards, company sites and official portals. Follow each source's terms when you use the results.

### Background reading

- Vidros et al., 2017. *Automatic Detection of Online Recruitment Frauds: Characteristics, Methods, and a Public Dataset* (EMSCAD). [Future Internet 9(1):6](https://www.mdpi.com/1999-5903/9/1/6)
- *Employment scams: a crime script and scoping review* (2026). [Trends in Organized Crime](https://link.springer.com/article/10.1007/s12117-026-09598-4)
- LinkedIn User Agreement §8.2 (automated access and scraping).

### Repository layout

```
skills/job-hunter/
  SKILL.md                    # the workflow the agent follows
  references/sources.md       # where and how to search (TR, international, LinkedIn), verification + visa sources
  references/verification.md  # fake/ghost-job rubric and labels
  references/scoring.md       # fit/potential scoring, blockers, pros/cons, cross-check
  scripts/ats.py              # official ATS board listing/verification (Greenhouse, Lever, Ashby, Workable, Workday)
  scripts/feeds.py            # Himalayas / Arbeitnow / Remotive feeds
  scripts/red_flags.py        # scam red-flag scanner (TR + EN)
  scripts/sponsors.py         # UK visa sponsor register lookup
  scripts/tracker.py          # Excel tracker: merge, applications, follow-ups
  scripts/common.py           # polite cached HTTP + normalized job record
```

### License

MIT (see `LICENSE`).

---

## Türkçe

### Ne işe yarar?

Yapay zekâ kodlama ajanları için çok ajanlı bir iş arama skill'i. **Sahte ilanları kabul etmez.** CV'ni okur, ne tür bir iş istediğini sorar, Türkiye'de ve yurt dışında paralel arama yapar. Kısa listeye giren her ilanı **işverenin kendi kanallarında doğrular**, kalanları araştırır (şirket sağlığı, maaş, vize), artı ve eksileriyle sıralar ve hepsini takip hatırlatmalı bir Excel dosyasında tutar.

> Senin yerine asla başvurmaz, mesaj göndermez, giriş yapmaz ya da ödeme yapmaz. "Gönder" tuşuna sen basarsın.

- **Dört ajanla paralel arama:**
  - **TR-web:** Türk ilan siteleri ve programlar
  - **Global-web:** işveren ATS panoları, ücretsiz ilan beslemeleri, EURES gibi resmî portallar
  - **LinkedIn-public:** sadece arama motoruyla bulunan herkese açık ilan sayfaları (giriş yok, otomasyon yok)
  - **Şirket avcısı:** profiline uyan 15–30 şirketi seçip kariyer sayfalarına doğrudan bakar; ilan sitelerine hiç düşmeyen işleri bulur
- **Sahte ve hayalet ilan doğrulaması:** varsayılan olarak ilk 10 ilan için, her ilana bir araştırmacı ajan.
  - Şirket gerçek mi? (resmî alan adı, sicil kayıtları, lisanslar, haberler)
  - İlan işverenin **kendi** kanalında var mı? (`ats.py`: Greenhouse, Lever, Ashby, Workable, Workday; tahminle bulunan bir panonun o şirkete ait olduğu ayrıca kanıtlanmalı)
  - Kırmızı bayrak taraması: ücret talebi, sadece WhatsApp üzerinden iletişim, kimlik/banka bilgisi isteme, "ürün beğen-para kazan" tuzakları, para aktarma (money mule) kalıpları, "İŞKUR kayıt ücreti"
  - Taklit alan adları, kapanmış ilanlar, sürekli açık "hayalet" ilanlar
  - **Etiketler:** ✅ Doğrulandı · 🟡 Muhtemel · 🟠 Şüpheli · ❌ Sahte (kanıtıyla "Elenenler" sekmesine gider)
- **Derin araştırma:** şirket sağlığı, maaş (ilanda yazan ya da kaynaklı aralık), vize gerçekliği (İngiltere resmî sponsor listesi betikle; Hollanda ve Almanya resmî sayfalardan, **maaş eşikleri dahil**), mülakat süreci, son başvuru tarihi.
- **Sıralama:** puan = %60 CV uyumu + %40 işin potansiyeli. Önce ulaşılabilir ilanlar gelir (etikete, sonra puana göre). Kesin engeli olan ilanlar (vize, zorunlu dil, çok fazla deneyim) en sonda ayrı bir grupta durur. Kaydetmeden önce iki bağımsız kontrolcü ajan sıralamayı ve artı/eksileri denetler.
- **Excel takip dosyası:** ilanlar, elenenler (nedenleriyle), başvurular ve takip tarihleri, arama geçmişi. Yeni aramalar senin girdiğin durum, tarih ve notları silmez; daha önce görülen ilanlar atlanır.
- **İsteğe bağlı ekstralar:** seçtiğin ilana özel CV ve ön yazı (uydurma bilgi yok), yapıştırdığın herhangi bir link için "bu ilan gerçek mi?" kontrolü, takip e-postası taslakları (asla gönderilmez).

### Kurulum

1. `skills/job-hunter/` klasörünü ajanının skill klasörüne kopyala. `SKILL.md` destekleyen, alt ajan çalıştırabilen, web araması ve komut çalıştırabilen her ajan uygundur.
2. `python -m pip install --user -r requirements.txt` komutunu çalıştır. Sadece `openpyxl` gerekiyor; diğer betikler Python standart kütüphanesiyle çalışır.
3. Ajana düz bir dille sor, örneğin: *"İş ara: CV'm şurada, yazılım stajı istiyorum, İstanbul veya uzaktan"* ya da *"Bu ilan gerçek mi? <link>"*.

### Test çalıştırmaları (gerçek aramalar, Ekim 2026)

**Test 1: küçük çalıştırma, gerçek profil (anonimleştirildi).** 4. sınıf bilgisayar mühendisliği öğrencisi, Türkiye'de yazılım/YZ stajı. Sadece TR-web ajanı, 3 ilan incelendi.
- **Telekom operatörü, Data & AI uzun dönem staj:** ✅ resmî portalda doğrulandı, son başvuru tarihi uyarısı verildi.
- **Yarı iletken şirketi, yazılım stajı:** ✅ LinkedIn'den şirketin resmî Workday ilanına kadar izlendi.
- **Küçük girişim, uzaktan YZ stajı:** 🟠 Şüpheli. Dolandırıcılık işareti yok, ama tüzel kişilik doğrulanamadı: sicilde iz yok, alan adı 47 günlük.

**Test 2: tam çalıştırma, kurgusal profil.** Uluslararası ticaret ve lojistik mezunu, giriş seviyesi; İzmir/İstanbul/Mersin + Almanya/Hollanda. 4 ajan → 28 benzersiz ilan → 10'u incelendi.
- 5 ulaşılabilir ilan: 1 doğrulandı, 4 muhtemel (ne kontrol edilmesi gerektiğiyle birlikte)
- 1 şüpheli
- 3 gerçek ama engelli ilan: Hollanda'da tanınmış sponsor şirketler, ama giriş seviyesi maaş vize eşiğinin altında
- 1 kapanmış ilan: en uygun ilan (uyum 92) çoktan doldurulmuştu; yakalandı ve listeden çıkarıldı
- 0 sahte ilan

**Testlerde bulunup düzeltilen hatalar:**
- Tahminle bulunan bir ATS panosu **benzer isimli başka bir şirkete** ait olabiliyordu ve yanlış bir ilanı "doğrulayabilirdi"; artık panonun sahipliği kontrol ediliyor.
- Workday desteği yoktu.
- Doğrulanmış ama ulaşılamaz ilanlar, gerçekçi ilanların üstünde sıralanıyordu; bunlar için ayrı bir engel grubu eklendi.
- Engel sınırı ilanlara tutarsız uygulanıyordu.
- Bir ajan, bir sitenin bot engelini sahte tarayıcı kimliğiyle aşmıştı; bu artık açıkça yasak.

### Sınırlar

- **Kapsam:** Bazı büyük ilan siteleri otomatik okumayı engelliyor. Testte Kariyer.net, Yenibiris ve Indeed 403 hatası verdi, LinkedIn ise istekleri sınırlıyor. Skill bu siteleri atlatmaya çalışmaz, raporlar. Bu yüzden sadece oralarda yayımlanan ilanlar kaçabilir.
- **Doğrulama derinliği değişken:** Büyük işverenler kendi ATS'leri üzerinden doğrulanabiliyor. Web sitesi olmayan küçük Türk şirketleri ise çoğunlukla en fazla "Muhtemel" etiketi alıyor. Ticaret sicili sorgusu giriş gerektirdiği için otomatik yapılamıyor.
- **Garanti yok:** "Doğrulandı" etiketli bir ilan sonradan doldurulabilir ya da dondurulabilir. "Doğrulanamadı" da sahte demek değil.
- **Maaş verisi zayıf:** İlanların çoğunda maaş yazmıyor; aralıklar kullanıcı beyanına dayalı ortalamalardan geliyor.
- **Vize kuralları her yıl değişiyor:** Eşikler çalışma anında güncel kaynaktan okunuyor, ama her zaman resmî kaynaktan ve işverenden teyit et.
- **Maliyet:** Tam çalıştırma çok sayıda alt ajan kullanıyor. Tam test yaklaşık 1,6 milyon token ve 30 dakika sürdü. Hızlı kontroller için küçük çalıştırmayı (tek ajan, ilk 3 ilan) kullan.
- **Yurt dışında dil engeli gerçek:** Almanya/Hollanda testinde giriş seviyesi lojistik işlerinin çoğu akıcı Almanca veya Hollandaca istiyordu.
- Skill senin değerlendirmenin yerini tutmaz: başvurmadan önce kanıtları oku.

### Yerleşik güvenlik kuralları

- Başvuru, form gönderme, mesaj atma, giriş yapma, CAPTCHA çözme ve ödeme yok.
- LinkedIn'de sadece arama motoruyla bulunan herkese açık sayfalar kullanılıyor (Kullanıcı Sözleşmesi §8.2).
- Engellenen siteler atlatılmıyor: sahte tarayıcı kimliği, proxy ya da başlık hilesi yok.
- TC kimlik, banka veya şifre bilgisi asla istenmiyor ya da girilmiyor. Gerçek işverenlerin teklif öncesi bunları istemeyeceği konusunda uyarı veriliyor.
- İlan metni veri olarak ele alınıyor; ilanın içine gizlenmiş talimatlar kırmızı bayrak olarak raporlanıyor.
- CV'n ve profilin bilgisayarında kalıyor.

### Lisans

MIT (`LICENSE` dosyasına bakın).
