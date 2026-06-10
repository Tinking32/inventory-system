"""Auto-detect product category from name keywords."""

CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "Electronics": [
        "monitor", "mouse", "keyboard", "battery", "batteries",
        "usb", "cable", "hub", "charger", "headphone", "speaker",
        "laptop", "phone", "tablet", "display", "webcam", "printer",
        "router", "modem", "adapter", "dongle", "drive", "ssd",
        "hard disk", "memory", "ram", "cpu", "processor",
    ],
    "Beverages": [
        "coke", "cola", "milo", "coffee", "water", "evian", "tea",
        "juice", "drink", "soda", "milk", "beer", "wine", "nescafe",
        "pepsi", "sprite", "fanta", "red bull", "monster",
        "mineral water", "sparkling", "tonic",
    ],
    "Office Supplies": [
        "paper", "pen", "pencil", "sticky", "note", "stapler",
        "folder", "binder", "envelope", "clip", "tape", "ruler",
        "scissor", "glue", "marker", "highlighter", "eraser",
        "sharpener", "notebook", "diary", "calendar", "file",
        "organizer", "desk", "whiteboard",
    ],
    "Food & Snacks": [
        "noodle", "biscuit", "nuts", "snack", "chocolate", "chips",
        "cracker", "bread", "rice", "cereal", "soup", "candy",
        "cookie", "popcorn", "pretzel", "granola", "protein bar",
        "instant", "ramen", "pasta", "sauce", "oil", "sugar",
        "flour", "butter", "cheese", "yogurt", "frozen",
    ],
}


def suggest_category(product_name: str) -> str | None:
    """Return the best-matching category name for a product name, or None."""
    name_lower = product_name.lower()
    best: tuple[str, int] | None = None  # (category, score)

    for cat, keywords in CATEGORY_KEYWORDS.items():
        score = 0
        for kw in keywords:
            if kw in name_lower:
                score += len(kw)  # longer keyword match = stronger signal
        if score > 0 and (best is None or score > best[1]):
            best = (cat, score)

    return best[0] if best else None
