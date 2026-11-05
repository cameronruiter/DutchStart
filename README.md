# Week 3 · Hackathon 3: DutchStart

**Where do I even start in the Netherlands?** DutchStart lets first-year international students in The Hague ask questions about Dutch government, housing, university and work & money, and get a plain-English explanation, clear next steps, the Dutch terms explained, and a reminder of where to check.

**SDG 10: Reduced Inequalities** | AI for Good, Hackathon 3 | Cameron Ruiter and Domilė Žukaitė

| | |
|---|---|
| 🌐 **Live app** | [dutchstart.streamlit.app](https://dutchstart.streamlit.app/) |
| 📦 **Code repository** | [github.com/cameronruiter/DutchStart](https://github.com/cameronruiter/DutchStart) |
| ⚖️ **Ethical reflection** | [Ethical reflection](#ethical-reflection) |
| 🎞️ **Presentation** | [Canva slides](https://www.canva.com/design/DAHWA-J538w/WME0XGq9bRpNwWMLlynnDQ/edit) · [PDF](Hackathon-week-3-slides-pdf.pdf) |
| 🌍 **SDG 10** | [sdgs.un.org/goals/goal10](https://sdgs.un.org/goals/goal10) |

## What it does
You choose one of four topics, **Government**, **Housing**, **University** or **Work & Money**, and type your question in English. DutchStart sends it to Google's Gemini through a live API call and shows:
- **A simple explanation** in plain English
- **Next steps**: what to actually do
- **Dutch terms explained**, such as *inschrijving*, *huurtoeslag* or *eigen risico*
- **A reminder to check** important information with official sources

## The problem
International students say Dutch bureaucracy is one of their biggest struggles. In a 2026 survey of about 700 international students by ISO, LSVb and ESN, students said they were happy with their education but struggled with housing and administrative systems [1]. In an earlier edition, almost 70% said it wasn't clear whether they needed Dutch health insurance [2].

Mistakes cost money. As soon as a student starts a side job, even part-time, they must take out Dutch basic health insurance [3]. If the CAK thinks you live or work here without it, you get letters, then fines, and the debt can go to a collection agency [4].

Most of the information is in Dutch, spread across many government websites, and full of unfamiliar terms. A Dutch student can ask their parents. A first-year international student usually has no one to ask, and searching in English often turns up outdated or expat-forum answers.

## Who it is for
**First-year non-EU international students in The Hague** (for example at THUAS) in their first months in the Netherlands. In those months they have to do a lot at once: register at the gemeente and get a BSN, set up DigiD, find a room and sign a Dutch rental contract, and, once they take a side job, arrange Dutch health insurance and zorgtoeslag. The four topics match the areas they run into first.

**Not for:** legal advice, disputes with a landlord or the Belastingdienst, or visa and residence-permit decisions. For those, students should go to Juridisch Loket, the IND or their university's international office.

## Why SDG 10
SDG 10 is about making sure people aren't left behind because of where they come from. Dutch systems assume you can read Dutch and have someone to ask. International students often have neither, so the same task costs them more time, more stress, and sometimes more money (fines, repaying toeslagen) than a Dutch student. DutchStart doesn't change the rules. It helps every student understand them.

## How it works
1. The student opens the app in their browser (Streamlit) and picks a topic.
2. They type a question. If the box is empty, the app asks them to type something first.
3. Python builds a prompt with the topic, the question and our instructions: answer in simple English, use the four-part layout, don't invent information, say when you're unsure, and point to official sources.
4. The prompt goes to Gemini through the `google-genai` Python library. The API key is stored as a server-side secret, so users never see it.
5. The answer is shown in the app. If the API call fails, the app shows an error message instead of an empty or broken answer.

## Ethical reflection
**1. Wrong rules sound just as confident as right ones.** Dutch rules change every year: zorgtoeslag amounts, income limits, housing rules. Gemini can give last year's answer in a confident, friendly tone. The students we built this for are the least able to notice, because they don't know the system yet. Our prompt tells Gemini to say when it is unsure and to point to the official source, but that is an instruction, not a guarantee. A student who acts on a wrong answer (for example, not taking Dutch insurance after starting a side job) could end up with fines.

**2. Students may type in personal details.** Someone asking about a letter might paste in their BSN, address or the amount they owe. Everything typed goes to Google's Gemini API, and on the free tier Google may use it to improve its products. We don't save questions, but the app doesn't yet stop users from sending this data.

**3. It could replace real help instead of leading to it.** If DutchStart feels good enough, a student with a serious problem, such as a landlord keeping their deposit or a visa question, might keep asking the app instead of going to Juridisch Loket or the international office. That's why we state what the app is not for, and every answer ends with where to check.

**4. Scams.** Rental scams often target internationals. If a student asks "Is this listing legit?", Gemini can't check the listing and might reassure them. The app should never be the reason someone transfers a deposit.

**5. Who is left out.** The app only works in English and needs a phone or laptop with internet. Students with weaker English, who need help the most, get less out of it.

**What we would change next:** mask BSN and IBAN numbers before anything is sent to Gemini, only show links from official government domains, and test the answers against official sources to measure how often Gemini is wrong.

## Run it yourself
The easiest way is the [live app](https://dutchstart.streamlit.app/), with nothing to install.

To run it locally:
```
git clone https://github.com/cameronruiter/DutchStart
cd DutchStart
python -m pip install -r requirements.txt
python -m streamlit run python.py
```
First create a `.env` file in the project folder containing `GEMINI_API_KEY=your_key_here`. Never commit that file.

**Sources.** [1] NL Times, [*International students happy with Dutch education, struggle with housing, bureaucracy*](https://nltimes.nl/node/87383) (16-03-2026). [2] The PIE News, [*Int'l students treated as "second class citizens"*](https://thepienews.com/netherlands-intl-students-treated-second-class-citizens-survey/) (01-09-2022). [3] Belastingdienst, [*Zorgtoeslag voor buitenlandse studenten*](https://www.belastingdienst.nl/wps/wcm/connect/nl/zorgtoeslag/content/Zorgtoeslag-buitenlandse-student). [4] Overstappen.nl, [*Working while studying as an international student*](https://www.overstappen.nl/zorgverzekering/compare-student-health-insurance/working-while-studying).
