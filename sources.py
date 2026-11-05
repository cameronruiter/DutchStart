"""Verified information DutchStart controls itself, so Gemini never has to invent it.

- OFFICIAL_SOURCES: the only links the app will ever show. Gemini may only pick IDs from
  this list; Python checks every ID and turns it into a link.
- GLOSSARY: our own definitions of Dutch terms first-year students run into.
"""

import re
from urllib.parse import urlparse

OFFICIAL_SOURCES = {
    "gemeente_den_haag": {
        "name": "Gemeente Den Haag (municipality)",
        "url": "https://www.denhaag.nl/en",
        "about": "Registering your address (BRP), getting a BSN, moving, municipal taxes in The Hague",
        "topics": ["Government", "Housing"],
    },
    "hague_international_centre": {
        "name": "The Hague International Centre",
        "url": "https://www.thehagueinternationalcentre.nl",
        "about": "Help for internationals arriving in The Hague: registration appointments, first steps",
        "topics": ["Government", "Housing", "Work & Money"],
    },
    "digid": {
        "name": "DigiD",
        "url": "https://www.digid.nl/en",
        "about": "Your digital login for Dutch government websites",
        "topics": ["Government", "Work & Money"],
    },
    "ind": {
        "name": "IND (Immigration and Naturalisation Service)",
        "url": "https://ind.nl/en",
        "about": "Residence permits, visas, rules about working next to your studies as a non-EU student",
        "topics": ["Government", "University", "Work & Money"],
    },
    "government_health_insurance": {
        "name": "Government.nl: health insurance",
        "url": "https://www.government.nl/topics/health-insurance",
        "about": "When you must take out Dutch basic health insurance (basisverzekering)",
        "topics": ["Work & Money", "Government"],
    },
    "cak": {
        "name": "CAK",
        "url": "https://www.hetcak.nl",
        "about": "Letters and fines for people who should have Dutch health insurance but don't",
        "topics": ["Work & Money", "Government"],
    },
    "belastingdienst": {
        "name": "Belastingdienst (Tax and Customs Administration)",
        "url": "https://www.belastingdienst.nl/wps/wcm/connect/en/individuals/individuals",
        "about": "Income tax, and toeslagen (allowances) like zorgtoeslag and huurtoeslag",
        "topics": ["Work & Money", "Housing"],
    },
    "duo": {
        "name": "DUO",
        "url": "https://duo.nl",
        "about": "Tuition fees, student finance, and the student travel product",
        "topics": ["University", "Work & Money"],
    },
    "studyinnl": {
        "name": "Study in NL (Nuffic)",
        "url": "https://www.studyinnl.org",
        "about": "Official guide for international students: studying, living and working in the Netherlands",
        "topics": ["University", "Housing", "Work & Money"],
    },
    "thuas": {
        "name": "The Hague University of Applied Sciences",
        "url": "https://www.thehagueuniversity.com",
        "about": "Your university's own rules, international office and student support",
        "topics": ["University"],
    },
    "huurcommissie": {
        "name": "Huurcommissie (Rent Tribunal)",
        "url": "https://www.huurcommissie.nl",
        "about": "Disputes about rent that is too high, service costs, or maintenance",
        "topics": ["Housing"],
    },
    "juridisch_loket": {
        "name": "Juridisch Loket (free legal advice)",
        "url": "https://www.juridischloket.nl",
        "about": "Free legal help for problems with a landlord, employer, debts or fines",
        "topics": ["Housing", "Work & Money", "Government"],
    },
    "fraudehelpdesk": {
        "name": "Fraudehelpdesk",
        "url": "https://www.fraudehelpdesk.nl",
        "about": "Report or check scams, including fake rental listings and fake government messages",
        "topics": ["Housing", "Work & Money"],
    },
    "cjib": {
        "name": "CJIB",
        "url": "https://www.cjib.nl",
        "about": "Collects traffic fines and other government fines",
        "topics": ["Government", "Work & Money"],
    },
}

