from unittest import mock

from app.pipeline import analyze_message
from tests.helpers import load


def test_phish_is_classified_phishing():
    result = analyze_message(load("phish_credential.eml"))
    assert result["label"] == "phishing"
    assert result["probabilities"]["phishing"] > 0.9
    assert result["top_signals"], "verdict must list the signals behind it"
    assert result["model_version"]
    assert result["summary"].startswith("Likely phishing")


def test_ham_is_legitimate_and_not_uncertain():
    result = analyze_message(load("ham_meeting.eml"))
    assert result["label"] == "legitimate"
    assert result["uncertain"] is False
    assert "not a guarantee" in result["summary"]


def test_probabilities_sum_to_one_and_label_is_valid():
    for name in ("phish_credential.eml", "ham_meeting.eml", "spam_marketing.eml", "with_attachment.eml"):
        result = analyze_message(load(name))
        assert result["label"] in {"phishing", "spam", "legitimate"}
        assert abs(sum(result["probabilities"].values()) - 1.0) < 0.01


def test_analysis_makes_no_network_calls():
    # Acceptance check: with the reputation provider disabled, nothing touches the network.
    with mock.patch("socket.socket", side_effect=RuntimeError("network call attempted")):
        analyze_message(load("phish_credential.eml"))
