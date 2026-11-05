"""Tests for the Python checks around Gemini. Run with: python -m pytest -v"""

import pytest

from safeguards import (check_question, clean_answer, detect_alerts, is_valid_bsn,
                        is_valid_iban, mask_personal_data)
from sources import find_glossary_terms, is_official_url, remove_unofficial_links


# --- Checking the question ---

@pytest.mark.parametrize("text", ["", "   ", "hi"])
def test_rejects_empty_or_too_short(text):
    assert check_question(text) is not None


def test_rejects_too_long():
    assert check_question("a" * 1501) is not None


def test_accepts_normal_question():
    assert check_question("How do I get a BSN in The Hague?") is None


# --- Masking personal data ---

def test_bsn_elfproef():
    assert is_valid_bsn("111222333")
    assert not is_valid_bsn("123456789")      # fails the 11-check
    assert not is_valid_bsn("000000000")


@pytest.mark.parametrize("text", ["My BSN is 111222333.", "bsn: 111 222 333", "BSN 111.222.333"])
def test_masks_valid_bsn(text):
    masked, found = mask_personal_data(text)
    assert "[BSN removed]" in masked and "BSN" in found
    assert "111" not in masked


def test_keeps_random_nine_digit_number():
    masked, found = mask_personal_data("Order number 123456789")
    assert masked == "Order number 123456789" and found == []


def test_masks_iban():
    assert is_valid_iban("NL91 ABNA 0417 1643 00")
    masked, found = mask_personal_data("Pay to NL91 ABNA 0417 1643 00 please")
    assert "[IBAN removed]" in masked and "ABNA" not in masked


def test_masks_email_phone_postcode():
    masked, found = mask_personal_data("Mail me at jan@student.hhs.nl or call 06-12345678, I live at 2521 EN")
    assert "jan@" not in masked and "12345678" not in masked and "2521" not in masked
    assert set(found) == {"email address", "phone number", "postcode"}


def test_question_without_personal_data_is_unchanged():
    q = "How much is zorgtoeslag in 2026?"
    assert mask_personal_data(q) == (q, [])


# --- Urgent-situation rules ---

def test_fine_letter_is_urgent():
    alerts = detect_alerts("I got an aanmaning from the CJIB")
    assert alerts and alerts[0].level == "urgent"


def test_rental_scam_warning():
    titles = [a.title for a in detect_alerts("The landlord is abroad and wants me to pay before viewing")]
    assert "Watch out for rental scams" in titles


def test_no_false_alarm_on_normal_question():
    assert detect_alerts("Is it fine to open a bank account before I get my BSN?") == []


def test_keywords_match_whole_words_only():
    # "ind" must not match inside "find" or "kind"
    assert detect_alerts("Where can I find a kind roommate?") == []


# --- Cleaning Gemini's answer ---

GOOD = {
    "on_topic": True,
    "simple_explanation": "You must register at the gemeente within five days of arriving.",
    "steps": ["Book an appointment", "Bring your passport and rental contract"],
    "dutch_terms": [{"term": "gemeente", "meaning": "municipality"}],
    "source_ids": ["gemeente_den_haag", "made_up_source"],
    "confidence": "medium",
    "uncertain_about": "",
}


def test_unknown_sources_are_removed():
    cleaned, notes = clean_answer(GOOD, "Government")
    assert cleaned["source_ids"] == ["gemeente_den_haag"]
    assert any("verified list" in n for n in notes)


def test_default_sources_when_none_picked():
    cleaned, _ = clean_answer({**GOOD, "source_ids": []}, "Housing")
    assert cleaned["source_ids"] == ["gemeente_den_haag", "huurcommissie"]


def test_unofficial_links_are_removed_from_text():
    answer = {**GOOD, "steps": ["Read https://random-expat-forum.com/bsn first", "See https://www.denhaag.nl/en"]}
    cleaned, notes = clean_answer(answer, "Government")
    assert "random-expat-forum" not in cleaned["steps"][0]
    assert "denhaag.nl" in cleaned["steps"][1]


def test_empty_explanation_is_rejected():
    with pytest.raises(ValueError):
        clean_answer({**GOOD, "simple_explanation": ""}, "Government")


def test_invalid_confidence_becomes_low():
    cleaned, _ = clean_answer({**GOOD, "confidence": "very sure"}, "Government")
    assert cleaned["confidence"] == "low"


# --- Sources and glossary ---

def test_official_url_check():
    assert is_official_url("https://ind.nl/en/residence-permits")
    assert is_official_url("https://www.denhaag.nl/en")
    assert not is_official_url("https://ind.nl.fake-site.com")


def test_glossary_finds_terms():
    found = find_glossary_terms("Do I need a BSN for zorgtoeslag?")
    assert {"BSN", "zorgtoeslag"} <= set(found)


def test_remove_links_counts():
    text, n = remove_unofficial_links("see https://scam.example and https://duo.nl")
    assert n == 1 and "duo.nl" in text
