import tiktoken  # type: ignore


def get_tokenizer(model: str):
    try:
        encoding = tiktoken.encoding_for_model(model)
        return encoding.encode
    except Exception:
        try:
            encoding = tiktoken.get_encoding("cl100k_base")
            return encoding.encode
        except Exception:
            return None


def count_tokens(text: str, model: str) -> int:
    tokenizer = get_tokenizer(model)
    if tokenizer:
        return len(tokenizer(text))
    return estimate_tokens(text)


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)
