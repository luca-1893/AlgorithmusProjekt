def tokenizer(word: str) -> int:
    """Normalizes the chunk into a list of lower words, stripped of punctuation."""
    lower = rawstring.lower()
    separated = lower.replace("-"," ")
    cleaned = "".join(char for char in separated if char.isalnum() or char.isspace())
    words = cleaned.split()
    return words
