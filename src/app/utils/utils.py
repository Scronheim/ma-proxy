import re

def slug_string(text) -> str:
    cleaned = re.sub(r'[^a-zA-Z0-9а-яА-ЯёЁöäüßóøÊ\s]', '', text)
    result = re.sub(r'\s+', '_', cleaned)
    return result
