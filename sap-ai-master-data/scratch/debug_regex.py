import re

m = "give the business partner whose address is delhi"
pat = r"(?:search|find|for|matching|named?)\s+(?:customer|item|warehouse|partner)?\s*['\"]?([A-Za-z0-9_-]{2,25})['\"]?"
s = re.search(pat, m, re.IGNORECASE)
if s:
    print("MATCHED 0:", repr(s.group(0)))
    print("MATCHED 1:", repr(s.group(1)))
else:
    print("NO MATCH")
