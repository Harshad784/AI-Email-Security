import csv
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from build_dataset import build_merged  # noqa: E402


def _eml(subject, body, sender="a@example.com"):
    return f"From: {sender}\nSubject: {subject}\n\n{body}\n".encode()


def test_merge_labels_and_deduplicate():
    with tempfile.TemporaryDirectory() as tmp:
        raw = Path(tmp) / "raw"
        (raw / "spamassassin" / "easy_ham").mkdir(parents=True)
        (raw / "spamassassin" / "spam").mkdir(parents=True)
        (raw / "enron").mkdir()
        (raw / "nazario").mkdir()

        (raw / "spamassassin" / "easy_ham" / "1").write_bytes(_eml("Hello", "normal mail"))
        (raw / "spamassassin" / "spam" / "1").write_bytes(_eml("Win", "buy now"))
        (raw / "spamassassin" / "spam" / "2").write_bytes(_eml("Win", "buy now"))  # duplicate
        with (raw / "enron" / "enron_spam_data.csv").open("w", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["Message ID", "Subject", "Message", "Spam/Ham", "Date"])
            writer.writerow(["1", "Lunch", "see you at noon", "ham", "2001-01-01"])
        (raw / "nazario" / "p.mbox").write_bytes(
            b"From a@example.com Mon Jan  1 00:00:00 2007\n"
            b"From: bad@example.org\nSubject: Verify\n\nclick here to verify\n\n"
        )

        out = Path(tmp) / "out" / "merged.csv"
        counts = build_merged(raw, out)
        rows = list(csv.DictReader(out.open(newline="")))

        labels = sorted(r["label"] for r in rows)
        assert labels == ["legitimate", "legitimate", "phishing", "spam"]
        assert counts["duplicate"] == 1
        assert {r["source"] for r in rows} == {"spamassassin", "enron", "nazario"}
