def tokenizer(chunk: str) -> list[str]:
    """Normalizes the chunk into a list of lowercase words, stripped of punctuation."""
    lower = chunk.casefold()
    cleaned = "".join(char if char.isalnum() or char == "-" else " " for char in lower)
    words = cleaned.split()
    dehyphenated = [word.strip("-").replace("-", "") for word in words]
    tokens = [word for word in dehyphenated if word]
    return tokens