# Email Analyzer

Classifies an email as **phishing**, **spam**, or **legitimate** and shows why, with
evidence for **links**, **sender**, and **language**. Built for small-business
administrators and security reviewers.

Status: **Milestone 1 (Week 1)**. Parsers, feature extractors, tests, CI, and a minimal API.
The classifier is a rule-based placeholder until the TF-IDF + logistic regression
baseline arrives in Week 2.

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
make install
make test
make run        # http://127.0.0.1:8000/docs
```

Try it:

```bash
curl -s localhost:8000/analyze -H 'content-type: application/json' \
  -d "$(python -c 'import json;print(json.dumps({"raw_email":open("data/samples/phish_credential.eml").read()}))')"
```

## Layout

```
app/
  config.py        settings (ATTACHMENTS_ENABLED=false by default, size limits)
  parsing/         EML and CSV import into one Message format
  features/        link / sender / language extractors (pure functions, no network)
  models/          placeholder classifier (swap for the trained baseline in Week 2)
  pipeline.py      analyze_message(): parse -> signals -> verdict -> plain summary
  api/main.py      FastAPI: /health, /model/version, /analyze
scripts/build_dataset.py   merge public datasets (see data/README.md)
data/samples/      synthetic emails used by tests (no real data)
tests/             pytest suite
```

## Safety defaults

- Email HTML is converted to inert text; nothing is executed.
- Links are never fetched. API output shows them defanged (`hxxp://example[.]com`).
- Attachments: metadata only (name, type, size, SHA-256). Contents are never opened.
- Analysis makes no network calls (covered by a test).
- Real email data is git-ignored. Tests use synthetic samples only.

## Week 1 checklist

- [x] Repo layout, CI (ruff + pytest on every PR)
- [x] EML and CSV parsers with limits and row-level errors
- [x] Link, sender, and language extractors with tests
- [x] Minimal `/analyze` endpoint
- [ ] Protect `main` on GitHub: require a pull request review and passing CI
- [ ] Add pre-commit with secret scanning
- [ ] Download datasets and run `make build-data` (data/README.md)

## Next (Week 2)

Baseline model (TF-IDF + logistic regression), fixed-seed evaluation script, CSV and
`.eml` upload endpoints, reputation provider interface (local default, API optional).
