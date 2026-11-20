"""Merge raw public datasets into one labeled CSV.

Expected layout under --raw (see data/README.md for download links):

  spamassassin/<folder>/<files>   folders with "ham" in the name -> legitimate,
                                  folders with "spam" in the name -> spam
  enron/enron_spam_data.csv       columns: Subject, Message, Spam/Ham  (ham -> legitimate)
  nazario/*.mbox                  every message -> phishing

Phishing Pot is NOT merged. Keep it as a separate recent test set:
  python scripts/build_dataset.py --phishing-pot data/raw/phishing_pot --test-out data/processed/test_phishing_pot.csv

Duplicates are removed by content hash. Raw files are only read, never sent anywhere.
"""
from __future__ import annotations

import argparse
import csv
import mailbox
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.parsing import ParseError, parse_eml_bytes  # noqa: E402
from app.parsing.message import Message  # noqa: E402

FIELDS = ["source", "label", "sender", "subject", "body", "content_hash"]
csv.field_size_limit(10_000_000)


def _row(source: str, label: str, message: Message) -> dict:
    return {
        "source": source,
        "label": label,
        "sender": message.from_raw,
        "subject": message.subject,
        "body": message.body_text,
        "content_hash": message.content_hash,
    }


def iter_spamassassin(root: Path):
    for folder in sorted(p for p in root.iterdir() if p.is_dir()):
        name = folder.name.lower()
        label = "legitimate" if "ham" in name else "spam" if "spam" in name else None
        if label is None:
            continue
        for path in sorted(folder.iterdir()):
            if not path.is_file() or path.name == "cmds":
                continue
            try:
                yield _row("spamassassin", label, parse_eml_bytes(path.read_bytes()))
            except ParseError:
                yield None


def iter_enron(csv_path: Path):
    with csv_path.open(newline="", encoding="utf-8", errors="replace") as handle:
        for raw in csv.DictReader(handle):
            row = {(k or "").strip().lower(): (v or "") for k, v in raw.items()}
            tag = row.get("spam/ham", "").strip().lower()
            if tag not in {"spam", "ham"}:
                yield None
                continue
            message = Message(
                source="enron", from_raw="", subject=row.get("subject", ""),
                text_body=row.get("message", ""),
            )
            yield _row("enron", "spam" if tag == "spam" else "legitimate", message)


def iter_nazario(root: Path):
    for path in sorted(root.glob("*.mbox")):
        for item in mailbox.mbox(str(path)):
            try:
                yield _row("nazario", "phishing", parse_eml_bytes(item.as_bytes()))
            except ParseError:
                yield None


def iter_eml_dir(root: Path, source: str, label: str):
    for path in sorted(root.rglob("*.eml")):
        try:
            yield _row(source, label, parse_eml_bytes(path.read_bytes()))
        except ParseError:
            yield None


def _write(rows, out: Path) -> Counter:
    out.parent.mkdir(parents=True, exist_ok=True)
    seen: set[str] = set()
    counts: Counter = Counter()
    skipped = 0
    with out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        for row in rows:
            if row is None:
                skipped += 1
                continue
            if row["content_hash"] in seen:
                counts["duplicate"] += 1
                continue
            seen.add(row["content_hash"])
            writer.writerow(row)
            counts[(row["source"], row["label"])] += 1
    counts["unparseable"] = skipped
    return counts


def build_merged(raw: Path, out: Path) -> Counter:
    def rows():
        if (raw / "spamassassin").is_dir():
            yield from iter_spamassassin(raw / "spamassassin")
        enron = raw / "enron" / "enron_spam_data.csv"
        if enron.is_file():
            yield from iter_enron(enron)
        if (raw / "nazario").is_dir():
            yield from iter_nazario(raw / "nazario")

    return _write(rows(), out)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--raw", type=Path, default=Path("data/raw"))
    parser.add_argument("--out", type=Path, default=Path("data/processed/merged.csv"))
    parser.add_argument("--phishing-pot", type=Path, help="folder of .eml files for the separate test set")
    parser.add_argument("--test-out", type=Path, default=Path("data/processed/test_phishing_pot.csv"))
    args = parser.parse_args()

    if args.phishing_pot:
        counts = _write(iter_eml_dir(args.phishing_pot, "phishing_pot", "phishing"), args.test_out)
        print(f"Test set written to {args.test_out}: {dict(counts)}")
        return
    counts = build_merged(args.raw, args.out)
    print(f"Merged dataset written to {args.out}")
    for key, value in sorted(counts.items(), key=str):
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
