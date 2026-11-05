"""Python checks that run before and after Gemini.

Before: check the question, mask personal data, and detect urgent situations.
After: validate Gemini's structured answer and clean it up.
"""

import re
from dataclasses import dataclass, field

from sources import OFFICIAL_SOURCES, TOPIC_DEFAULTS, remove_unofficial_links

MIN_LENGTH = 5
MAX_LENGTH = 1500


# ---------- 1. Check the question ----------

def check_question(text: str) -> str | None:
    """Return a message for the user if the question can't be sent, otherwise None."""
    text = (text or "").strip()
    if not text:
        return "Please type a question first."
    if len(text) < MIN_LENGTH:
        return "Your question is very short. Can you add a bit more detail?"
    if len(text) > MAX_LENGTH:
        return (f"Your question is {len(text)} characters. Please keep it under {MAX_LENGTH}, "
                "and don't paste whole letters or contracts: describe the part you don't understand.")
    return None


# ---------- 2. Mask personal data ----------

def is_valid_bsn(digits: str) -> bool:
    """The official 11-check (elfproef) for a BSN: 9 digits, weights 9..2 and -1."""
    if len(digits) != 9 or not digits.isdigit() or digits == "0" * 9:
        return False
    weights = [9, 8, 7, 6, 5, 4, 3, 2, -1]
    return sum(int(d) * w for d, w in zip(digits, weights)) % 11 == 0


def is_valid_iban(iban: str) -> bool:
    """The international mod-97 check for IBANs."""
    iban = iban.replace(" ", "").upper()
    if not re.fullmatch(r"[A-Z]{2}\d{2}[A-Z0-9]{10,30}", iban):
        return False
    rearranged = iban[4:] + iban[:4]
    number = "".join(str(int(c, 36)) for c in rearranged)
    return int(number) % 97 == 1


IBAN_RE = re.compile(r"\b[A-Z]{2}\d{2}(?:\s?[A-Z0-9]{4}){2,7}(?:\s?[A-Z0-9]{1,3})?\b", re.IGNORECASE)
EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
BSN_RE = re.compile(r"(?<![\d\w])\d{3}[\s.]?\d{3}[\s.]?\d{3}(?![\d\w])")
PHONE_RE = re.compile(
    r"(?<!\d)(?:(?:\+31|0031)[\s-]?|0)(?:6[\s-]?\d{8}|[1-9]\d[\s-]?\d{7})(?!\d)"
)
POSTCODE_RE = re.compile(r"\b\d{4}\s?[A-Z]{2}\b")


def mask_personal_data(text: str) -> tuple[str, list[str]]:
    """Replace personal data with placeholders before anything is sent to Gemini.

    Returns the masked text and a list of what was removed, so the app can tell the user.
    """
    found = []

    def _iban(m):
        if is_valid_iban(m.group(0)):
            found.append("bank account number (IBAN)")
            return "[IBAN removed]"
        return m.group(0)

    def _bsn(m):
        if is_valid_bsn(re.sub(r"\D", "", m.group(0))):
            found.append("BSN")
            return "[BSN removed]"
        return m.group(0)

    def _simple(label, placeholder):
        def _swap(m):
            found.append(label)
            return placeholder
        return _swap

    text = IBAN_RE.sub(_iban, text)
    text = EMAIL_RE.sub(_simple("email address", "[email removed]"), text)
    text = BSN_RE.sub(_bsn, text)
    text = PHONE_RE.sub(_simple("phone number", "[phone number removed]"), text)
    text = POSTCODE_RE.sub(_simple("postcode", "[postcode removed]"), text)

    return text, sorted(set(found))


# ---------- 3. Detect urgent situations ----------

@dataclass
class Alert:
    level: str          # "urgent", "warning" or "info"
    title: str
    message: str
    source_ids: list = field(default_factory=list)


