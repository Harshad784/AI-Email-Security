from pathlib import Path

from app.parsing import parse_eml_bytes

SAMPLES = Path(__file__).resolve().parent.parent / "data" / "samples"


def load(name: str):
    return parse_eml_bytes((SAMPLES / name).read_bytes())


def raw(name: str) -> str:
    return (SAMPLES / name).read_text()
