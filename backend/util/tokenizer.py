from transformers import AutoTokenizer

from config import config

def get_tokens(text: str, tokenizer: str = config.TOKENIZER,  cache_dir: str = config.MODEL_CACHE_DIR) -> list[str]:
    tokenizer = AutoTokenizer.from_pretrained(tokenizer, cache_dir=cache_dir, trust_remote_code=True)
    tokens = tokenizer.encode(text)
    tokens = [tokenizer.decode(token) for token in tokens]
    return tokens


def get_token_count(text: str, tokenizer: str = config.TOKENIZER,  cache_dir: str = config.MODEL_CACHE_DIR) -> list[str]:
    tokenizer = AutoTokenizer.from_pretrained(tokenizer, cache_dir=cache_dir, trust_remote_code=True)
    tokens = tokenizer.encode(text)
    return len(tokens)
