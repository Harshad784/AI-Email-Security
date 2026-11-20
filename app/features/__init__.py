from app.features.language import analyze_language
from app.features.links import analyze_links
from app.features.sender import analyze_sender
from app.parsing.message import Message


def extract_signals(message: Message) -> dict:
    """Run all extractors. Pure functions: no network calls, no storage."""
    return {
        "links": analyze_links(message),
        "sender": analyze_sender(message),
        "language": analyze_language(message),
        "attachments": [
            {"filename": a.filename, "content_type": a.content_type, "size": a.size, "sha256": a.sha256}
            for a in message.attachments
        ],
    }
