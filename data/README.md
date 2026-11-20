# Data

Real email data is never committed. `data/raw/` and `data/processed/` are git-ignored.
Only the synthetic emails in `data/samples/` are tracked and used by tests.

Before using any dataset, record its license in `docs/datasets.md` and spot-check about
50 labels per source. Do not send these emails through a live mail system.

## Sources

| Source | Link | Label |
|---|---|---|
| SpamAssassin public corpus | https://spamassassin.apache.org/old/publiccorpus/ | ham / spam |
| Enron-Spam (CSV) | https://github.com/MWiechmann/enron_spam_data | ham / spam |
| Nazario phishing corpus | http://monkey.org/~jose/phishing/ (verify the page still works) | phishing |
| Phishing Pot (recent test set) | https://github.com/rf-peixoto/phishing_pot | phishing (test only) |

Ready-made merged alternatives: the Kaggle "Phishing Email Dataset" and the IEEE DataPort
multi-source email dataset. Check their licenses too.

## Layout expected by `scripts/build_dataset.py`

```
data/raw/
  spamassassin/easy_ham/...   (extract each .tar.bz2 into a folder; "ham" or "spam" in the folder name)
  spamassassin/spam/...
  enron/enron_spam_data.csv   (columns: Subject, Message, Spam/Ham)
  nazario/*.mbox
  phishing_pot/               (kept separate, never merged)
```

## Build

```
make build-data
python scripts/build_dataset.py --phishing-pot data/raw/phishing_pot
```

The merged CSV has columns `source, label, sender, subject, body, content_hash`.
Duplicates are removed by hash. Train on the merged file and test on the Phishing Pot file.
The script has been tested only on small synthetic data. Check the real files' column names
and folder names on first use.
