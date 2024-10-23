import time


class APIKey:
    def __init__(self, key, holder_name, sleep_value, call_number=0):
        """Initialize an API key with holder's name, sleep value, and call number."""
        self.key = key
        self.holder_name = holder_name
        self.sleep_value = sleep_value  # Time to sleep between calls to avoid rate limiting
        self.call_number = call_number  # Tracks the number of calls allowed per minute with this key
# Example usage
if __name__ == "__main__":
    # Create an instance of APIKey
    APIKey(key="1CGin0RE5GqcHVsq", holder_name="billysnob", sleep_value=2),
    APIKey(key="eTsKvHBUa84tbulK", holder_name="l_valk", sleep_value=2),
    APIKey(key="fY2UwuW4uyscBAKx", holder_name="Sweetanimal",sleep_value=2),
    APIKey(key="Fu4EYMR57L0tSIMS", holder_name="Chainimal", sleep_value=2),
    APIKey(key="lQESuISveRhsiDIH", holder_name="An0nymous", sleep_value=2),
    APIKey(key="DexJF6HJwpDn68xN", holder_name="PierogiPirat", sleep_value=2),