# Links shown with every answer for a topic when Gemini picks none.
TOPIC_DEFAULTS = {
    "Government": ["gemeente_den_haag", "hague_international_centre"],
    "Housing": ["gemeente_den_haag", "huurcommissie"],
    "University": ["thuas", "studyinnl"],
    "Work & Money": ["belastingdienst", "government_health_insurance"],
}

OFFICIAL_DOMAINS = {
    urlparse(s["url"]).netloc.removeprefix("www.") for s in OFFICIAL_SOURCES.values()
} | {"overheid.nl", "rijksoverheid.nl", "toeslagen.nl"}

GLOSSARY = {
    "BSN": "Burgerservicenummer: your personal citizen service number. You get it when you register at the gemeente, and you need it to work, get insurance and use DigiD.",
    "BRP": "Basisregistratie Personen: the government's register of where people live. Registering your address here is how you get a BSN.",
    "inschrijving": "Registration, for example registering your address at the gemeente, or enrolling at your university.",
    "gemeente": "Municipality: the local government of your city.",
    "DigiD": "Your digital ID for logging in to Dutch government websites like the Belastingdienst and DUO.",
    "basisverzekering": "Basic health insurance. It is required by law for people who live or work in the Netherlands, including students with a paid side job.",
    "zorgtoeslag": "Healthcare allowance: money from the government to help pay for Dutch health insurance if your income is low.",
    "huurtoeslag": "Rent allowance: money from the government to help pay rent, only for certain independent homes and incomes.",
    "toeslagen": "Allowances from the government, such as zorgtoeslag and huurtoeslag. If you get too much, you have to pay it back.",
    "eigen risico": "The deductible on Dutch health insurance: the amount you pay yourself each year before insurance pays for most care.",
    "huisarts": "General practitioner (GP). In the Netherlands you register with one near your home and go there first for most health problems.",
    "borg": "Deposit: money you pay a landlord at the start, which you should get back at the end if there is no damage.",
    "huurcontract": "Rental contract.",
    "servicekosten": "Service costs: extra costs on top of rent, for things like cleaning, energy or internet in shared buildings.",
    "aanmaning": "A formal reminder that you haven't paid yet. Ignoring it usually leads to extra costs.",
    "deurwaarder": "Bailiff: an official who collects debts and can take legal steps. Contact them quickly if you get a letter.",
    "incassobureau": "Debt-collection agency. Your debt has been passed on to them because it wasn't paid on time.",
    "collegegeld": "Tuition fee for your studies, paid via Studielink/your university.",
    "Studielink": "The national website where you enrol for a study programme in the Netherlands.",
    "bijbaan": "A side job next to your studies.",
}


def find_glossary_terms(text: str) -> dict:
    """Return the glossary entries whose term appears in the text (whole words, any case)."""
    found = {}
    for term, meaning in GLOSSARY.items():
        if re.search(rf"(?<!\w){re.escape(term)}(?!\w)", text, flags=re.IGNORECASE):
            found[term] = meaning
    return found


def is_official_url(url: str) -> bool:
    host = urlparse(url).netloc.lower().removeprefix("www.")
    return any(host == d or host.endswith("." + d) for d in OFFICIAL_DOMAINS)


URL_PATTERN = re.compile(r"https?://[^\s)\]>\"']+")


def remove_unofficial_links(text: str) -> tuple[str, int]:
    """Replace any link that isn't on an official domain. Returns (clean text, links removed)."""
    removed = 0

    def _swap(match):
        nonlocal removed
        if is_official_url(match.group(0)):
            return match.group(0)
        removed += 1
        return "[link removed: not an official source]"

    return URL_PATTERN.sub(_swap, text), removed


def sources_prompt_list() -> str:
    """The source list as it is given to Gemini: ID plus what it covers."""
    return "\n".join(f"- {sid}: {s['name']}. {s['about']}" for sid, s in OFFICIAL_SOURCES.items())
