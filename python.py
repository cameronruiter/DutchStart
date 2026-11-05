import os

import streamlit as st
from dotenv import load_dotenv
from enum import Enum
from google import genai
from google.genai import errors, types
from pydantic import BaseModel, ValidationError

from safeguards import check_question, clean_answer, detect_alerts, mask_personal_data
from sources import OFFICIAL_SOURCES, find_glossary_terms, remove_unofficial_links, sources_prompt_list

MODEL = "gemini-3.6-flash"
TOPICS = ["Government", "Housing", "University", "Work & Money"]

EXAMPLES = {
    "Pick an example question…": None,
    "I start a side job next week. Do I need Dutch health insurance?": "Work & Money",
    "How do I register my address in The Hague and get a BSN?": "Government",
    "I got a letter with 'aanmaning' from CJIB. What does it mean?": "Government",
    "A landlord abroad wants the deposit before viewing the room. Is this legit?": "Housing",
    "My BSN is 111222333. Why did the Belastingdienst send me a letter?": "Work & Money",
    "What is collegegeld and how do I pay it?": "University",
}

st.set_page_config(page_title="DutchStart", page_icon="🇳🇱")

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY")
if not api_key:
    st.error("No API key found.")
    st.stop()

client = genai.Client(api_key=api_key)


# ---------- What we ask Gemini for: structured output ----------

class Confidence(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"


class DutchTerm(BaseModel):
    term: str
    meaning: str


class DutchStartAnswer(BaseModel):
    on_topic: bool
    simple_explanation: str
    steps: list[str]
    dutch_terms: list[DutchTerm]
    source_ids: list[str]
    confidence: Confidence
    uncertain_about: str


SYSTEM_INSTRUCTION = f"""
You are DutchStart, an assistant for first-year international students in The Hague
who are new to Dutch systems. They read English, but not Dutch.

Rules:
- Use simple, clear English. Short sentences. Explain every Dutch word you use.
- Only answer questions about life as a student in the Netherlands (government, housing,
  university, work and money). If the question is about something else, set on_topic to false
  and explain briefly what DutchStart can help with.
- Do not invent rules, amounts, deadlines, phone numbers or websites. Never write URLs.
- If rules depend on the student's situation (EU or non-EU, income, type of room) say so.
- Set confidence to "low" when you are not sure or when rules change often, and write
  what you are unsure about in uncertain_about (otherwise leave it empty).
- Never say that a rental listing, letter or message is genuine. You cannot check that.
- Personal data in the question has been replaced with placeholders like [BSN removed].
  Do not ask for it.
- In source_ids, pick 1 to 3 IDs ONLY from this list of official sources:
{sources_prompt_list()}
""".strip()

FOLLOWUP_INSTRUCTION = SYSTEM_INSTRUCTION.split("- In source_ids")[0] + """
- This is a follow-up question about the earlier answer. Answer in plain text, at most
  150 words. End by saying which official source from the earlier answer they can check.
"""


# ---------- Calls to Gemini ----------

def friendly_error(e: Exception) -> str:
    """Turn API errors into a message the student can act on."""
    code = getattr(e, "code", None)
    if code == 429:
        return "DutchStart is getting a lot of questions right now. Please wait a minute and try again."
    if isinstance(e, errors.ServerError) or (code and code >= 500):
        return "Gemini is busy or down at the moment. Please try again in a few minutes."
    if code in (400, 401, 403):
        return "DutchStart can't connect to Gemini because of a setup problem. Please tell the developers."
    return "Something unexpected went wrong. Please try again in a moment."


@st.cache_data(ttl=3600, show_spinner=False)
def ask_gemini(topic: str, question: str) -> tuple[dict, list[str], int]:
    """Ask Gemini for a structured answer, check it, and retry once if it's unusable.

    Answers are cached for an hour, so the same question doesn't use the API quota twice.
    """
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_INSTRUCTION,
        response_mime_type="application/json",
        response_schema=DutchStartAnswer,
        temperature=0.3,
    )
    prompt = f"Topic chosen by the student: {topic}\n\nQuestion:\n{question}"
    last_problem = None

    for attempt in (1, 2):
        if attempt == 2:
            prompt += (f"\n\nYour previous answer could not be used ({last_problem}). "
                       "Answer again and follow the JSON schema exactly.")
        response = client.models.generate_content(model=MODEL, contents=prompt, config=config)
        try:
            parsed = response.parsed or DutchStartAnswer.model_validate_json(response.text)
            answer, notes = clean_answer(parsed.model_dump(mode="json"), topic)
            return answer, notes, attempt
        except (ValidationError, ValueError, TypeError) as e:
            last_problem = str(e)[:200]

    raise ValueError("Gemini gave two answers in the wrong format.")


def ask_followup(history: list[dict], question: str) -> str:
    """Multi-turn conversation: send the earlier question and answer with the new question."""
    contents = [
        types.Content(role=m["role"], parts=[types.Part(text=m["text"])]) for m in history
    ]  # earlier turns, so Gemini remembers the conversation
    contents.append(types.Content(role="user", parts=[types.Part(text=question)]))
    response = client.models.generate_content(
        model=MODEL,
        contents=contents,
        config=types.GenerateContentConfig(system_instruction=FOLLOWUP_INSTRUCTION, temperature=0.3),
    )
    text, _ = remove_unofficial_links(response.text or "")
    return text


# ---------- Display helpers ----------

def show_alerts(alerts):
    for a in alerts:
        links = " · ".join(f"[{OFFICIAL_SOURCES[s]['name']}]({OFFICIAL_SOURCES[s]['url']})" for s in a.source_ids)
        text = f"**{a.title}.** {a.message}\n\n{links}"
        {"urgent": st.error, "warning": st.warning, "info": st.info}[a.level](text)


