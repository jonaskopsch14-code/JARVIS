"""Offline tests for the mailbox-hygiene classifier (no network/IMAP needed)."""

import sys
from pathlib import Path

# Allow running directly: python jarvis_v6/tests/test_mailbox.py
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from integrations.mailbox import (  # noqa: E402
    MailMessage, SpamClassifier, classify_messages,
)


def _msg(uid, subject, from_, text):
    return MailMessage(uid=uid, subject=subject, from_=from_, text=text)


def test_obvious_spam_is_flagged():
    c = SpamClassifier()
    m = _msg("1", "YOU HAVE WON!!! claim now",
             "promo@deals.top", "Click here to verify your account and claim free money bitcoin")
    assert c.classify(m).label == "spam"


def test_business_enquiry_is_lead():
    c = SpamClassifier()
    m = _msg("2", "Anfrage Großhandel Kooperation",
             "einkauf@boutique.de", "Wir sind interessiert an einer Zusammenarbeit und Großbestellung.")
    assert c.classify(m).label == "lead"


def test_normal_mail_is_kept():
    c = SpamClassifier()
    m = _msg("3", "Mittagessen morgen?", "freund@gmail.com", "Hast du morgen Zeit?")
    assert c.classify(m).label == "keep"


def test_salesy_but_genuine_lead_not_trashed():
    # Mixes one weak spam-ish token with strong lead intent → must NOT be spam.
    c = SpamClassifier()
    m = _msg("4", "Angebot: Vertrieb Ihrer Produkte",
             "sales@distrib.de", "Wir bieten Vertrieb und Distribution, gerne ein Angebot / quotation.")
    assert c.classify(m).label == "lead"


def test_batch_report_counts():
    msgs = [
        _msg("1", "WIN FREE MONEY!!!", "x@spam.top", "viagra bitcoin click here"),
        _msg("2", "Anfrage Kooperation", "a@b.de", "Interessiert an Zusammenarbeit, Bestellung"),
        _msg("3", "Hi", "c@d.com", "wie gehts"),
    ]
    rep = classify_messages(msgs)
    assert rep.scanned == 3
    assert rep.spam == 1 and rep.leads == 1 and rep.kept == 1
    assert rep.lead_items and rep.lead_items[0]["uid"] == "2"


if __name__ == "__main__":
    funcs = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for fn in funcs:
        try:
            fn()
            print(f"PASS  {fn.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL  {fn.__name__}: {e}")
    print(f"\n{len(funcs) - failed}/{len(funcs)} passed")
    sys.exit(1 if failed else 0)
