# Week 3 · Hackathon 3: DutchStart

**Where do I even start in the Netherlands?** DutchStart helps first-year international students in The Hague understand Dutch government, housing, university and work & money rules. It explains things in plain English, but first it removes their personal data, warns them when a situation is urgent or looks like a scam, and only ever sends them to official websites.

**SDG 10: Reduced Inequalities** | AI for Good, Hackathon 3 | Cameron Ruiter and Domilė Žukaitė

| | |
|---|---|
| 🌐 **Live app** | [dutchstart.streamlit.app](https://dutchstart.streamlit.app/) |
| 📦 **Code repository** | [github.com/cameronruiter/DutchStart](https://github.com/cameronruiter/DutchStart) |
| ⚖️ **Ethical reflection** | [Ethical reflection](#ethical-reflection) |
| 🎞️ **Presentation** | [Canva slides](https://www.canva.com/design/DAHWA-J538w/WME0XGq9bRpNwWMLlynnDQ/edit) · [PDF](Hackathon-week-3-slides-pdf%20%281%29.pdf) |
| 🌍 **SDG 10** | [sdgs.un.org/goals/goal10](https://sdgs.un.org/goals/goal10) |

## What it does
You pick a topic (**Government**, **Housing**, **University** or **Work & Money**) and type a question in English, or try one of the example questions. DutchStart shows:
- **A plain-English explanation**, with a confidence label (🟢 high, 🟡 medium, 🔴 low) and what Gemini isn't sure about
- **A checklist of next steps**
- **Dutch terms explained**: ✅ from our own glossary where we have the term, 🤖 marked as AI-explained where we don't
- **Official sources to check**, picked only from our list of 14 verified websites
- **Warnings** when the question is about a fine, a debt, an eviction, a deposit, a possible rental scam, a CAK letter or a residence permit
- **A follow-up chat**, so you can ask "what if I miss the deadline?" about the same answer

## The problem
International students say Dutch bureaucracy is one of their biggest struggles. In a 2026 survey of about 700 international students by ISO, LSVb and ESN, students said they were happy with their education but struggled with housing and administrative systems [1]. In an earlier edition, almost 70% said it wasn't clear whether they needed Dutch health insurance [2].

Mistakes cost money. As soon as a student starts a side job, even part-time, they must take out Dutch basic health insurance [3]. If the CAK thinks you live or work here without it, you get letters, then fines, and the debt can go to a collection agency [4]. Students in the same survey also said rental scams seem to target internationals [2].

A Dutch student can ask their parents what an *aanmaning* is. A first-year international student usually has no one to ask. Asking a general chatbot helps a bit, but it will happily take your BSN, link you to an expat forum, and answer "is this listing legit?" in a reassuring tone.

## Who it is for
**First-year non-EU international students in The Hague** (for example at THUAS) in their first months in the Netherlands. In those months they have to do a lot at once: register at the gemeente and get a BSN, set up DigiD, find a room and sign a Dutch rental contract, and, once they take a side job, arrange Dutch health insurance and zorgtoeslag. The four topics match the areas they run into first.

**Not for:** legal advice, disputes with a landlord or the Belastingdienst, checking whether a listing or letter is real, or visa and residence-permit decisions. For those, the app sends students to Juridisch Loket, the Huurcommissie, the Fraudehelpdesk or the IND.

## Why SDG 10
SDG 10 is about making sure people aren't left behind because of where they come from. Dutch systems assume you can read Dutch and have someone to ask. International students often have neither, so the same task costs them more time, more stress, and sometimes more money (fines, repaying toeslagen, a lost deposit) than a Dutch student. DutchStart doesn't change the rules. It helps every student understand them in time.

## How it works
1. **Python checks the question.** Empty, too short (under 5 characters) or too long (over 1,500) questions are stopped with a clear message.
2. **Python removes personal data** before anything leaves the app: BSN numbers (only real ones, checked with the official *elfproef*), IBANs (checked with the mod-97 check), email addresses, Dutch phone numbers and postcodes. The student sees what was removed.
3. **Python checks for urgent situations** with fixed keyword rules, in English and Dutch (*aanmaning*, *deurwaarder*, *ontruiming*, "pay before viewing"…). The warning is shown whatever Gemini answers, and even if Gemini fails.
4. **Gemini answers in structured JSON.** We use a **system instruction** (rules kept separate from the question), a **response schema** (a Pydantic model with explanation, steps, terms, source IDs, confidence and what it's unsure about), and a low temperature (0.3) for consistent answers.
5. **Python checks Gemini's answer.** If the JSON doesn't fit the schema or the explanation is empty, the app asks Gemini again once. After that it shows an error instead of a broken answer. Source IDs that aren't on our list are dropped, and any link to a non-official website is removed from the text.
6. **Python adds verified information**: links from our own source list, and Dutch terms from our own glossary of 20 terms.
7. **Follow-up questions** use Gemini's **multi-turn conversation**: the earlier question and answer are sent along, so Gemini knows what "it" refers to. Follow-ups go through the same masking, warnings and link filter.
8. **Answers are cached for an hour**, so the same question doesn't use up the free API quota, and API errors get their own message (too many requests, Gemini down, setup problem).

Every answer has a **"What Python checked for this answer"** box that shows exactly what the app did.

### What Gemini does vs what Python does
| Gemini | Python |
|---|---|
| Explains the rule in plain English | Checks the question before it is sent |
| Fills in our JSON schema: steps, terms, confidence, what it's unsure about | Removes BSN, IBAN, email, phone number and postcode |
| Picks which official sources fit, from our list | Shows warnings for fines, evictions, deposits, scams, CAK letters and visas |
| Answers follow-up questions about the same answer | Checks the JSON, retries once, drops made-up sources and unofficial links |
| | Adds links and glossary definitions we wrote and checked ourselves |
| | Caches answers and handles each type of API error separately |

**Why not just use the Gemini website?** It gives a similar explanation, but it doesn't remove your BSN, it doesn't warn you about a likely scam no matter how the answer comes out, and it can send you to any website. DutchStart only sends you to official ones.

## Results
`test_safeguards.py` has **25 automatic tests** for the Python checks, and all 25 pass (`python -m pytest -v`). They check, for example, that:
- a real BSN (`111222333`) is removed, but a random 9-digit order number is not
- an IBAN, email, phone number and postcode are removed, and a normal question isn't changed
- "I got an aanmaning from the CJIB" gives an **urgent** warning, and "the landlord is abroad and wants me to pay before viewing" gives a **scam** warning
- "Is it fine to open a bank account…" gives **no** false alarm, and "find" doesn't trigger the "IND" rule
- a made-up source ID and a link to an expat forum are removed from Gemini's answer

**Limits.** Masking only finds patterns: a name or a street address written out in words still goes to Gemini. The keyword rules miss situations described in other words (for example "my landlord wants me out" without "evict"). The tests check our Python, not whether Gemini's explanations are correct. That would need a Dutch speaker to check answers against official sources.

## Ethical reflection
**1. Wrong rules sound just as confident as right ones.** Dutch rules change every year: zorgtoeslag amounts, income limits, housing rules. Gemini can give last year's answer in a friendly, confident tone, and the students we built this for are the least able to notice. So we ask Gemini to rate its own confidence and say what it's unsure about, we show that at the top of the answer, and every answer links to the official source. A confidence label from an AI is still not proof, so the app says plainly that it can be wrong.

**2. Students type in personal details.** Someone asking about a letter will often paste in their BSN, IBAN or address. Everything sent goes to Google's Gemini API, and on the free tier Google may use it to improve its products. DutchStart removes BSNs, IBANs, emails, phone numbers and postcodes before sending, tells the student what it removed, and saves nothing. It can't catch everything (a name, or an address written in words), so the question box also asks students not to share personal details.

**3. It could replace real help instead of leading to it.** If DutchStart feels good enough, a student with a serious problem might keep asking the app instead of getting help. That's why urgent situations (fines, debts, eviction, deposits) get a warning with a link to Juridisch Loket or the Huurcommissie, and visa questions are always sent to the IND. These warnings are fixed Python rules, so Gemini can't talk them away.

**4. Scams.** Rental scams often target internationals. If a student asks "is this listing legit?", a chatbot can't check the listing but may still sound reassuring. DutchStart shows a scam warning with the red flags and the Fraudehelpdesk, and Gemini is told never to say a listing or letter is genuine.

**5. Sending people to the wrong place.** A chatbot can link to outdated expat blogs or sites that look official but aren't. DutchStart only shows links from our own list of 14 official websites and removes every other link from Gemini's answer. The other side is that our list can go out of date too, so it has to be checked regularly.

**6. Who is left out.** The app works in English only and needs a phone or laptop with internet. Students with weaker English, who need help the most, get less out of it.

## Run it yourself (Windows)
The easiest way is the [live app](https://dutchstart.streamlit.app/), with nothing to install.

To run it locally:
```
git clone https://github.com/cameronruiter/DutchStart
cd DutchStart
python -m pip install -r requirements.txt
copy .env.example .env
python -m streamlit run python.py
```
Put your own Gemini API key in `.env` first. Never commit that file. To run the tests: `python -m pytest -v`.

**Files.** `python.py`: the Streamlit app and Gemini calls. `safeguards.py`: question checks, data masking, warning rules and answer checks. `sources.py`: our official source list and glossary. `test_safeguards.py`: the tests.

**Sources.** [1] NL Times, [*International students happy with Dutch education, struggle with housing, bureaucracy*](https://nltimes.nl/node/87383) (16-03-2026). [2] The PIE News, [*Int'l students treated as "second class citizens"*](https://thepienews.com/netherlands-intl-students-treated-second-class-citizens-survey/) (01-09-2022). [3] Belastingdienst, [*Zorgtoeslag voor buitenlandse studenten*](https://www.belastingdienst.nl/wps/wcm/connect/nl/zorgtoeslag/content/Zorgtoeslag-buitenlandse-student). [4] Overstappen.nl, [*Working while studying as an international student*](https://www.overstappen.nl/zorgverzekering/compare-student-health-insurance/working-while-studying).
