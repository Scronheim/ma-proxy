import re

def clean_string(text) -> str:
    cleaned = re.sub(r'[^a-zA-Z0-9а-яА-ЯёЁ\s]', '', text)
    result = re.sub(r'\s+', '_', cleaned)
    return result
