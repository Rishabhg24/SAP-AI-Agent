import re

tests = [
    "create the vendor name ABC with cardcode V10099 and update the phone of V10099 to 9876543210",
    "create customer XYZ with cardcode C20099 and update the phone of XYZ to 919876543210",
    "create vendor ABC cardcode V10099 phone 9876543210",
    "update the phone of V10099 to 9876543210",
    "phone of C20000 is 9876543210",
    "set phone to 9876543210",
]

pat = re.compile(
    r"\b(?:(?:update|set|change)\s+(?:the\s+)?)?(?:phone|mobile|telephone|contact)(?:\s*(?:number|no|num))?(?:\s+of\s+[A-Za-z0-9_\s&.-]+?)?\s*(?:to|is|:=|=|:|\bas\b|\bwith\b)?\s*['\"]?(\+?\d[\d\s-]{6,16}\d)['\"]?",
    re.IGNORECASE
)

for t in tests:
    m = pat.search(t)
    print(f"Text: '{t}' -> Found: {m.group(1) if m else 'NONE'}")