ALERT_RULES = [
    {
        "level": "urgent",
        "title": "This sounds time-sensitive",
        "keywords": ["aanmaning", "boete", "incasso", "incassobureau", "deurwaarder", "bailiff",
                     "debt collector", "final reminder", "laatste herinnering", "cjib", "a fine",
                     "fined", "dwangbevel"],
        "message": ("Don't ignore letters about fines or debts: the costs usually go up if you wait. "
                    "Contact the sender using the details on their official website, or get free help "
                    "from Juridisch Loket."),
        "source_ids": ["juridisch_loket", "cjib"],
    },
    {
        "level": "urgent",
        "title": "Possible eviction",
        "keywords": ["ontruiming", "uitzetting", "evict", "evicted", "eviction", "kicked out",
                     "thrown out", "change the locks", "changed the locks"],
        "message": ("A landlord usually can't simply put you out without a court decision. "
                    "Get free legal advice from Juridisch Loket as soon as possible."),
        "source_ids": ["juridisch_loket", "huurcommissie"],
    },
    {
        "level": "warning",
        "title": "Watch out for rental scams",
        "keywords": ["before viewing", "without viewing", "pay before", "western union", "landlord abroad",
                     "landlord is abroad", "living abroad", "send the keys", "post the keys", "wire the deposit",
                     "too good to be true", "scam", "legit"],
        "message": ("Red flags: paying before you've seen the room, a landlord who is 'abroad', keys sent by post, "
                    "or a price far below other rooms. DutchStart can't check whether a listing is real. "
                    "Never transfer money because an app or chatbot said it looks fine."),
        "source_ids": ["fraudehelpdesk"],
    },
    {
        "level": "warning",
        "title": "Problem with a deposit or rent",
        "keywords": ["borg", "deposit back", "keep my deposit", "keeping my deposit", "kept my deposit",
                     "rent too high", "huurverhoging", "servicekosten"],
        "message": ("Deposit and rent disputes have clear rules in the Netherlands. The Huurcommissie and "
                    "Juridisch Loket can help for free or at low cost."),
        "source_ids": ["huurcommissie", "juridisch_loket"],
    },
    {
        "level": "warning",
        "title": "Health insurance letter",
        "keywords": ["cak", "no health insurance", "without health insurance", "not insured",
                     "uninsured", "zorgverzekering boete"],
        "message": ("If you work in the Netherlands, even a small side job, you must have Dutch basic health "
                    "insurance. A letter from the CAK has a deadline: act before it passes."),
        "source_ids": ["cak", "government_health_insurance"],
    },
    {
        "level": "info",
        "title": "Visa and residence permits",
        "keywords": ["ind", "verblijfsvergunning", "residence permit", "visa", "mvv", "deported",
                     "work permit", "twv"],
        "message": ("DutchStart can explain terms, but mistakes here can affect your right to stay. "
                    "Always check with the IND or your university's international office."),
        "source_ids": ["ind", "thuas"],
    },
]


def _contains(text: str, keyword: str) -> bool:
    return re.search(rf"(?<!\w){re.escape(keyword)}(?!\w)", text, flags=re.IGNORECASE) is not None


def detect_alerts(text: str) -> list[Alert]:
    """Fixed Python rules, so urgent situations are flagged whatever Gemini says."""
    alerts = []
    for rule in ALERT_RULES:
        if any(_contains(text, k) for k in rule["keywords"]):
            alerts.append(Alert(rule["level"], rule["title"], rule["message"], rule["source_ids"]))
    order = {"urgent": 0, "warning": 1, "info": 2}
    return sorted(alerts, key=lambda a: order[a.level])


# ---------- 4. Validate and clean Gemini's answer ----------

def clean_answer(answer: dict, topic: str) -> tuple[dict, list[str]]:
    """Check Gemini's structured answer and fix what we can.

    Returns the cleaned answer and a list of notes about what Python changed.
    Raises ValueError if the answer is unusable, so the app can ask Gemini again.
    """
    notes = []
    explanation = (answer.get("simple_explanation") or "").strip()
    if answer.get("on_topic", True) and len(explanation) < 20:
        raise ValueError("Gemini's explanation is empty or too short.")

    removed_total = 0
    explanation, removed = remove_unofficial_links(explanation)
    removed_total += removed

    steps = []
    for step in (answer.get("steps") or [])[:7]:
        step, removed = remove_unofficial_links(str(step).strip())
        removed_total += removed
        if step:
            steps.append(step)

    terms = []
    for t in (answer.get("dutch_terms") or [])[:8]:
        term, meaning = str(t.get("term", "")).strip(), str(t.get("meaning", "")).strip()
        if term and meaning:
            terms.append({"term": term, "meaning": meaning})

    picked = answer.get("source_ids") or []
    valid_ids = [sid for sid in dict.fromkeys(picked) if sid in OFFICIAL_SOURCES]
    unknown = len(picked) - len(valid_ids)
    if unknown > 0:
        notes.append(f"Removed {unknown} source(s) Gemini suggested that aren't on our verified list.")
    if not valid_ids:
        valid_ids = TOPIC_DEFAULTS.get(topic, [])
        notes.append("Gemini didn't pick a source, so we show the default official sources for this topic.")

    if removed_total:
        notes.append(f"Removed {removed_total} link(s) to websites that aren't official sources.")

    confidence = str(answer.get("confidence", "medium")).lower()
    if confidence not in {"high", "medium", "low"}:
        confidence = "low"

    cleaned = {
        "on_topic": bool(answer.get("on_topic", True)),
        "simple_explanation": explanation,
        "steps": steps,
        "dutch_terms": terms,
        "source_ids": valid_ids[:4],
        "confidence": confidence,
        "uncertain_about": (answer.get("uncertain_about") or "").strip(),
    }
    return cleaned, notes
