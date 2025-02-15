import re


def parse_config_string(config: str) -> dict:
    """Parses a key=value string into a dictionary using regex, handling optional fields."""

    pattern = re.compile(r'(\w+)=([^,]+)')
    result = {}

    for match in pattern.findall(config):
        key, value = match
        
        # Convert booleans to actual bool type
        if value.lower() in {'true', 'false'}:
            value = value.lower() == 'true'
        result[key] = value

    return result