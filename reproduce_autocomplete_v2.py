import questionary

def matcher(text=None):
    print(f"Matcher called with: '{text}'")
    return ["foo", "bar", "baz"]

try:
    questionary.autocomplete(
        "Test:",
        choices=matcher,
    ).ask()
except Exception as e:
    print(f"Caught exception: {e}")