def show_answer(result):
    answer, notes = result["answer"], result["notes"]

    if not answer["on_topic"]:
        st.info(answer["simple_explanation"])
        return

    badge = {"high": "🟢 High", "medium": "🟡 Medium", "low": "🔴 Low"}[answer["confidence"]]
    st.write(f"### Answer  \nConfidence: **{badge}**")

    st.write("#### In simple words")
    st.write(answer["simple_explanation"])

    if answer["uncertain_about"]:
        st.warning(f"**Not sure about:** {answer['uncertain_about']}")

    if answer["steps"]:
        st.write("#### What to do")
        for i, step in enumerate(answer["steps"], 1):
            st.checkbox(f"{i}. {step}", key=f"step_{result['id']}_{i}")

    # Dutch terms: our verified glossary first, then Gemini's explanations, clearly labelled.
    scanned = " ".join([result["question"], answer["simple_explanation"], *answer["steps"],
                        *[t["term"] for t in answer["dutch_terms"]]])
    verified = find_glossary_terms(scanned)
    gemini_terms = [t for t in answer["dutch_terms"] if t["term"].lower() not in {k.lower() for k in verified}]
    if verified or gemini_terms:
        st.write("#### Dutch terms")
        for term, meaning in verified.items():
            st.markdown(f"- **{term}** ✅ *DutchStart glossary*: {meaning}")
        for t in gemini_terms:
            st.markdown(f"- **{t['term']}** 🤖 *explained by AI*: {t['meaning']}")

    st.write("#### Check it here (official sources)")
    for sid in answer["source_ids"]:
        s = OFFICIAL_SOURCES[sid]
        st.markdown(f"- [{s['name']}]({s['url']}): {s['about']}")

    st.caption("DutchStart uses AI and can be wrong. Rules change every year: "
               "check important decisions with the official sources above.")

    with st.expander("What Python checked for this answer"):
        st.markdown(
            f"- Personal data removed before sending: **{', '.join(result['masked']) or 'none found'}**\n"
            f"- Urgent-situation rules triggered: **{len(result['alerts'])}**\n"
            f"- Answer checked against our JSON schema: **passed on attempt {result['attempts']}**\n"
            f"- Sources limited to our verified list of {len(OFFICIAL_SOURCES)} official websites"
        )
        for n in notes:
            st.markdown(f"- {n}")


# ---------- Page ----------

st.title("🇳🇱 DutchStart")
st.write("Plain-English help for first-year international students in The Hague: "
         "registration, housing, university, and work & money.")

if "result" not in st.session_state:
    st.session_state.result = None
    st.session_state.chat = []

example = st.selectbox("Not sure what to ask? Try an example:", list(EXAMPLES))
default_topic = EXAMPLES[example] or "Government"

category = st.selectbox("Choose a topic:", TOPICS, index=TOPICS.index(default_topic))
question = st.text_area(
    "What do you need help with?",
    value=example if EXAMPLES[example] else "",
    max_chars=1500,
    help="Don't type your BSN, bank number or address. If you do, DutchStart removes them before sending.",
)

if st.button("Explain", type="primary"):
    problem = check_question(question)
    if problem:
        st.warning(problem)
    else:
        masked_question, masked = mask_personal_data(question.strip())
        alerts = detect_alerts(question)
        try:
            with st.spinner("Checking your question and asking Gemini…"):
                answer, notes, attempts = ask_gemini(category, masked_question)
            st.session_state.result = {
                "id": abs(hash((category, masked_question))),
                "question": masked_question,
                "masked": masked,
                "alerts": alerts,
                "answer": answer,
                "notes": notes,
                "attempts": attempts,
            }
            st.session_state.chat = []
        except ValueError:
            st.session_state.result = None
            show_alerts(alerts)
            st.error("Gemini's answer didn't pass our checks, so we're not showing it. "
                     "Try rephrasing your question, or check the official sources below.")
        except Exception as e:
            st.session_state.result = None
            print(f"DutchStart error: {type(e).__name__}: {e}")
            show_alerts(alerts)
            st.error(friendly_error(e))

result = st.session_state.result
if result:
    if result["masked"]:
        st.info(f"🔒 We removed your **{', '.join(result['masked'])}** before sending your question "
                "to Gemini. You never need to share these to get an explanation.")
    show_alerts(result["alerts"])
    show_answer(result)

    if result["answer"]["on_topic"]:
        st.divider()
        st.write("#### Ask a follow-up question")
        for m in st.session_state.chat:
            with st.chat_message("user" if m["role"] == "user" else "assistant"):
                st.write(m["text"])
                show_alerts(m.get("alerts", []))

        followup = st.chat_input("For example: what happens if I miss the deadline?")
        if followup:
            problem = check_question(followup)
            if problem:
                st.warning(problem)
            else:
                masked_followup, masked = mask_personal_data(followup.strip())
                first_turn = [
                    {"role": "user", "text": f"Topic: {category}\n{result['question']}"},
                    {"role": "model", "text": result["answer"]["simple_explanation"]
                        + "\nSteps: " + "; ".join(result["answer"]["steps"])},
                ]
                try:
                    with st.spinner("Thinking…"):
                        reply = ask_followup(first_turn + st.session_state.chat, masked_followup)
                    st.session_state.chat += [
                        {"role": "user", "text": masked_followup},
                        {"role": "model", "text": reply, "alerts": detect_alerts(followup)},
                    ]
                    if masked:
                        st.session_state.chat[-1]["text"] = (
                            f"🔒 *Removed your {', '.join(masked)} before sending.*\n\n" + reply)
                    st.rerun()
                except Exception as e:
                    print(f"DutchStart follow-up error: {type(e).__name__}: {e}")
                    st.error(friendly_error(e))
