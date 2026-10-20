# Scoring and pros/cons

Score (0–100) = 0.6 × **Fit** + 0.4 × **Potential**. The tracker puts **reachable** jobs first, sorted by
verification label (Doğrulandı → Muhtemel → Şüpheli) and then score; jobs with a **hard blocker** go to the end
regardless of label, with the blocker named in the `blocker` field.

**Hard blocker** = something the candidate can't fix before applying: work permit impossible or very unlikely
(e.g. salary far below the visa threshold, employer not a recognised sponsor), a mandatory language the
candidate doesn't speak at the required level, or required experience far beyond theirs (e.g. supervisor
role with years of team leading for a new graduate). A hard blocker caps **fit at 30**: apply the cap the
same way to every job (in testing, one job was capped and an equally blocked one wasn't). A softer gap
(1–2 years asked, internship only) lowers the skills/eligibility points instead.

## Fit: how well this job matches THIS candidate (0–100)

| Part | Points | Look at |
|---|---|---|
| Must-have skills covered | 40 | each must-have requirement vs. the CV, with evidence from the CV (project, course, job). Nice-to-haves only as tie-breakers |
| Eligibility | 20 | student/graduate status and dates, required degree, work authorisation, minimum hours, internship type (zorunlu/gönüllü). A hard blocker → fit ≤ 30 and say why |
| Location and schedule | 15 | city/remote/hybrid vs. the user's constraints, start date, duration |
| Language | 10 | required languages and levels vs. the CV |
| Interest and direction | 15 | match with the user's stated goals (e.g. AI, cryptography) |

## Potential: how good the opportunity is (0–100)

| Part | Points | Look at |
|---|---|---|
| Learning and mentorship | 20 | structured program, mentor, real project, tech stack worth learning |
| Company health | 20 | layoffs, funding, growth, review trends |
| Pay vs. market | 20 | stated pay or researched range vs. market for this level and city; unpaid internships score low |
| Career value | 20 | brand, network, how relevant the experience is for the next step |
| Path forward | 20 | return offers / full-time conversion, visa sponsorship history, graduate programs |

Write the sub-scores into the verification note or pros/cons when they decide the ranking.

## Pros and cons

- At least two of each, concrete and sourced: "Glassdoor 4.1/5 (230 reviews, link)", "pays 35.000 TL/month (stated in posting)", not "good company".
- Cons must include real risks: competition, unpaid, relocation cost, visa uncertainty, ghost-job signals, unverified points.
- Never invent numbers. If salary is unknown, say so and give a researched range with its source, or "bilinmiyor".

## Cross-check of the ranking

Before writing the tracker, two independent reviewers see the anonymized top list (Job A, B, C…) with the
CV summary and the evidence, and answer: is the order right, is any pro/con wrong or unsupported, is any
risk missing? Fix confirmed errors; mention unresolved disagreements in the report.
